# Claude Code • Review Diễn Đàn SI AI 00–04 + Link Mẫu Chung • 2026-11-22

**Loại:** READ ONLY REVIEW. Không sửa Notion, không cấp ID, không kích hoạt agent.
**Đáp ứng:** ghi chú tại trang 00 “Trang 01–04 chưa được Claude review. REVIEW BLOCKED”.
**Lưu ý độc lập:** Claude Code là tác giả PR #236 (Website), nên **không** được làm reviewer độc lập cho #236. Review dưới đây chỉ áp dụng cho các trang Notion do bên khác soạn.

## Phiên bản đã đọc (Notion `page_last_edited_at`, UTC)

| Trang | ID | Sửa lần cuối |
|---|---|---|
| Link Mẫu Chung SI AI + Siêu Phần Mềm | `401caac9a557819e885fd962f56ee47c` | 2026-11-13T22:48:07Z |
| 00 • Mục lục chuẩn Diễn Đàn | `405caac9a557817b85aecf95b6cbe9c4` | 2026-10-26T18:27:29Z |
| 01 • Đăng ký • Xác minh | `405caac9a55781cabe65c92315e83435` | 2026-10-26T08:51:40Z |
| 02 • Ma trận Siêu Bộ Đôi • ACK | `405caac9a55781d3b904dad89df623ce` | 2026-11-14T23:56:14Z |
| 03 • Siêu Phần Mềm 24/24 | `405caac9a5578138901fe9e4e078f4e6` | 2026-11-16T18:04:35Z |
| 04 • Runbook • Sự cố • Nghiệm thu | `405caac9a5578151bbf9c37172b30111` | 2026-10-26T13:46:49Z |
| 58 • Luật Thép CFP+ | `41dcaac9a5578129bb42e2bed13f3081` | 2026-11-19T06:11:59Z |

## Đánh giá chung

Các trang 01–04 **nhất quán về nguyên tắc an toàn**: mặc định không kích hoạt, ACK phải có receipt, tác giả không tự nghiệm thu, cần read-back. Không phát hiện chỗ nào tuyên bố ACTIVE/CONNECTED khi thiếu bằng chứng. Các finding dưới đây là về **tính nhất quán, độ cập nhật và một lỗ hổng trong quy tắc Evidence**.

## Findings

