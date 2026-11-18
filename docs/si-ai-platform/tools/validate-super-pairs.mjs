#!/usr/bin/env node
// CFP+ • Siêu Bộ Đôi tree validator • REVIEW CANDIDATE
// Zero dependencies (Node >= 22), same runtime family as PR #124 drafts/si-office.
// Read-only: never writes Registry data, never allocates IDs.

import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

export const STATUSES = ['PLANNED', 'RESERVED', 'PROPOSED', 'BOUND', 'ACTIVE'];
const POSITION_RE = /^[0-9](\.[0-9])*$/;
const NODE_KEYS = new Set(['planned_position', 'tier', 'parent_position', 'chapter', 'chapter_name_source',
  'anchor_page', 'canonical_id', 'governance_decision', 'status', 'components', 'capabilities', 'lineage',
  'grants', 'evidence', 'notes']);
const REQUIRED = ['planned_position', 'tier', 'parent_position', 'chapter', 'canonical_id', 'status',
  'components', 'capabilities', 'lineage', 'grants', 'evidence'];

/** Theoretical capacity per tier. mode 'A': digits 0–9 all usable; mode 'B': 0 reserved for expansion. */
export function capacity(tiers, mode) {
  if (!['A', 'B'].includes(mode)) throw new Error(`unknown zero mode: ${mode}`);
  const branching = mode === 'A' ? 10 : 9;
  const perTier = [];
  for (let t = 1; t <= tiers; t++) perTier.push(t === 1 ? 10 : 10 * branching ** (t - 1));
  return { mode, perTier, total: perTier.reduce((a, b) => a + b, 0) };
}

/**
 * Validate a list of planning nodes.
 * @param {object[]} nodes
 * @param {{zeroMode?: 'A'|'B'|null, knownIds?: Set<string>}} opts
 * @returns {{ok:boolean, errors:{position:string, code:string, message:string}[], counts:object}}
 */
