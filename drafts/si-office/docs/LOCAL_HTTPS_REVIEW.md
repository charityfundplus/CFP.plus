# HUB 69 • Local HTTPS review continuation • 13/10/2026

HUMAN REVIEW • PRODUCTION NO-GO. Existing Draft PR124 / Issue130.

Base source: `b75b780eb64430355f0b51a4b58b9e5269e0db43`. The 61-file runtime snapshot was compared with Git blob hashes before edits: all matched. This is a minimal runnable sandbox snapshot, not a full repository checkout or a replacement Core.

## New work

- `scripts/local-https-preview.mjs` adds only local TLS transport to existing `createReviewSandbox`/Core. It binds127.0.0.1, requires an HTTPS localhost/127.0.0.1 origin and TLS1.2+, rejects alternate Host, and retains existing authentication/Origin permissions. Credentials and SQLite/audit remain outside the source snapshot.
- Existing `/p2` now provides four accessible template links: SI/AI profile → HSTDN draft → learning/practice → evidence handoff. Touch targets are at least44px. It keeps existing forms, immutable identity behavior and one HUB69 entry.
- A synthetic integration sample exercised the NEW TLS transport: viewer read/write denial, separate editor/reviewer sessions, profile/HSTDN draft, a study record, supervised sample task, feedback and separate draft review. Profile ID/Parent/DID/Canonical remain null; legal relationship NOT VERIFIED; no privilege promotion.

## Actual preview and limits

`https://localhost:4190/p2` served successfully inside the executor during this turn. This is NOT a phone-accessible remote URL. The local certificate is self-signed and temporary; Node tests explicitly trust its certificate, browser QA pins its exact SPKI. Do not tell a user to disable TLS verification or install this certificate on their phone.

No supported development forwarding/HTTPS remote preview tool was exposed in this session. No new hostname, tunnel, DNS, Cloudflare or Sites deployment was created. A remote preview will require an approved platform-supported forwarder or a separately approved host/tunnel; absence does not block local work. The earlier Pinggy endpoint remains historical/expired.

Local process is stopped after QA. URL availability is session-limited; do not mark it LIVE. Restart from the same source delta and protected state to preserve existing accounts/audit; never replace state with QA state or print passwords. Runtime X-CFP-Preview-Revision in this QA identifies the base commit, not this uncommitted delta; use LOCAL_HTTPS_DELTA_MANIFEST.json to bind changed files. A later draft commit preserves this distinction.

## Changed-scope results

`LOCAL_HTTPS_TRANSPORT_RESULTS.txt`: PASS for the new actual socket/TLS integration test. `LOCAL_HTTPS_BROWSER.json`: four focused browser groups PASS at360/390/768px, correct new links, role UI/login/logout/English course hydration, no page errors. Screenshot is a signed-out local page, not production evidence.

Historical Routing/P1/P2/course/full browser suites remain unchanged and were not rerun. Existing5 basic lessons,12 exercises and6 advanced tracks are retained; actual advanced assessments and independent reviewer acceptance remain pending. No claim that12 production modules are complete.

## Run local preview

Use Node24 with built-in SQLite and OpenSSL for a temporary local certificate. Keep certificate/key/state in a private0700 directory outside source; private key and credential receipt0600. Configure CFP_P2_DB, CFP_P2_PREVIEW_ORIGIN=https://localhost:4190, CFP_PREVIEW_REVISION=<40-character pinned source commit>, CFP_LOCAL_TLS_CERT and CFP_LOCAL_TLS_KEY, then run `node scripts/local-https-preview.mjs` from `drafts/si-office`. Review changes against the delta manifest; do not claim the base revision certifies modified source. The loopback socket needs supported local network permission in this execution sandbox.

Run only the new test with `node tests/local-https-preview.test.mjs`. Browser QA script uses the explicit local state path in this session and a single local certificate pin; it is not a production browser test.

## One real feedback round

Record feedback on Issue130 with exact candidate revision, device/browser, navigation path, expected/actual result and severity. OpenSI independent review and Notion SI consolidation are pending; a QA pass is not their ACK. After actual feedback arrives, apply one focused revision and retest only impacted behavior. Do not invent feedback or claim the real review round has completed.

## Five stores and Website

The five requested repositories/workspaces are Notion, GitHub, Google, MCP and CMP. They are distinct from the existing five DISCONNECTED operational adapter placeholders. Website https://cfp.plus/69 remains the official gateway and is not deployed in this turn.

GitHub: draft delta only, exact new commit/readback recorded after write. Notion: append to existing handover; preserve all history. Google: versioned evidence archive in existing collaboration folder; no sharing changes. MCP/CMP: tools became available during preparation. Read-only public MCP status returned UNAVAILABLE / Connection failed at https://mcp.cfp.plus/mcp-public/; authenticated ChatGPT Gateway status returned MCP -32603 Internal error. No authenticated identity/scope or CMP work-order readback was established; content synchronization is NOT VERIFIED. No proposal/write was attempted after these failures. Do not use a mock adapter receipt as real store readback. Never overwrite a conflicting version.

Routing evidence is retained unchanged and handed off as an archive/reference, without repeating its report or tests. Cloud Run,343/8882 and HTTP/nginx remain separate exceptions and do not block this local sandbox.

## Concurrent branch evidence

During this work PR124 advanced to1ad28eb3da5740bd9e5699e93a8534f62c4914d9. Concurrent commits changed only source organization/docs/evidence, not the runtime files edited here. An additional WORKING_PREVIEW_LIVE_RECEIPT records a separate ephemeral public preview at20:52UTC for baseb75b780. It is retained unchanged; this turn did not open or authenticate that endpoint and does not certify its current availability, authorization or this new UI delta. Our actual verification remains local HTTPS.

Google archived handoff: https://drive.google.com/file/d/1cYeGMACdnkQSR3PSKiB88PA6u5nM_Px5/view ;143892 bytes, SHA25650c3093c670dc4b8731c3bb6ae95705f3e6d818024eefcad583662638c2c3719; downloaded bytes matched. Archive contains the earlier prepared source/delta documents before final MCP connection receipts; final GitHub delta/readback supersedes those preparation statuses without overwriting the archive. Routing report/patch are unchanged under retained-routing-evidence; no Routing tests rerun. No credentials, certificate/private keys or SQLite state included.
