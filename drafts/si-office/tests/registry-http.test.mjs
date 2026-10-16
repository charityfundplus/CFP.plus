import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync, rmSync} from 'node:fs';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {DatabaseSync} from 'node:sqlite';
import {P2Sandbox} from '../sandbox/p2-service.mjs';
import {createP2HTTP} from '../sandbox/p2-http.mjs';
import {requestHandlerFetch} from './harness.mjs';
import {hash} from '../core/common.mjs';
const password = 'Synthetic-registry-password';
function fixture(options = {}) {
  const dir = mkdtempSync(join(tmpdir(), 'cfp-registry-http-')), db = join(dir, 'state.db'), service = new P2Sandbox(db, options);
  for (const [id, role, workspace] of [['viewer', 'viewer', 'alpha'], ['editor', 'editor', 'alpha'], ['outsider', 'editor', 'beta']]) service.provision({id, password, role, workspace});
  const fetch = requestHandlerFetch(createP2HTTP({service}));
  const request = (path, cookie = '', body, headers = {}) => fetch('http://localhost:4174' + path, {method: body === undefined ? 'GET' : 'POST', headers: {Origin: 'http://localhost:4174', Cookie: cookie, 'Content-Type': 'application/json', ...headers}, ...(body === undefined ? {} : {body: JSON.stringify(body)})});
  const login = async id => (await request('/api/session', '', {id, password})).headers.get('set-cookie').split(';')[0];
  return {db, service, request, login, clean() { service.close(); rmSync(dir, {recursive: true, force: true}); }};
}
test('registry routes require existing authentication and preserve 401/400/404, strict inputs and source failure 503', async () => {
  const x = fixture(); try {
    assert.equal((await x.request('/api/core/registry')).status, 401); const cookie = await x.login('viewer');
    assert.equal((await x.request('/api/core/registry/691181', cookie)).status, 200);
    assert.equal((await x.request('/api/core/registry/003', cookie)).status, 404);
    assert.equal((await x.request('/api/core/registry/V', cookie)).status, 400);
    for (const query of ['?limit=101', '?offset=-1', '?limit=1&limit=2', '?private=true', '?chapter=V', '?__proto__=untrusted']) assert.equal((await x.request('/api/core/registry' + query, cookie)).status, 400);
    assert.equal((await x.request('/api/core/hstdn-openai?scope=all', cookie)).status, 400);
  } finally { x.clean(); }
  const bad = fixture({registryFactory() { throw Error('REGISTRY_SOURCE_UNAVAILABLE'); }}); try {
    assert.equal((await bad.request('/api/core/registry', await bad.login('viewer'))).status, 503);
  } finally { bad.clean(); }
});
test('OpenAI profile and ChatGPT packet are read-only for viewers; no identity mutation or external project creation', async () => {
  const x = fixture(); try {
    const cookie = await x.login('viewer'), profile = await (await x.request('/api/core/hstdn-openai', cookie)).json();
    assert.equal(profile.developer.id, '69118'); assert.equal(profile.ai[0].parent, '69118'); assert.equal(profile.id, null);
    const response = await x.request('/api/core/chatgpt-project', cookie, {id: '691181'}); assert.equal(response.status, 200);
    const packet = await response.json(); assert.equal(packet.projectID, null); assert.equal(packet.externalProjectCreated, false);
    assert.equal((await x.request('/api/core/chatgpt-project', cookie, {id: '691181', parent: '0'})).status, 400);
    assert.equal((await x.request('/api/core/chatgpt-project', cookie, {id: 691181})).status, 400);
    assert.equal((await x.request('/api/core/chatgpt-project', cookie, {id: '691181'}, {Origin: 'https://hostile.example'})).status, 403);
    assert.equal((await x.request('/api/core/chatgpt-project', cookie, {id: '691181'}, {Host: 'hostile.example'})).status, 403);
    assert.equal((await x.request('/api/core/registry', cookie, {id: '1'})).status, 404);
    const state = await (await x.request('/api/core/state', cookie)).json(); assert(state.pairs.every(p => p.identity.id === null && p.identity.did === null));
  } finally { x.clean(); }
});
test('public Registry cannot export private task content; response digest is durably bound to the authenticated workspace', async () => {
  const x = fixture(); try {
    const editor = await x.login('editor'), outsider = await x.login('outsider');
    await x.request('/api/core/tasks', editor, {pairKey: 'hub69-content-demo', kind: 'website-draft', title: 'PRIVATE-TASK-ALPHA', text: 'PRIVATE-CUSTOMER-ALPHA', resource: 'website-demo', idempotencyKey: 'private'});
    const response = await (await x.request('/api/core/registry?query=OpenAI', outsider)).json();
    assert.equal(response.records[0].id, '69118'); assert(!JSON.stringify(response).includes('PRIVATE-'));
    const db = new DatabaseSync(x.db, {readOnly: true});
    const event = db.prepare('SELECT value FROM events ORDER BY seq DESC LIMIT 1').get(); db.close();
    const audit = JSON.parse(event.value); assert.equal(audit.workspace, 'beta'); assert.equal(audit.subject, 'outsider');
    assert.equal(audit.action, 'registry:search'); assert.equal(audit.result, 'sha256:' + hash(response));
    const state = await (await x.request('/api/core/state', outsider)).json(); assert.equal(state.tasks.length, 0);
  } finally { x.clean(); }
});
