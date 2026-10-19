# Issue #156 • Core → Website / App / Gemini handoff

HOLD ACTIVATION • PRODUCTION NO-GO. Design review only; no merge, deploy, DNS,
ID/Parent/DID/Canonical mutation, live connector or new Registry/service.

## Sources actually inspected

- Repository: charityfundplus/CFP.plus (default main).
- main HEAD observed: `835616308111f6851c0387fa9f5eda60c9ffa624`.
- Core PR124 HEAD/base for this contract: `06f386b1ba52358779cec6bc26c2d88f6a33664a`,
  branch `codex/si-office-p0-draft-20261013`, PR base `main`.
- New review branch: `codex/issue156-openapi-readonly`; PR targets the existing
  Core branch to isolate this contract delta. This does not merge either branch.
- No checkout was initially present. Git clone failed connecting to the configured
  proxy; pinned files and complete, non-truncated Git trees were read via GitHub.
- No AGENTS.md appeared in either complete main or Core tree.
- Duplicate search for OpenAPI/#156 PRs found no match; existing PR124/140/141
  remain the integration sources, not replaced by this handoff.
- `50d17cc1be8408e4e0fd9981a4ff0e15129e6efa` exists, but the commit changes
  SI Office Core files; its complete tree contains root `sitemap.xml` and no path
  matching Google Sites. This neither proves nor disproves an external Gemini
  package. The reported 65 files / 40 tests have NOT been independently accepted.
  Supply exact package paths, run logs, manifest and Gemini branch to reconcile.

## Contract and compatibility

`openapi.json` is OpenAPI 3.1, JSON serialization. All operations are GET.
It covers existing search/detail and proposed public projection, with separate
schemas to avoid presenting future fields as already implemented.

Existing `/api/core/registry` and `/api/core/registry/{id}` match the inspected
`drafts/si-office/sandbox/p2-http.mjs` and `core/registry-read-model.mjs` at Core pin.
Use `public/registry-client.js` with same-origin credentials for Website and an
approved same-origin App shell. Exact numeric strings preserve zeros; Core accepts
up to 256 digits while that UI currently rejects display IDs above 80 digits.
Native App OAuth/PKCE and cross-origin access are BLOCKED pending an approved
identity design. Do not copy the demo bearer-role session from `server.mjs` into
P2: it is a different synthetic demo API.

Existing companion routes outside this narrowed read contract:
`GET /api/core/registry-validation`, `GET /api/core/hstdn-openai`,
`GET /api/core/state`, `POST /api/session`, `POST /api/logout`,
`POST /api/core/chatgpt-project` and synthetic task/office operations. The project
route creates a manual packet, not an external ChatGPT project. None becomes a
public API through this specification. Query keys are allowlisted, duplicates
rejected; errors use `{error: string}`. Never substitute a 404/503 with cached
identity data. Read/search are idempotent but each access appends an audit event.

Proposed `/api/core/public/registry` and `.../{id}` are DESIGN_ONLY_DISABLED,
not mounted. They belong in the existing service only after review; no second
API backend. Anonymous reads are permitted ONLY for externally approved exact
public projections. Missing approval, expired approval or source/audit failure
fails closed; unknown and unpublished IDs both return 404. Lists/counts/pagination
must run AFTER filtering authorized records, including parent, child and evidence
links. Do not leak private parents/owners through lineage, errors or count changes.
Unresolved Parent/collision records are excluded rather than repaired.

Published fields: id, parent, did, SI, AI, software, robot, capability, owner,
status, evidence, canonicalLink, name/type, source status/revision, hold flags.
All keys required; unknown identity/owner/DID is null, missing verified bindings
are empty arrays. Null is unknown, never a new allocation or a claim of no owner.
Each exposed field (including evidence URLs, Owner and Parent references) needs
an explicit public disclosure decision. DID has no invented syntax: original
Registry value only. Capabilities and binding references grant no execution rights.
`status` in public records/capabilities is restricted to `approved` during HOLD;
`sourceStatus` preserves raw Registry status. Internal Capability lifecycle remains
separate. `active`, `discovered` and `pending_review` cannot appear as public status.
Populated SI/AI/Robot bindings and software claims require nonempty Evidence;
missing verified bindings stay empty. A later active schema requires separate
review of actual output/readback and Governance authorization. This Draft grants
no activation. An externally approved claim remains subject to all these checks.

