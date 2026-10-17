# CMP provider → Notion adapter • Issue #148

This continues the existing outbound executor and the Gemini/Meta pilot workflows.
It adds no server, HUB, Registry, Core session route or consumer-app login.
Status: **LOCAL CONTRACT TESTED • LIVE INTEGRATION BLOCKED • PRODUCTION NO-GO**.

## Provider boundary

- `gemini`: Gemini Developer API `generateContent`, fixed Google origin and
  `x-goog-api-key` header. Model is required configuration; its account availability
  is not inferred. Vertex AI credentials/transport are not implemented by this adapter.
- `meta`: the Meta Model API's OpenAI-compatible chat-completions surface at the
  fixed `https://api.meta.ai/v1/chat/completions` origin. Model is required configuration;
  account entitlement, model availability and license/terms need verification.
  Arbitrary `META_BASE_URL` values from the previous pilot are no longer accepted.
- These are server-side API adapters. They do not enable Notion inside Gemini or
  Meta AI consumer interfaces, and do not claim those interfaces accept arbitrary MCP.

Official protocol references inspected during implementation:
https://ai.google.dev/api/generate-content
https://dev.meta.ai/docs/overview
https://developers.notion.com/reference/post-page
The Notion reference was inaccessible through the read tool in this session; live
sandbox acceptance must confirm the existing create-page/blocks protocol. A public
API reference does not establish CFP+ account permissions, current model availability,
commercial terms acceptance or credentials.

## Existing workflow modes

The two existing workflow files remain the entry points. `repository_dispatch`
was removed; only explicit manual workflow dispatch is accepted. The CI contract
workflow runs synthetic tests only, without any provider or Notion secrets.

| Mode | Behavior | Possible side effect |
| --- | --- | --- |
| `read` | Read one allowlisted source's bounded plaintext blocks | Notion GET only |
| `draft` | Read source and call the selected provider | Approved source leaves Notion; provider request may incur cost |
| `create-sandbox` | Write externally reviewed, signed text without regenerating it; read back exact created child | Creates one child under the fixed sandbox parent; session ledger consumes approval |

None of these modes edits/appends/replaces official documents. The old hardcoded
locked-page/heading write is removed. Unsupported/nested source blocks stop with
`UNSUPPORTED_SOURCE_BLOCK`; the adapter does not silently summarize a partial page.
Source reads cap pagination at ten pages and each HTTP response at256KiB. Output
is limited to1800characters. Streaming/tool execution is not enabled.

`Notion.plan(provider, model, source_page, approved_text)` returns the private
write contract. `Provider.generate(prompt)` returns draft text to its authorized
in-process caller. Codex2 can present that plan in the existing private review
surface. The manual workflow intentionally uploads hashes only: it is not a
private draft-delivery UI. A private delivery/review channel must exist before
using provider-generated drafts in a live write rehearsal; do not upload raw text
to a public Issue/PR or Actions artifact to bypass this dependency.

## Approval contract

`create_and_readback(plan, approval, context, public_key, ledger)` verifies:

1. Server-owned readable-source allowlist and sandbox parent; entire rebuilt plan
   equality, including action/provider/model/text/source/parent/title.
2. Ed25519 signature by a separately authorized human/custodian. The executor has
   only the public key. The private signing key must never enter the runner,
   repository, model prompt, workflow secret or generated output.
3. Signed claims: `plan_sha256`, exact GitHub context, `issued_at`, `expires_at`
   (max15minutes), nonce, approver reference and scope `create-sandbox`.
4. Context fields are `repository`, `ref`, `sha`, `run_id`, `run_attempt` from the
   trusted runner. Repo is fixed to charityfundplus/CFP.plus. Approval cannot be
   reused across commits, providers, targets, content or rerun attempts.
5. SQLite consumes the nonce **before** POST. Uncertain/failed POST is never
   automatically replayed; operator reconciles Notion before requesting a new
   approval. Signature verification authenticates a trusted issuer key, not a
   real-world identity by itself; Human Governance must establish that key's role.

