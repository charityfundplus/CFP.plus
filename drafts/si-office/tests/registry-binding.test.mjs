import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync, mkdirSync, copyFileSync, writeFileSync, rmSync, existsSync} from 'node:fs';
import {join, dirname} from 'node:path';
import {tmpdir} from 'node:os';
import {fileURLToPath} from 'node:url';
import {bindRegistrySource, loadRegistryReadModel, registrySourceFromEnvironment} from '../core/registry-read-model.mjs';
import {gitRead} from '../scripts/build-provenance.mjs';
import {packRelease} from '../sandbox/release-control.mjs';
import {P2Sandbox} from '../sandbox/p2-service.mjs';
import {serveActiveRelease} from '../scripts/p2-release-serve.mjs';
import {createRegistryClient, projectCoreRecord} from '../public/registry-client.js';
const root = fileURLToPath(new URL('../../../', import.meta.url));
const source = fileURLToPath(new URL('../', import.meta.url));
const revision = gitRead(root, 'rev-parse', 'HEAD').toString().trim();

test('explicit source binding requires absolute path and exact revision; no authority or identity writes', () => {
  assert.equal(registrySourceFromEnvironment({}), undefined);
  for (const input of [{}, {root}, {revision}, {root: 'registry', revision}, {root, revision: 'main'}]) assert.throws(() => bindRegistrySource(input), /BINDING_INVALID/);
  assert.throws(() => registrySourceFromEnvironment({CFP_REGISTRY_SOURCE_ROOT: root}), /BINDING_INVALID/);
  const bound = bindRegistrySource({root, revision})().validation();
  assert.equal(bound.provenance.binding, 'EXPLICIT_EXISTING_REPOSITORY_PIN');
  assert.equal(bound.provenance.sourceOrderPath, 'registry/SYNC_CURRENT_SYSTEM.md');
  assert.equal(bound.provenance.authorityVerified, false); assert.equal(bound.registryWrites, 0);
  assert.throws(() => bindRegistrySource({root, revision: '0'.repeat(40)})(), /SOURCE_UNAVAILABLE/);
});
test('binding rejects modified bytes, moved HEAD, nested root and missing source without fallback', () => {
  const dir = mkdtempSync(join(tmpdir(), 'cfp-binding-pin-'));
  try {
    const paths = loadRegistryReadModel().validation().provenance.files.map(f => f.path);
    for (const path of paths) { mkdirSync(dirname(join(dir, path)), {recursive: true}); copyFileSync(join(root, path), join(dir, path)); }
    const git = (...args) => gitRead(dir, ...args);
    git('init', '-q'); git('config', 'user.name', 'Synthetic Test'); git('config', 'user.email', 'synthetic@example.invalid'); git('add', '.'); git('commit', '-qm', 'fixture');
    const pin = git('rev-parse', 'HEAD').toString().trim(), read = bindRegistrySource({root: dir, revision: pin});
    assert.equal(read().validation().namedBindings, 26);
    writeFileSync(join(dir, paths[0]), '[]'); assert.throws(read, /SOURCE_UNAVAILABLE/);
    copyFileSync(join(root, paths[0]), join(dir, paths[0])); assert.equal(read().validation().namedBindings, 26);
    git('commit', '--allow-empty', '-qm', 'moved'); assert.throws(read, /SOURCE_UNAVAILABLE/);
    assert.throws(() => loadRegistryReadModel(join(dir, 'registry')), /SOURCE_UNAVAILABLE/);
    rmSync(join(dir, paths[1])); assert.throws(() => loadRegistryReadModel(dir), /SOURCE_UNAVAILABLE/);
  } finally { rmSync(dir, {recursive: true, force: true}); }
});

