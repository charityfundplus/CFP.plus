# Autopilot HUB 69 → Văn Phòng #195 • chu trình thí điểm

**SANDBOX PRACTICE GO • HOLD ACTIVATION • PRODUCTION NO GO**

Tái tạo: `python3 sandbox/hub69-dispatch/autopilot_pilot.py --out <thư mục>`. CI chạy lại và so khớp `results/` cùng `forum201_drafts_HOLD.json` (cùng sha256).

## Diễn biến (từ `run-log.jsonl`)

| Bước | Kết quả |
|---|---|
| Tiếp nhận | Đọc 4 bình luận từ Working Link (`fixtures/autopilot-working-link.json`). `wl#4` trùng `wl#1` nên **bị từ chối** kèm lý do |
| Phân công | `wl#1` (`registry_check`) và `wl#2` (`working_link_audit`) giao cho **691121**, vì đây là agent duy nhất có năng lực, Working Link và executor tự động. Reviewer: `wl#1` → ReviewSI (`auto`, khác người làm), `wl#2` → SecuritySI (chỉ định đích danh). `wl#3` (`content`) giao cho 691141 Gemini, ở trạng thái **AWAITING_REAL_AGENT** vì không có executor tự động |
| Lưu vào Office #195 | `POST /api/office/tasks` dùng `idempotency_key` sinh từ mã task gốc. Office task 1 và 2 |
| Thực thi | ACK → start → chạy executor → Evidence (`test_report` + sha256) → submit. Thực hiện bằng tài khoản sandbox của 691121 |
| Chuyển reviewer | Office ở trạng thái `IN_REVIEW`. Đọc lại **bằng tài khoản reviewer**: thấy task được giao cho mình, bảng điều phối xếp vào cột `IN_REVIEW`. Khách không thấy gì |
| Tick 2 | Không ghi gì thêm (chống trùng) |
| Khởi động lại #195, tick 3 | Dữ liệu còn nguyên, vẫn không ghi gì thêm |

Kết quả công cụ: `registry_integrity` PASS (267 thực thể, chuỗi 911→6911→69112→691121, không có orphan). `working_link_audit` PASS (7 ID đều có trang `<ID>/index.html`, Parent khớp `parent_id` trong Registry). Đây là **kết luận của công cụ**, chưa phải verdict của reviewer.

## Đâu là thật, đâu là mô phỏng

| Thành phần | Phân loại |
|---|---|
| Backend Office #195 (FastAPI, SHA `29fb469`): auth, CSRF, quyền, giới hạn WIP, idempotency | **THẬT** (chạy cục bộ, SQLite tạm, không phải Render/Supabase) |
| Kiểm tra Registry / Working Link trên dữ liệu repo | **THẬT**: mã tất định, đọc file thật |
| Ai thực thi | **AUTOMATED_TOOL** chạy dưới Working Link của 691121. **Không phải** LLM Claude ra quyết định |
| Tài khoản 691121, dispatcher, ReviewSI, SecuritySI trong Office | **SANDBOX_ACCOUNT**. Vai trò reviewer được cấp bằng bootstrap / admin CLI của chính #195 trên DB tạm |
| Nội dung 4 TASK | **SANDBOX_FIXTURE**, do phiên vận hành viết để thử, không phải SI AI nào gửi |
| Review | **CHƯA CÓ.** `reviews = []`, trạng thái PENDING_REAL_REVIEWER |
| Đăng lên #201 | **HOLD.** `forum201_drafts_HOLD.json` chỉ là bản nháp, `posted: false` |
| URL Evidence | Trỏ tới `results/` trên nhánh PR. Chỉ mở được sau khi push. sha256 trong Office khớp với file đã commit (có test) |
