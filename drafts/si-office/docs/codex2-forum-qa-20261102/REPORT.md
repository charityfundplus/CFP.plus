# Codex 2 • Independent forum/backend P0 QA

Observed UTC: 2026-11-02T03:09:14.656688+00:00

- Requested backend: `codex1/p0-forum-foundation-audit-20261026`, full HEAD `73e705edbe69e82a62791ec1e56072f990c011d5`; the GitHub PR #179 head ref resolves to the same SHA.
- Fix/test delivery: `codex2/p0-forum-independent-qa-20261102`, code commit `5e29d174864873fb81f24e50631468f2738ba65e`. Evidence-only successor commits do not change this tested application source.
- Runtime: Node v24.19.0, real loopback TCP/HTTP, temporary on-disk SQLite, explicitly synthetic local accounts. Chromium mobile emulation at 390x844 and 320x844; no physical phone or Safari claim.
- No production deployment, merge, ID, Parent, DID or Canonical changes. Acceptance remains with Human Governance.

## Results

| Status | Capability | Evidence / boundary |
|---|---|---|
| PASS | Create task, durable storage, reopen process/database, fresh independent session readback | QA-01; exact task key/owner/content compared |
| PASS | Idempotent create retry; changed-payload conflict | QA-02; 409 on conflict, one stored task |
| PASS | Anonymous/viewer/foreign workspace/ungranted pair restrictions | QA-03; no unauthorized mutation/disclosure in tested cases |
| PASS | Generated synthetic output, task-key-bound SHA256, independent draft review, valid audit on reopen | QA-04; does not prove upload of an external Evidence file |
| PASS | Independent sessions and isolated logout | QA-05 |
| PASS | Origin, role/owner injection, oversized body, SQL-like credential rejection | QA-06 |
| PASS | Persisted state tampering detected | QA-07; local checksum chain, not independent WORM custody |
| FAIL → PASS locally | Malformed unauthenticated target crashes HTTP process on original commit; fixed commit returns 400 and still serves requests | QA-09, baseline-crash.txt, fixed-independent.txt |
| PASS | Mobile UI creation/execution/reload, separate reviewer context, viewer controls, foreign-workspace isolation, title escaping | mobile-results.json, mobile-task.png; generated mock output only |
| UNAVAILABLE | Forum recipient assignment/ACK, posts/replies, external Evidence upload and exact-task retrieval API | Seven proposed `/api/core/forum/*` routes return 404 on inspected baseline; route probe success is NOT feature acceptance |
| BLOCKED | Existing Canva forum and linked sandbox UI inspection | Proxy CONNECT 403 before origin/TLS; not an application 403 |
| BLOCKED | Public HUB 69 comparison | Same network restriction |
| UNAVAILABLE | Hosted staging URL and deployed source SHA binding | No configured staging variable or verified deployment provenance |
| UNAVAILABLE | Supabase connection | No Supabase binding names present or implementation reference in inspected backend; no conclusion about other systems |
| BLOCKED | GitHub API comment/PR creation | `api.github.com` CONNECT 403; HTTPS Git read works. Repository branch delivery is separate from recipient ACK |

Original independent run: **8 passed, 1 failed** (includes a route-absence inventory check, not a forum acceptance test).
Fixed independent suite: **8 passed, 0 failed** (route-absence check intentionally excluded from the reusable acceptance suite).
Existing targeted suites: **22 passed, 0 failed**.
Existing core suite: **40 passed, 0 failed**.
Fixed mobile script: **PASS**, six functional check groups, no page errors, no horizontal overflow at both tested widths.
No full-forum end-to-end PASS is claimed: required recipient ACK, uploaded Evidence and forum posts/replies remain unavailable.

## Reproduction and fix for Codex 1

Unauthenticated request on an allowed local host:

```http
GET http://[ HTTP/1.1
Host: 127.0.0.1:<test-port>
Connection: close
```

`new URL(req.url, ...)` executes outside the async handler's try/catch on the original source. `ERR_INVALID_URL` becomes an unhandled rejection and Node exits 1. This is a reproduced availability defect in the sandbox; public production exposure is not established. The one-line relocation moves parsing into the existing request error boundary. The regression uses a separate child server, checks HTTP 400 and a subsequent successful GET, and never attacks the public site.

Codex 1 handoff: review/cherry-pick `5e29d174864873fb81f24e50631468f2738ba65e` onto PR #179's backend lane, then rerun the commands below. No claim that Codex 1 has acknowledged or applied this change. The missing forum endpoints are implementation gaps recorded in the original Codex 1 report, not silently replaced by a new forum system. Add recipient-authorized ACK and task-bound Evidence contracts to the existing Core before the full requested acceptance scenario can pass.

## Repeat

From `drafts/si-office`:

```sh
node --test tests/forum-independent-qa.test.mjs
node --test tests/office-intake.test.mjs tests/forum-foundation-loopback.test.mjs tests/p2-http.test.mjs tests/p2.test.mjs
npm test
CFP_FORUM_QA_EVIDENCE_DIR=/tmp/cfp-forum-browser python3 tests/forum-mobile-qa.py
```

Requires Node 22+ with `node:sqlite` (validated on Node 24.19.0); the browser check requires Python Playwright and `/usr/bin/chromium`. Fixtures use synthetic credentials defined only for temporary local test accounts. No real tokens are included. Servers/databases are cleaned up by the scripts.

URLs requested:
- https://canva.link/nrga02csz6vj2hs
- https://canva.link/oijkt90d60qiwkp
- https://cfp.plus/69
- https://github.com/charityfundplus/CFP.plus/pull/179
- https://github.com/charityfundplus/CFP.plus/commit/5e29d174864873fb81f24e50631468f2738ba65e

Network draft saved: custom domains `canva.link`, `cfp.plus`, `api.github.com`; existing package-manager presets retained. Saving does not apply runtime access. Review/save the network settings to unblock affected requests; a subsequent Canva redirect may identify another required destination. No credentials need to be sent in chat. Real staging accounts, if supplied later, belong in secure environment configuration.