async function releaseFixture(bound, run) {
  const dir = mkdtempSync(join(tmpdir(), 'cfp-bound-release-')); let launched;
  try {
    const release = join(dir, 'release'), digest = packRelease(source, release), database = join(dir, 'state.db');
    assert.equal(existsSync(join(release, 'registry')), false);
    const provision = new P2Sandbox(database); const password = 'Synthetic-release-viewer';
    provision.provision({id: 'viewer', password, role: 'viewer', workspace: 'alpha'}); provision.close();
    writeFileSync(join(dir, 'active.json'), JSON.stringify({release, digest}));
    launched = await serveActiveRelease({directory: dir, database, port: 0, ...(bound ? {registrySource: {root, revision}} : {})});
    const origin = 'http://127.0.0.1:' + launched.server.address().port; let cookie = '';
    const transport = (path, options = {}) => fetch(origin + path, {...options, headers: {Origin: origin, Cookie: cookie, ...options.headers}});
    const client = createRegistryClient({fetchImpl: transport});
    await assert.rejects(client.snapshot(), e => e.status === 401);
    const login = await transport('/api/session', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({id: 'viewer', password})});
    cookie = login.headers.get('set-cookie').split(';')[0];
    await run({client, transport});
  } finally { if (launched) { await new Promise(done => launched.server.close(done)); launched.service.close(); } rmSync(dir, {recursive: true, force: true}); }
}
test('real packaged launcher -> pinned Registry -> UI client: auth, 224 references, OpenAI data, assets and session revocation', async () => {
  await releaseFixture(true, async ({client, transport}) => {
    const snapshot = await client.snapshot(); assert.equal(snapshot.records.length, 224);
    assert.equal(snapshot.records.filter(r => ['ai', 'developer'].includes(r.type)).length, 26);
    const chatgpt = snapshot.records.find(r => r.id === '691181');
    assert.equal(chatgpt.parent_id, '69118'); assert.equal(chatgpt.conflict, true); assert.equal(chatgpt.operationsAllowed, false);
    assert.equal(chatgpt.provenance.sourceRevision, revision);
    const detail = await client.detail('911'); assert(detail.descendants.some(r => r.id === '691181' && r.depth === 3));
    const profile = await client.openai(); assert.equal(profile.contacts[0].url, 'https://help.openai.com/');
    assert.equal(profile.sources.length, 4); assert.equal(profile.id, null); assert.equal(profile.did, null);
    assert.equal(profile.legalRelationshipVerified, false); assert(profile.dataStatus.startsWith('PARTIAL'));
    const packet = await client.project('691181'); assert.equal(packet.projectID, null); assert.equal(packet.parent, '69118');
    const asset = await transport('/registry-client.js'); assert.equal(asset.status, 200); assert((await asset.text()).includes('createRegistryClient'));
    const office = await transport('/registry-office.js'); assert((await office.text()).includes('import {createRegistryClient}'));
    await assert.rejects(client.detail('000'), e => e.status === 404);
    const logout = await transport('/api/logout', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'}); assert.equal(logout.status, 200);
    await assert.rejects(client.snapshot(), e => e.status === 401);
  });
});
test('unbound release returns 503 instead of using its historical duplicate JSON', async () => {
  await releaseFixture(false, async ({client}) => {
    await assert.rejects(client.snapshot(), e => e.status === 503 && e.message === 'REGISTRY_SOURCE_UNAVAILABLE');
  });
});
test('Core client rejects 503, unverifiable metadata and changed revision during pagination', async () => {
  const response = (value, status = 200) => new Response(JSON.stringify(value), {status});
  await assert.rejects(createRegistryClient({fetchImpl: async () => response({error: 'REGISTRY_SOURCE_UNAVAILABLE'}, 503)}).snapshot(), e => e.status === 503);
  await assert.rejects(createRegistryClient({fetchImpl: async () => response({records: []})}).snapshot(), /SOURCE_UNVERIFIED/);
  const actual = loadRegistryReadModel().search({limit: 100}); let calls = 0;
  await assert.rejects(createRegistryClient({fetchImpl: async () => response(calls++ ? {...actual, offset: 100, provenance: {...actual.provenance, revision: '0'.repeat(40)}} : actual)}).snapshot(), /SOURCE_CHANGED/);
});
test('UI projection preserves 0/000/003, explicit Parent and source hash; refuses long IDs without truncation', () => {
  const provenance = {revision, files: [{path: 'registry/source.json', sha256: 'a'.repeat(64), gitBlobSHA: 'b'.repeat(40)}]};
  const record = {type: 'super-pair', sourcePath: 'registry/source.json', issues: [], did: null};
  for (const value of ['0', '000', '003']) {
    const row = projectCoreRecord({...record, id: value, parent: '00'}, provenance);
    assert.equal(row.id, value); assert.equal(row.parent_id, '00'); assert.equal(row.type, 'pair'); assert.equal(row.did, null);
  }
  assert.throws(() => projectCoreRecord({...record, id: '1'.repeat(81), parent: null}, provenance), /UI_ID_LENGTH/);
  assert.throws(() => projectCoreRecord({...record, id: '003', parent: null, sourcePath: '../private'}, provenance), /SOURCE_UNVERIFIED/);
});
