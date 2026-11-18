// Run: node --test docs/si-ai-platform/tools/super-pair-lifecycle.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { canTransition, activeGate, deriveStage, lifecycleReport, STAGES } from './super-pair-lifecycle.mjs';
import { loadInventory } from './pr124-super-pair-adapter.mjs';

const entry = { id: '4376' };
const bind = { pairKey: 'p', account: 'a' };
const snap = (tasks, status = 'READY') => ({ pairs: [{ key: 'p', status }], tasks });
const task = (status, extra = {}) => ({ key: 'k', pairKey: 'p', owner: 'a', status, ...extra });
const future = new Date(Date.now() + 3600e3).toISOString();
const goodVerification = { runtime: { verified: true, adapter: 'readonly-source', receiptSha256: 'a'.repeat(64) }, access: { verified: true, grantRef: 'grant-1' }, decisionRef: 'HG-17', expiresAt: future };

test('L1 transitions: forward order only; BLOCKED/REVOKED from anywhere; REVOKED terminal', () => {
  for (let i = 0; i < 4; i++) assert.ok(canTransition(STAGES[i], STAGES[i + 1]), STAGES[i]);
  assert.ok(!canTransition('REGISTERED', 'ASSIGNED'));
  assert.ok(!canTransition('READY', 'REVIEWED'));
  assert.ok(!canTransition('EXECUTING', 'ACTIVE'), 'ACTIVE only after REVIEWED');
  assert.ok(canTransition('REVIEWED', 'ACTIVE'));
  assert.ok(canTransition('EXECUTING', 'BLOCKED') && canTransition('ACTIVE', 'REVOKED'));
  assert.ok(!canTransition('REVOKED', 'READY') && !canTransition('REVOKED', 'BLOCKED'));
  assert.ok(canTransition('BLOCKED', 'READY'));
  assert.ok(!canTransition('X', 'READY'));
});

test('L2 stage derived from Core evidence', () => {
  assert.equal(deriveStage(entry, undefined, undefined).stage, 'REGISTERED');
  assert.equal(deriveStage(entry, bind, snap([])).stage, 'READY');
  assert.equal(deriveStage(entry, bind, snap([task('QUEUED')])).stage, 'ASSIGNED');
  assert.equal(deriveStage(entry, bind, snap([task('ACKNOWLEDGED')])).stage, 'ASSIGNED');
  assert.equal(deriveStage(entry, bind, snap([task('RUNNING')])).stage, 'EXECUTING');
  assert.equal(deriveStage(entry, bind, snap([task('AWAITING HUMAN REVIEW')])).stage, 'EXECUTING');
  assert.equal(deriveStage(entry, bind, snap([task('REVIEWED DRAFT', { review: { actor: 'b' } })])).stage, 'REVIEWED');
  assert.equal(deriveStage(entry, bind, snap([task('FAILED')])).stage, 'BLOCKED');
  assert.equal(deriveStage(entry, bind, snap([], 'STOPPED')).stage, 'BLOCKED');
});

test('L3 self-review never counts as REVIEWED', () => {
  assert.equal(deriveStage(entry, bind, snap([task('REVIEWED DRAFT', { review: { actor: 'a' } })])).stage, 'READY');
});

test('L4 ACTIVE gate: all conditions required; mock runtime never qualifies', () => {
  const reviewed = snap([task('REVIEWED DRAFT', { review: { actor: 'b' } })]);
  assert.equal(deriveStage(entry, bind, reviewed, goodVerification).stage, 'ACTIVE');
  for (const [k, v] of [['runtime', { ...goodVerification.runtime, adapter: 'mock-local' }], ['runtime', { ...goodVerification.runtime, verified: false }], ['access', { verified: false }], ['decisionRef', 'approved'], ['expiresAt', '2000-01-01T00:00:00Z']]) {
    const r = deriveStage(entry, bind, reviewed, { ...goodVerification, [k]: v });
    assert.equal(r.stage, 'REVIEWED', k);
    assert.ok(r.active.missing.length > 0);
  }
  assert.ok(!activeGate('EXECUTING', goodVerification).ok);
  assert.equal(deriveStage(entry, bind, reviewed, { ...goodVerification, revoked: true }).stage, 'REVOKED');
});

test('L5 report over the 91 inventory without evidence: all REGISTERED, ACTIVE 0', () => {
  const r = lifecycleReport(loadInventory().rows, {}, undefined, {});
  assert.equal(r.counts.REGISTERED, 91);
  assert.equal(r.counts.ACTIVE, 0);
  assert.equal(r.readOnly, true);
});