The signed envelope is `{claims:{...}, signature:"<base64>"}`; the signature covers
canonical JSON (sorted keys, compact separators, UTF-8). `plan_sha256` hashes that
same canonical encoding of the full private plan. No approval signer is shipped
in the production runner. Unit tests generate ephemeral synthetic signing keys.
The approver needs the actual plan and queued run_id/run_attempt before issuing
approval; an unsigned boolean or an old approval file is insufficient.

## Configuration • do not configure or dispatch without approval

Use an **existing** private GitHub Environment with required reviewers and
`prevent_self_review=true`. Set its name in repository variable
`CMP_NOTION_APPROVAL_ENVIRONMENT`. If unset, live jobs are skipped. The runner
reads the Environment metadata and fails closed if reviewer protection cannot be
verified. No Environment, ACL or reviewer is created/modified by this change.

Environment-scoped secrets:

- `CMP_NOTION_TOKEN`: dedicated minimally scoped CFP+ integration; never reuse Claude's token.
- `GEMINI_API_KEY` / `META_API_KEY`: only the provider being exercised needs its key.
- `CMP_NOTION_APPROVAL_JSON` and `CMP_APPROVED_TEXT`: externally reviewed write
  envelope and exact text; write mode only. Scope these to the approved run.

Trusted variables: `CMP_NOTION_READABLE_PAGE_IDS` (JSON UUID list),
`CMP_NOTION_SOURCE_PAGE`, `CMP_NOTION_SANDBOX_PARENT`, `CMP_APPROVAL_PUBLIC_KEY`
(base64 raw Ed25519 public key), `GEMINI_MODEL` and `META_MODEL`.
Provider-specific access/export/cost approval is required before `draft` dispatch.
Sandbox parent's sharing/permissions remain its existing ones: code does not
assert that any arbitrary UUID is private or change its ACL. Human Governance
must verify private parent and token capabilities before a live run.

`CMP_APPROVAL_LEDGER_PATH` is runner-owned, not an HTTP request field. In Actions
it is in runner.temp and protected by exact signed run_id/run_attempt. A rerun
needs a new signature. Any non-Actions launcher must supply durable storage and
trustworthy context and retain the ledger; it must not reset a ledger or reuse
context identifiers. No self-hosted deployment is enabled here.

## Secrets, transport and audit

Secrets enter processes through environment bindings, never shell-source
interpolation or request URLs. No raw provider/Notion responses, drafts, prompts,
headers, exception messages or approval envelopes are uploaded or printed.
Only `cmp-evidence.json` is an artifact. It contains controlled stage statuses,
content/plan digests and a hash of the created page ID, not source contents or
private page URLs. Receipts are informational; they cannot authorize writes.

Fixed HTTPS origins, standard CA verification/proxy handling, no redirects,
25second timeout, bounded GET retry for429/502/503/504. No POST retry on provider
or Notion calls; a timeout does not prove nothing happened. 401/403 fail closed.
Generated text containing bound provider/Notion credentials is rejected.
The caller must protect other credentials from entering source data in the first
place. This is not a claim of general-purpose DLP or a full secret audit of history.
Existing receipts remain history; rotation/revocation/deletion needs its own
operator authorization and evidence. No credential values were inspected here.

## Codex2 handoff / acceptance

Run `python -m unittest discover -s cmp/executor/tests -v` using synthetic transports.
Review exact plan/approval/context schema, 401/403, absent approval, tampered payload,
replay, secret-echo, corrupt provider output, target mismatch and exact readback.
No Staging URL is needed for these tests. Do not mark independent acceptance until
Codex2 returns its own evidence; no Codex2 execution/ACK is inferred.

Live sequence, only after authority/credentials/private scope are verified:
read approved page → privately review provider draft → obtain per-run signed
approval → CREATE sandbox child → GET exact child → compare → redacted receipt.
Report each provider independently. Source read is a separate mode, not automatically
PASS when only create/readback succeeded. Failed readback after a successful
creation is still a blocked integration and requires reconciliation, not another
blind creation. Never test official-document writes as a workaround.

PR141/Codex2 and Core06f386b1 are not modified. Registry/Canonical/Parent/DID/ACL
remain unchanged. No live calls, workflow dispatch, paid resource, Notion write,
merge, staging activation or Production deployment was performed.
