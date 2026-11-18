# 08 • 6 Kho Dữ Liệu • Mô-đun Làm Việc • Thí Điểm Thực Tế

**Trạng thái:** PILOT • SANDBOX • READ ONLY • PRODUCTION NO-GO
**Chạy lúc:** 2026-11-18T23:16Z • Core PR #124 ghim `e994ea8` (không sửa)

## 1 • P0 • Kế thừa và chống trùng lặp

| Kiểm tra | Kết quả |
|---|---|
| Core API / Registry | Dùng **PR #124**: `createRegistryReadModel` (91 Siêu Bộ Đôi) và `P2Sandbox` + `CoreEngine` (vòng đời nhiệm vụ, audit chain). Không sửa mã PR #124 |
| Backend thứ hai | **Không tạo.** Thí điểm chỉ thêm mô-đun phân tích chỉ-đọc và một kịch bản gọi API công khai của `P2Sandbox` |
| Trùng lặp phát hiện | Hiện đã có **một backend song song khác**: PR #195/#193 (Python Diễn Đàn + Supabase schema `cfp_office` + dịch vụ Render sandbox). Hai Core cùng tồn tại → **HG-15** cần chọn một |
| Canonical ID, Parent, DID, Luật Thép | Không thay đổi. `registryWrites = 0` |

## 2 • P1 • Trạng thái thật của 6 Kho (thăm dò chỉ đọc, 2026-11-18)

| Kho | Vai trò | Thăm dò | Trạng thái |
|---|---|---|---|
| **GitHub** | Mã nguồn, kiểm thử, Evidence | git + GitHub MCP | ✅ **CONNECTED**: đọc toàn repo; ghi chỉ trên nhánh làm việc |
| **Notion** | Tri thức, giáo trình, hồ sơ Siêu Bộ Đôi | Notion MCP | ✅ **CONNECTED (READ)**: 18/18 trang + tìm kiếm. Chưa ghi |
| **Google** | Tài liệu, bảng dữ liệu | Google Drive MCP | ⏳ **PENDING**: connector trả lời nhưng tài khoản này thấy **0** file CFP+; tài liệu Drive mà Notion trỏ tới báo "not found" |
| **Web** | Nguồn công khai | curl qua proxy | ⚠️ **PARTIAL**: chỉ `cfp.plus` (91 ID đã kiểm). Wikipedia, arXiv, notion.so, docs.google.com bị chặn |
| **Cloud** | Lưu trữ, xử lý | Supabase, Render, Cloudflare, BigQuery | ⚠️ **READ metadata**: Supabase 1 project sandbox, schema `cfp_office` 13 bảng, **0 dòng**. Render 1 dịch vụ Diễn Đàn sandbox. Cloudflare 0 Worker. BigQuery thiếu project ID. Chưa ghi gì |
| **Lượng Tử** | Nghiên cứu lượng tử | Notion search | ⏳ **PENDING**: chỉ có trang nghiên cứu (v0.1, Siêu Bộ Đôi 5878). Không có hạ tầng |

**Tổng: 2/6 kết nối đầy đủ (GitHub, Notion đọc) • 2/6 một phần (Web, Cloud) • 2/6 PENDING (Google, Lượng Tử).** Dữ liệu: [`data/six-stores-inventory.json`](data/six-stores-inventory.json).

## 3 • P2 • Mô-đun vận hành cho mỗi Siêu Bộ Đôi

