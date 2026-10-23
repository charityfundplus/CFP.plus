# Issue #154 • existing Core sandbox catalogue read

Baseline: PR #124 at `06f386b1ba52358779cec6bc26c2d88f6a33664a`. Adds a versioned read projection to the existing P2 Core server, SQLite workspace state, account sessions, pair grants and durable hash-chain audit. No new server, Registry, database schema or seed-on-startup. PR #157 remains the separate disabled public-publication proposal; this route does not enable it.

`GET /api/v1/commerce/catalog?pairKey=hub69-content-demo&query=&kind=all&limit=30&offset=0`

Authentication: existing `cfp_p2` HttpOnly SameSite=Strict session, provided by `POST /api/session` with locally provisioned synthetic accounts. HTTPS Preview sets Secure when configured. No credentials in URLs or browser storage. The read is private to the authenticated workspace and requires an existing pair grant; there is no anonymous/public catalogue.

Allowed query fields: required `pairKey` (lowercase sandbox key, maximum 80 characters), optional `query` (string, maximum 160 characters, NFKC/case-insensitive name search), `kind` (`all`, `profile`, `hstdn`, `product`, `service`), integer `limit` 1–100 default 30 and integer `offset` 0–10000 default 0. Duplicate/unknown fields, malformed values and excessive lengths fail 400. Numeric Stable IDs are neither input nor assigned here.

Response 200:

```json
{
  "items": [], "total": 0, "limit": 30, "offset": 0,
  "catalogRevision": "<64 lowercase hex SHA-256 of the complete projected catalogue>",
  "sandbox": true, "synthetic": true, "readOnly": true,
  "registryWrites": 0, "activationAllowed": false
}
```

Each item contains only `key`, `name`, `kind`, `scope`, `maturity`, `status`, `id`, `parent`, `did`, `canonical`, `synthetic`, `verification`. `key` is an opaque existing sandbox record reference, never a Stable ID or Canonical URL. `scope`/`maturity` are strings or null. `status` is always `SANDBOX_ONLY`; `verification` is `NOT VERIFIED`; identity fields are all null. Source URLs, contacts, declarations, subjects, task data, inquiry/opportunity records and membership references are omitted. Within an authorized workspace/pair, the catalogue is shared between its authorized users; inquiries/opportunities remain under their existing owner rules.

Errors: 401 session missing/invalid/expired; 403 Host or pair scope denied; 400 invalid query or unavailable pair; 503 audit/storage integrity failure. Unsupported POST does not invoke a writer and follows the existing server's 404 route policy. Every successful read appends `commerce:catalog` with `sha256:<hash(response)>`, authenticated subject/workspace. Read fails closed if storage/audit verification or append fails. No Office state or Registry is written by the reader; only audit is appended.

Data is read from existing Office records created through `office-create`; an empty workspace returns zero rows. Tests alone create synthetic fixtures through existing methods. This change adds no moderation/publication approval, inventory synchronization, merchant verification, payment, order placement or CFPT path.

Codex 2: use same-origin `fetch` with `credentials: 'same-origin'`, `cache: 'no-store'`; display sandbox labels and auth/loading/error/empty states. Do not replace a failed Core read with local demo rows. PWA worker must bypass this API. HUB 69 remains the entry route.

Validation: `node tests/commerce-catalog-v1.test.mjs` (4/4), affected `node tests/commercial-flow.test.mjs` (3/3). These invoke the real HTTP request handler with Node stream requests and temporary SQLite, without sockets. The default sandbox denied loopback listen with EPERM. Root later confirmed additional sandbox network permission allows loopback TCP, and reported real Core TCP7 and Chromium integrated12 PASS on these four copied source files against a full baseline checkout. Root will bind its final receipts to the published commit; these cross-agent checks are not included in this agent's 7-test log. The new standalone loopback test was authored but its requested run was interrupted before any result, so it is NOT RUN in this receipt. Safari iPhone, approved HTTPS staging and production acceptance remain NOT RUN. `tests.log` records this candidate's tests; `evidence.json` pins modified sources.

Existing #157 malformed approval finding was already remediated at current SHA `383ffcf5fa3a229d442393a86fa189e52bc09289`; no duplicate fix was created. Its PR body still lists the older finding. Identity/Parent coverage, six-vault connections and Quantum vault authority remain unresolved and untouched.

Rollback: revert this source delta; no schema migration or data deletion. HOLD ACTIVATION • PRODUCTION NO-GO. Draft only; Independent Review and Human Governance required before activation. No merge/deploy/mount, production credentials or identity mutation.

Primary-agent final receipt supersedes the earlier default-sandbox EPERM note: actual TCP 1/1 PASS in loopback-root.log. Companion UI #172 records real Registry HTTP 6/6, commerce HTTP 1/1 and Chromium common-Backend flow 12/12 PASS. HTTPS, physical Safari iPhone and native acceptance remain NOT RUN. OpenAPI 3.1 review contract: openapi.json. No Registry source bytes changed.
