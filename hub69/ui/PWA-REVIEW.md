# HUB 69 PWA sandbox handoff

Extends UI PR #164 at `a1f888d4308636fde979e9a678ed8e15d0c69800`, related to #156. Reuses the Website, routes, design system and existing Core binding. No second Backend or Registry.

Run `node build.mjs` in this directory. Serve `dist/` on loopback for snapshot review, or review `core-dist/` for a future approved same-origin Core mount. No mount or deployment is performed here. The self-contained `HUB69-review.html` remains a file review with no PWA registration.

The HTTPS/loopback bundle includes a scoped manifest, generated 192/512 PNG icons and a service worker. Its only cached resource is a data-free offline notice. Shell navigation uses the network first. API, authentication, Registry and all other requests bypass the worker. Reconnecting requires reloading through HUB 69. Offline login is unavailable. No installability or physical-device acceptance is claimed.

Acceptance evidence: `evidence/pwa/results.json` binds source hashes; `unit.log` records 92 direct Node test assertions, zero failures. Build verifies the unchanged Registry blob. Four new tests exercise worker isolation, offline navigation, bundle/PNG consistency and inert registration. Browser launch is BLOCKED by sandbox Chromium SIGTRAP (`setsockopt: Operation not permitted`); no screenshot, browser accessibility, installation, HTTPS or real iPhone result is claimed.

P0A: existing unified UI retained, browser acceptance pending. P0B: PWA bundle prepared, installation pending. P0C: existing synthetic directory/reference screens retained; real product/service catalogue and search remain OPEN. P0D: existing Core seam retained; exact handler conformance and integrated Core acceptance remain OPEN. P0E: unit/build evidence available; integrated device demo remains BLOCKED.

Native direction: prioritize this shared PWA for sandbox review. SwiftUI is a later iOS client of the same API; Xtool requires a separate current-toolchain and signing check. Android can evaluate a Trusted Web Activity once the approved HTTPS origin and asset association exist. No native toolchain research or builds were completed in this change.

Before any release: review this exact commit, validate private HTTPS and Core authorization, test install/relaunch/offline/reconnect on actual Safari iPhone and Android, check keyboard/accessibility and all sample links, then obtain Independent Review and Human Governance. Rollback is reverting this UI-only delta; no server state changes exist.

HOLD ACTIVATION • PRODUCTION NO-GO. No production deploy, merge, payment, CFPT, Registry, Stable ID, Parent, DID or Canonical changes.
