import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync, mkdirSync, copyFileSync, writeFileSync, rmSync, symlinkSync} from 'node:fs';
import {join, dirname} from 'node:path';
import {tmpdir} from 'node:os';
import {fileURLToPath} from 'node:url';
import {createRegistryReadModel, loadRegistryReadModel} from '../core/registry-read-model.mjs';
import {gitRead} from '../scripts/build-provenance.mjs';
const root = fileURLToPath(new URL('../../../', import.meta.url));
const row = (id, parent = null, name = 'Pair') => ({id, parent, name, type: 'super-pair'});
const model = rows => createRegistryReadModel({rows, provenance: {revision: 'synthetic-fixture', sourceBytesVerified: false}});

test('actual root Registry: hashes, 26 named bindings, 99 countries, explicit OpenAI chain and governance hold', () => {
  const m = loadRegistryReadModel(), v = m.validation(), p = m.openai();
  assert.equal(v.records, 224); assert.equal(v.namedBindings, 26); assert.equal(v.counts.country, 99);
  assert.equal(v.counts.developer, 20); assert.equal(v.counts.ai, 6); assert.equal(v.counts['super-pair'], 0);
  assert.equal(v.provenance.sourceBytesVerified, true); assert.equal(v.provenance.files.length, 6);
  assert.equal(v.roster91Verified, false); assert.equal(v.verifiedOperationalEntities, 0);
  assert.deepEqual([p.country.id, p.aiCountry.id, p.developer.id, p.ai[0].id], ['911', '6911', '69118', '691181']);
  assert.deepEqual([p.aiCountry.parent, p.developer.parent, p.ai[0].parent], ['911', '6911', '69118']);
  assert(p.ai[0].issues.some(f => f.code === 'EXISTING_GOVERNANCE_HOLD'));
  assert.equal(p.id, null); assert.equal(p.parent, null); assert.equal(p.did, null); assert.equal(p.canonical, null);
  assert.equal(p.vaults.length, 6); assert(p.vaults.every(v => !v.connected));
  assert.deepEqual(m.detail('911').descendants.filter(r => r.id === '691181').map(r => r.depth), [3]);
});
test('numeric IDs stay strings: 0, 000, 003, 0031 and long IDs remain distinct; V is not an ID', () => {
  const m = model([row('0'), row('000'), row('003'), row('0031', '003'), row('1234567890123456789012345')]);
  for (const id of ['0', '000', '003', '0031', '1234567890123456789012345']) assert.equal(m.detail(id).record.id, id);
  assert.equal(m.detail('0031').record.parent, '003'); assert.equal(m.detail('003').children[0].id, '0031');
  assert.equal(m.detail('003').record.group, '000');
  for (const id of [0, 3, 'V', ' 003', '003/', '3e2', '../003']) assert.throws(() => m.detail(id), /NUMERIC_ID_STRING_REQUIRED/);
  assert.throws(() => m.detail('3'), /NOT_FOUND/);
});
test('search supports all entity categories, pagination, same-name records and strict fields', () => {
  const m = model([row('001', null, 'Same'), row('002', null, 'Same'), {...row('71'), type: 'hstdn'}, {...row('61'), type: 'si'}]);
  assert.equal(m.search({query: 'same'}).total, 2); assert.equal(m.search({type: 'hstdn'}).records[0].id, '71');
  assert.equal(m.search({type: 'si'}).records[0].id, '61'); assert.equal(m.search({chapter: '0', limit: 1, offset: 1}).records[0].id, '002');
  for (const query of [{limit: 101}, {offset: -1}, {chapter: 'V'}, {type: 'admin'}, {parent: '0'}, {query: 'x'.repeat(161)}, {limit: '2'}]) assert.throws(() => m.search(query), /REGISTRY_/);
});
test('duplicate, missing Parent, cycles and lineage conflicts are findings, never automatic repairs', () => {
  const rows = [row('001'), row('001'), row('002', '999'), row('003', '004'), row('004', '003'), {...row('123'), chapter: '2'},
    {id: '911', type: 'country', name: 'US', parent: null}, {id: '6911', type: 'ai-country', name: 'US AI', parent: '911'},
    {id: '69118', type: 'developer', name: 'OpenAI', parent: '6911', countryID: '984'}];
  const before = structuredClone(rows), m = model(rows), findings = m.validation().findings;
  for (const code of ['DUPLICATE_ID', 'MISSING_PARENT', 'PARENT_CYCLE', 'CHAPTER_MISMATCH', 'COUNTRY_LINEAGE_MISMATCH']) assert(findings.some(f => f.code === code));
  assert.throws(() => m.project('001'), /ID_CONFLICT/); assert.equal(m.detail('002').record.parent, '999');
  assert(m.detail('003').descendants.length <= 1); assert.deepEqual(rows, before);
});
test('ChatGPT action reuses source ID/link, exports public instructions only and never allocates a project ID', () => {
  const m = model([{...row('003', null, 'Pair A'), internalSecret: 'DO-NOT-EXPORT'}]), p = m.project('003');
  assert.equal(p.id, '003'); assert.equal(p.canonicalLink, 'https://cfp.plus/003'); assert.equal(p.projectID, null);
  assert.equal(p.projectURL, null); assert.equal(p.allocatedID, false); assert.equal(p.externalProjectCreated, false);
  assert.equal(p.entryURL, 'https://chatgpt.com/'); assert(p.instructions.includes('ID 003'));
  assert(!JSON.stringify(p).includes('DO-NOT-EXPORT')); assert.equal(p.activationAllowed, false);
  assert(!JSON.stringify(m.detail('003')).includes('DO-NOT-EXPORT'));
});
test('source adapter rejects modified source bytes, missing source and symlinks without using a fallback Registry', () => {
  const dir = mkdtempSync(join(tmpdir(), 'cfp-registry-source-'));
  try {
    const provenance = loadRegistryReadModel().validation().provenance;
    for (const {path} of provenance.files) { mkdirSync(dirname(join(dir, path)), {recursive: true}); copyFileSync(join(root, path), join(dir, path)); }
    const git = (...args) => gitRead(dir, ...args);
    git('init', '-q'); git('config', 'user.name', 'Synthetic Test'); git('config', 'user.email', 'synthetic@example.invalid'); git('add', '.'); git('commit', '-qm', 'fixture');
    assert.equal(loadRegistryReadModel(dir).validation().records, 224);
    const path = provenance.files[0].path; writeFileSync(join(dir, path), '[]');
    assert.throws(() => loadRegistryReadModel(dir), /SOURCE_UNAVAILABLE/); copyFileSync(join(root, path), join(dir, path));
    rmSync(join(dir, path)); symlinkSync(join(root, path), join(dir, path)); assert.throws(() => loadRegistryReadModel(dir), /SOURCE_UNAVAILABLE/);
  } finally { rmSync(dir, {recursive: true, force: true}); }
});
