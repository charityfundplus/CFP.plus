// Run: node --test docs/si-ai-platform/tools/work-modules.test.mjs
// With CFP_PR124_ROOT set, the pilot lifecycle test also runs against PR #124's P2Sandbox.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { githubRegistryAudit, notionCrossCheck, classifyAndJoin, groupOf, sha256 } from './work-modules.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const pr124 = process.env.CFP_PR124_ROOT;

test('modules are deterministic (same input → same SHA-256)', () => {
  for (const f of [githubRegistryAudit, notionCrossCheck, classifyAndJoin]) assert.equal(sha256(f()), sha256(f()));
});

test('GitHub audit finds the known Gemini / Meta / DeepMind ID conflicts', () => {
  const r = githubRegistryAudit();
  assert.equal(r.readOnly, true);
  assert.equal(r.counts.registryEntities, 26);
  const multi = r.findings.filter((f) => f.code === 'SAME_NAME_MULTIPLE_IDS').map((f) => f.ids.join('/'));
  assert.ok(multi.includes('691141/6911421'));
  assert.ok(multi.includes('69115/691151'));
  assert.ok(r.findings.some((f) => f.code === 'REGISTRY_NAME_VS_PAGE_TITLE' && f.id === '691141' && /Google Cloud AI/.test(f.pageTitle)));
});

test('Notion cross-check finds 333 duplicate, 2624 outlier, 2 missing links, 8 additions, new-table title drift', () => {
  const r = notionCrossCheck();
  const by = (c) => r.findings.filter((f) => f.code === c);
  assert.deepEqual(by('DUPLICATE_SOURCE_PROFILE').map((f) => f.id), ['333']);
  assert.deepEqual(by('IN_DANH_MUC_NOT_IN_91').map((f) => f.id), ['2624']);
  assert.deepEqual(by('NOTION_LINK_MISSING').map((f) => f.id).sort(), ['2273', '2588']);
  assert.deepEqual(by('IN_91_NOT_IN_BAN_DO').map((f) => f.id).sort(), ['2273', '2588', '2838', '2877', '330', '4347', '4742', '5835']);
  assert.equal(r.counts.banDo, 84);
  assert.equal(r.counts.banDoUniqueIds, 83);
  assert.equal(r.counts.bangLink91, 91);
  assert.deepEqual(by('BANG_LINK_URL_DIFFERS'), []);
  assert.deepEqual(by('LINKED_PAGE_TITLE_DIFFERS_FROM_NAME').map((f) => f.id), ['333', '4742', '5284']);
});

test('classification covers all 91 and uses PR #124 group display rule', () => {
  const r = classifyAndJoin();
  assert.equal(r.rows.length, 91);
  assert.equal(groupOf('003'), '000');
  assert.equal(groupOf('5284'), '135');
  assert.equal(groupOf('6969'), '246');
  assert.equal(groupOf('8882'), '789');
  assert.equal(Object.values(r.counts.byGroup).reduce((a, b) => a + b, 0), 91);
  assert.ok(r.rows.every((x) => !/ID_CHANGE/.test(x.proposedAction)));
});

test('pilot: create → ACK/run → independent review → audit, with denials', { skip: pr124 ? false : 'CFP_PR124_ROOT not set' }, () => {
  const out = mkdtempSync(join(tmpdir(), 'cfp-pilot-test-'));
  try {
    execFileSync(process.execPath, [join(here, 'pilot-run.mjs'), out], { env: { ...process.env }, stdio: 'pipe' });
    const p = JSON.parse(readFileSync(join(out, 'pilot-run.json'), 'utf8'));
    assert.equal(p.tasksCompleted, 3);
    assert.ok(p.tasks.every((t) => t.reportSha256 === t.recheckSha256));
    assert.ok(p.coreTaskStatuses.every((t) => t.owner !== t.reviewer && t.productionApproved === false));
    assert.equal(p.lifecycle.filter((l) => l.result === 'DENIED').length, 4);
    assert.equal(p.lifecycle.filter((l) => l.result === 'UNEXPECTED_ALLOW').length, 0);
    assert.ok(p.lifecycle.filter((l) => l.action.startsWith('runTask')).every((l) => l.outputBindsReportSha === true));
    assert.ok(Number.isInteger(p.auditCheckpoint.sequence) && /^[0-9a-f]{64}$/.test(p.auditCheckpoint.sha256));
    assert.equal(p.core.pr124BranchModified, false);
    if (p.ackMode.startsWith('ackTask')) assert.match(p.core.localPatch.sha256, /^[0-9a-f]{64}$/);
    assert.equal(p.lifecycleCounts.ACTIVE, 0);
    assert.equal(p.lifecycleCounts.REVIEWED + p.lifecycleCounts.READY + p.lifecycleCounts.REGISTERED, 91);
    if (p.ackMode.startsWith('ackTask')) assert.equal(p.lifecycle.filter((l) => l.action === 'ackTask' && l.result === 'ACKNOWLEDGED').length, 3);
  } finally { rmSync(out, { recursive: true, force: true }); }
});
