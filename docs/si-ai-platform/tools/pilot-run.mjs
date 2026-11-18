#!/usr/bin/env node
// CFP+ • P4 pilot • READ ONLY work + PR #124 P2Sandbox task lifecycle.
// Usage: CFP_PR124_ROOT=/path/to/pr124-checkout node docs/si-ai-platform/tools/pilot-run.mjs <outDir>
//
// What is real:   the three work modules read the actual repository / Notion snapshots and produce
//                 findings; reports are written with SHA-256; an independent reviewer account re-runs
//                 each module and only acknowledges when the hash matches.
// What is reused: task create / run / independent review / audit chain come from PR #124's own
//                 P2Sandbox + CoreEngine (pinned SHA). No second backend, no Core modification.
// What is NOT:    PR #124 keeps its SI adapter mock-only by design ("do not activate real reads without
//                 separate approval"), so the Core run step echoes the bound summary; the real work runs
//                 outside the Core and is bound by hash. Nothing is written to any Registry or store.
import { mkdirSync, writeFileSync, mkdtempSync, rmSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { tmpdir } from 'node:os';
import { pathToFileURL } from 'node:url';
import { randomBytes } from 'node:crypto';
import { githubRegistryAudit, notionCrossCheck, classifyAndJoin, sha256 } from './work-modules.mjs';
import { PR124_PINNED_SHA } from './pr124-super-pair-adapter.mjs';

const pr124 = process.env.CFP_PR124_ROOT;
if (!pr124) { console.error('CFP_PR124_ROOT required'); process.exit(2); }
const out = resolve(process.argv[2] || 'pilot-out');
mkdirSync(out, { recursive: true });
const { P2Sandbox } = await import(pathToFileURL(join(pr124, 'drafts/si-office/sandbox/p2-service.mjs')).href);

// Super-pair roles for this pilot (role labels from the Notion ACK matrix; IDs from the 91 source list).
const ROLES = {
  executor: { account: 'sbd-4376-idso', superPair: '4376 • ID Số', role: 'editor', duty: 'Thực hiện kiểm kê ID và đối chiếu' },
  reviewer: { account: 'sbd-5284-kiemchung', superPair: '5284 • Kiểm Chứng Tổng Hợp', role: 'reviewer', duty: 'Kiểm chứng độc lập, chạy lại và so mã băm' },
  observer: { account: 'cmp-267-dieuphoi', superPair: '267 • CMP', role: 'viewer', duty: 'Điều phối, chỉ đọc (kiểm tra quyền tối thiểu)' },
};
const MODULES = [
  { key: 'T1', title: 'GitHub • Kiểm kê Registry AI và trang route', run: githubRegistryAudit, source: 'GitHub (repo checkout)' },
  { key: 'T2', title: 'Notion • Đối chiếu 3 danh sách Siêu Bộ Đôi', run: notionCrossCheck, source: 'Notion (snapshot đọc qua connector)' },
  { key: 'T3', title: 'Phân loại 91 Siêu Bộ Đôi theo 5 Nhóm, 10 Chương + Web', run: classifyAndJoin, source: 'GitHub + Web (cfp.plus)' },
];

const dir = mkdtempSync(join(tmpdir(), 'cfp-pilot-'));
const password = randomBytes(24).toString('hex'); // never written to disk or output
const s = new P2Sandbox(join(dir, 'state.db'));
const log = [];
const step = (task, actor, action, result, extra = {}) => log.push({ time: new Date().toISOString(), task, actor, action, result, ...extra });
const results = [];
try {
  for (const r of Object.values(ROLES)) s.provision({ id: r.account, password, role: r.role, workspace: 'pilot-hub69', maintainer: false, pairs: ['hub69-content-demo'] });
  const tok = Object.fromEntries(Object.entries(ROLES).map(([k, r]) => [k, s.login(r.account, password)]));

  // Least-privilege checks (must be DENIED).
  try { await s.execute(tok.observer, 'createTask', { pairKey: 'hub69-content-demo', input: { kind: 'registry-audit', title: 'x', text: 'x', resource: 'website-demo', scenario: 'normal' } }, { idempotencyKey: 'deny-1' }); step('-', ROLES.observer.account, 'createTask', 'UNEXPECTED_ALLOW'); }
  catch (e) { step('-', ROLES.observer.account, 'createTask', 'DENIED', { reason: e.message }); }

  for (const m of MODULES) {
    // 1. Intake: executor runs the real module (read only) and writes the report.
    const report = m.run();
    const body = JSON.stringify(report, null, 2) + '\n';
    const reportSha = sha256(body);
    writeFileSync(join(out, `${m.key}-${report.module}.json`), body);
    const top = (report.findings || []).slice(0, 6).map((f) => `${f.code} ${f.id ?? f.name ?? ''}`).join('; ');
    const summary = `${m.key} • ${m.title}\nNguồn: ${m.source}\nSiêu Bộ Đôi thực hiện: ${ROLES.executor.superPair}\nKết quả: ${JSON.stringify(report.counts)}\nVí dụ: ${top}\nBáo cáo: ${m.key}-${report.module}.json sha256:${reportSha}\nREAD ONLY • không ghi Registry • không đổi ID`.slice(0, 2900);

    // 2. Task created in PR #124 Core (identity, owner, source, status are Core-managed).
    const task = await s.execute(tok.executor, 'createTask', { pairKey: 'hub69-content-demo', input: { kind: 'registry-audit', title: m.title, text: summary, resource: 'website-demo', scenario: 'normal' } }, { idempotencyKey: 'pilot-' + m.key });
    step(m.key, ROLES.executor.account, 'createTask', task.status, { taskKey: task.key });

    // 3. ACK = executor's authenticated run intent (Core writes a durable run-intent event), 4. execution.
    const run = await s.execute(tok.executor, 'runTask', { taskKey: task.key });
    step(m.key, ROLES.executor.account, 'runTask (ACK + run)', run.status, { checks: run.checks?.length ?? 0, outputBindsReportSha: (run.output?.text || '').includes(reportSha) });

    // 5. Self-review must be refused.
    try { await s.execute(tok.executor, 'reviewTask', { taskKey: task.key, verdict: 'acknowledge-draft' }); step(m.key, ROLES.executor.account, 'self-review', 'UNEXPECTED_ALLOW'); }
    catch (e) { step(m.key, ROLES.executor.account, 'self-review', 'DENIED', { reason: e.message }); }

    // 6. Independent cross-check: reviewer re-runs the module and compares the hash.
    const recheck = sha256(JSON.stringify(m.run(), null, 2) + '\n');
    const verdict = recheck === reportSha && (run.output?.text || '').includes(reportSha) ? 'acknowledge-draft' : 'reject-draft';
    const reviewed = await s.execute(tok.reviewer, 'reviewTask', { taskKey: task.key, verdict });
    step(m.key, ROLES.reviewer.account, 'reviewTask', reviewed.status, { recheckSha: recheck, match: recheck === reportSha });

    results.push({ key: m.key, title: m.title, module: report.module, taskKey: task.key, finalStatus: reviewed.status, reportSha256: reportSha, recheckSha256: recheck, counts: report.counts });
  }
  const snapshot = await s.execute(tok.reviewer, 'snapshot');
  const audit = s.verify();
  const pilot = {
    scope: 'PILOT • SANDBOX • READ ONLY • PRODUCTION NO-GO',
    core: { pr: 124, pinnedSha: PR124_PINNED_SHA, service: 'P2Sandbox + CoreEngine', modified: false },
    roles: ROLES,
    tasks: results,
    tasksCompleted: results.filter((r) => r.finalStatus === 'REVIEWED DRAFT').length,
    coreTaskStatuses: snapshot.tasks.map((t) => ({ key: t.key, kind: t.kind, owner: t.owner, status: t.status, reviewer: t.review?.actor ?? null, productionApproved: t.review?.productionApproved ?? null })),
    lifecycle: log,
    auditCheckpoint: audit,
    limits: [
      'PR #124 SI adapter is mock-only by design; the real module runs outside the Core and is bound by SHA-256.',
      'PR #124 has no dedicated ACK command; ACK = executor run-intent event in the audit chain.',
      'Accounts are sandbox role labels for super-pairs; no external SI AI runtime is connected; ACTIVE = 0.',
      'Temporary database is deleted after the run; only this receipt and the reports are kept.',
    ],
  };
  writeFileSync(join(out, 'pilot-run.json'), JSON.stringify(pilot, null, 2) + '\n');
  console.log(JSON.stringify({ tasksCompleted: pilot.tasksCompleted, tasks: results.map((r) => [r.key, r.finalStatus, r.reportSha256.slice(0, 12)]), denials: log.filter((l) => l.result === 'DENIED').length, audit }, null, 2));
} finally {
  s.close();
  rmSync(dir, { recursive: true, force: true });
}
