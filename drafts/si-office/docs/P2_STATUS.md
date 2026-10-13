# Current P2 extension — PASS WITH FINDINGS / HUMAN REVIEW

Authenticated HTTP/UI implemented; 10/10 P2, 5/5 HTTP/release and 40/40 shared regression PASS. Browser actual 8/8 PASS at commit 566c7067885db15bb14d5c026525765cc20b0eb0; verified 26 build files, VI/EN desktop/mobile390, no page errors, server/session stopped. Following that browser run, only Host-denial handling during maintenance was hardened; its targeted HTTP regression passes. UI bytes unchanged; no final-revision browser rerun is claimed.

Executable rollback is bounded local release control: actual code health executed from two verified complete runtime bundles, active pointer switched, pre-upgrade DB restored into a new generation; current DB/audit retained. Trusted local sources and stopped HTTP process required; automatic live-daemon replacement, cross-schema migrations and multi-process lock not certified. Full production/executable upgrade approval remains NO-GO.

Remaining material findings: independent external audit checkpoints/WORM; real five-vault owner/URL/scope and approved adapters; independent OpenSI post-review tied to new commit; broader independent process-kill rehearsal. Account pair scope added and tested; existing locally provisioned accounts retain legacy workspace-wide scope. Nothing grants real authority or binds locked identity.

Evidence: P2_BROWSER_QA_REPORT.json; P2_HTTP_RELEASE_TEST_RESULTS.txt; P2_TEST_RESULTS.txt; P2_CORE_REGRESSION_RESULTS.txt; P2_EXTENSION_MANIFEST.json + SHA-256. Earlier sections below are retained phase history.

# P2-A to P2-E sandbox implementation — PARTIAL / HUMAN REVIEW

2026-10-13. Single shared CoreEngine; existing PR124; PRODUCTION NO-GO.
User reports OpenSI PASS WITH FINDINGS; direct reviewer source/revision/authority not received. Record as USER-REPORTED, not authenticated ACK. Formal P1 acceptance remains gated.

| Workstream (local mapping; original P2 labels not located) | Implemented and tested | Remaining |
|---|---|---|
| P2-A Authentication | synthetic account provisioning, scrypt hashes, hashed random session tokens, expiry/revoke, login attempt limit | HTTP/UI login integration, production IdP/TLS, credential administration |
| P2-B Authorization/isolation | server-sourced roles, workspace-partitioned state, config mission/tool/resource policy, independent subject review after restart, separate maintainer for upgrades/backups | per-user pair grants, multi-process concurrency, HTTP deployment verification |
| P2-C Durable storage/audit | SQLite WAL/FULL; transaction commits checkpoint/event/idempotency together; hash chain binds stored state; RUNNING intent before adapter; tampering/write failures blocked | independently held checkpoints/WORM, encryption at rest/retention, broader disk/process fault injection |
| P2-D 5 vaults | five disconnected read-only descriptors; no external calls or live credentials | actual owners/URLs/scopes and approved adapter reads; live connection BLOCKED |
| P2-E Recovery/compatibility | state reopen, interrupted RUNNING checkpoint stops pair, explicit reviewer recovery/new retry; consistent SQLite backup, isolated restore/revoked sessions, exact schema compatibility, bounded metadata upgrade/rollback | executable upgrade/migration/downgrade, measured RPO/RTO, independent process-kill rehearsal |

New tests: 10/10 PASS. Existing Core/Office handler regression: 40/40 PASS because checkpoint hooks changed. No duplicate browser cycle; 16/16 P1 browser result remains historical and does not certify P2 service. P2 transport is a local library/CLI, not yet wired to Office HTTP UI. P1 demo HTTP roles remain demo-only; never expose that server as P2 authenticated transport.

Evidence: P2_TEST_RESULTS.txt, P2_CORE_REGRESSION_RESULTS.txt, P2_DEMO_RESULTS.txt, P2_EVIDENCE_MANIFEST.json. Original P1 manifest/ZIP/receipt remains pinned to its prior commit; it does not certify modified P2 source. No P1 evidence overwritten on Drive.

Audit trust boundary: same OS user/database administrator could rewrite entire history; hash checks are not WORM. External checkpoint custodian pending. Storage is single-process sandbox; account provisioning and restore are trusted local administrative APIs, not public endpoints. Serialized commands do not offer concurrent stop/revoke while an adapter runs; current mock deadline is bounded. No real customer data or identities.

## P2 build extension — HTTP/UI and executable release control

The historical table above describes the first P2 commit. This extension adds a separate authenticated loopback HTTP transport at sandbox/p2-http.mjs and /p2 UI reusing public/core.js. Cookie HttpOnly/SameSite Strict, strict Origin/Host, bounded JSON, no role/identity provisioning endpoint. Persistent account pair grants constrain task access, creation and filtered snapshots; legacy locally provisioned accounts retain explicit workspace-wide access. P1 HTTP server remains separately demo-only.

New HTTP/release tests: 5/5 PASS; existing P2 10/10 and shared regression 40/40 PASS. Browser QA for this extension pending until the new pinned build is executed. P1 16/16 is not P2 browser evidence.

Executable release control packs complete local runtime source into digest-verified bundles, executes each bundle's health module against its own service/Core code, checks quiescence under a single-process maintenance lease, snapshots before activation, and atomically fsyncs active pointer. Rollback executes previous bundle health, retains current DB/audit backup, restores pre-upgrade state into a new generation and invalidates sessions; current DB/history is not overwritten. p2-release-serve.mjs boots the selected verified release. Tests execute actual code from two bundle paths with distinct build outputs; no remote code is fetched.

Bounds: trusted local-admin release sources; hash pinning does not establish code trust or isolation. Stop the HTTP process before local maintenance and restart through release bootstrap; live daemon replacement/multi-process locking is not implemented. Unsupported database/config versions fail closed; general executable migration/downgrade is not certified. Independent audit checkpoint/WORM still PENDING; real adapters still disabled. Original P2 evidence manifest remains pinned to earlier commit, new P2_BUILD_MANIFEST covers this changed runtime. No production permission.
