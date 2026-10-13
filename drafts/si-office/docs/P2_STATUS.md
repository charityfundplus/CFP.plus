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
