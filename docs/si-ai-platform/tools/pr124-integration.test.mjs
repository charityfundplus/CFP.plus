// Integration: Notion super-pair inventory running inside PR #124's own Registry read model.
// Run: CFP_PR124_ROOT=/path/to/pr124-checkout node --test docs/si-ai-platform/tools/pr124-integration.test.mjs
// Without CFP_PR124_ROOT the PR #124 tests are reported as SKIPPED (never as PASS).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { loadInventory, toRegistryRows, buildSuperPairReadModel, PR124_PINNED_SHA } from './pr124-super-pair-adapter.mjs';
import { collectKnownIds } from './validate-super-pairs.mjs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = process.env.CFP_PR124_ROOT;
const skip = root ? false : 'CFP_PR124_ROOT not set — PR #124 checkout unavailable';
const inv = loadInventory();
const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..', '..');

test('inventory: 91 source rows, chapter counts match Notion chapter pages', () => {
  assert.equal(inv.rows.length, 91);
  const counts = {};
  for (const r of inv.rows) counts[r.chapter] = (counts[r.chapter] ?? 0) + 1;
  assert.deepEqual(counts, { 0: 5, 1: 4, 2: 18, 3: 15, 4: 6, 5: 12, 6: 9, 7: 8, 8: 8, 9: 6 });
  assert.deepEqual(inv.rows.filter((r) => !r.notion_url).map((r) => r.id), ['2273', '2588']);
  assert.ok(inv.rows.every((r) => r.id[0] === r.chapter && r.parent === null));
  assert.equal(new Set(inv.rows.map((r) => r.id)).size, 91, 'no duplicate IDs in inventory');
});

test('adapter rows use PR #124 shape and never infer Parent', () => {
  const rows = toRegistryRows(inv);
  assert.ok(rows.every((r) => r.type === 'super-pair' && r.parent === null && /^\d+$/.test(r.id)));
  assert.ok(rows.every((r) => Object.keys(r).every((k) => ['id', 'type', 'name', 'parent', 'chapter', 'sourceStatus', 'sourcePath', 'description'].includes(k))));
});

test('pinned PR #124 checkout is at the expected SHA', { skip }, () => {
  const head = execFileSync('git', ['-C', root, 'rev-parse', 'HEAD']).toString().trim();
  assert.equal(head, PR124_PINNED_SHA);
});

test('PR #124 read model accepts all 91 super-pair rows with 0 findings', { skip }, async () => {
  const model = await buildSuperPairReadModel({ pr124Root: root });
  const v = model.validation();
  assert.equal(v.records, 91);
  assert.equal(v.counts['super-pair'], 91);
  assert.deepEqual(v.findings, []);
  assert.equal(v.readOnly, true);
  assert.equal(v.registryWrites, 0);
  assert.equal(v.activationAllowed, false);
  assert.equal(v.verifiedOperationalEntities, 0);
});

test('search by chapter and type returns Notion chapter counts', { skip }, async () => {
  const model = await buildSuperPairReadModel({ pr124Root: root });
  assert.equal(model.search({ type: 'super-pair', chapter: '2', limit: 100 }).total, 18);
  assert.equal(model.search({ type: 'super-pair', chapter: '6', limit: 100 }).total, 9);
  const hit = model.search({ query: 'Luật Thép', limit: 5 });
  assert.deepEqual(hit.records.map((r) => r.id), ['4742']);
});

test('detail keeps every record unverified and preserves leading zeros', { skip }, async () => {
  const model = await buildSuperPairReadModel({ pr124Root: root });
  const d = model.detail('003');
  assert.equal(d.record.id, '003');
  assert.equal(d.record.canonicalLink, 'https://cfp.plus/003');
  assert.equal(d.record.identityVerified, false);
  assert.equal(d.record.operationallyActive, false);
  assert.equal(d.children.length, 0, 'no children because no Parent is inferred');
  assert.throws(() => model.detail('99999999'), /REGISTRY_NOT_FOUND/);
  assert.throws(() => model.detail('6.1'), /NUMERIC_ID_STRING_REQUIRED/);
});

test('group display follows PR #124 (000/135/246/789); V/D not emitted as numeric IDs', { skip }, async () => {
  const model = await buildSuperPairReadModel({ pr124Root: root });
  const groups = new Set(model.search({ limit: 100 }).records.map((r) => r.group));
  assert.ok([...groups].every((g) => ['000', '135', '246', '789'].includes(g)));
});

test('IDs shared with existing repository entities are reported, not re-allocated', () => {
  const known = collectKnownIds(repoRoot);
  const shared = inv.rows.filter((r) => known.has(r.id)).map((r) => r.id);
  // A super-pair profile is a role on an existing numeric ID (Notion rule), so overlap is expected.
  assert.ok(shared.includes('69') === false);
  assert.ok(shared.length >= 19);
});
