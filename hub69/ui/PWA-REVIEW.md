# HUB 69 PWA review handoff

Related: existing Issues #154, #138, #169 and #156. Reuses UI #164 and Core #124 through the existing PR #172. No new Backend or Registry.

Run `node build.mjs`. `dist/` is the synthetic snapshot; `core-dist/` starts empty and uses the existing same-origin Core client. `HUB69-review.html` is the self-contained file review, without manifest/worker registration. Loopback review is not a deploy to cfp.plus.

The scoped PWA manifest/icons/worker cache only a data-free offline notice. API/auth/Registry responses bypass the worker. The retry form forces full navigation, fixing the fragment-only reconnect bug found in browser testing. Worker v2 removes the known v1 notice cache on activation. No offline login or stale data fallback.

Current evidence: `evidence/commerce/results.json`, browser/HTTP logs and screenshots. Chromium now runs with sandbox network permission on loopback; earlier default-sandbox EPERM is not the current browser blocker. Actual Safari iPhone, Android installation, HTTPS, full accessibility and native acceptance remain NOT RUN.

See `TMTC-INTEGRATION.md` for API/demos/findings and `APP-TECHNOLOGY-REVIEW.md` for official-source feasibility. No framework installed or activated.

HOLD ACTIVATION • PRODUCTION NO-GO. No merge, deploy, payment, CFPT or Registry/Stable ID/Parent/DID/Canonical change. Independent Review and Human Governance retain activation authority.
