# Issue #148 — implementation evidence and Codex 2 handoff

Date: 2026-10-17 UTC. Scope: Draft source change only; no merge, activation or production deployment.

## DONE

- Shared Python adapter and private CLI under existing cmp/executor; no new server/HUB.
- Gemini Developer API and native Meta Llama API request/response contracts; allowlisted Notion read, reviewed summary plan, approved sandbox CREATE and exact READBACK.
- Header-only credentials, fixed HTTPS provider endpoints, no redirects, no raw response upload, safe errors, read/egress/write audit, owner-only files, pagination, bounded GET retry/Retry-After, signed exact-content approval, durable one-use execution journal.
- Legacy Gemini and Meta Actions entrypoints now invoke offline checks only. Removed fixed-page append and arbitrary bearer-token destination. This Draft does not alter running production infrastructure.
- 33 offline tests PASS, 0 FAIL, Python 3.12.14; command and full output in OFFLINE-148.txt. Fixture transport only; no live HTTP services were used. Test suite requires no third-party dependency.
- Codex 2 independently added 8 adversarial tests and confirmed offline PASS after malformed-response and symlink findings were repaired. Final suite also includes a Retry-After deferral check. Independent review is code/testing assistance, not Human Governance approval.

## Source and environment provenance

Baseline main: 835616308111f6851c0387fa9f5eda60c9ffa624. Existing PR #141 observed Draft at head 8ca11c26fbe3ba76db75ae1aa62b204744233d85; not edited by this change.

Local workspace contains only the changed/tested files and fetched executor/workflow/template inputs. git clone failed because the local proxy could not be reached. GitHub connector fetched pinned source and will create the review commit from the existing base tree. This is an executor environment limitation, not evidence CFP+ is unhealthy. Full-repository or deployment E2E tests were not performed. MANIFEST-148.json records SHA-256 of exact source/test/workflow inputs; it excludes itself and narrative evidence.

Managed runtime status reported current/enforced network policy but zero secret bindings, runtime variables and outbound identities. It does not establish whether repository Actions secrets exist, nor prove remote API permission. No credentials were read from secret files, reused from Claude, or requested in public chat.

Official Notion CREATE/pagination pages and Gemini generateContent/auth documentation were retrieved. Meta website documentation retrieval was unsupported; official meta-llama/llama-api-python sources were read instead. Observed official SDK blob pins:

| Path | Git blob SHA |
|---|---|
| src/llama_api_client/_client.py | 5b11e679998fd59525660951588d63c73eed29f5 |
| src/llama_api_client/resources/chat/completions.py | 3b6f83338c5bda22b36d53599c918befc42bb0b2 |
| src/llama_api_client/types/completion_message.py | c4f22f2ac615ac0285430ef6112ef877c83698fc |

Native endpoint/parser are source-backed. Current API service availability, licensed account/model access and terms acceptance remain unverified. Vertex IAM and consumer UI connectors are not implemented or tested. The generic Vertex documentation extraction did not yield sufficient project/auth passages; no claim of verified Vertex configuration is made.

## BLOCKED / live results

| Provider | Runtime availability | READ | CREATE | READBACK | Live page URL |
|---|---|---|---|---|---|
| Gemini Developer API | BLOCKED: dedicated credentials, entitlement, egress permission and private parent not handed over | NOT RUN | NOT RUN | NOT RUN | none |
| Meta Llama API | BLOCKED: licensed API/account/credential/model and policy not handed over | NOT RUN | NOT RUN | NOT RUN | none |

No private staging endpoint has been handed over. Source work and local acceptance do not depend on one. No UI staging or LIVE claim is made. No official Notion content, Canonical ID, Parent, DID, ACL, Registry, /69 or /id was changed.

## REMAINING / NEXT

Codex 2 can independently reproduce the suite from the Draft PR commit using python3 -m unittest discover -s tests/cmp -v. Once Human Governance authorizes credentials, provider data transfer and sandbox creation, the operator must configure the existing private CMP executor (not a new backend), confirm the dedicated parent and inherited access are private, and provide persistent protected journal/audit storage. Use prepare, review the exact proposal privately, obtain the signed scope-bound approval, then execute and independently inspect the new page and receipt. Report provider, READ/CREATE/READBACK, private evidence URL, tested commit SHA and actual environment separately.

An exact-content signing service is outside this package; existing governance must produce the envelope. The trusted executor holds a shared HMAC verifier key and is trusted accordingly. Private ancestor directories, state path, key holder and operator policy are security prerequisites. API metadata alone cannot prove private ACL. No real write should be attempted until these prerequisites and explicit write approval are satisfied. No broad permission, release approval or production deployment is requested by this Draft.
