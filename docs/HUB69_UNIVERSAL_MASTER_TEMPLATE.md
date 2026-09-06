# HUB 69 Universal Master Template • Five-Repository • Review Candidate

## Mục tiêu

Một mẫu chung duy nhất để **Notion • GitHub • Google • Cloud Website • ChatGPT** cùng phản chiếu một identity CFP+ theo HUB 69, cùng Stable ID, cùng Parent, cùng metadata lõi và cùng Canonical Web URL.

**Architecture:** Five-Repository  
**Architecture Decision:** KEEP  
**Direction:** GO WITH FINDINGS  
**Governance Approved:** NO  
**Canonical Locked:** NO  
**Production Release:** NO

## 0 • Canonical Web Link

1. HUB 69: https://cfp.plus/69
2. Mọi ID: `https://cfp.plus/{StableID}`
3. Một Stable ID → một Canonical Web URL.
4. Không nền tảng nào được tự tạo Canonical URL khác.
5. Không đổi, reuse, remap hoặc renumber Stable ID.
6. Chỉ ghi `LIVE` khi URL thật mở đúng nội dung.

## 1 • Five-Repository Architecture

1. **Notion** — Editorial / Review Workspace.
2. **GitHub** — Technical Registry / Version Registry.
3. **Google** — Evidence / Archive / Collaboration.
4. **Cloud Website** — Canonical Public Runtime.
5. **ChatGPT** — AI Workspace / downstream mirror sau khi Cloud ổn định.

Tất cả 5 kho độc lập nhưng đồng bộ qua **HUB 69**.

Publication flow:

`Notion → GitHub → Google → Cloud Website → Stability Verification → ChatGPT Mirror`

## 2 • Universal Identity Fields

Mọi hồ sơ trên cả 5 kho phải dùng cùng mẫu metadata:

- Title
- Stable ID
- Parent ID
- HUB ID: `69`
- Node Type
- Group
- Chapter
- Language
- Content Status
- Review Status
- Governance Status
- Canonical Web URL: `https://cfp.plus/{StableID}`
- Notion Page URL / ID
- GitHub Path / Commit SHA
- Google Drive URL / File ID / Revision
- Cloud Route / Build SHA / Validation Evidence
- ChatGPT Mirror Reference / Sync State
- Content Hash
- Evidence Link
- Review Record
- Governance Decision
- Last Updated
- Next Action
- Sync State

## 3 • Universal Page Template

### Identity

**Title:**  
**Stable ID:**  
**Parent ID:**  
**HUB ID:** `69`  
**Canonical Web URL:** `https://cfp.plus/{StableID}`  
**Node Type:**

### Placement

**Group:**  
**Chapter:**  
**Language:**

### Content

Toàn văn nội dung hiện hành.

### Evidence

Nguồn, provenance, trạng thái evidence và thời điểm kiểm tra.

### Review

`Finding → Evidence/Reason → Proposed Action → Closure Criteria`

### Governance

AI chỉ review, phân loại finding và đề xuất. AI không tự Governance Approve, Canonical Lock hoặc Production Release.

### Five-Repository Sync

**Notion:**  
**GitHub:**  
**Google:**  
**Cloud Website:**  
**ChatGPT:**  
**Canonical Web URL:** `https://cfp.plus/{StableID}`  
**Sync State:** `SYNC PENDING | SYNC PASS`

### Release

**Cloud Route:**  
**Build SHA:**  
**Validation:**  
**Rollback Reference:**  
**LIVE:** `NO` cho đến khi URL thật mở đúng nội dung.

## 4 • Sync Rules

1. Cùng Stable ID.
2. Cùng Parent ID.
3. Cùng Title/identity binding theo Registry.
4. Cùng HUB 69.
5. Cùng Canonical Web URL.
6. Metadata lõi phải khớp giữa 5 kho.
7. Payload có thể khác theo chức năng từng kho nhưng không được tạo identity khác.
8. Chỉ `SYNC PASS` khi tất cả trường identity bắt buộc khớp và Web URL đã được kiểm tra.
9. Nếu một kho chưa sẵn sàng, ghi `SYNC PENDING`; không sửa ID để ép đồng bộ.

## 5 • Stable ID Guardrail

- ID số là identity cố định.
- Nội dung thay đổi không làm thay đổi ID số.
- Không cấp, đổi, xóa, tái sử dụng hoặc bind Stable ID trong giai đoạn review nếu chưa có thẩm quyền Human Governance.
- Platform ID chỉ là reference.
- Registry là technical registry, không phải governance authority.

## 6 • Web-Link Rule

Mọi trang/mục đã có Stable ID phải chuẩn bị trường Web:

`https://cfp.plus/{StableID}`

Ví dụ HUB 69:

`https://cfp.plus/69`

Các kho Notion, GitHub, Google và ChatGPT phải trỏ về URL này. Cloud Website là nơi URL canonical được phục vụ công khai.

Không ghi `LIVE` chỉ vì link đã được tạo trong metadata. `LIVE` chỉ khi route thật đã deploy và mở đúng nội dung.

## 7 • Review / Release Boundary

**Current state:**

- Five-Repository Architecture: REVIEW COMPLETE
- Architecture Decision: KEEP
- Architecture Blockers: 0
- Direction: GO WITH FINDINGS
- Canonical Data Contract v1: REVIEW CANDIDATE
- Publishing & Recovery Runbook v1: REVIEW CANDIDATE
- Governance Approved: NO
- Canonical Locked: NO
- Production Release: NO

Một finding chỉ trở thành Release Blocker khi chưa được giải quyết/kiểm chứng bằng evidence **và** trực tiếp ngăn Governance Approval, Canonical Lock hoặc Production Release.

## 8 • CMP

CMP điều phối sync, finding, evidence, closure và publication readiness.

CMP không tự tạo governance power và không tự đổi Stable ID, Canonical URL, Governance Status hoặc Canonical Lock.

## 9 • Điểm vào

- HUB 69 Web: https://cfp.plus/69
- GitHub Template: `docs/HUB69_UNIVERSAL_MASTER_TEMPLATE.md`
- Google Template: `HUB 69 Universal Master Template`
- Notion: HUB 69 / Universal Master Template
- CMP: https://cfp.plus/267

## 10 • Chuẩn chung bắt buộc

**ONE ID → ONE CANONICAL WEB LINK → FIVE INDEPENDENT REPOSITORIES → ONE HUB 69 SYNC CONTRACT**

Không tạo 5 identity khác nhau. Không tạo 5 Canonical URL khác nhau. Các kho độc lập về chức năng nhưng phải cùng xác định một identity CFP+.