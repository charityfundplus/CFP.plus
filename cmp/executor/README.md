# CMP Notion bridge — issue #148

This extends the existing CMP executor directory and two pilot workflow entrypoints. It adds no backend, HUB, Registry, login service, MCP server or production route. The previous public Actions live pilots are replaced by offline contract checks: the Gemini pilot exposed a key in its URL, directly interpolated secrets into shell, wrote a fixed page without a fresh approval, and uploaded raw responses. The Meta pilot sent a bearer token to an arbitrary configured base URL and did not integrate Notion.

## Contract and trust boundary

`prepare(policy, notion, model, execution, source, parent, audit) -> private plan` reads an explicitly allowlisted Notion page, sends only its top-level textual blocks to the approved model API, and produces a summary proposal. It audits before reads and model egress, and never writes Notion. Nested pages/blocks, links, attachments and arbitrary model tool calls are not followed. Empty or oversized sources fail closed. Source content and model output are untrusted data.

`execute(policy, notion, plan, approval, key, journal, audit) -> receipt` verifies an exact plan digest and HMAC approval, rechecks the source digest and parent, durably reserves the execution ID, creates ONE child page under a dedicated sandbox parent, then reads the new page metadata and paginated blocks and compares exact parent/title/body. No PATCH, DELETE, official-document update or ACL/share call exists. Retrying a reserved execution ID is blocked, including after ambiguous CREATE failures. Reconcile remotely through an authorized operator before any new execution; do not delete/reset the journal to retry.

Host policy, approval key, model configuration, durable state and transport belong to the trusted existing executor. They must never be exposed as model tool arguments or editable by untrusted users. The HMAC key is a shared verifier secret: this protects against untrusted callers, not a compromised executor/key holder. Human Governance signs externally after reviewing the exact private proposal; this package deliberately has no approval-issuing command. A model answer, comment, checkbox, execution ID or workflow dispatch is not approval.

## Provider scope and actual availability

| Surface | Implemented path | Live status in this change |
|---|---|---|
| Gemini Developer API | REST generateContent; x-goog-api-key header; strict model identifier | BLOCKED: no configured credential, model entitlement or approved data egress |
| Vertex AI | Different Google Cloud project/location/IAM/endpoint contract; not implemented by this adapter | BLOCKED: no project/IAM handoff; no silent Developer API fallback |
| Gemini consumer UI | No connector or MCP availability claim | BLOCKED / not tested |
| Meta native Llama API | Fixed api.llama.com/v1/chat/completions; native completion_message parser, including string/text-object content | BLOCKED: no licensed account/credential/model entitlement verified |
| Other licensed Llama host | Requires its own reviewed endpoint/parser/terms change | BLOCKED; arbitrary META_BASE_URL is not accepted |
| Meta AI consumer UI | No connector or MCP availability claim | BLOCKED / not tested |

The official Meta SDK is evidence of a documented API contract, not proof of current account availability or terms acceptance. Do not relabel the Meta API as a Meta AI UI connection. Do not reuse Claude tokens. A successful fake transport test proves local behavior only.

## Private executor setup (operator handoff; not performed here)

Python 3.10+ standard library only; no installation or new service required. Use the existing private CMP executor's secure credential injection. Keep policy/approval/plan at owner-only 0600, and durable state directory at owner-only 0700. Do not put these files under a public website root or upload them to public Actions artifacts.

Trusted `CMP_POLICY_FILE` JSON fields:

- `read_pages`: explicitly shared source page UUIDs; no workspace search or implicit child access.
- `egress_pages`: subset authorized for transfer to the selected model provider. Reading permission alone does not authorize external model transfer.
- `sandbox_parents`: dedicated sandbox parent UUIDs, disjoint from source pages.
- `private_parent_confirmed`: literal true only after owner verifies the parent and inherited child access are private and authorizes sandbox creation. Notion page retrieval does not prove ACL/privacy; the API cannot establish this gate alone.
- `provider_access`: gemini and/or meta only after lawful API/model entitlement and applicable terms are confirmed by the operator.

No IDs or grants are supplied by default. Policy is protected operator configuration, not a request JSON body. Use a dedicated Notion integration restricted to the source and sandbox parent with Read content + Insert content. Do not request Update content, broad workspace sharing, user data or production permissions. Read and Insert under the same integration remain constrained by page sharing and the host allowlists. Notion controls actual permission inheritance; code does not modify it.

Secure environment bindings:

- `CMP_NOTION_TOKEN`: dedicated integration credential, never a Claude credential.
- `CMP_MODEL_TOKEN`, `CMP_MODEL`: selected licensed provider credential and actual entitled model ID; not browser cookies.
- `CMP_POLICY_FILE`: trusted policy path.
- `CMP_APPROVAL_FILE`, `CMP_APPROVAL_KEY`: external approval envelope and verification secret (at least 32 characters; use high entropy).
- `CMP_STATE_DIR`: protected persistent journal + fsynced audit directory; retain across process restarts and runs. Ephemeral Actions runners are unsuitable for live replay protection.

From a private executor, prepare using the selected provider and actual authorized page IDs:

```sh
python3 cmp/executor/bridge_cli.py prepare --provider gemini --execution-id UNIQUE_RUN --source-page SOURCE_UUID --parent-page PRIVATE_SANDBOX_UUID --plan /private/proposal.json
```

For Meta use `--provider meta` and its own token/model/entitlement policy. The command prints only AWAITING_APPROVAL and the plan hash. The private proposal contains the summary, IDs and source digest. Review it through the existing private governance channel. Never paste internal content/credentials into a public issue.

Approval envelope contract (no usable approval is included in source):

```json
{"claims":{"plan_sha256":"SHA256_OF_EXACT_PLAN","action":"sandbox_create","environment":"sandbox","reviewer":"AUTHORIZED_HUMAN_ID","expires_at":0},"signature":"EXTERNAL_HMAC_SHA256_HEX"}
```

Sign UTF-8 JSON of claims with keys sorted, separators comma/colon, ensure_ascii=false, using HMAC-SHA256. Plan digest uses the same JSON canonicalization and SHA-256. Approval expiry must be a Unix integer in the next hour at execution. The plan digest binds provider, model, source ID/digest, parent ID, execution ID, title and exact body. Human Governance must review those fields; its approval service is outside this package. A generic permission grant does not substitute for this exact-content approval.

```sh
python3 cmp/executor/bridge_cli.py execute --plan /private/proposal.json
```

Run on private infrastructure only: successful stdout includes the new sandbox page URL. Audit logs contain execution/provider/hash/reviewer/action/time and final page ID/URL, never source text, model text, tokens or upstream response bodies. Audit records are local durable records, not a tamper-proof ledger; protect and retain them using the existing executor's log controls. No public artifact upload exists. Transport preserves inherited proxy/CA settings, disables redirects, bounds responses/timeouts, retries only GET 429/selected 5xx with bounded Retry-After. Model requests and CREATE are never automatically retried.

## Codex 2 independent acceptance

Offline command: `python3 -m unittest discover -s tests/cmp -v`. Test IDs, tokens and content are synthetic. No live API or staging is required for these tests. See EVIDENCE-148.md for the exact local result and reviewed limitations.

When valid rights and approvals are handed over, Codex 2 should independently pin the Draft PR commit, run the offline suite, then run prepare/approved execute in the existing private executor for each provider. Verify READ, CREATE and READBACK separately, inspect source/parent policy and inherited private access, capture the actual new page URL and commit/environment in private evidence, and publish only a redacted summary. Until then both providers' live READ/CREATE/READBACK are NOT RUN, not FAIL or PASS. No staging UI is claimed without a handed-over endpoint.

PR #141 remains Draft with its existing staging gates. Canonical ID, Parent, DID, ACL, Registry, /69, /id and official Notion documents are unchanged. Merge, production deploy and release remain outside this Draft PR.

## Official references checked 2026-10-17

- https://developers.notion.com/reference/post-page — page parent/title/children and Insert capability.
- https://developers.notion.com/reference/get-block-children — top-level block pagination; nested traversal is separate.
- https://developers.notion.com/reference/request-limits — rate limits and request bounds.
- https://ai.google.dev/api/generate-content — Developer API generateContent contract.
- https://ai.google.dev/gemini-api/docs/api-key — API authentication; key belongs in header, not query/log.
- https://cloud.google.com/vertex-ai/generative-ai/docs/start/quickstarts/quickstart-multimodal — separate Vertex project/IAM setup.
- https://github.com/meta-llama/llama-api-python — official native API SDK; _client.py base URL, resources/chat/completions.py request, types/completion_message.py response.

The llama.com documentation scrape was unsupported in this session. The official SDK source was read through GitHub instead. Current provider availability and legal entitlements remain unverified, not inferred from documentation.

