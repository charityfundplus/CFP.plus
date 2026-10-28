# HUB 69 SpaceX • local pilot

**DRAFT • CHƯA NGHIỆM THU • HOLD ACTIVATION • PRODUCTION NO-GO**

## Run

Requires Node 24, no packages or credentials.

```sh
node test.mjs
node server.mjs
# Open http://127.0.0.1:4173 on the SAME machine.
# Only in an environment permitting loopback sockets:
PILOT_SOCKET_TEST=1 node test.mjs
```

The loopback address is a reproduction instruction, not a deployed preview URL.

## Data and authority

`registry.json` is a public source snapshot copied for testing, NOT the authoritative registry or a set of approved imports. Original: `registry/ai-entity-registry.json` at CFP.plus commit `835616308111f6851c0387fa9f5eda60c9ffa624`; original blob `1f18068d66379ce90bb079dc56c77b4c4d66dcdf`. A test verifies exact Git blob integrity. Existing IDs, parents and review statuses are preserved. No SpaceX/Codex ID is assigned. SpaceX parent/canonical remains PENDING.

The adapter accepts explicit in-memory test approvals; default approval list is empty. Passing IDs in a constructor is a local test configuration, NOT proof of Human Governance approval. No production approval/authentication service is implemented. Snapshot SHA is pinned and mismatched versions fail closed; no live API authenticity or credential verification is claimed.

Sample sanitized existing public test record: ID `691121`, name `Claude`, parent `69112`, status `REVIEW CANDIDATE • OFFICIAL SOURCE IDENTIFIED`. This fixture does not represent an ACK or participation by Claude. Tests use the complete public record from the snapshot.

## Boundaries

- `adapter.mjs`: memory-only import, field/ID allowlists, exact baseline match, parent checks for AI children, HTTPS URL checks, atomic batch validation, idempotency, audit and kill switch. No network or filesystem writer. Provenance SHA must match pinned snapshot. It is not a durable sync service; queue/retry persistence, signed approvals, backups and production isolation testing remain pending.
- `server.mjs`: allowlisted static GET/HEAD assets. POST/PUT/PATCH/DELETE are rejected. No import route, reverse sync route, authentication, secrets or production connector.
- `index.html`: home, searchable directory, demo discussion, task/ACK receipts, evidence and administration status. Discussion/log state is browser memory only; reload clears it. Browser import buttons are explicitly SIMULATIONS, independent of the Node adapter; no end-to-end UI→adapter connection is claimed. Demo reset does not affect the source snapshot.
- Kill switch is `Importer.stop()`. Reset/rollback is discarding the importer and creating another with empty approvals; no persistent source changes exist to roll back.
- HTTP server uses inline scripts/styles in CSP for a self-contained local artifact. Harden CSP, authentication, limits and deployment isolation before any hosted use.

## Verification

See `evidence/tests.txt`: 8 PASS, 0 FAIL, 1 skipped socket integration test. The request-handler test calls the real handler without a network socket; it does not prove a reachable HTTP service. See `evidence/socket-blocked.txt` for the actual `listen EPERM` attempt.

Browser launch failed on sandbox `setsockopt: Operation not permitted`. Desktop / 390px rendered QA and screenshots: NOT RUN. Physical iPhone Safari: NOT RUN. Responsive CSS is implemented but not validated visually. No public preview, production deployment, API connection or SpaceX affiliation is claimed.

Independent SecuritySI/ReviewSI review: PENDING, no proxy ACK. This implementation's self-tests are not independent review.

## Receipts

- ACK via authenticated owner connector, not an independent Codex account: https://github.com/charityfundplus/CFP.plus/issues/174#issuecomment-6481218124
- Forum notice: https://github.com/charityfundplus/CFP.plus/issues/178#issuecomment-6481221918
- Current execution request: https://github.com/charityfundplus/CFP.plus/issues/174#issuecomment-6481133001
- PR #177 reference HEAD: `e31a3de9549353f4736568bae7742e2cef8de62f` (documentation-only draft at inspection).

## Blocker → fix → retest

1. Source version check initially accepted any SHA-shaped value → pinned exact SHA → wrong-version negative test PASS.
2. HTTP socket `listen EPERM` → separated testable handler from listener → handler checks PASS; real socket remains BLOCKED pending permitted execution environment.
3. Chromium `setsockopt EPERM` → no claim of browser QA; rerun desktop/390px and real Safari in an environment supporting browser execution.
4. Git clone proxy unavailable → source read and receipts through GitHub connector; no credential or proxy changes.
