# CFP+ • CODEX HANDOFF • NAMECHEAP + CLOUDFLARE + R2
Date: 2026-10-17
Status: READY FOR CODEX REVIEW • NO PRODUCTION DEPLOYMENT

## Goal
CFP+ states it currently uses Namecheap and Cloudflare services as a customer. Publish concise independent HSTDN profiles for both companies; prepare a private Cloudflare R2 object store for website/app/backend/Siêu Bộ Đôi artifacts. Do not imply official partnerships.

## Codex 1 — registry and backend
1. Look up existing immutable numeric Canonical IDs and Parents for both companies in authoritative Master Registry; do not mint, guess, renumber or lock DID/0.
2. Confirm official company product, sales and support URLs, and phone/email only if verified.
3. Design R2 adapter with least-privilege credentials held in secrets management, explicit authorization, bucket access policy, object-key convention, idempotency, checksums, write receipts, readback verification, retry and audit events.
4. Use existing backend `services/cfp-core` as a prototype reference, not a production integration. No sensitive or financial data transfers without explicit approval.

## Codex 2 — website and app
1. After registry confirmation, create one canonical numeric page per HSTDN and link from HUB 69.
2. Each page: short introduction, products/services, official buy/sales/support links, CFP+ independent customer relationship statement.
3. Verify mobile Safari, navigation, official links, preview URL and deployed SHA.
4. Do not duplicate website architecture or bypass existing staging/production approval.

## Siêu Phần Mềm — automation
Implement checks for canonical routes, parent-child navigation, link availability, outbox processing state and storage write/read receipts. Report PASS/FAIL/BLOCKED with timestamp, SHA and evidence; never report untested functionality as ACTIVE.

## Cloudflare R2 — staged implementation
- P0: Verify account/project ownership and approved access path (no tokens in GitHub issues).
- P1: Create private test bucket only after authorization; confirm encryption, access control, lifecycle and backup/recovery requirements.
- P2: Test upload → checksum → readback → delete/retention behavior using non-sensitive synthetic data.
- P3: Add reviewed backend adapter, then connect permitted storage workflows and monitoring.
- P4: Production release only after evidence and Human Governance approval.

## Definition of done
Two pages with verified canonical IDs and functioning official links; R2 bucket and adapter verified independently with synthetic-data receipts; no unsupported claims of partnerships, payment handling, sync completion or production activation.

References: `website/HSTDN-NAMECHEAP-CLOUDFLARE-V1.md`, `services/cfp-core/README.md`, PR #142.
