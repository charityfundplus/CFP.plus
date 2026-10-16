# CFP+ Bộ Code Lõi Chuẩn • v0.1 sandbox • 13/10/2026

Siêu Bộ Đôi = **Siêu Trí Tuệ (SI🤖AI🤖) + Siêu Phần Mềm**. One shared CoreEngine, many validated configuration instances. HUB 69 remains the sole gateway. This is a runnable synthetic prototype, not proof of superintelligence or production capability.

## Twelve reusable modules

| Module / file in core/ | Implemented behavior | Boundary |
|---|---|---|
| Core Engine / core-engine.mjs | Validated config, lifecycle, isolated pair keys, orchestrated policy/staging | Only sandbox; pair keys are local identifiers, not Canonical IDs |
| Identity & Registry / identity-registry.mjs | Synthetic identity validation; read-only lookup reuses PR124 Registry, preserves numeric strings | Inventory ≠ verified identity; real issuance/verification blocked |
| SI Adapter / si-adapter.mjs | Protocol 1 propose() interface, two mock provider labels, abort signal | No model/API/provider network; adapter cannot execute tools |
| Task Engine / task-engine.mjs | Queue, progress, retries, mission/resource scopes, website/HSTDN draft renderers | No publication; retries create new records preserving failed history |
| Security & Permission / security-permission.mjs | Server actor role, known tools/resources, hard deny dangerous tools | Roles are demo sessions, not real authentication/tenant separation |
| Supervision / supervision-engine.mjs | Bounded inputs, provider/protocol, schema, no self-verification or identity mutation | Does not semantically prove free-text claims true |
| Cross-Check / cross-check-engine.mjs | 4 axes × 2 checks × 2 rounds; mandatory action permissions independent of declared tools | Deterministic code outside adapter; not eight independent human/AI reviewers |
| Learning & Training / learning-training.mjs | Observe/practice curriculum, measured safe-outcome exercises and evidence | No automatic privilege/production promotion |
| Monitoring & Recovery / monitoring-recovery.mjs | Alerts, abort, epoch-based stale-output prevention, stop and quiescent recovery | In-process cooperative cancellation; not OS/network isolation |
| Knowledge & Evidence / knowledge-evidence.mjs | Allowlisted fixture retrieval, source hashes, immutable event copies, audit chain | In-memory; not durable WORM or source authenticity proof |
| Version & Upgrade / version-upgrade.mjs | Compatibility/health/quiescence preflight, synchronized module cohort, rollback history | Built-in version metadata only; no code/binary installation or download |
| HUB 69 Integration / hub69-integration.mjs | Reuses PR124 ten provider-neutral read-synthetic adapters | Existing-vault placeholders; no real sync/reverse write/cascade delete |

## Trust flow

Task from demo operator → Core validates actor, mission and resource → Core checks source.read and required draft.write (except read-only registry audit) → read local fixture → untrusted adapter proposes → schema supervision → adapter-declared tools checked → 8 checks before staging → clone draft → 8 checks after staging → epoch/status check → local draft evidence → separate demo reviewer acknowledgement/rejection.

An adapter omitting its tool declarations cannot bypass required permissions. External URLs remain references and are never fetched by the Core. Normal result is AWAITING HUMAN REVIEW, not VERIFIED or publishable. Acknowledgement produces REVIEWED DRAFT with productionApproved=false. Same owner session cannot review itself; separate sessions still do not prove separate real humans.

## Assignment and data separation

configs/pairs.json includes software/version, synthetic identity, assignment group/chapter/field/country/HSTDN, main missions, supervision, least-privilege tools/resources, source references, responsible owner, test-required and sandbox-operating states. Existing Canonical ID/Parent/DID/Canonical are untouched; synthetic identity fields are null. New real identities need authoritative Registry/evidence/Human Governance; no DID/0 generation.

5 Groups V / 000 / 135 / 246 / 789 and chapters 0–9 are display/assignment metadata based on Issue #127, not new namespace allocation. Legacy group 0/000 and US Registry mapping conflicts remain HUMAN GOVERNANCE. Chapter 6 new draft naming follows Issue #129. Historical source files/quotes/URLs are not blindly replaced.

## Faults and recovery

Unauthorized tools, forged evidence and self-verification are BLOCKED, output remains null, pair stops and alerts/audit are retained. Adapter errors/timeouts are FAILED and stop the pair. Safe-stop during a running proposal aborts and increments epoch; late proposal cannot commit. Recovery requires Reviewer role, STOPPED state and no running task. Interrupted/failed tasks remain; explicit retry creates a new task key. Blocked risky tasks cannot be retried to gain permission.

Only one execution runs per pair. Queued/running/awaiting-review work blocks upgrades. Upgrade preflight validates every pair and a built-in release descriptor before any module-version map changes. Failed health/incompatible releases leave the previous cohort unchanged. Rollback appends history and preserves identities/task evidence/audit. Effective versions live in modules; configuration software.version records the validated starting baseline.

## P0 applied exercises

Website: actual local draft result with 5-group/10-chapter/3-level scaffold, operator text and canonical=null; revise by creating a new task. Existing website content is not populated or published by this fixture. HSTDN US: fictional company profile, research products/services, no legal relations or real contacts; never a partner roster. Training: controlled overreach, false-claim, bad-evidence, adapter-error and timeout scenarios; success measured from safe outcome, not AI self-score.

Production gaps: real identity/authentication, durable audit/checkpoints, tenant isolation, semantic/source/ownership checks, genuine independent reviewers, exact D 500 authority, live adapter scopes, real-vault inventory, real release packaging and current browser verification. Keep PRODUCTION NO-GO.