`publication_policy.py` is an OFFLINE reference helper, not a deployed endpoint,
signature verifier or approval issuer. Caller MUST verify external Governance
signature, issuer, key, decision revocation and field access before setting its
trusted `signatureVerified` input; it must never accept that boolean from HTTP.
The helper then enforces exact content hash, public audience, revision, expiry,
field approval, schema, evidence and hold. Its hash is sorted-key compact UTF-8
JSON with ensure_ascii=False; this is not a cross-language canonicalization
standard. Other languages must consume exact signed bytes or agree on a reviewed
canonical encoding before integration. No unsigned checkbox is an approval.

## Public pagination pin (disabled facade / offline model)

`published_page()` models fail-closed publication filtering BEFORE search/counts/
offsets. It accepts trusted source records and externally verified current approval
receipts from ONE atomic authorization snapshot. The real caller must verify
signatures, linked-field disclosure and revocation; caller-injected booleans never
authorize public access. Malformed/unapproved claims are excluded; an inconsistent
source or duplicate ID fails the request. Every outcome still requires runtime audit.

The helper sorts public records by exact ID string. It derives approvalSetRevision
as SHA-256 of the sorted public `{id, recordHash, approvalHash}` receipt list using
the documented JSON digest encoding. It exposes only the pin, not approval content.
Expired/revoked receipts are removed by current policy before pinning. Renewal of
an effective decision changes approvalHash. The pin identifies the authorized
public view, never counts/private contents. Query is applied after deriving the
pin; repeat the same query/limit for continuation.

Initial offset=0 may omit pins and returns both. For offset>0, clients must send
`revision=sourceRevision` AND `approvalRevision=approvalSetRevision`. Missing pins
map to 400; source/approval mismatch maps to 409 PUBLICATION_SNAPSHOT_CHANGED.
Discard all partial pages and restart; never reuse old approval snapshots or offset.
A long gap/expiry requires revalidation. Native real signature verification,
revocation snapshot consistency and audit are still NOT IMPLEMENTED by this helper.

## Security review and acceptance requirements

| Control | Inspected current behavior | Proposed / unresolved requirement |
|---|---|---|
| Authentication | P2 service validates server-side account/session; 900s HttpOnly SameSite=Strict cookie; Secure on configured HTTPS preview; revoke/logout | No demo role self-selection; HTTPS mount and actual accounts not available here; native identity design pending |
| Authorization | `readRegistry` authenticates any provisioned account; Registry is a public-reference view, not pair grants | Record/field publication filter is NOT implemented by existing routes; do not expose Core directly to Google Sites |
| Least privilege | Fixed source paths/revision binding, no HTTP-selected source path; no Registry writer in read model | Source mount read-only; adapter identity only approved-reference.read, no canonical write scopes; no role inheritance from capability/Owner |
| Audit | Existing readRegistry appends response hash in service transaction; denies go through httpDenial | Public route must audit allow/deny with correlation, pseudonymous actor, operation, source/approval hashes and decision; log failure returns 503; retention/access/redaction and independent custody remain pending |
| Idempotency/replay | GET reads do not mutate Registry, though audit grows | Public first page returns sourceRevision + approvalSetRevision; continuation must send revision + approvalRevision. Re-evaluate current signatures/expiry/revocation, recompute approval-set pin from one atomic source/auth snapshot; mismatch returns 409, discard mixed pages. No promotion on replay or write idempotency endpoint |
| Retry | No new transport added | Safe GET only, <=3 attempts, 5s each, total 20s, full jitter 1s/2s capped 5s; retry 429/502/503/504, validated connection resets/timeouts only; no auth/parse/conflict retry; long Retry-After ends this budget |
| Credentials | No credential accessed by this change | Dedicated runtime secret bindings, never URLs/logs/query/browser/localStorage/artifacts; rotate/revoke per owner; TLS verification, fixed HTTPS origin+path allowlist, no redirects, no caller URL, block private/metadata destinations and DNS rebinding |
| Browser access | Existing exact Host policy, no CORS; POST Origin check; no-store response, CSP frame-ancestors none | Preserve same-origin Core. Google Sites cannot embed existing P2 iframe/cookie flow; approved public projection fetch or generated link card only. CORS allowlisted approved origins, no credentials, no wildcard credentialed policy; preview tests pending |
| Resource limits | Existing query 160 chars, limit 1..100, offset 0..10000 | Rate-limit anonymous read before expensive work, max response 1MiB, timeout/connection caps; query stripping is not authorization; 429 Retry-After; all limits require runtime tests |

