# CFP+ Standard Core — independent Codex-agent review

Date: 2026-10-13. Reviewer: separate Codex review agent, not OpenSI or Grok. The four-axis/eight-check mechanism is deterministic code executed twice; it is not eight real reviewers. Scope: `core/*.mjs`, `configs/pairs.json`, Core routes in `server.mjs`, handler harness and `tests/standard-core.test.mjs`. No deployment, external communication, network request or browser execution was performed by this reviewer.

## Decision

PARTIAL / P1 readiness candidate — synthetic local implementation; production remains NO-GO. The initial material draft permission defect was repaired and independently regression-tested before this final recommendation. Browser verification of current UI remains BLOCKED by the reported sandbox socket EPERM; this review verifies code and in-process handlers only.

## Initial material finding — resolved on final recheck

**P1: adapter-declared tool omission bypasses draft.write scope.** `CoreEngine.runTask` originally validated only tools named by the untrusted adapter. Reviewer reproduced a source.read-only config with a custom adapter returning `tools: []`; a website artifact was still committed with `AWAITING HUMAN REVIEW`. The adapter must not determine whether trusted Core needs write permission. Before staging non-registry draft output, Core must independently require `draft.write` for the task resource, and test tool omission. No production write occurred; the defect affects the synthetic draft authorization contract. Remediation recheck is recorded below.

## Verified boundaries

- Immutable/frozen configuration and detached snapshots prevent external mutation of policy. Identity accepts only synthetic fixture lineage; ID, Parent, DID and Canonical stay null.
- Mission/resource scope, input/proposal allowlists, provider/protocol binding, output size/title/source hash and separate unverified source/capability/legal flags are enforced outside the adapter. Production/payment/identity/permission/external-write tools are denied.
- Stop increments an epoch, aborts the controller and interrupts queued/running tasks. Late adapter output cannot commit after stop. Recovery requires STOPPED and no active task; retry creates a separate task retaining the old evidence. Timeout bounds result acceptance, not execution of arbitrary third-party code.
- Upgrades use only built-in sandbox release metadata, require quiescent tasks, reject incompatible/health-failing releases before mutation and synchronously update module version labels as one cohort. Rollback preserves identity and audit. This is metadata simulation, not atomic installation/rollback of executable modules or durable database transactions; immutable config.software.version describes initial config, while module/version state describes active simulated cohort.
- Learning evaluation cannot grant privileges or promote a pair to authorized operation. Separate session IDs provide a demo review separation check, not proof of a different human identity.
- Knowledge fixture hashes and audit links are recomputable. Fixtures explicitly state synthetic:true and verifiedSource:false. A fixture hash verifies local bytes, not public-source authenticity or company/legal capability. `sourceCheckedAt` in synthetic artifacts must be read as generation/check timestamp for fixture content, not independent live-source verification.
- HUB 69 mock inventory is disconnected, makes zero external requests and does not create another hub. Group labels V/000/135/246/789 remain draft display metadata with legacy conflict disclosed.

## Evidence and remaining gates

Reviewer independently ran the initial `npm test`: **38/38 passed**. Tests cover request handlers and core engine in-process without sockets; they did not include the tool-omission defect at initial review. Actual browser, network integration, genuine SI identity, independent OpenSI/Grok participation, exact D 500 authority, registry conflict resolution, five-vault permissions, real operations and production approval remain BLOCKED/MISSING EVIDENCE/HUMAN GOVERNANCE as applicable. Existing initial browser screenshots are historical baseline only.

Remaining environment boundaries: role selection is self-service demo authentication; memory state/audit are lost on restart and lack tenant isolation or independent immutable storage. Adapter extension is not a security sandbox for arbitrary executable code. Any live adapter must receive independent runtime/network isolation and human authorization before use. No product or legal capability is certified by this review.


## Final remediation recheck

Reviewer independently inspected the trusted Core action checks and repeated `npm test`: **40/40 passed, zero failures**. Before calling any adapter, Core now requires source.read and requires draft.write for all non-registry-audit tasks; the independent cross-check repeats these required checks. Regression test supplies a source.read-only configuration and adapter that omits tool declarations: result is BLOCKED, output null, adapter never called. The initial P1 permission omission finding is **RESOLVED**. Read-only registry lookup also preserves numeric strings including zero, without verifying or binding identity. No further material defect was found in the scoped final recheck. Browser and live-operation limitations remain as stated above; this does not grant DESIGN / TESTING ACCEPTED or production approval.