| # | Bước | Thực hiện ở đâu | Đã chạy? |
|---|---|---|---|
| 1 | Tiếp nhận nhiệm vụ | `P2Sandbox.execute('createTask')` (PR #124) | ✅ 3 task |
| 2 | Xác định quyền | Tài khoản + `pairs` grant + role (PR #124) | ✅ 4 lần từ chối đúng thiết kế |
| 3 | Tìm, đọc dữ liệu | `tools/work-modules.mjs` (chỉ đọc) | ✅ GitHub, Notion snapshot, Web audit |
| 4 | Phân loại 5 Nhóm / 10 Chương / ID | `classifyAndJoin()` + quy tắc nhóm của PR #124 | ✅ 91/91 |
| 5 | Phát hiện trùng, thiếu, sai, mâu thuẫn | `githubRegistryAudit()`, `notionCrossCheck()` | ✅ 22 + 50 phát hiện |
| 6 | Nghiên cứu, đề xuất | `proposedAction` mỗi ID + mục 5 bên dưới | ✅ |
| 7 | Kiểm chứng chéo | Reviewer **chạy lại** mô-đun, so SHA-256, rồi mới duyệt | ✅ 3/3 khớp |
| 8 | Tạo sản phẩm | Báo cáo JSON T1–T3 | ✅ |
| 9 | Lưu Evidence, kiểm thử | `evidence/pilot/` + audit checkpoint + 5 test | ✅ |
| 10 | Báo cáo, giới hạn, việc tiếp | Tài liệu này | ✅ |

## 4 • P3 + P4 • Thí điểm có kết quả thật

Luồng: **HUB 69 → (Diễn Đàn: chưa có backend chọn) → Văn Phòng `pilot-hub69` → Task Queue (PR #124) → Kho GitHub / Notion / Web → Review độc lập → Evidence → Sản phẩm**

### Siêu Bộ Đôi tham gia (vai trò sandbox)

| Vai trò | Siêu Bộ Đôi (ID nguồn Notion) | Tài khoản sandbox | Quyền |
|---|---|---|---|
| Thực hiện | 4376 • ID Số | `sbd-4376-idso` | editor, chỉ pair `hub69-content-demo` |
| Kiểm chứng độc lập | 5284 • Kiểm Chứng Tổng Hợp | `sbd-5284-kiemchung` | reviewer |
| Điều phối | 267 • CMP | `cmp-267-dieuphoi` | viewer (thử quyền tối thiểu) |

> Ai thực sự chạy? Phần trí tuệ (SI AI) trong thí điểm là **Claude Code trong phiên này**; phần Siêu Phần Mềm là các mô-đun trong `tools/`. Các ID 4376/5284/267 là **vai trò được gán**, không phải tác nhân độc lập đang chạy 24/24. **ACTIVE = 0.**

### Kết quả nhiệm vụ

| Task | Nội dung | Trạng thái Core | Báo cáo (SHA-256) | Kết quả chính |
|---|---|---|---|---|
| T1 | GitHub • Registry AI và trang route | **REVIEWED DRAFT** | [`T1-github-registry-audit.json`](evidence/pilot/T1-github-registry-audit.json) `412205bc…` | 26 thực thể, **22 phát hiện**: Gemini 691141 nhưng trang 691141 là "Google Cloud AI" còn Gemini ở 6911421; "Meta AI" ở cả 69115 và 691151; "Google DeepMind" ở 69114 và 691142; 3 trang 698402–698404 cùng tiêu đề; 11 developer không có trang |
| T2 | Notion • đối chiếu 3 danh sách | **REVIEWED DRAFT** | [`T2-notion-cross-check.json`](evidence/pilot/T2-notion-cross-check.json) `3ef54639…` | **50 phát hiện**: 333 có 2 hồ sơ; 2624 nằm ngoài danh sách 91; 2273, 2588 thiếu link; 32 ID có 2 trang Notion; 6 ID khác tên giữa các danh sách (8882 "TTTC" so với "Tri Thức Toàn Cầu"…) |
| T3 | Phân loại 91 + Web | **REVIEWED DRAFT** | [`T3-classify-and-join.json`](evidence/pilot/T3-classify-and-join.json) `15fb3ef0…` | Nhóm 000: 5 • 135: 31 • 246: 33 • 789: 22. Đề xuất: 19 giữ trang, 70 đề nghị tạo trang (cần HG), 2 cần hồ sơ Notion |

**Vòng đời mỗi task** ([`pilot-run.json`](evidence/pilot/pilot-run.json)): createTask → QUEUED → runTask (ACK + chạy, 18 kiểm tra Core) → AWAITING HUMAN REVIEW → tự review **bị từ chối** → reviewer chạy lại mô-đun, SHA khớp → **REVIEWED DRAFT**, `productionApproved=false`. Audit chain: **23 sự kiện**, checkpoint `811ed13e…`.

**Từ chối đúng thiết kế:** 1 lần tài khoản viewer (CMP 267) tạo task; 3 lần người thực hiện tự review.

## 5 • Đề xuất từ thí điểm (chờ HG, không tự áp dụng)

1. **ID Gemini/Google:** sửa một trong hai nguồn sao cho `691141` thống nhất giữa Registry JSON và trang. Registry custodian quyết định (HG-7).
2. **Tên Registry so với tiêu đề trang:** 7 ID (69111, 69114–69117, 691141, 691151) cần thống nhất tên. Đề xuất giữ tên Registry, sửa tiêu đề trang khi được duyệt.
3. **698402–698404:** ba trang cùng tiêu đề "Developer AI Việt Nam"; cần tên riêng hoặc ghi rõ là slot.
4. **Notion:** gộp hoặc ghi rõ quan hệ cho 32 ID có 2 trang (hồ sơ và trang học hỏi); xử lý 333, 2624, 2273, 2588 (HG-14).
5. **Core PR #124:** bổ sung lệnh **ACK** riêng và một **adapter đọc thật** chỉ-đọc, chỉ khi HG phê duyệt; đồng thời chọn một Core duy nhất (HG-15).

## 6 • Giới hạn trung thực

- Adapter SI trong PR #124 là mock theo thiết kế. Bước `runTask` của Core lặp lại bản tóm tắt; công việc thật chạy ngoài Core và được gắn bằng SHA-256.
- Cơ sở dữ liệu sandbox là file tạm và bị xóa sau khi chạy; chỉ giữ receipt và báo cáo.
- Không có SI AI bên ngoài nào được kết nối. Không có runtime 24/24. Chưa kiểm thử iPhone thật.
