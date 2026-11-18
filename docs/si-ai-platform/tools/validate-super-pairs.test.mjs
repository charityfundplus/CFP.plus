// Run: node --test docs/si-ai-platform/tools/
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { validateNodes, capacity, collectKnownIds } from './validate-super-pairs.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const plan = JSON.parse(readFileSync(join(here, '..', 'data', 'super-pair-plan.json'), 'utf8'));
const repoRoot = resolve(here, '..', '..', '..');
const STD = ['Hiến Chương', 'Luật Thép'];

const node = (pos, extra = {}) => {
  const segs = pos.split('.');
  return {
    planned_position: pos, tier: segs.length, parent_position: segs.length === 1 ? null : segs.slice(0, -1).join('.'),
    chapter: Number(segs[0]), canonical_id: null, status: 'PLANNED',
    components: { si_ai: null, super_software: null }, capabilities: { primary: 'x', secondary: [] },
    lineage: { inherits_standards: STD, inherits_permissions: false }, grants: [], evidence: [], ...extra,
  };
};
const codes = (r) => r.errors.map((e) => e.code);

test('shipped plan: 10 tier-1 slots, valid, no IDs allocated', () => {
  const r = validateNodes(plan.nodes, { knownIds: collectKnownIds(repoRoot) });
  assert.deepEqual(r.errors, []);
  assert.equal(r.counts.nodes, 10);
  assert.deepEqual(r.counts.perTier, { 1: 10 });
  assert.ok(plan.nodes.every((n) => n.canonical_id === null && n.status === 'PLANNED'));
  assert.deepEqual(plan.nodes.map((n) => n.chapter), [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]);
});

test('capacity: mode A = 1.110, mode B = 910, recursion unbounded', () => {
  assert.deepEqual(capacity(3, 'A').perTier, [10, 100, 1000]);
  assert.equal(capacity(3, 'A').total, 1110);
  assert.equal(capacity(3, 'B').total, 910);
  assert.equal(capacity(6, 'A').total, 1111110);
  assert.throws(() => capacity(3, 'C'));
});

test('deep recursion (tier 7) validates without depth limit', () => {
  const chain = ['6', '6.1', '6.1.2', '6.1.2.3', '6.1.2.3.4', '6.1.2.3.4.5', '6.1.2.3.4.5.6'].map((p) => node(p));
  assert.equal(validateNodes(chain).ok, true);
});

test('rejects duplicate positions, orphans, wrong parent and tier', () => {
  assert.ok(codes(validateNodes([node('6'), node('6')])).includes('DUPLICATE_POSITION'));
  assert.ok(codes(validateNodes([node('6.1')])).includes('ORPHAN'));
  assert.ok(codes(validateNodes([node('6'), node('6.1', { parent_position: '5' })])).includes('PARENT_MISMATCH'));
  assert.ok(codes(validateNodes([node('6', { tier: 2 })])).includes('TIER_MISMATCH'));
  assert.ok(codes(validateNodes([node('6', { chapter: 5 })])).includes('CHAPTER_MISMATCH'));
  assert.ok(codes(validateNodes([node('61')])).includes('BAD_POSITION'));
});

test('zero mode B reserves segment 0; mode A allows it', () => {
  const nodes = [node('6'), node('6.0')];
  assert.ok(codes(validateNodes(nodes, { zeroMode: 'B' })).includes('ZERO_RESERVED'));
  assert.equal(validateNodes(nodes, { zeroMode: 'A' }).ok, true);
});

test('no self-allocated IDs: unknown ID, missing decision, duplicates rejected', () => {
  const known = new Set(['6', '69']);
  assert.ok(codes(validateNodes([node('6', { canonical_id: '999999', governance_decision: 'GD-1' })], { knownIds: known })).includes('UNKNOWN_ID'));
  assert.ok(codes(validateNodes([node('6', { canonical_id: '6' })], { knownIds: known })).includes('ID_WITHOUT_DECISION'));
  const dup = [node('6', { canonical_id: '6', governance_decision: 'GD-1' }), node('6.1', { canonical_id: '6', governance_decision: 'GD-1' })];
  assert.ok(codes(validateNodes(dup, { knownIds: known })).includes('DUPLICATE_ID'));
  assert.equal(validateNodes([node('6', { canonical_id: '6', governance_decision: 'GD-1', status: 'BOUND' })], { knownIds: known }).ok, true);
});

test('status gates: BOUND/ACTIVE need ID; ACTIVE needs evidence and both components', () => {
  assert.ok(codes(validateNodes([node('6', { status: 'BOUND' })])).includes('STATUS_WITHOUT_ID'));
  const known = new Set(['6']);
  const active = node('6', { status: 'ACTIVE', canonical_id: '6', governance_decision: 'GD-1' });
  const c = codes(validateNodes([active], { knownIds: known }));
  assert.ok(c.includes('ACTIVE_WITHOUT_EVIDENCE') && c.includes('ACTIVE_WITHOUT_PAIR'));
  assert.ok(codes(validateNodes([node('6', { status: 'LIVE' })])).includes('BAD_STATUS'));
});

test('permissions never inherit; grants need a decision', () => {
  assert.ok(codes(validateNodes([node('6', { lineage: { inherits_standards: STD, inherits_permissions: true } })])).includes('PERMISSION_INHERITANCE'));
  assert.ok(codes(validateNodes([node('6', { grants: [{ action: 'draft.write' }] })])).includes('GRANT_WITHOUT_DECISION'));
});

test('child cannot drop a parent standard but may add stricter ones', () => {
  const parent = node('6');
  const drop = node('6.1', { lineage: { inherits_standards: ['Hiến Chương'], inherits_permissions: false } });
  assert.ok(codes(validateNodes([parent, drop])).includes('STANDARD_DROPPED'));
  const add = node('6.1', { lineage: { inherits_standards: [...STD, 'Chuẩn riêng Chương 6'], inherits_permissions: false } });
  assert.equal(validateNodes([parent, add]).ok, true);
});

test('unknown fields rejected (schema additionalProperties=false parity)', () => {
  assert.ok(codes(validateNodes([node('6', { owner_override: true })])).includes('UNKNOWN_FIELD'));
});

test('known IDs include existing route folders and registry keys', () => {
  const ids = collectKnownIds(repoRoot);
  for (const id of ['69', '28882', '8682', '267', '6911']) assert.ok(ids.has(id), id);
  assert.ok(!ids.has('8882'), '8882 has no folder on this revision (conflict C3)');
});
