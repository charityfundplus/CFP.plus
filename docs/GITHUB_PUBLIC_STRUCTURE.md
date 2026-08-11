# CFP+ GitHub Public Structure & Legacy Handling

**Status:** Review Candidate  
**Scope:** Public GitHub organization only  
**Authority boundary:** No Canonical ID/Link change; no Canonical Lock; no merge authority.

## Objective

Keep CFP+ GitHub clean, understandable and compact while preserving evidence and history.

## Public active layer

Use the shortest path needed for a reader to understand CFP+:

1. `README.md` — concise entry point.
2. `HUB69.md` — global gateway.
3. `CMP.md` — coordination/orchestration contract.
4. `AI_INDEX.md` — current discoverable AI directory.
5. `registry/` — current identity/profile records and machine-readable references.
6. `website/` — public website implementation and maps.
7. `governance/` — current governance rules and locked-document references.

## Working/review layer

- Feature branches and Draft PRs hold changes under review.
- `reports/` holds validation, migration and review packages.
- Working evidence should not be promoted into active public navigation until validated.

## Legacy / quarantine rule

Information that is stale, conflicting, duplicated or unsafe to edit immediately must not remain presented as current authority.

Classify it as:

- `LEGACY` — historical but still useful for provenance;
- `QUARANTINE` — conflicts with current authority or validation;
- `MIGRATION_BACKLOG` — requires later reconciliation or Human Governance decision.

Preserve original evidence, timestamp, source and change history. Do not silently delete or rewrite history.

## Promotion rule

A record returns to the active public layer only after:

`Evidence → Validation → Review → Authority Gate (when required) → Current/Public`

## Simplicity rule

Prefer one current page per concept. Avoid parallel current indexes, duplicate navigation pages, temporary IDs, repeated explanations and legacy material in primary navigation.

**Public should be simple. History should remain traceable. Authority should be unambiguous.**