export function validateNodes(nodes, { zeroMode = null, knownIds = new Set() } = {}) {
  const errors = [];
  const err = (position, code, message) => errors.push({ position: String(position), code, message });
  if (!Array.isArray(nodes)) return { ok: false, errors: [{ position: '-', code: 'NOT_ARRAY', message: 'nodes must be an array' }], counts: {} };

  const byPos = new Map();
  for (const n of nodes) {
    const p = n?.planned_position;
    if (byPos.has(p)) err(p, 'DUPLICATE_POSITION', 'planned_position appears more than once');
    else byPos.set(p, n);
  }
  const seenIds = new Map();

  for (const n of nodes) {
    const p = n?.planned_position ?? '?';
    for (const k of REQUIRED) if (!(k in (n ?? {}))) err(p, 'MISSING_FIELD', `missing ${k}`);
    for (const k of Object.keys(n ?? {})) if (!NODE_KEYS.has(k)) err(p, 'UNKNOWN_FIELD', `unknown field ${k}`);
    if (typeof p !== 'string' || !POSITION_RE.test(p)) { err(p, 'BAD_POSITION', 'planned_position must look like 6 or 6.1.2'); continue; }

    const segs = p.split('.');
    if (n.tier !== segs.length) err(p, 'TIER_MISMATCH', `tier ${n.tier} != ${segs.length} segments`);
    if (n.chapter !== Number(segs[0])) err(p, 'CHAPTER_MISMATCH', `chapter ${n.chapter} != first segment ${segs[0]}`);
    if (zeroMode === 'B' && segs.slice(1).includes('0')) err(p, 'ZERO_RESERVED', 'mode B: segment 0 is reserved for expansion');

    // Parent must be explicit AND consistent with the prefix (see conflict C6).
    const expectedParent = segs.length === 1 ? null : segs.slice(0, -1).join('.');
    if (n.parent_position !== expectedParent) err(p, 'PARENT_MISMATCH', `parent_position must be ${expectedParent}`);
    else if (expectedParent !== null && !byPos.has(expectedParent)) err(p, 'ORPHAN', `parent ${expectedParent} not present`);

    if (!STATUSES.includes(n.status)) err(p, 'BAD_STATUS', `status must be one of ${STATUSES.join(', ')}`);

    // No self-generated IDs: an ID must already exist in the Registry and be backed by a decision.
    if (n.canonical_id !== null && n.canonical_id !== undefined) {
      if (!/^[0-9]+$/.test(String(n.canonical_id))) err(p, 'BAD_ID', 'canonical_id must be numeric string or null');
      else if (!knownIds.has(String(n.canonical_id))) err(p, 'UNKNOWN_ID', `canonical_id ${n.canonical_id} not found in Registry (no self-allocation)`);
      if (!n.governance_decision) err(p, 'ID_WITHOUT_DECISION', 'canonical_id requires governance_decision');
      const prev = seenIds.get(String(n.canonical_id));
      if (prev) err(p, 'DUPLICATE_ID', `canonical_id also used by ${prev}`);
      seenIds.set(String(n.canonical_id), p);
    }
    if ((n.status === 'BOUND' || n.status === 'ACTIVE') && !n.canonical_id) err(p, 'STATUS_WITHOUT_ID', `${n.status} requires canonical_id`);
    if (n.status === 'ACTIVE' && !(Array.isArray(n.evidence) && n.evidence.length)) err(p, 'ACTIVE_WITHOUT_EVIDENCE', 'ACTIVE requires evidence');
    if (n.status === 'ACTIVE' && !(n.components?.si_ai && n.components?.super_software)) err(p, 'ACTIVE_WITHOUT_PAIR', 'ACTIVE requires both SI AI and Siêu Phần Mềm');

    // Permissions never inherit; grants need a decision.
    if (n.lineage?.inherits_permissions !== false) err(p, 'PERMISSION_INHERITANCE', 'lineage.inherits_permissions must be false');
    if (Array.isArray(n.grants) && n.grants.length && !n.governance_decision) err(p, 'GRANT_WITHOUT_DECISION', 'grants require governance_decision');

    // Standards inherit and cannot be dropped by a child.
    if (expectedParent && byPos.has(expectedParent)) {
      const parentStd = byPos.get(expectedParent).lineage?.inherits_standards ?? [];
      const mine = new Set(n.lineage?.inherits_standards ?? []);
      const dropped = parentStd.filter((s) => !mine.has(s));
      if (dropped.length) err(p, 'STANDARD_DROPPED', `child drops parent standards: ${dropped.join('; ')}`);
    }
  }

  const perTier = {};
  for (const n of nodes) if (typeof n?.tier === 'number') perTier[n.tier] = (perTier[n.tier] ?? 0) + 1;
  const status = {};
  for (const n of nodes) status[n?.status] = (status[n?.status] ?? 0) + 1;
  return { ok: errors.length === 0, errors, counts: { nodes: nodes.length, perTier, status } };
}

/** Collect numeric IDs that already exist in the repository (route folders + registry JSON keys). */
export function collectKnownIds(repoRoot) {
  const ids = new Set();
  for (const name of readdirSync(repoRoot)) {
    if (/^[0-9]+$/.test(name) && statSync(join(repoRoot, name)).isDirectory()) ids.add(name);
  }
  const reg = join(repoRoot, 'registry', 'ai-entity-registry.json');
  if (existsSync(reg)) for (const k of Object.keys(JSON.parse(readFileSync(reg, 'utf8')))) if (/^[0-9]+$/.test(k)) ids.add(k);
  return ids;
}

function main() {
  const here = dirname(fileURLToPath(import.meta.url));
  const file = process.argv[2] ?? join(here, '..', 'data', 'super-pair-plan.json');
  const repoRoot = resolve(here, '..', '..', '..');
  const doc = JSON.parse(readFileSync(file, 'utf8'));
  const knownIds = collectKnownIds(repoRoot);
  const report = {
    file,
    knownRegistryIds: knownIds.size,
    validation: validateNodes(doc.nodes, { zeroMode: null, knownIds }),
    capacity3Tiers: { A: capacity(3, 'A'), B: capacity(3, 'B') },
    readOnly: true,
    idsAllocated: 0,
  };
  console.log(JSON.stringify(report, null, 2));
  process.exitCode = report.validation.ok ? 0 : 1;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
