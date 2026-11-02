# CFP+ • HUB 69 • Codex 2 • Website & Preview

Ngày 16/10/2026 • America/New_York.

**Kết quả: 54/54 kiểm tra PASS, 0 FAIL. Giao diện và tích hợp sandbox đã hoàn thiện trong phạm vi được phép; Preview HTTPS riêng tư chưa có URL.**

## Mã nguồn và phần kế thừa

- Repository: charityfundplus/CFP.plus.
- Nhánh: `codex2/integration-readiness`; nhánh này chưa có trên remote lúc bắt đầu. Đã tạo bằng cách tiếp tục UI hiện hữu ở PR140, không xây HUB/API/Registry mới.
- Baseline UI: `6daec1ca72a65f542392aeb70592a7ed9b5453f6`.
- Execution SHA Codex 2: `0145feb42c2e453af99d8b6bf184b6b82e3d32a8`.
- Core Codex 1 được ghim và chỉ đọc: `06f386b1ba52358779cec6bc26c2d88f6a33664a`.
- Root Registry, Canonical ID, Parent, DID, dữ liệu và các route `/69`/`/id` hiện hữu không thay đổi. Không sửa nhánh Codex 1 hoặc PR124.

## Kết quả đã thực hiện

| Hạng mục | Trạng thái thực tế |
|---|---|
| 5 nhóm / 10 chương / 3 tầng | Kế thừa UI P0; giữ V/000/135/246/789, ID chuỗi và Parent nguồn |
| Tra cứu, hồ sơ, điều hướng | Kiểm thử trạng thái, ID chưa có, số 0, trùng/lineage, quay lại danh mục và lưu mục |
| Core API | Bộ asset `core-dist/` dùng client nguyên bản Codex 1 cùng miền; 6 ca HTTP + DOM stub đạt; chưa mount lên HTTPS |
| Phiên và lỗi | 401/403/404/503, retry, logout, phản hồi muộn, revision thay đổi và ẩn dữ liệu cũ đã kiểm |
| Dữ liệu nguồn | 224 tham chiếu Core = 99 quốc gia + 99 AI-country + 20 developer + 6 AI; không phải 224 verified identities hoặc roster 91 |
| OpenAI mẫu | Chuỗi 911 → 6911 → 69118 → 691181 và nội dung từ Core; HSTDN ID/Parent/DID/Canonical riêng vẫn null |
| 6 Kho | Hiển thị readback do Core cung cấp; không nâng thành connected hoặc runtime sync |
| Đào tạo | 5 bài / 12 bài tập / 6 hướng từ giáo trình Codex 1 ghim hash; ghi nhận đọc ở trình duyệt, chưa assessment |
| iPhone / desktop | Điều chỉnh responsive, vùng chạm và safe-area; chưa kiểm render trình duyệt hoặc iPhone thật |
| GitHub | Source và nhánh đã lưu; Evidence ghim execution SHA và hash |

## Evidence mới và giới hạn

- **48/48** kiểm tra Node/VM (39 kế thừa + 9 tích hợp/đào tạo) đạt.
- **6/6** kiểm tra HTTP loopback với Core nguyên bản và DOM stub đạt, gồm API thực trả 401/404/503, đọc 224 tham chiếu, nguồn OpenAI, thu hồi session và ẩn dữ liệu cũ. Một ca 503 sau lần đọc thành công dùng lỗi được inject; được ghi rõ trong tên ca.
- Không có kiểm thử browser rendering, WebKit/Safari, iPhone thật, chứng nhận bảo mật production hoặc hậu kiểm độc lập.
- Build Manifest kiểm 17 tệp đầu vào khớp byte với execution commit; có hash của asset/HTML được build.

## HTTPS và Preview

Các request không đăng nhập đã nhận HTTPS 200 cho `https://cfp.plus/69` và `https://cfp.plus/691181`; title tương ứng HUB 69 và ChatGPT, có hash nội dung trong Evidence. Đây là website hiện hữu, không phải bản Codex 2 mới hoặc bằng chứng Preview riêng tư. Google Sites HUB 69 cũng trả HTTPS; quyền và revision của bản đó chưa được xác minh. HTTP 200 không nâng hồ sơ thành ACTIVE.

Site HUB 69 review hiện hữu được giữ owner-private; không thêm người hoặc mở public. Site trước đó có 2 saved version nhưng không có live/preview URL hay deployment. Bản mới đã lưu thành công ở **version 3**, source export `92cea0584da46628868a5551c6e9a239f98139b0`; deployment_id vẫn null, quyền truy cập giữ revision 1, chỉ 1 chủ sở hữu và 0 khách ngoài. Đây là source export cùng UI, không phải execution SHA backend hoặc deployment SHA. Công cụ Sites ghi rõ mọi deployment URL là production; vì yêu cầu chưa kích hoạt Production, không gọi deploy để tạo URL thay thế.

**Preview HTTPS riêng tư: NOT AVAILABLE.** Không có đường staging riêng tư hoặc deployment pin được bàn giao trong môi trường này.

## Hai điểm cần chủ môi trường / Human Governance hỗ trợ

1. Cung cấp endpoint HTTPS staging riêng tư hiện hữu đã được phép, chủ vận hành, cách mount `core-dist/` cùng origin với Core, executable/source pins và tài khoản kiểm thử đúng quyền. Core chỉ cần quyền đọc checkout Registry được ghim, không cần quyền ghi Registry. Không gửi mật khẩu/token vào chat.
2. Cho phép kiểm trên browser được hỗ trợ / iPhone Safari thật tại endpoint đó và bàn giao người review nghiệm thu. Không đổi ACL để thay việc kiểm.

Authority cho binding pair/HSTDN thật vẫn chờ chủ Registry/Human Governance; không tự cấp ID để lấp thiếu. Công việc này không mở lại các PASS lịch sử không bị ảnh hưởng.

Theo [Sites SKILL.md](skill://plugin_connector_1p_689987207de08191979cf68eca2941c6/sites/SKILL.md): “If `$control-browser` is unavailable, skip browser QA: do not start a preview server, install a browser, or improvise another browser-control path.” Công cụ đó không có trong phiên; các kiểm tra HTTP ở đây chỉ là fixture sống trong ca test, không phải Preview hoặc nghiệm thu thiết bị.

HOLD ACTIVATION • HUMAN REVIEW • PRODUCTION NO-GO.
