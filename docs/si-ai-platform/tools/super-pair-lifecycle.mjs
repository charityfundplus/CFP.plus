// CFP+ • Super-pair lifecycle (read model) • REVIEW CANDIDATE
// REGISTERED → READY → ASSIGNED → EXECUTING → REVIEWED → (ACTIVE only behind a strict gate)
// Side states: BLOCKED (recoverable), REVOKED (terminal until a new decision).
// Derived from evidence only (source inventory + PR #124 Core snapshot + verification records);
// it never writes and never promotes a state by itself.

export const STAGES = ['REGISTERED', 'READY', 'ASSIGNED', 'EXECUTING', 'REVIEWED', 'ACTIVE'];
export const SIDE = ['BLOCKED', 'REVOKED'];
const FORWARD = { REGISTERED: ['READY'], READY: ['ASSIGNED'], ASSIGNED: ['EXECUTING'], EXECUTING: ['REVIEWED', 'ASSIGNED'], REVIEWED: ['ASSIGNED', 'ACTIVE'], ACTIVE: ['ASSIGNED'], BLOCKED: ['READY'], REVOKED: [] };

/** Is a transition allowed? Any state may go to BLOCKED or REVOKED. */
export function canTransition(from, to) {
  if (![...STAGES, ...SIDE].includes(from) || ![...STAGES, ...SIDE].includes(to)) return false;
  if (to === 'BLOCKED' || to === 'REVOKED') return from !== 'REVOKED';
  return FORWARD[from].includes(to);
}

const DECISION = /^HG-[0-9]{1,4}(-[A-Z0-9]{1,12})?$/;
/**
 * ACTIVE gate: every condition must hold, with evidence. Returns {ok, missing[]}.
 * verification = { runtime:{verified, adapter, receiptSha256}, access:{verified, grantRef},
 *                  decisionRef, expiresAt, revoked }
 */
export function activeGate(stageBefore, v, now = Date.now()) {
  const missing = [];
  if (stageBefore !== 'REVIEWED' && stageBefore !== 'ACTIVE') missing.push('NOT_REVIEWED');
  if (!v?.runtime?.verified) missing.push('RUNTIME_NOT_VERIFIED');
  if (!v?.runtime?.adapter || /mock/i.test(v.runtime.adapter)) missing.push('RUNTIME_IS_MOCK_OR_UNKNOWN');
  if (!/^[0-9a-f]{64}$/.test(v?.runtime?.receiptSha256 ?? '')) missing.push('RUNTIME_RECEIPT_MISSING');
  if (!v?.access?.verified || !v?.access?.grantRef) missing.push('ACCESS_NOT_VERIFIED');
  if (!DECISION.test(v?.decisionRef ?? '')) missing.push('HG_DECISION_MISSING');
  if (!(Date.parse(v?.expiresAt ?? '') > now)) missing.push('DECISION_EXPIRED_OR_MISSING');
  return { ok: missing.length === 0, missing };
}

/**
 * Derive the stage of one super-pair.
 * @param {{id:string}} entry  row from the source inventory (REGISTERED by definition)
 * @param {{pairKey:string, account:string}|undefined} binding  sandbox binding to a PR #124 pair + account
 * @param {object|undefined} snapshot  PR #124 snapshot {pairs:[{key,status}], tasks:[...]}
 * @param {object|undefined} verification  see activeGate
 */
export function deriveStage(entry, binding, snapshot, verification, now = Date.now()) {
  const evidence = [`registered:${entry.id}`];
  if (verification?.revoked) return { id: entry.id, stage: 'REVOKED', evidence, active: { ok: false, missing: ['REVOKED'] } };
  let stage = 'REGISTERED';
  const pair = binding && snapshot?.pairs?.find((p) => p.key === binding.pairKey);
  if (pair) {
    if (pair.status !== 'READY') return { id: entry.id, stage: 'BLOCKED', evidence: [...evidence, `pair:${pair.key}:${pair.status}`], active: { ok: false, missing: ['PAIR_NOT_READY'] } };
    stage = 'READY'; evidence.push(`pair:${pair.key}:READY`, `account:${binding.account}`);
    const mine = (snapshot.tasks || []).filter((t) => t.pairKey === binding.pairKey && t.owner === binding.account);
    const last = mine[mine.length - 1];
    if (last) {
      evidence.push(`task:${last.key}:${last.status}`);
      if (['BLOCKED', 'FAILED'].includes(last.status)) return { id: entry.id, stage: 'BLOCKED', evidence, active: { ok: false, missing: ['TASK_' + last.status] } };
      if (['QUEUED', 'ACKNOWLEDGED'].includes(last.status)) stage = 'ASSIGNED';
      else if (['RUNNING', 'AWAITING HUMAN REVIEW'].includes(last.status)) stage = 'EXECUTING';
      else if (last.status === 'REVIEWED DRAFT' && last.review?.actor && last.review.actor !== last.owner) stage = 'REVIEWED';
      else if (last.status === 'INTERRUPTED' || last.status === 'REJECTED DRAFT') stage = 'READY';
    }
  }
  const gate = activeGate(stage, verification, now);
  return { id: entry.id, stage: gate.ok ? 'ACTIVE' : stage, evidence, active: gate };
}

export function lifecycleReport(inventoryRows, bindings, snapshot, verifications = {}, now = Date.now()) {
  const rows = inventoryRows.map((r) => deriveStage(r, bindings[r.id], snapshot, verifications[r.id], now));
  const counts = Object.fromEntries([...STAGES, ...SIDE].map((s) => [s, rows.filter((x) => x.stage === s).length]));
  return { readOnly: true, counts, rows };
}
