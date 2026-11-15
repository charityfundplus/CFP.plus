# Codex 1 → Codex 2 • Registry/Core API binding • 16/10/2026

This is an additive continuation of PR124, not a new API, Registry or deployment. The earlier `p0-20261016` handoff remains historical evidence. PR140 UI at `6daec1ca72a65f542392aeb70592a7ed9b5453f6` is a static source snapshot and has not been mounted into Core or production by this change.

## Existing authority and source boundary

`registry/SYNC_CURRENT_SYSTEM.md` orders GitHub current Registry/master standard, Notion working directory/review queue, Google copy, then verified public website. `AI_CANONICAL_ID_REGISTRY.md` declares a **Review / Working Registry**, governed by CFP+ Human Governance. This is the authoritative working source path for the API; it is not evidence of Canonical Lock, identity approval, a verified 91-pair runtime roster or grants.

The Core reads exactly six existing root files, matching each byte to the checked-out Git revision:

- `registry/global-country-ai-index.json`
- `registry/country-route-map.json`
- `registry/ai-entity-registry.json`
- `registry/AI_CANONICAL_ID_REGISTRY.md`
- `registry/CFP_GLOBAL_AI_ID_LINK_MASTER_STANDARD.md`
- `registry/SYNC_CURRENT_SYSTEM.md`

The entity JSON has 20 developer + 6 AI bindings. The country index adds 99 country and 99 AI-country references: **224 read-model rows**, not 224 verified identities or 91 pairs. The Notion review list is not loaded by the runtime. Offline comparison is evidence only; it cannot allocate IDs or import Parent/DID. No root Registry file or historical JSON copy is changed.

## Packaged release binding

The existing `P2Sandbox` accepts the server-only option `registrySource: {root, revision}`. The two existing launchers also accept **both** `CFP_REGISTRY_SOURCE_ROOT` (absolute path to the existing repository checkout) and `CFP_REGISTRY_SOURCE_REVISION` (its exact 40-character HEAD). These are operator configuration, never HTTP request fields. The service account needs read access to those six files, the repository Git objects and the Git executable. No Registry write permission is needed.

The release points at that checkout; it does not bundle a second Master Registry. Invalid configuration fails startup. Missing source, changed source bytes or a moved source HEAD produces `503 REGISTRY_SOURCE_UNAVAILABLE`, even when the package contains historical JSON. Retain the configured source checkout at the pinned revision for the local rehearsal; do not silently move/rebind it. The source pin and executable revision are separate provenance scopes. Local test configuration is not approval to change a cloud host or launch a preview.

## One API, one authenticated client

Routes and status codes remain the existing contract in `../p0-20261016/CORE_API_CONTRACT.md`. Session cookie, Origin, Host, read authorization and durable response-digest audit are unchanged. New `/registry-client.js` is a same-origin ES module; the existing `/p2` Link Mẫu panel now uses it. It performs no third-party call or identity write and has no snapshot fallback on 401/404/503.

```js
import {createRegistryClient} from '/registry-client.js';
const client = createRegistryClient(); // existing cfp_p2 login first
const data = await client.snapshot(); // all pages, one revision, 224 references now
const openai = await client.openai();
const detail = await client.detail('691181');
```

For PR140, provide the returned `data` to the UI **before** `app.js` captures `HUB69_DATA.records`. The projection maps `parent → parent_id`, `super-pair → pair`, `description → intro`, preserves ID/DID/Parent values and provides each record's actual source revision/blob/SHA-256. Source bytes do not imply identity or runtime authority. Pagination rejects a revision/hash change, duplicate IDs or incomplete pages. IDs longer than PR140's 80-character limit fail explicitly; Core still accepts up to 256 digits without conversion or truncation.

PR140 currently hardcodes its source link and OpenAI/vault views. Codex 2 must render the returned per-record provenance and `client.openai()` data instead of presenting the static 8356163 snapshot as runtime evidence. It must handle loading, login/401, not-found/404, source-unavailable/503, logout, navigation and retry without showing stale profiles. A same-origin mount with the existing auth session is required; cross-origin hosting is not enabled here. This handoff is a contract and tested adapter, not a claim that PR140 is already connected.

## OpenAI data and remaining authority

The existing chain stays `911 → 6911 → 69118 → 691181`. The reference profile adds four checked public content sources: OpenAI About, ChatGPT overview, official support guidance and Projects documentation. A public support channel is distinct from a verified CFP+ contact. Products remain references to the existing ChatGPT ID, not new product IDs. HSTDN ID/Parent/DID/Canonical remain null; SI roster, legal relationship, operational permissions, competence and 6-vault sync remain unverified. The existing US mapping hold remains in force.

## Required handoff from Codex 2 / Human Governance

| Dependency | Needed source/access | Approver / owner |
|---|---|---|
| PR140 runtime integration | UI bootstrap/error/provenance updates using this same-origin client, its own branch and reviewable commit | Codex 2; Codex 1 reviews integration |
| 91 runtime pair bindings | Existing Master source/export with record identity, explicit Parent/DID where applicable, revision/checksum, visibility and granted scope | CFP+ Human Governance / designated Registry custodian; a REVIEW ONLY page is insufficient |
| HSTDN OpenAI identity | Approved existing HSTDN binding and relationships, or an explicit decision that the reference remains unallocated | CFP+ Human Governance with HSTDN/SI AI source owners |
| Preview verification | Existing approved private HTTPS URL, deployed executable/source pins, authorized test account and service read access to the pinned Registry checkout | Human Governance and environment owner; Codex 2 tests UI/iPhone |
| Independent acceptance | Exact executable SHA, manifest and affected-scope test evidence | ReviewSI; no ACK inferred |

GitHub and the two Notion source pages were readable. No missing read permission blocked this local delta. The remaining identity authority, preview environment and UI integration are specific missing dependencies. Do not request or send passwords/tokens. HOLD ACTIVATION • HUMAN REVIEW • PRODUCTION NO-GO.
