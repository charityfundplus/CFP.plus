import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {P2Sandbox} from '../sandbox/p2-service.mjs';
import {createP2HTTP} from '../sandbox/p2-http.mjs';

test('actual loopback HTTP: authenticated Registry -> OpenAI -> ChatGPT packet, CSP assets, denied anonymous and revoked session', async () => {
  const dir = mkdtempSync(join(tmpdir(), 'cfp-registry-socket-')), service = new P2Sandbox(join(dir, 'state.db'));
  const password = 'Synthetic-loopback-password'; service.provision({id: 'viewer', password, role: 'viewer', workspace: 'alpha'});
  const server = createP2HTTP({service});
  try {
    await new Promise(done => server.listen(0, '127.0.0.1', done)); const origin = 'http://127.0.0.1:' + server.address().port;
    let cookie = '';
    const request = (path, body) => fetch(origin + path, {method: body === undefined ? 'GET' : 'POST', headers: {Origin: origin, Cookie: cookie, 'Content-Type': 'application/json'}, ...(body === undefined ? {} : {body: JSON.stringify(body)})});
    assert.equal((await request('/api/core/registry')).status, 401);
    const login = await request('/api/session', {id: 'viewer', password}); assert.equal(login.status, 200); cookie = login.headers.get('set-cookie').split(';')[0];
    const search = await (await request('/api/core/registry?query=OpenAI')).json(); assert.equal(search.records[0].id, '69118');
    assert.equal(search.provenance.sourceBytesVerified, true);
    const profile = await (await request('/api/core/hstdn-openai')).json(); assert.equal(profile.ai[0].id, '691181'); assert.equal(profile.id, null);
    const packet = await (await request('/api/core/chatgpt-project', {id: profile.ai[0].id})).json(); assert.equal(packet.canonicalLink, 'https://cfp.plus/691181'); assert.equal(packet.projectID, null);
    const html = await request('/p2'); assert(html.headers.get('content-security-policy').includes("script-src 'self'")); assert((await html.text()).includes('/registry-office.js'));
    const asset = await request('/registry-office.js'); assert.equal(asset.status, 200); assert(asset.headers.get('content-type').includes('javascript')); assert((await asset.text()).includes('Làm Dự Án tại ChatGPT'));
    assert.equal((await request('/api/core/registry/000')).status, 404); await request('/api/logout', {}); assert.equal((await request('/api/core/registry')).status, 401);
  } finally { await new Promise(done => server.close(done)); service.close(); rmSync(dir, {recursive: true, force: true}); }
});
