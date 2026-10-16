# Existing Link Mẫu — nine sections and synthetic commerce UI

Source: Issue130 comments6164223236 and6164303346; existing Notion template
https://app.notion.com/p/3f3caac9a557816fb38bd1629d7c300d, snapshot last edited
2026-10-14T02:47:12.504Z, native verification unverified. Three display levels are
a proposed mapping; V/000/135/246/789 groups and ten chapters are source-derived.
Slot0 is a recursive topic position, distinct from Chapter0 and immutable IDs.

Existing Core Office preserves12modules and routes. Nine navigation sections:
identity, introduction, registration, training, work, commerce, evidence,
governance and links. Authenticated declarations remain unresolved/pending;
HUB69 /4376 /267 expected routes are not destination-readback verified.

New commercial-office.js uses the existing server API and granted pair only:
catalog-search → inquiry-create (buy/sell/partner/invest) → inquiry-match
(score/reasons) → opportunity-create → opportunity-status → commerce-state
readback. Empty result/record states explicitly show zero/no match. All entities,
matching and opportunities are synthetic; no real contacts, payments, contracts,
partnership certification or automatic grants. UI role restrictions supplement
server enforcement. Creating a new inquiry clears old matches; match buttons
capture their originating inquiry; pair refresh clears stale office selections.

Validation: Node syntax checks for office-intake.js and commercial-office.js.
Browser renderer tests/link-commercial-render.py uses intercepted static assets
and mocked401 API only. Attempted run BLOCKED before page creation: Chromium
crashpad setsockopt EPERM and SIGTRAP. No mobile screenshot or renderer PASS.
Real HTTP E2E, Safari iPhone and already-approved HTTPS preview remain BLOCKED;
server-handler API receipts are separately produced by the integration owner.
No network approval re-requested. No remote write/deployment by UI subtask.

Focused no-socket validation: tests/commercial-export-validation.test.mjs PASS4
using the actual export callback in a VM with mocked transport: final audit
readback/digest, tampered record rejection, changed pair rejection and changed
build rejection. This is export logic evidence, not browser/server E2E.
Creation requests supply top-level idempotency keys, retained for identical
failed requests and cleared after successful readback. Export includes own
commercial records only, authenticates scope again, checks final audit links
and record hashes, and preserves the original training digest envelope.
