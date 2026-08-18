# CFP+ • AI WORK STANDARD v0.2 • CMP DIRECT WORK STANDARD

Status: REVIEW CANDIDATE

## Architecture

`AI ↔ CMP ↔ Notion / GitHub / Google`

No AI-system interaction may bypass CMP.

## Common capability contract

`READ → WRITE → VERIFY → EVIDENCE → RETURN`

CMP controls:

- Work Order
- AI identity
- Target system and resource
- Allowed action
- Verification / read-back
- Evidence receipt and return

## Platform requirements

### Notion
AI may read or write only through CMP under the active Work Order.

### GitHub
AI may read repository content and write through controlled file/branch/PR operations routed by CMP.

### Google
AI integration must support direct Google Docs read/write, not Drive read-only access.

## Verification rule

Do not mark a connection VERIFIED because a link opens. A platform connection is VERIFIED only after executable READ and WRITE tests pass and the written result is read back successfully.

## Gemini pilot

CH7 • Doanh Nghiệp is the first Gemini pilot target. CH7 is not an architectural limit and tool schemas must remain generic.

Current status: `HUMAN MEDIATED • INTEGRATION NOT VERIFIED`

## Guardrails

- No renumber
- No Canonical Drift
- No automatic Governance Approve
- No automatic Canonical Lock
- No fabricated execution evidence

Only Plus+ For Life
