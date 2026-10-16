# CFP+ P0 + P1 + Standard Core — consolidated handover v1

HUMAN REVIEW • PRODUCTION NO-GO. User accepted continuation of DESIGN / SYNTHETIC TESTING on 2026-10-13; this is not final P1 organizational acceptance.

Central Draft PR: https://github.com/charityfundplus/CFP.plus/pull/124
Evidence revision: 61a32f4f949c0ce5fca1fe59fd838374802a72ec
Application browser-tested revision: 50d17cc1be8408e4e0fd9981a4ff0e15129e6efa
Drive version folder: https://drive.google.com/drive/folders/1b2ebHt2WIK6Ys5SuYsBGNZScZ6fi4IHO

## Coverage and classification

VERIFIED: byte integrity of 74 manifest entries; previous 35/65-entry archives and sidecars reconciled; current 40/40 automated tests and actual 16/16 browser QA recorded. VERIFIED here is bounded integrity/test evidence, not identity, capability or legal verification.

PASS WITH FINDINGS: 12 bilingual Office subsystems, 12 shared Core modules, configurable synthetic pairs, tasks, supervision, cross-checks, safe stop/recovery and metadata upgrade/rollback. Separate Codex independent review supports synthetic design/testing; transient audit/demo roles/mock integrations remain limitations.

MISSING EVIDENCE: genuine named reviewer ACK, actual five-vault URL/owner/scope inventory, verified identities/Registry authority resolution, legal/capability proof. Baseline PNG images are historical only; current UI tested in browser without current screenshots.

BLOCKED: production, merge, live integration/credentials, payments, real customer data, locked registry mutation or DID/0. No material implementation blocker identified in tested mock-only scope; organizational acceptance gates remain pending.

HUMAN GOVERNANCE: final P1 acceptance conditions, named review requirements, exact identity/registry authority and any future real-operation permission.

## Single shared Core

CoreEngine remains shared by all configured pairs. Each configuration carries mission, domain/country, permissions, allowed evidence sources and supervision. Configuration replication does not copy the core or grant new rights. No runtime code change in this handover; no duplicate test cycle.

## Step by Step

1. Obtain the pinned draft source from PR124 or ZIP04; use synthetic data only.
2. Run node scripts/verify-evidence.mjs from drafts/si-office to verify the manifest.
3. Read README.md, docs/CORE_RUNBOOK.md and the Office instructions. Start npm start locally with Node22+; open the loopback Office and /core.
4. Select a demo role; use separate editor/reviewer sessions. Register synthetic Country/Developer/SI/HSTDN and catalog drafts; never bind canonical identity.
5. Select a configured pair, submit a scoped task, examine evidence/supervision/cross-check records. Final review remains a demo acknowledgement, not production approval.
6. Inspect denied actions and audit; use reviewer safe recovery. Upgrade/rollback only built-in metadata.
7. Read review/findings; submit material exceptions to Human Governance. No merge/deploy/publish.

## Independent review handoff

OpenSI: architecture, permissions, supervision independence, audit durability, P1 BLOCKER/NONBLOCKER.
Grok: Country/Developer/SI/HSTDN lineage and Registry conflicts; separate source, capability and legal verification; SpaceX/Starmind/quantum claims.
Claude: security/governance; Gemini: usability/data consistency; Perplexity: sources; Meta: interoperability; Team: specialist scopes.

For every response require reviewer identity, exact revision, readable evidence, methods, findings and status. ACK only when genuinely received. No reachable named OpenSI/Grok custom agent found; shared review packet availability is not proof of delivery to a specific AI. All named reviewers remain PENDING ACK.

## Preservation

All previous ZIP bytes preserved, no parent-folder sharing changes, no locked ID/Parent/DID/Canonical mutations or DID/0. Existing HUB69 remains sole gateway. First P0 archive has no original SHA sidecar; new inventory hashes its bytes without retroactively certifying an embedded manifest.


## CODEX P2 SANDBOX READINESS PLAN — P1 linkage and preparation
Date: 2026-10-13. Status: PREPARATION / PARTIAL / HUMAN REVIEW / PRODUCTION NO-GO.
This section extends the existing handover, not a second Core or a second P1 evidence pack. The user reports acceptance of an earlier P2 plan; its exact original document was not located by workspace file/content search, PR124 inspection or accessible Notion search. This is NOT LOCATED IN CURRENT ACCESS, not a claim the plan does not exist. Preserve this additive section until its original URL/revision is supplied; reconcile into that original rather than maintain parallel plans.