No runtime security acceptance is claimed from these offline tests. Signed approval
verification, revocation, audit failure, CORS/rate-limit/SSRF behavior require
implementation and independent adversarial HTTP tests before any activation.

## Adapter contract

`adapters.json` supplies five disabled adapter slots: US HSTDN, VN HSTDN, Chi Hội,
8682 TMTC, 8882 TTTC. Keys are operational configuration names, NOT Canonical IDs.
Reference IDs are source/task references, not verified HSTDN/Chi Hội identity binds.
Transport interface: `readApprovedReference({existingID, sourceRevision,
approvalDecision, fieldAllowlist, cursor}) -> {projection, sourceHash,
readbackHash, observedAt, auditReceipt}`. All fields server-owned except the exact
ID/filter input authorized by policy. Each adapter maps via explicit reviewed
source field → public contract field, never by numeric prefix or name similarity.

Only GET from approved fixed endpoints; output validated against PublishedRecord.
No credentials, network calls or writes occur in these configs. Missing endpoint,
owner, identity, scope, approval or revision returns BLOCKED, never fake success.
No canonical writer dependency, approval endpoint or activation operation exists.
Discovery → pending_review → approved requires evidence and authorized decision;
active requires actual authorized readback/output evidence. Quarantine any
changed ID/Parent/DID/conflict in the existing review queue, never overwrite.
8682 has no checkout/order/payment action; 8882 has no financial/account action.

## Integration and rollback

1. Gemini/Codex 2 review pinned OpenAPI, mapping and blockers from Draft PR.
2. Generate types with a reviewed OpenAPI 3.1 generator. Existing Website/App
   uses CorePage/CoreDetail; PublishedRecord is a FUTURE adapter boundary.
3. Implement publication approval verification/filter/audit inside existing Core,
   offline first. No Google Sites API key or Core cookie in page HTML.
4. After separately authorized HTTPS staging/account/source mount, run real
   401/403/404/409/503/revoke, field isolation, stale-approval, pagination,
   credentials redaction, audit failure, retry and actual Google Sites origin tests.
5. Record caller-specific readback, exact source/deploy SHA, URL/TLS/rollback and
   independent acceptance. No assertion that Gemini/Codex 2 ACKed this delivery.

Rollback for this PR is removal of added `contracts/issue156/` files on this review
branch. No migration or persisted data is introduced. Future runtime rollback
requires a separate data-preserving reviewed plan; do not switch live pointers.

## Blockers

- Gemini package/file manifest and 40-test execution evidence not reconciled.
- Parent 6→69→696→6969 lacks verified Registry rows/explicit edges.
- US identity collision and VN Parent/coverage conflicts (REGISTRY_MAPPING.md).
- No authoritative complete Siêu Bộ Đôi/SI/Robot/HSTDN/Chi Hội roster, DID, Owner,
  capability bindings or public field approval receipts supplied.
- 8682/8882 endpoint, ACL/owner, credentials, scopes and protocol unverified.
- Public projection routes, signature verification/revocation, field authorization,
  anonymous rate limits and hardened adapter transports are design only.
- No approved staging URL/account/source mount, native App identity, Google Sites
  origin/preview or authorized live readback; no device/Safari acceptance.
- Full OpenAPI semantic validator unavailable locally (dependency installation
  blocked by proxy); JSON Schema Draft2020-12 and structural checks are separate.
- Independent external Gemini/Codex 2 review and Human Governance decision pending.
- Medium remediation is candidate-only; see FINDING_CLOSURE.md for evidence, owners
  and exact closure criteria. Same-session checks are not external acceptance.
