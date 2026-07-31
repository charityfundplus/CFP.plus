# CFP+ GitHub Migration Manifest

**Document Type:** Migration Control Registry  
**Lifecycle Status:** Active  
**Governance Authority:** CFP+ Human Governance  
**Source of Truth:** Notion  
**Working Space:** Google Drive  
**Canonical Public Repository:** GitHub  

## 1. Purpose

Tài liệu này kiểm soát việc chuyển toàn bộ tài liệu CFP+ sang GitHub theo nguyên tắc:

- Canonical First
- Public First
- Evidence First
- Foundation trước Implementation
- Không ghi đè tài liệu đã khóa bằng bản chưa xác minh
- Một tài liệu Canonical có một đường dẫn công khai trực tiếp

## 2. Migration Order

1. Foundation
2. Constitution
3. Charters
4. Governance Standards
5. Canonical Registries
6. Website Standards
7. Operations
8. Independent Reviews
9. Evidence Packages
10. Archive và Superseded Documents

## 3. Documents Identified for Migration

| Priority | Document | Document ID / Canonical ID | Source Status | GitHub Status |
|---|---|---|---|---|
| P0 | Priority Work Order Execution Report — 30-07-2026 | CFP-REP-2026-0730 | Locked for Migration | Pending content import |
| P0 | CFP+ Canonical AI Profile Master Template | 600 | Review Candidate | Pending governance check |
| P0 | ChatGPT Canonical AI Profile | 6666600 | Review Candidate | Pending ID reconciliation |
| P0 | Gemini Canonical AI Profile | 66666-100 | Review Candidate | Pending ID reconciliation |
| P0 | Website Framework v1.0 | CFP-WEB-001 | Candidate / working source | Pending conflict review |
| P1 | Gemini Website Architecture Review Package | CFP-AI-REV-GEM-001 | Review Evidence | Pending import |
| P1 | Canonical Alignment — Gemini Work Order | Priority 2 | Operational Work Order | Pending import |
| P1 | GitHub Migration and AI Work Queue Instruction | Unassigned | Operational Instruction | Pending canonical classification |

## 4. Existing Canonical Repository Anchors

- `README.md`
- `GITHUB_HUB.md`
- `AI_INDEX.md`
- `registry/AI_CANONICAL_ID_REGISTRY.md`
- `registry/6911.md`
- `registry/6984.md`
- `website/WEBSITE_MASTER_MAP_VI.md`
- `website/PUBLIC_ID_REGISTRY_00_99_VI.md`
- `governance/LOCKED_DOCUMENTS_REGISTRY_VI.md`
- `governance/OPEN_REVIEW_WORKFLOW_VI.md`

## 5. Migration Gates

Một tài liệu chỉ được ghi là `Migrated — Canonical` khi đáp ứng đủ:

1. Có Document ID hoặc Canonical ID duy nhất.
2. Có Lifecycle Status rõ ràng.
3. Không xung đột với tài liệu đã có trong repository.
4. Nội dung nguồn được xác minh đầy đủ.
5. Có lịch sử nguồn và evidence phù hợp.
6. Đường dẫn GitHub trực tiếp đã được kiểm tra.
7. Human Governance cho phép công khai nếu tài liệu chưa ở trạng thái Canonical Locked.

## 6. Immediate Blocking Issues

- Namespace AI cũ `66666...` chưa được đối chiếu hoàn toàn với cấu trúc AI Country Hub `69...`.
- `69119` đang có mâu thuẫn giữa Apple, VietLinker AI và các registry tham chiếu.
- `69849` cần được xác minh trước khi chuyển hoặc khóa bất kỳ hồ sơ liên quan nào.
- CFP-WEB-002 và CFP-WEB-003 cần Governance Decision trước khi hợp nhất.
- Canonical Namespace Architecture và Evidence Standard chưa được khóa.

## 7. Current Migration Decision

Bắt đầu migration theo danh mục có kiểm soát. Không thực hiện chuyển hàng loạt mù quáng và không tái phân bổ Canonical ID trong quá trình migration.

**Current Status:** Migration Intake Open — Canonical Validation Required
