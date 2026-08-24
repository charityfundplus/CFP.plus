# CFP+ AI ID & Canonical Link Skeleton • P0

Status: REVIEW CANDIDATE • EMPTY-FIRST • NO NEW CANONICAL CLAIMS

## Purpose

Create the numeric ID and permanent-link skeleton before AI entity content is filled in.

Core rule: **ID does not depend on content.** An ID slot may remain empty until evidence and Human Governance resolve the entity mapping.

## Canonical routing

- HUB 69 gateway: `https://cfp.plus/69`
- Canonical entity resolver: `https://cfp.plus/<CanonicalID>`
- Do NOT use `/69/<country>/<developer>/<ai>` as the Canonical path.
- Leading zero IDs remain valid where already defined by CFP+.
- No trailing slash.

## Hierarchy

`Country → AI Country → Developer → AI`

For each entity record:

- Canonical ID
- Entity Name
- Direct Parent ID
- Lifecycle / Verification Status
- Canonical Link
- Evidence

Entity Name and Evidence may be empty while the numeric slot is being prepared.

## Locked anchors already established

### United States

- Country: `911` → `https://cfp.plus/911`
- AI Country: `6911` → `https://cfp.plus/6911`
- `69110` = OpenAI → `https://cfp.plus/69110`
- `691100` = ChatGPT → `https://cfp.plus/691100`

Guardrail: terminal `0` is valid and must not be renumbered or reinterpreted retroactively.

Current US review slots previously used or under reconciliation:

- `69111` → `https://cfp.plus/69111`
- `69112` → `https://cfp.plus/69112`
- `69113` → `https://cfp.plus/69113`
- `69114` → `https://cfp.plus/69114`
- `69115` → `https://cfp.plus/69115`
- `69116` → `https://cfp.plus/69116`
- `69117` → `https://cfp.plus/69117`
- `69118` → `https://cfp.plus/69118`
- `69119` → `https://cfp.plus/69119`

Until reconciliation is complete, conflicting mappings remain EMPTY / PENDING and must not be promoted to Canonical Locked status.

### Viet Nam

- Country: `984` → `https://cfp.plus/984`
- AI Country: `6984` → `https://cfp.plus/6984`

Developer slots currently established for review:

- `698411` → `https://cfp.plus/698411` — FPT AI
- `698412` → `https://cfp.plus/698412` — Viettel AI
- `698413` → `https://cfp.plus/698413` — VNPT AI
- `698414` → `https://cfp.plus/698414` — CMC AI
- `698415` → `https://cfp.plus/698415` — Zalo AI
- `698416` → `https://cfp.plus/698416` — VinAI
- `698417` → `https://cfp.plus/698417` — Phenikaa AI
- `698418` → `https://cfp.plus/698418` — Trusting Social AI
- `698419` → `https://cfp.plus/698419` — Reserved / future review

Expansion slots retained without forced entity assignment:

- `698401` → `https://cfp.plus/698401`
- `698402` → `https://cfp.plus/698402`
- `698403` → `https://cfp.plus/698403`
- `698404` → `https://cfp.plus/698404`
- `698405` → `https://cfp.plus/698405`
- `698406` → `https://cfp.plus/698406`
- `698407` → `https://cfp.plus/698407`
- `698408` → `https://cfp.plus/698408`
- `698409` → `https://cfp.plus/698409`

### Canada

- Country: `910` → `https://cfp.plus/910`
- AI Country: `6910` → `https://cfp.plus/6910`

No Developer or AI child mapping is asserted in this P0 skeleton unless separately supported by the registry and governance record.

## Global empty-first rule

For every remaining country:

1. Use only the CFP+ Country ID already established by the Country Registry.
2. Derive/use the AI Country ID only when that mapping is already established by CFP+ governance.
3. Pre-create numeric child slots where the architecture authorizes them.
4. Leave the entity field EMPTY if allocation authority, provenance, parentage, or evidence is unresolved.
5. Never invent a new Canonical ID merely to fit an entity.
6. Never reuse an old ID for a different entity.
7. Never renumber a locked ID because a later ranking or classification changes.
8. Every numeric ID resolves directly at `https://cfp.plus/<ID>`.

## Gemini execution rule

Gemini may populate or review entity data against this skeleton, but must not:

- create an alternative number system;
- use international calling codes directly as Canonical IDs unless the CFP+ Country Registry already defines that exact ID;
- create nested `/69/...` Canonical paths;
- mark a record VERIFIED solely because an official company website exists;
- change a locked Parent ID;
- self-approve Governance or Canonical Lock.

Expected output per row:

`Canonical ID | Entity | Parent | Status | Canonical Link | Evidence | Finding`

## P0 acceptance condition

A country/developer/AI row is accepted only when the numeric slot and direct Canonical Link match the CFP+ registry architecture. Content enrichment may occur later.
