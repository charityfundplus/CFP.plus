# HUB 69 • MASTER STANDARD

**Status:** MASTER FRAMEWORK — DRAFT BASELINE
**Canonical ID:** 69
**Canonical Language:** Tiếng Việt
**Authority:** Human Governance

## 1. Purpose

HUB 69 is the common structural framework for CFP+. It is not itself the Website. Notion, GitHub, Google and Website use the same structural IDs and canonical mapping while retaining their own operational roles.

## 2. Core rule

**Có tài liệu thật → định vị → gán ID → xác định canonical source → liên kết các kho.**

Không tạo nội dung để lấp chỗ. Không tạo link trống chỉ để hoàn thành cây.

## 3. Hierarchy

```text
HUB 69
└── 10 Chapters
    └── Con
        └── Cháu
            └── Canonical Record
                ├── Document
                ├── Source
                ├── GitHub
                ├── Notion
                ├── Google
                └── Website presentation
```

The hierarchy must support both forward and reverse reading:

```text
HUB 69 → Chapter → Con → Cháu → Record → Source
Source → Record → Cháu → Con → Chapter → HUB 69
```

## 4. ID principles

- One entity has one Canonical ID.
- Never invent or reuse an existing locked ID.
- Never change a locked ID without Human Governance approval.
- If lineage or placement is uncertain, mark `REVIEW` or `UNKNOWN`.
- Do not infer hierarchy solely from the number of digits.
- Existing country/chapter namespace rules remain authoritative until Governance changes them.

## 5. 10-Chapter baseline

| Chapter | Namespace | Baseline subject |
|---|---|---|
| 0 | 0 + Country ID | Foundation, Constitution, Charter, Governance |
| 1 | 1 + Country ID | Life |
| 2 | 2 + Country ID | Human |
| 3 | 3 + Country ID | Three Funds, CFPI, CFPT |
| 4 | 4 + Country ID | Religion |
| 5 | 5 + Country ID | Community |
| 6 | 6 + Country ID | AI & Technology |
| 7 | 7 + Country ID | Business |
| 8 | 8 + Country ID | Organizations |
| 9 | 9 + Country ID | Countries |

This table is a structural baseline, not permission to migrate or rewrite legacy content.

## 6. Canonical record

Every accepted record should contain, when available:

- ID
- Parent ID
- Chapter ID
- Title
- Type
- Short human-readable description
- Canonical Source
- Official URL
- GitHub URL
- Notion URL
- Google/Web URL
- Related IDs
- Legacy ID
- Status
- Evidence
- Confidence
- Last Checked

## 7. Source roles

- `CANONICAL` — primary authoritative record/source selected by Governance.
- `SUPPORTING` — supporting source such as documentation or repository.
- `REFERENCE` — external directory/reference.
- `RELATED` — related record.
- `LEGACY` — preserved historical source.
- `REVIEW` — requires human decision.
- `UNKNOWN` — insufficient evidence.

## 8. Storage roles

### Notion
Management, working documents, governance, AI coordination, review and structured knowledge operations.

### GitHub
Version-controlled canonical source for code and structured public documentation where designated. Changes should be traceable through commits/reviews.

### Google
Search/discovery and public web presentation where designated. Google is not automatically the canonical source merely because it indexes content.

### Website
Human-first presentation layer. It should present verified content, not empty navigation or unverified placeholders.

### Legacy CFP+
Preservation/reference layer. Legacy content is not migrated, renamed, deleted or unpublished without an explicit execution order.

## 9. One object, multiple controlled representations

A single logical object may be represented in multiple systems, but there must be one designated Canonical Record. Other systems should reference or project the canonical object rather than create competing versions.

## 10. Document intake

```text
New document
→ Read
→ Identify topic
→ Find existing ID
→ Check duplicates
→ Map to Chapter/Con/Cháu
→ Select canonical source
→ Record evidence
→ Store/link in appropriate systems
→ Review if uncertain
```

## 11. Anti-duplication

Do not create separate canonical records merely because the same entity has a different website, GitHub repository, documentation page or directory listing.

## 12. Human-first Website rule

Website readers must be able to understand the subject without understanding the internal ID system. IDs provide traceability and navigation behind the presentation layer.

## 13. Governance guardrails

Until a separate Human Governance execution order authorizes it:

- no bulk migration;
- no bulk duplication;
- no deletion;
- no unpublish;
- no domain change;
- no Homepage change;
- no mass publishing;
- no rewriting legacy content;
- no automatic invitation or permission changes.

## 14. Current domain architecture

- `cfpplus.notion.site` — intended HUB 69 Master Hub target; Homepage remains unselected until separately authorized.
- `charityfundplus.notion.site` — CFP+ primary public/content space during transition; preserve unless separately authorized.
- `rhinestone-phone-26e.notion.site` — legacy; preserve unless separately authorized.
- `cfp.notion.site` — unresolved/unavailable; do not act on it.

## 15. Completion criterion

A HUB 69 area is considered structurally ready only when its records have real source material, stable IDs, canonical mapping, evidence/status and usable links. Empty pages do not count as completed content.

**MASTER STANDARD — LOCKED FOR STRUCTURE, OPEN FOR CONTENT REVIEW**