### Exact P1 anchors
- Repository and sole code-review record: https://github.com/charityfundplus/CFP.plus/pull/124
- Immutable handover receipt: https://github.com/charityfundplus/CFP.plus/blob/f224bd8652698f1782977a5b6c5d077f7ae07d6e/drafts/handover-v1/POST_UPLOAD_RECEIPT.json
- Existing versioned Drive pack: https://drive.google.com/drive/folders/1b2ebHt2WIK6Ys5SuYsBGNZScZ6fi4IHO
- Existing Notion P1 report: https://app.notion.com/p/3f8caac9a55781f794dcc175b857057c
- P1 application browser-tested revision: 50d17cc1be8408e4e0fd9981a4ff0e15129e6efa; evidence revision: 61a32f4f949c0ce5fca1fe59fd838374802a72ec.

### Direct verification this turn versus historical reports
Direct current connector reads succeeded for all four named P1 sources. PR124 resolves to charityfundplus/CFP.plus, head f224bd8652698f1782977a5b6c5d077f7ae07d6e, open, draft=true, merged=false before this additive update. This proves current read access to these objects; it does not establish production or reviewer access.
Drive contains the 16 files named in the receipt, each matching ID/name/byte count, plus POST_UPLOAD_RECEIPT.json. Downloaded Drive receipt and manifest bytes were compared exactly with GitHub copies this turn:
- Receipt: 7288 bytes, SHA-256 56f12d9e2718ed93d6fe1d52e4e4672e5f9c20dc81de00dd8c8849e39bfc068e.
- Manifest: 15406 bytes, SHA-256 f8b4e7ac04fdcefe1d0ec7940f9c12fbf939f649ad3db6a9915318932298ef73.
Notion report is readable and contains the same PR, Drive, digest and handover links. Native verification/recency is not legal or capability verification.
Historical reported evidence read this turn: 40/40 automated tests, 16/16 browser QA, 74 manifest file entries and prior ZIP roundtrip verification. No test suite or browser was rerun this turn; the ZIP itself and all 74 individual files were not re-downloaded/rehashed this turn. Prior results remain tied to their recorded commits.
Unreachable named P1 sources: NONE in this turn. Original P2 plan: NOT LOCATED; no absent-source inference. No new named reviewer reply was authenticated; Grok/OpenSI/Perplexity ACK remains PENDING.

### Sandbox implementation sequence — planned, not implemented or certified here
1. Persist state through ports on the existing CoreEngine and Office state path. Keep one engine; inject a shared repository/unit-of-work abstraction, auth context, durable audit writer and adapter inventory. SQLite is the proposed single-process sandbox implementation behind replaceable interfaces; no hosted provider requirement. Do not bolt on a second task engine.
2. Replace self-selected demo roles in the P2 mode with a separate test-user authentication boundary. Bind sandbox account subject to allowed roles/resources server-side; role selection in the request is never authority. Retain P1 demo mode only as explicitly separate synthetic mode. Do not map sandbox account subjects to canonical/DID identities.
3. Commit each authorized state transition and its audit event in one transaction, then test crash/restart and authorization failures. No externally effective action before durable intent and policy check.
4. Add persistent isolation and least-privilege checks per synthetic workspace/pair/mission/resource; trusted HTTP auth context is never accepted from adapter/user output. Authorization checks occur at request admission and immediately before commit.
5. Prepare five read-only adapter descriptors on the existing HUB69 adapter path. Real URLs/owners/scopes remain pending, all disabled/mock by default. Do not use Collaboration Evidence Pack as one of the five operational vaults.
6. Rehearse backup/restore and version compatibility on copied synthetic state; only then conduct a new P2 acceptance test set for material P2 changes. No repeat of unchanged P1 browser/test evidence.

### Concrete storage and audit contracts
StateRepository: open(schemaVersion), transaction(work), readScoped(subject, pair, resource), checkpoint(), close(). Persist synthetic Office proposals/records, pair config/version/stop state, tasks/results, review history, evidence references and session revocation. Migration metadata records schemaVersion, coreVersion and configVersion; no write path for locked identity fields.
Task create carries an idempotency key scoped to authenticated subject/workspace and a request digest. Same key and digest returns the existing result; same key with different digest is denied. Output commit uses expected task revision/epoch; stale or resumed RUNNING work must not replay automatic tool calls. On startup unresolved RUNNING tasks become INTERRUPTED/REVIEW REQUIRED with a recovery audit event. Reviewer explicitly retries into a new retained task record.
AuditWriter: append immutable sanitized event within the state transaction; sequence, event ID, subject, pair, policy version, resource, action, result, request/evidence digest, UTC time, previous hash and event hash. Untrusted text is bounded and serialized safely. Never log passwords, bearer tokens, secrets or real customer content.
Hash chains detect modification; they do not prevent an administrator rewriting the whole database. Periodic independent checkpoints must record externally held digest/sequence and backup reference, with authorized custodian pending Human Governance. Database/audit integrity failure causes fail-closed read-only mode, not silent chain regeneration. Denials are durably logged where storage works; audit-write failure blocks all state mutation.

