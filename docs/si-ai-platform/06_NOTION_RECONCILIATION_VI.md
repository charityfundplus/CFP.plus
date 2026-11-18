# 06 • Đối Chiếu Notion ↔ GitHub ↔ Website ↔ Registry

**Trạng thái:** REVIEW CANDIDATE • Chỉ đọc và đối chiếu • Không sửa Notion, Registry hay Canonical
**Thời điểm đọc Notion:** 2026-11-18 (qua connector Notion của phiên này)
**Mốc GitHub:** `main` @ `835616308111f6851c0387fa9f5eda60c9ffa624` • PR #124 @ `e994ea884fdf7a06ca5efe20674b96a0d51e24f8`

## 1 • Trang Notion đã đọc (18/18 truy cập được)

| # | Trang | Sửa lần cuối (UTC) | Đọc | Nhãn trạng thái ghi trong trang |
|---|---|---|---|---|
| 1 | [Bản Đồ Link Gốc & Hồ Sơ Sống](https://app.notion.com/p/c49caac9a557821da26a81752cc1daca) | 2026-10-20 | Toàn bộ | SOURCE INVENTORY / CANONICAL LINK PROPOSED / RUNTIME UNVERIFIED |
| 2 | [Danh Mục Siêu Bộ Đôi theo 10 Chương](https://app.notion.com/p/3f2caac9a55781fd97afe7ecd489c3fc) | 2026-11-11 | Toàn bộ | LIVING INDEX • REVIEW CANDIDATE • Canonical Lock NO |
| 3 | [HUB 69 • 5 Nhóm • 10 Chương](https://app.notion.com/p/3ffcaac9a557819f8f1ff524b757518e) | 2026-11-16 | **Một phần** (~142 nghìn ký tự; đã đọc mục lục, quy ước ID/SBD, 5 Nhóm D•V, 10 Module, Core Backend, và tìm theo từ khóa Luật Thép/8882/28882/số 0) | Bản copy để sắp xếp • PROPOSED • REVIEW REQUIRED |
| 4 | [Mẫu Chung Siêu Bộ Đôi](https://app.notion.com/p/3f2caac9a557813ea55defe8118accaf) | 2026-11-11 | Toàn bộ | SETUP / REVIEW CANDIDATE • Canonical Lock NO |
| 5 | [Kiến Trúc 10 Chương Đệ Quy](https://app.notion.com/p/41bcaac9a557810287dac33c21f8d7b9) | 2026-11-17 | Toàn bộ | BẢN THẢO NGHIÊN CỨU • REVIEW • CHƯA NỘP |
| 6 | [Văn Phòng SI AI • Link Mẫu Chung](https://app.notion.com/p/404caac9a5578101a46ee8246ea7d002) | 2026-11-16 | **Một phần** (~72 nghìn ký tự; mục lục, phần đầu, Siêu Bộ Đôi đa nền tảng, kết quả sandbox, Kho Tri Thức) | SANDBOX GO • PRODUCTION NO-GO |
| 7 | [Diễn Đàn Team S0S SI AI](https://app.notion.com/p/405caac9a55781eda523d237254863de) | 2026-11-16 | **Một phần** (~67 nghìn ký tự; mục lục, đầu mối thực thi, 20 Văn Phòng, quy ước trạng thái) | PILOT • HOLD ACTIVATION • PRODUCTION NO-GO |
| 8 | [Ma trận phân công & ACK](https://app.notion.com/p/405caac9a55781d3b904dad89df623ce) | 2026-11-14 | Toàn bộ | DOCUMENT ASSIGNED • ACK PENDING • RUNTIME UNVERIFIED |
| 9–18 | 10 trang Chương 0–9 "Link Học Hỏi & Áp Dụng" | 2026-11-11 | Toàn bộ | CHƯA XÁC MINH • CHỜ ĐỐI CHIẾU |

**Không truy cập được:** 0 trang. Các trang con được nhắc đến (Danh sách 91 chuẩn đặt tên, Master84, Bản đồ lõi 5 Kho, 20 Văn Phòng riêng…) **chưa mở** trong lượt này.

## 2 • Bản Canonical, bản sao, nội dung chưa phê duyệt

| Loại | Tài liệu | Căn cứ |
|---|---|---|
| **Canonical có khóa** | `HUB69.md` trên GitHub (P0 Baseline **LOCKED**): HUB 69 là HUB duy nhất | Nhãn trong tài liệu |
| **Baseline Candidate** | `website/WEBSITE_MASTER_MAP_VI.md`, `README.md`, Open Review Workflow | Nhãn trong tài liệu |
| **Bản sao (theo chính nhãn Notion)** | Mục "HUB 69 • Mục lục mới" và "Danh mục Siêu Bộ Đôi • Bản copy" trong trang HUB 69 Notion | "Bản copy để sắp xếp tài liệu. Bản chuẩn không bị thay đổi" |
| **Hai trang Notion cho cùng một ID** | 33 ID có cả "Link Siêu Bộ Đôi" (trang Danh Mục, tiền tố `3f2c…`) lẫn "Link Học Hỏi & Áp Dụng" (trang Chương, tiền tố `3f3c…`), ví dụ 237 | Trang Chương tự ghi "không phải DID hoặc hồ sơ canonical thứ hai" |
| **Chưa phê duyệt** | Toàn bộ 18 trang Notion; toàn bộ 91 Siêu Bộ Đôi | Không trang nào ghi VERIFIED hoặc Canonical Lock YES |

## 3 • Đối chiếu link Siêu Bộ Đôi (đã chạy thật)

Nguồn: 10 trang Chương → [`data/super-pair-source-inventory.json`](data/super-pair-source-inventory.json). Kiểm tra: [`tools/link-audit.mjs`](tools/link-audit.mjs) → [`evidence/link-audit.json`](evidence/link-audit.json), chạy lúc 2026-11-18T22:59:50Z.

| Chỉ số | Kết quả |
|---|---|
| Siêu Bộ Đôi trong 10 trang Chương | **91** (0:5 • 1:4 • 2:18 • 3:15 • 4:6 • 5:12 • 6:9 • 7:8 • 8:8 • 9:6), khớp số ghi trên trang Danh Mục |
| Có Link Notion riêng | **89/91**. Thiếu: 2273, 2588 |
| Có thư mục trang trong repo (`<ID>/index.html`) | **19/91** |
| `cfp.plus/<ID>/` có trang riêng (OWN_PAGE) | **19/91**, trùng khớp 100% với 19 thư mục trong repo |
| `cfp.plus/<ID>/` chỉ trả trang dự phòng `/id/` (ID_FALLBACK) | **72/91**. HTTP 200 nhưng nội dung giống hệt từng byte trang `/id/` ("CFP+ • AI Office") |
| VERIFIED / ACTIVE | **0/91** |
| Bản Đồ Link Gốc (trang 1) | 84 dòng = 83 ID (333 xuất hiện 2 lần). 91 = 83 + 8 ID: 2273, 2588, 2838, 2877, 330, 4347, 4742, 5835. Khớp số liệu ghi trong PR #124 |
| Trang Danh Mục (trang 2) | 33 hồ sơ "Link Siêu Bộ Đôi". **2624 • Bảo Mật** không có trong 91 (91 chỉ có 2684 • Bảo Mật Tổng Hợp) |

## 4 • Xung đột cập nhật sau khi đọc Notion

| Mã | Nội dung | GitHub / Website | Notion | Đề xuất |
|---|---|---|---|---|
| **C1** | 5 Nhóm | Master Map: `V • 0 • 135 • 246 • 789`, cấm D | `[D • V] • 000 • 135 • 246 • 789`, D = 500, V = 5, "một nhóm thống nhất" (PROPOSED 2026-10-20). PR #124 hiển thị 000/135/246/789, V là governance | HG chọn một bộ. Website giữ Master Map đến khi có quyết định |
| **C2** | Tên Chương 6 | "AI & Công Nghệ" | Đề nghị "SI 🤖 AI 🤖 Robot 🤖 Siêu Phần Mềm & Công Nghệ" (PROPOSED). Trang Chương 6 vẫn ghi "AI & Công Nghệ" | Chờ HG |
| **C3** | 8882 / 28882 | 28882 có trang riêng (OWN_PAGE). 8882 chỉ là trang dự phòng | **Ba tên khác nhau cho 8882**: "TTTC", "Tri Thức Toàn Cầu", "Thị Trường Toàn Cầu". Một mục HUB 69 ghi "28882 → lối cũ, redirect sang 8882" | HG xác nhận 8882 là gì và có chuyển 28882 hay không |
| **C4** | Luật Thép • ID 58 | Không có văn bản. `website/58.md` = "Tổ Chức trong Cộng Đồng". `/58/` là trang dự phòng | Luật Thép nằm trong tên **4742** "Hiến Pháp, Hiến Chương, DNA, Công Thức, Quy Tắc & Luật Thép" (Chương 4). Không trang nào ghi Luật Thép = 58 | Cần văn bản nguyên văn và ID chính thức |
| **C5** | Quy tắc số 0 | Numeric Link Rule: 0–9 đầy đủ (→ 1.110) | Kiến trúc đệ quy: "vị trí 0 dành cho mở rộng; vị trí thường ưu tiên 1–9". Mẫu Chung: X0 = nâng cấp, X1–X9 = chức năng (→ 910 + nhánh X0). **Nhưng 6 ID nguồn đã dùng 0 làm vị trí thường**: 00, 000, 003, 005, 330, 500 | HG quyết định quy tắc cho ID mới mà không đổi 6 ID đã có |
| **C6** | Parent | PR #124: Parent lấy từ tham chiếu tường minh | **Cả 84 dòng** Bản Đồ Link Gốc ghi "Parent: chờ đối chiếu" | Chưa dựng được cây Cha–Con–Cháu thật. Adapter giữ `parent: null` |
| **C8** | ID Gemini | `registry/ai-entity-registry.json` 691141 ≠ thư mục 6911421 | — | Registry custodian |
| **C9** | Nguồn có thẩm quyền | GitHub Registry JSON (PR #124, PUBLIC_CURRENT_SYSTEM) | HUB 69 Notion: "Notion là nơi làm việc chính … Source of Truth"; cùng trang yêu cầu HG giải quyết khác biệt với JSON Registry | HG lập ma trận: loại dữ liệu → nguồn có thẩm quyền |
| **C10** | ID 333 | — | Hai hồ sơ nguồn: "Quỹ Đầu Tư" và "Tài Chính & Ba Quỹ" | Chờ Human Review (Notion đã ghi) |
| **C11** | 2273, 2588 | Không có trang | Không có Link Notion riêng | Chờ đối chiếu |
| **C12** | Mã Nhóm trùng ID Siêu Bộ Đôi | — | 000, 135, 246, 789 vừa là mã Nhóm vừa là ID Siêu Bộ Đôi; 500 = D | Notion ghi "quan hệ phả hệ và quan hệ điều phối Nhóm là hai loại riêng". Cần ghi rõ trong Registry |
| **C13** | 2624 so với 2684 | — | Danh Mục có 2624 • Bảo Mật; danh sách 91 có 2684 • Bảo Mật Tổng Hợp | Xác định có phải hai thực thể |
| **C14** | "4 Phương 10 Hướng" hay "4 Phương 8 Hướng" | — | Trang Chương 0 ghi 10 Hướng; trang Chương 1–9 ghi 8 Hướng | Thống nhất câu chữ |

## 5 • PR sandbox đang chồng chéo (rủi ro trùng lặp)

Notion và GitHub cho thấy nhiều PR Draft cùng làm Diễn Đàn/Văn Phòng. PR #232 **không** dựng thêm một Diễn Đàn hay backend, chỉ liên kết tới các nguồn sẵn có.

| Phạm vi | PR / Issue đang mở |
|---|---|
| Core API & Registry | #124 (nền tảng được kế thừa), #137, #173 |
| Diễn Đàn & Văn Phòng backend | #195, #219, #183, #184, #193, #214, #179 |
| Văn Phòng / Link Mẫu sandbox | #203, #206, #207, #218 |
| Website khung 10 Chương | #189, #111, #110, #217 |
| Diễn Đàn tạm | Issue #201 |

**Đề xuất:** Human Governance chỉ định **một** PR Diễn Đàn chính (ứng viên: #195 hoặc #219) và **một** Core (#124). Các PR còn lại chuyển vào PR chính hoặc đóng có ghi chú.
