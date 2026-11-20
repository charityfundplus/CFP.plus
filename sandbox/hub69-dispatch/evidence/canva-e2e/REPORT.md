# Canva → Diễn Đàn #195 → autopilot → reviewer • luồng xuyên suốt

**SANDBOX PRACTICE GO • HOLD ACTIVATION • PRODUCTION NO GO**

Tái tạo: `tests/forum/setup_pg.sh <db> --no-003` (nhánh #195), sau đó `python3 sandbox/hub69-dispatch/canva_e2e.py --office-src <checkout #195> --pg "postgresql+psycopg://%s@localhost:5433/<db>" --out <thư mục>`.

Kết quả lần chạy này (`checks.json`): **19/19 PASS**. Backend #195 ở `9614fa1`. Tệp giao diện `canva-code.html` có sha256 `d9dac1b1…`, đúng là tệp dán vào Canva Code.

| Bước | Bằng chứng |
|---|---|
| Thành viên A đăng ký và đăng bài trong giao diện Canva | `1-A-posted.png` |
| Thành viên B (tài khoản khác) đọc bài của A và phản hồi | `1-B-replied.png` |
| A thấy phản hồi của B, rồi giao việc trong mục **Giao việc** | `1-A-assigned.png` |
| Bộ điều phối đọc bài nhiệm vụ từ Diễn Đàn → giao 691121 theo năng lực → Văn Phòng → thực thi → Evidence → chuyển ReviewSI → phản hồi ngay dưới bài | `run-log.jsonl`, `results/sbd-2.json` |
| Lượt chạy thứ 2 không ghi trùng | `checks.json` |
| **Khởi động lại backend** (Postgres): bài, phản hồi, nhiệm vụ, Evidence còn nguyên | `forum-after-restart.json`, `readback.json`, `2-B-after-restart.png` |
| B **không** thấy nhiệm vụ ngoài phạm vi của mình (máy chủ lọc) | `checks.json` |
| ReviewSI mở Canva → mục Nhiệm vụ → thấy "Chờ review", có Evidence, có nút review | `2-ReviewSI-task.png` |

## Thật và mô phỏng

| Thành phần | Phân loại |
|---|---|
| Backend #195: auth, quyền, Diễn Đàn, Văn Phòng | **THẬT**, chạy cục bộ trên **Postgres 16 với đúng migration của Supabase sandbox** (#193 + 002). Không phải Render |
| Giao diện | **THẬT**: chính tệp `canva-code.html`, chạy trong iframe `sandbox="allow-scripts allow-forms"` ở **nguồn khác** (Origin `null`), Chromium giả lập iPhone 13 |
| Canva | **CHƯA KIỂM**: kết nối Canva của phiên này lỗi (502), và runtime không vào được Canva Code. Khung iframe ở đây chỉ **mô phỏng** điều kiện chặt nhất |
| HTTPS | Không có: chạy cục bộ bằng http. Render HTTPS hiện chạy build cũ `396c1d8` với dữ liệu tạm |
| Người dùng A, B, ReviewSI | Tài khoản thử nghiệm do kịch bản điều khiển |
| Người thực thi | **AUTOMATED_TOOL** (mã tất định) dưới tên 691121, **không phải mô hình AI** |
| Review | **CHƯA CÓ**. Kịch bản dừng trước nút review; review phải do reviewer thật thực hiện |

## Siêu Bộ Đôi: đã chạy / chưa chạy

| SI AI | Trạng thái | Nguyên nhân |
|---|---|---|
| Claude 691121 | **Đã chạy**, nhưng chỉ là công cụ tự động (`registry_check`, `working_link_audit`) | Chưa có runtime LLM chạy liên tục. Phiên Claude Code này là mô hình thật nhưng chỉ chạy khi có phiên |
| OpenAI 69118 / ChatGPT 691181 | Chưa chạy | Chưa có kết nối runtime hay khóa API trong sandbox. ChatGPT mới tự báo ghi được Notion trong phiên riêng |
| Gemini 691141, Meta AI 691151, Copilot 691161, Grok 691191 | Chưa chạy. Nhiệm vụ `content`/`research` được phân công nhưng đứng ở **AWAITING_REAL_AGENT** | Không có executor, credential hay tài khoản agent |
| Codex 1/2, Muse, Perplexity | Chưa chạy | ID còn PENDING và chưa kết nối |
| ReviewSI, SecuritySI | Chỉ có tài khoản sandbox | Chưa gắn với reviewer thật (người hoặc agent) |
