# Website / App / TMTC 8682 sandbox integration

Related existing work: #154 Backend, #138 Website/App, #169 technology feasibility, Core #124, UI #164 and PWA #172. Keep the existing stacked Draft PRs; no duplicate task or inventory is created.

## Implemented

The existing HUB 69 `#commerce` screen now includes a product/service catalogue, with `#catalog` filters and opaque sandbox detail routes. Website, App shortcuts and TMTC use the same router, design system, session and Core binding. Search supports Vietnamese accent folding locally, explicit server search, category selection, pagination and empty/loading/denied states. Detail navigation preserves the selected Core page/filter. These hash routes are UI navigation, never new Canonical links or Stable IDs.

Snapshot mode contains four visibly synthetic fixtures with null ID/Parent/DID/Canonical. Core mode starts empty and never falls back to them. It reads the existing Core projection:

`GET /api/v1/commerce/catalog?pairKey=hub69-content-demo&query=&kind=all&limit=30&offset=0`

The existing Core owns the HttpOnly session, workspace/pair authorization, SQLite Office records and durable audit. The UI adds the read inside its same-origin client wrapper; no cross-origin API URL, new authentication system or credential storage. The pair name is a sandbox reference, not authority or an entity binding. No auto-seed occurs outside tests.

The UI accepts only synthetic/read-only/non-activating envelopes with zero Registry writes, bounded pagination/revision and null identities. It drops private/extra fields, escapes text and rejects duplicate keys and active status claims. Reload clears the old response; failed reads/logout hide rows. The PWA never caches this API/authentication.

## Reproduce

Build with `node build.mjs`. Open `HUB69-review.html#catalog` for snapshot review. For a local PWA bundle use `python -m http.server --bind 127.0.0.1 --directory dist 4173`, then `http://127.0.0.1:4173/index.html#catalog`. This loopback address is not an external preview.

Set `CFP_COMMERCE_CORE_SOURCE` to the reviewed Core checkout and run `node integration/commerce-core.test.mjs` and `node integration/commerce-browser-core.mjs`. The latter temporarily serves `core-dist/` beside Core on loopback, provisions synthetic accounts/Office drafts in temporary SQLite, launches Chromium and removes server/state afterwards. It reads the actual Git-bound Registry through Core. Python Playwright and system Chromium are test dependencies; loopback/browser sockets require sandbox network permission.

`python integration/commerce-browser.py` separately tests 390/768/1440 px, existing five groups/ten chapters, search, labels/menu focus, PWA registration/cache isolation and offline/reconnect. These are Chromium/basic accessibility smoke checks, not physical iPhone or WCAG certification. The new catalogue emits internal router links; inherited external sample links are not certified by these checks.

## Acceptance and findings

| Deliverable | Sandbox evidence | Remaining acceptance |
|---|---|---|
| P0A Website + HUB 69 | Shared router, five groups/ten chapters, responsive checks | Production unchanged; live content/group-baseline reconciliation and independent acceptance pending |
| P0B App/PWA | Build, manifest/icons, worker, App navigation, offline/reconnect | Real Safari iPhone, Android/desktop installation, HTTPS and native builds not run |
| P0C TMTC | Synthetic cards/detail/search/category/pagination; authenticated Office read | No real merchants, provenance/moderation approval, inventory or public listings |
| P0D Common Backend | Real Core session → Registry ID screen → App → TMTC → logout on Chromium loopback | No production/native client or six-vault/Quantum synchronization claim |
| P0E Demo/evidence | Local artifact, screenshots, hashes, test receipts | No externally hosted demo URL; Independent Review/Human Governance pending |

HIGH/Governance: US/Vietnam identity/Parent coverage and chain evidence remain unresolved; Registry is untouched. Six-vault connections and Quantum authority remain unverified and are shown pending.

MEDIUM: inherited UI/Core display projection caps numeric IDs at 80 digits while server permits 256; long-ID compatibility remains open. Local search folds Vietnamese diacritics; server follows its documented normalization and may differ. Independent catalogue pages do not promise a transactional snapshot if drafts change concurrently; `catalogRevision` is available for review and every page is authorized independently.

BLOCKED/PENDING: actual iPhone/Android access and private HTTPS staging URL are unavailable. Full accessibility, all inherited external links, native toolchain/signing, full dependency SBOM/advisory review and real merchant acceptance remain open. Technology research is feasibility, not approval.

Firecrawl retrieved https://cfp.plus/, /69 and /8682 with HTTP 200 on 2026-10-23. This proves page retrieval only, not this revision's deployment, complete navigation, TLS/device acceptance or common Backend integration.

Rollback: revert the UI delta and rebuild; no schema/data migration. HOLD ACTIVATION • PRODUCTION NO-GO. No production mount, DNS/IAM change, payment, CFPT, merge or deployment. Activation remains with Independent Review and Human Governance.
