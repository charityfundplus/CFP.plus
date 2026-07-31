# CFP+ GitHub Migration Manifest

**Document Type:** Migration Control Registry  
**Lifecycle Status:** Active  
**Governance Authority:** CFP+ Human Governance  
**Source of Truth:** Notion  
**Working Space:** Google Drive  
**Canonical Public Repository:** GitHub  

## 1. Purpose

Tài liệu này kiểm soát việc chuyển **toàn bộ tài liệu CFP+** sang GitHub theo đúng chương và đúng vị trí trong kiến trúc CFP+.

Tất cả tài liệu đều được đưa vào GitHub, bao gồm:

- Canonical Locked
- Governance Approved
- Review Complete
- Review Candidate
- Draft
- Active
- Superseded
- Archived
- Evidence
- Work Orders

Lifecycle Status phải được giữ nguyên trong metadata. Trạng thái chưa khóa không phải là lý do để loại tài liệu khỏi GitHub.

## 2. Mandatory Placement Rule

Mỗi tài liệu phải được đặt theo **nội dung và chương phụ trách**, không đặt theo trạng thái lifecycle.

- Chương xác định vị trí lưu trữ.
- Lifecycle Status xác định mức độ thẩm quyền của tài liệu.
- Canonical ID hoặc Document ID xác định danh tính.
- Không tái phân bổ ID trong quá trình migration.
- Không biến Draft thành Locked chỉ vì tài liệu đã được đưa lên GitHub.
- Không để tài liệu chưa khóa nằm ngoài hệ thống chương.

## 3. Chapter Structure

| Chapter | Scope | GitHub Directory |
|---|---|---|
| 0 | Foundation, Entry Point, System Baseline | `0/` |
| 1 | Sự Sống | `1/` |
| 2 | Con Người | `2/` |
| 3 | Ba Quỹ | `3/` |
| 4 | Tôn Giáo | `4/` |
| 5 | Cộng Đồng | `5/` |
| 6 | AI và Công Nghệ | `6/` |
| 7 | Doanh Nghiệp | `7/` |
| 8 | Tổ Chức | `8/` |
| 9 | Quốc Gia và Vùng lãnh thổ | `9/` |

Các thư mục kỹ thuật hiện có như `governance/`, `registry/`, `website/`, `operations/`, `reviews/`, `evidence/` được giữ trong thời gian chuyển tiếp, nhưng mọi tài liệu phải có Chapter Reference rõ ràng và sau đó được ánh xạ về cấu trúc 0–9.

## 4. Migration Order

Việc nhập tài liệu không phụ thuộc vào trạng thái khóa. Thứ tự ưu tiên dùng để kiểm soát migration:

1. Foundation và Constitution
2. Charters
3. Governance Standards
4. Country Registry và Chapter 9
5. AI Registry và Chapter 6
6. Website Standards
7. Operations
8. Independent Reviews
9. Evidence Packages
10. Draft, Superseded và Archive

## 5. Documents Identified for Migration

| Priority | Document | Document ID / Canonical ID | Chapter | Source Status | GitHub Status |
|---|---|---|---|---|---|
| P0 | Priority Work Order Execution Report — 30-07-2026 | CFP-REP-2026-0730 | 0 / Operations | Locked for Migration | Pending content import |
| P0 | CFP+ Canonical AI Profile Master Template | 600 | 6 | Review Candidate | Pending content import |
| P0 | ChatGPT Canonical AI Profile | 6666600 | 6 | Review Candidate | Pending ID reconciliation, not blocked from import |
| P0 | Gemini Canonical AI Profile | 66666-100 | 6 | Review Candidate | Pending ID reconciliation, not blocked from import |
| P0 | Website Framework v1.0 | CFP-WEB-001 | 0 / Website | Candidate / Working Source | Pending content import |
| P1 | Gemini Website Architecture Review Package | CFP-AI-REV-GEM-001 | 0 / Review | Review Evidence | Pending content import |
| P1 | Canonical Alignment — Gemini Work Order | Priority 2 | 6 / Operations | Operational Work Order | Pending content import |
| P1 | GitHub Migration and AI Work Queue Instruction | Unassigned | 0 / Operations | Operational Instruction | Pending content import |

## 6. Existing Repository Anchors

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

## 7. Publication Labels

Mỗi file phải ghi đúng một trạng thái nguồn, chẳng hạn:

- `Lifecycle Status: Canonical Locked`
- `Lifecycle Status: Governance Approved`
- `Lifecycle Status: Review Candidate`
- `Lifecycle Status: Draft`
- `Lifecycle Status: Superseded`
- `Lifecycle Status: Archived`

GitHub lưu toàn bộ lịch sử; chỉ tài liệu đạt gate mới được gọi là Canonical Locked.

## 8. Migration Validation

Một tài liệu được ghi là `Migrated` khi:

1. Nội dung nguồn đã được chuyển đầy đủ.
2. Có Chapter Reference.
3. Có Lifecycle Status.
4. Có Source Reference.
5. Có đường dẫn GitHub trực tiếp.

Một tài liệu chỉ được ghi là `Migrated — Canonical` khi ngoài các điều kiện trên còn có Governance Approval và Canonical Lock hợp lệ.

## 9. Known Conflicts to Preserve as Evidence

Các xung đột không được dùng làm lý do bỏ tài liệu khỏi GitHub. Chúng phải được đưa vào đúng chương và gắn nhãn conflict:

- Namespace AI cũ `66666...` và cấu trúc AI Country Hub `69...`.
- Mâu thuẫn `69119` giữa Apple và VietLinker AI.
- Trạng thái thực thể tại `69849`.
- Xung đột CFP-WEB-002 và CFP-WEB-003.
- Canonical Namespace Architecture chưa khóa.
- Evidence Standard chưa khóa.

## 10. Current Migration Decision

**Đưa tất cả tài liệu vào GitHub theo đúng chương, không phân biệt đã khóa hay chưa khóa.**

Không xóa, không che giấu và không bỏ qua tài liệu chỉ vì tài liệu đang Draft, Review Candidate, có conflict hoặc đã Superseded. Trạng thái và mâu thuẫn phải được ghi công khai, rõ ràng và truy vết được.

**Current Status:** Full Migration Intake Open — Chapter Placement Required