### Authentication and authorization design
Use synthetic local test accounts provisioned outside public HTTP routes; no public registration or self-grant endpoint. Passwords if used must have salted memory-hard/approved slow hash (Node scrypt is available), never plaintext; bounded login attempts and generic error responses. Random session tokens stored hashed, expiration/revocation checked at every call, restart behavior explicit. Any cookie mode requires HttpOnly/SameSite and origin/CSRF handling; Secure/TLS is required beyond local sandbox. Do not claim local authentication is an approved production IdP.
Viewer: scoped read; editor: allowed scoped draft/task operations; reviewer: scoped review/recovery. Upgrade or rollback additionally requires separately assigned sandbox maintainer permission, never inherent in every reviewer. Reviewer must differ from submitter by authenticated subject, including after restart. Neither sandbox maintainer nor reviewer grants production permissions. Cross-pair/workspace access, adapter-provided roles and identity assignment are denied by default.

### Five-vault adapter contract and gates
Descriptor per slot 1–5: logical key, actual URL, provider, owner, approved scopes, content classification, egress allowlist, credential reference (never secret value), approval evidence, health/status, adapter protocol and source revision. Until these values are evidenced, each slot is MISSING EVIDENCE / DISCONNECTED.
ReadReceipt: source URI/revision, retrieval time, content digest, scope decision, adapter version, verified-source flag and synthetic/live flag. Source retrieval does not verify legal relationship or technical capability. Sandbox mock reads make zero external calls.
Future approved live reads require timeout/size caps, HTTPS and allowlisted targets, redirect/private-address/SSRF defenses, bounded retries, rate limits, revoked-scope failure and no executable instructions from retrieved content. Protocol has no write/delete/permission/publish operation. Credentials remain disabled until explicit separate approval; no live adapter activated in this preparation.

### Backup, restore, rollback and compatibility
Proposed SQLite transaction settings: foreign keys enabled, explicit busy timeout, WAL with durable synchronous mode; support single-process sandbox first. Back up through a consistent SQLite snapshot mechanism; do not copy only a live main database while ignoring its WAL. Store snapshot, schema/core/config versions, migration IDs, audit checkpoint and SHA-256 together. Access-protect backups as state.
Restore only into an isolated synthetic destination after digest, schema and audit validation; default adapters disabled and sessions invalidated. Validate scoped records and replay safety before starting the shared engine. Never overwrite historical evidence or rollback audit history; log restore as a new generation with previous checkpoint link.
Release compatibility matrix covers core API/config/adapter protocol/database schema; unsupported combinations fail closed before mutation. Preflight on cloned snapshot; quiesce tasks; checkpoint; migrate transactionally. Incompatible migration fails without partial state. Executable rollback requires a supported downgrade or a preserved pre-upgrade snapshot plus retained migration/audit evidence; P1 metadata rollback is not proof of this.
Sandbox target for rehearsal: recover all committed synthetic transitions to the most recent valid backup; restore within 5 minutes on the measured test environment. These are proposed targets, not measured RPO/RTO claims.

### P2 acceptance evidence to produce after material implementation
- Kill/restart during transition: no half state/audit commit, no repeated tool effect, interrupted tasks require explicit recovery.
- Missing/tampered audit checkpoint, disk-full/write failure, stale revision and conflicting idempotency key: mutations denied, existing history preserved.
- Expired/revoked/forged sessions, changed request role, cross-pair access and self-review after restart: denied and audited without secrets.
- Five disconnected mock slots: no egress; unsupported scopes/protocol and injected sources fail closed. Live read tests blocked pending approved descriptor/credentials.
- Consistent backup restores into a separate sandbox; corrupted/incompatible snapshot rejected; sessions invalidated; audit continuity retained.
- Unsupported core/config/schema/adapter combinations and failed migrations: no partial upgrade. Rehearse supported rollback with checkpoint preservation.
For each run record exact code/config/schema versions, inputs, expected versus actual outcome, output digest, environment, timestamps and independent reviewer findings. Current status: NOT RUN; no P2 pass count invented.

### Human Governance and named review
Human Governance decisions required: exact P2 scope/acceptance and custodian of audit checkpoints/backups, verified named reviewer contacts, actual five-vault descriptors/scopes, Registry conflicts and any eventual real-operation authentication/integration authority. Prepare synthetic storage/auth work independently while these real-operation gates remain blocked.
Only genuine authenticated responses from Grok/OpenSI/Perplexity can advance their ACK. Shared packet availability, user forwarding or listed names alone is not such a response. Preserve all existing ID/Parent/DID/Canonical and audit history; never create DID/0. No merge/deploy/production payment/customer data or live vault permissions.