| ID | Mức | Trang | Finding | Đề xuất |
|---|---|---|---|---|
| F-R1 | **HIGH** | Link Mẫu, 58, quy tắc "Public Live" | **Mọi URL số trên `cfp.plus` đều trả HTTP 200.** Route `/[0-9]+` dự phòng về `/id/index.html` (trang "AI Office" dùng JS tra registry; không có thì hiển thị công thức). Ví dụ: `/99999999999` → 200; `/8882` (link "AI Office" trong bảng P1 của Link Mẫu) và `/58` ("Link CFP+ dự kiến" của Luật Thép) **không có trang riêng**, nhưng vẫn 200 với nội dung chung. Quy tắc `PUBLIC_CURRENT_SYSTEM.md` #6 "Public Live chỉ khi URL mở được" vì vậy **không đủ để làm Evidence** | Bằng chứng LIVE của một ID phải kiểm tra **nội dung**: `<ID>/index.html` tồn tại trong repo tại SHA production, hoặc ID có trong `registry/*.json`, hoặc `<title>` chứa đúng ID. Không chỉ dựa vào HTTP 200 |
| F-R2 | MEDIUM | Link Mẫu (bảng điều phối P0 Website) | Trạng thái "thiếu deployment receipt, BLOCKED nghiệm thu" đã cũ. Ngày 20/11 đã **VERIFIED** production = `main` `8356163` (#235, PR #236). Bảo mật: live đang lộ `/.git/index` | Cập nhật hàng P0 Website: source→production SHA VERIFIED; blocker mới là D1–D4 trong PR #236 (bản vá bảo mật, làn nội dung, IAM read-only) |
| F-R3 | MEDIUM | 01, 02, Link Mẫu, #232 | **Bốn bộ trạng thái khác nhau** cho cùng khái niệm: 01 `SUBMITTED→IDENTITY REVIEW→VERIFIED→AUTHORIZED→ACTIVE`; 02 có 6 nhãn (Đã cấu hình / Chờ ACK / Đã kết nối…); Link Mẫu `INVITED→ACK PENDING→…→COMPLETED VERIFIED` và `DISCOVERED • ID PENDING`; #232 `PLANNED→RESERVED→PROPOSED→BOUND→ACTIVE` | Một bảng ánh xạ duy nhất (gợi ý đặt tại 02): ba trục của 02 (cấu hình/kết nối, ACK/thực hiện, mức kiểm chứng), mỗi nhãn ở trang khác ánh xạ vào đúng một trục. Không đổi tên nhãn cũ để giữ lịch sử |
| F-R4 | MEDIUM | 02 (bảng phân công P0) | "Claude + nhóm phản biện AI" là đầu mối kiểm chứng cho Codex 1 và Notion AI. Thực tế Claude Code đã **viết mã** cho Website (PR #236, làn của Codex 2) và có thể sẽ viết thêm, nên dễ phát sinh xung đột lợi ích | Ghi rõ: với sản phẩm Claude Code tạo ra, reviewer phải là ReviewSI hoặc SI AI khác. Giữ Claude ở vai trò review cho sản phẩm không do Claude tạo |
| F-R5 | MEDIUM | 03 | Cấu hình giám sát hàng giờ chưa chọn môi trường hay danh tính thực thi; trang có yêu cầu "service account, không lưu credentials", nhưng chưa có phương án cụ thể | Có thể dùng lại phương án keyless (WIF, không khóa dài hạn) trong `ops/GCP_IAM_LEAST_PRIVILEGE_VI.md` (PR #236) để có danh tính chung. Chỉ là đề xuất; cần SecuritySI + HG duyệt, vẫn `enabled=false` |
| F-R6 | LOW | 04 | "Bộ kiểm thử trước nghiệm thu" có mục "Safari iPhone/Website P0" nhưng chưa có công cụ tái hiện | `tools/smoke_test_site.sh <URL>` (PR #236) chạy được với bất kỳ URL nào, chỉ đọc, kiểm tra 42 mục (trang công khai, file nội bộ, header). Có thể dùng làm bước nghiệm thu Website. Safari iPhone thật vẫn cần người có thiết bị |
| F-R7 | LOW | 04 | Gate bảo mật Notion ghi nhận trang 00 và Link Mẫu ở "bucket public". Hai trang này chứa sơ đồ vận hành nội bộ (không có bí mật) | SecuritySI xác nhận có chủ ý công khai hay không. Đây là quyết định của HG, không phải lỗi kỹ thuật |
| F-R8 | LOW | 00 | Danh mục cũ có mention trùng (hai trang "Danh Sách AI Đã Được Cấp Link Mẫu • Registry" khác ID: `3e2c…` và `bebc…`). Trang 00 đã tự ghi nhận, nhưng chưa có quyết định | Giữ nguyên, chuyển HG chọn bản gốc; không xóa |

## Trạng thái Claude theo đúng mẫu phản hồi chuẩn của Link Mẫu

**Task link:** Notion 00 (ghi chú "Trang 01–04 chưa được Claude review") • **SI AI / phiên làm việc:** Claude Code, phiên cloud của PR #236 • **Phản hồi:** ACK REVIEW (chỉ đọc) • **Thời điểm UTC:** 2026-11-22 • **Quyền được xác minh:** đọc Notion qua connector, đọc/ghi nhánh GitHub `claude/cfp-website-hub69-update-j56w9f` • **Kết quả:** 8 finding (1 HIGH, 4 MEDIUM, 3 LOW) • **Evidence:** file này, commit trên nhánh PR #236 • **Reviewer:** chưa có (đề nghị ReviewSI) • **Bước tiếp theo:** HG quyết định có cho ghi tóm tắt vào Notion không (Văn phòng Claude `404caac9a55781d89ab8e408034198b3` hoặc trang 00).

Không có thay đổi nào được ghi vào Notion trong lượt này.
