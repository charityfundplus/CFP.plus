# CFP-WEB-000 • Website Master Blueprint v1.0

**Document Type:** Website Architecture Blueprint  
**Lifecycle Status:** Foundation Locked  
**Governance Authority:** Human Governance  
**Canonical Source:** Notion — https://app.notion.com/p/f73f82520ca74436aa8b2487203e5532  
**Source Snapshot:** 2026-07-08T03:27:26.435Z  

*(Website Master Blueprint — entry point & relationship map for the CFP+ Website Architecture Framework)*

## Purpose

Provide a single entry point that:

- introduces the CFP+ Website Architecture Framework,
- lists the foundational specifications (CFP-WEB-001 → CFP-WEB-005),
- clarifies the relationship between them,
- and identifies the Source of Truth for each architecture domain.

## Role (what this document is / is not)

**This document is:** Master Index + Architecture Map (single entry point).

**This document is NOT:**

- detailed implementation instructions,
- Website content,
- Publishing workflow details,
- or a place to restate other specifications.

## Architecture Scope

**Architecture Layer:** Website Foundation  
**Applies To:** All Website Architecture specifications  
**Authority:** CFP-WEB-000 governs the Website Architecture framework only.

It does **not** replace the Source of Truth of any individual architecture specification.

## Constitutional Foundation (Website Root Repository references)

CFP-WEB-000 đóng vai trò **entry point** cho Website Architecture. Tuy nhiên, khi áp dụng triệt để nguyên tắc **“mỗi phạm vi chỉ có một Source Of Truth”**, Website cũng cần một “Root Repository” để **tham chiếu** tới toàn bộ tài sản hiến định và nền tảng phục vụ Website.

> Nguyên tắc: CFP-WEB-000 **không chép lại** nội dung hiến định. CFP-WEB-000 **chỉ làm bản đồ tham chiếu** tới các Source Of Truth tương ứng.

### Proposed structure (reference map)

- **Constitution**
  - Hiến pháp CFP+
  - Hiến pháp Ba Quỹ
  - Các Hiến pháp chuyên đề (future)
- **Charter**
  - Hiến chương Sự Sống
  - Hiến chương Con Người
  - Hiến chương Cộng Đồng
  - Hiến chương Doanh Nghiệp
  - Hiến chương AI
  - Các Hiến chương khác (future)
- **Identity**
  - CFP-IDN — Identity Constitution (CFP+ là ai?)
  - CFP-LOGO — Logo Constitution (Logo chuẩn là gì?)
  - CFP-BRAND — Brand Standard (Sử dụng nhận diện như thế nào?)
  - CFP-MEDIA — Media Assets (Tài nguyên truyền thông chính thức ở đâu?)
- **Language**
  - Language Constitution
  - Official Translation
  - Glossary
  - Canonical Statements
  - Title Standard
  - Editorial Standard
- **Architecture**
  - Master Architecture
  - Website Architecture
  - Knowledge Architecture
  - Universal ID System
  - Registry Standards
- **Source Of Truth Management**
  - Master Copy
  - Version History
  - Change Log
  - Official Release
  - Archive Reference

## Framework map (canonical)

```text
CFP-WEB-000
├── CFP-WEB-001 • Website Content Architecture (SoT: overall website content structure)
├── CFP-WEB-002 • Website Navigation Architecture (SoT: navigation & internal linking)
├── CFP-WEB-003 • Portal Architecture (SoT: portal-page layout standard)
├── CFP-WEB-004 • Content Architecture (SoT: object-level structure: Group/Chapter/Topic/Article/Q&A)
└── CFP-WEB-005 • Publishing Architecture (SoT: publishing workflow, versions, multilingual, registry sync)
```

## Architecture dependency (canonical build order)

```text
CFP-WEB-000
↓
CFP-WEB-001
↓
CFP-WEB-002 / CFP-WEB-003 / CFP-WEB-004 / CFP-WEB-005
↓
Portal Specifications
↓
Page Specifications
↓
Website Content
↓
Published Website
```

## Architecture Principles

The CFP+ Website Architecture shall follow these principles:

- Single Source of Truth.
- Single Responsibility for each specification.
- No duplicated architecture.
- Reference instead of repetition.
- Stable architecture, extensible implementation.
- Long-term compatibility.

## Future Expansion

Additional Website Architecture specifications may be added in the future.

Every new specification shall:

- have a unique Document ID,
- define a single architecture domain,
- identify its Source of Truth,
- declare its relationship to existing specifications,
- and be registered through CFP-WEB-000.

## Architecture Lifecycle

**Status:** Foundation Locked  
**Changes:** Only structural architecture changes are permitted through an approved architecture revision.

Implementation changes shall not modify this blueprint.

## Source of Truth matrix

| Domain | Source of Truth |
|---|---|
| Website content structure (overall) | CFP-WEB-001 |
| Navigation + internal linking | CFP-WEB-002 |
| Portal page layout | CFP-WEB-003 |
| Content objects (Group/Chapter/Topic/Article/Q&A) | CFP-WEB-004 |
| Publishing + release + multilingual + registry sync | CFP-WEB-005 |

## Governance notes

- CFP-WEB-001 → CFP-WEB-005 are intended to be stable, long-lived architecture specifications.
- Implementation priorities (e.g., “Website First Strategy”) live in separate strategy documents (e.g., CFP-WEB-STR-001) and may evolve without changing this framework.
- When in doubt: link back to the applicable SoT document above instead of redefining architecture elsewhere.
