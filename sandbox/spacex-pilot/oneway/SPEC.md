# HUB 69 SpaceX One-Way Sandbox Experiment

Codex implementation proposal 0.2; supplements GrokSI SPEC-DRAFT-01 receipt at Issue #174, comment 6485556500. Not a Grok-authored/approved revision or a new Work Order. Reference: CFP-WO-20260929-GROK-HANDOFF-001. SANDBOX PRACTICE GO • PRODUCTION NO-GO.

## Behavioral contract

Entirely synthetic, flat object with exactly six string properties: record_id, source, status, timestamp_utc, version, content_hash. record_id matches SIM-YYYYMMDD-NNN (synthetic record key, not Registry identity); source is CFP+_SANDBOX; status is sandbox_practice or review_pending; version is 0.1. Extra/missing/wrong-type properties fail INVALID_PAYLOAD.

Normalize the five non-hash strings with trim then Unicode NFC. Validate allowed enums/record format after normalization. content_hash must already be 64 lowercase hexadecimal characters. Hash excludes content_hash itself. Canonical bytes: UTF-8 of compact JSON containing those five normalized string fields sorted by ASCII key: record_id, source, status, timestamp_utc, version. No BOM, trailing newline or spaces. This is a restricted flat-string contract, not general RFC 8785. SHA-256 digest is compared with content_hash; disagreement fails HASH_MISMATCH. See canonical known bytes and independent SHA256('abc') known-answer check in test.mjs.

Timestamp must be valid calendar UTC YYYY-MM-DDTHH:mm:ssZ, exactly round-trip through Date, within inclusive +/-300 seconds of clock.now(). Default clock is OS UTC, not authenticated external time. Tests and isolated-run explicitly use a fixed simulated clock; those audit UTC values are simulated. Evidence envelopes give actual execution UTC.

Import starts BEGIN IMMEDIATE on SQLite, validates before mutation, inserts row and audit in one synchronous=FULL transaction. Same record_id+hash is IDEMPOTENT and adds audit; different hash is CONFLICT and never overwrites. Rejected attempts persist failure audit without a row. Malformed/reverse attempts have null identity/hash because unvalidated values are not trusted. A storage/audit error propagates rather than acknowledging successful ingestion. No automatic retry loop: caller may retry same payload; accepted repeats are idempotent. SQLite busy errors are surfaced. No queue or production transport.

Audit seq, utc, source, version, hash, result and record_id are durable. UPDATE/DELETE audit triggers reject mutations through normal SQL. A process with file write/DDL access can tamper: this is not a tamper-proof external ledger. Rollback deletes the sandbox row and appends ROLLED_BACK in one transaction; it never truncates audit. It does not roll back source data or application deployment.

Only direction CFP_TO_SANDBOX is accepted. isolated-run reads a source fixture under Node --permission and grants writes only to a separate state directory. It imports normally, rejects reverse direction, directly attempts source write, expects ERR_ACCESS_DENIED and compares actual raw source bytes before/after by SHA-256. No production source is mounted or used. Node permissions are defense in depth, not an OS hostile-code sandbox. No network clients, credentials, native add-ons or child processes in the isolated runner. Infrastructure/IAM/network isolation certification remains PENDING.

UI is a static export from the persisted adapter snapshot, not live synchronization. Embedded JSON escapes '<'; DOM insertion uses textContent. HTTP server is loopback only, exact-path GET/HEAD allowlist, all writes 405. Actual HTTP/socket and browser execution may be BLOCKED by environment and never count as PASS.

## Acceptance matrix

E1 missing/extra/type validation → INVALID_PAYLOAD, zero inserted rows.
E2 valid-shaped wrong hash → HASH_MISMATCH, zero inserted rows.
E3 reverse request → WRITEBACK_BLOCKED; direct fixture write denied; raw source hash equal. Independent SecuritySI sign-off still required.
E4 invalid calendar/offset/outside tolerance → INVALID_TIMESTAMP; boundary +300 seconds accepted.
E5 repeat same ID/hash → IDEMPOTENT; different hash → CONFLICT; original remains.
Additional: fixed canonical bytes, injected failure rollback, retry/reopen persistence, rollback audit retention, audit UPDATE/DELETE rejection, static UI payload/audit equality, read-only HTTP handler.

Acceptance requires reviewer independent of implementation. Self-test PASS does not close that gate. Browser desktop/mobile screenshots and real Safari iPhone remain required evidence if requested for UI acceptance; data embedding checks do not substitute for rendering.
