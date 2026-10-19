# Codex 2 • Website & Preview • Integration readiness

## Bổ sung Website/App P0 • 19/10/2026

Hai P0 đã ACK trong phiên triển khai: HSTDN/danh mục sàn/8682 TMTC và
Quantum/Space/Future Technologies. Tiếp tục đúng nhánh/Draft PR #141, từ
`8ca11c26fbe3ba76db75ae1aa62b204744233d85`. Xem phần đầu README hiện hữu
cho tuyến review, Design Tokens 1.0.0, mapping Google Sites và checklist Safari.
Receipt mới nằm tại `evidence/WEBSITE-P0-20261019.*`; logs lịch sử dưới đây
không được dùng thay test của thay đổi mới.

Prototype mở offline ở `HUB69-review.html`; HSTDN minh họa, sàn tham chiếu
và tài liệu nghiên cứu tách khỏi các binding Core. Không có thay đổi Core
client, nguồn Registry, grant, mount hoặc adapter. Core bundle vẫn bắt đầu
rỗng; không thay bằng mẫu minh họa khi tra cứu ID thật thất bại.

**BLOCKED cho browser responsive / screenshot / Safari iPhone thật / HTTPS**:
thiếu browser được hỗ trợ; chưa có URL staging riêng tư được duyệt, mount,
tài khoản thử, deployment readback và receipt thiết bị. Source guards chỉ
đối chiếu CSS, không phải nghiệm thu render. HOLD ACTIVATION • PRODUCTION NO-GO.

Nhánh tiếp tục: `codex2/integration-readiness`. Nguồn UI: PR140, commit `6daec1ca72a65f542392aeb70592a7ed9b5453f6`. Nhánh đích chưa có trên remote ở đầu lượt làm việc; bản này tiếp tục đúng UI đó, không thay hoặc merge nhánh Codex 1.

## Những gì đã triển khai

- Kế thừa 5 nhóm V/000/135/246/789, 10 chương và cây Chương → Con → Cháu. ID được xử lý như chuỗi, giữ số 0 và quan hệ Parent nguồn.
- Hai đầu ra cùng giao diện: snapshot đọc nguồn (`dist/`, HTML offline) và bộ asset để mount vào Core (`core-dist/`). Bản Core không chứa 26 hàng snapshot và không chuyển sang snapshot khi lỗi.
- Nối client Codex 1 hiện hữu bằng same-origin import `/registry-client.js`, cookie hiện hữu, không nhận URL API/token từ người dùng. Không có API, Registry, login service hoặc adapter mới.
- Xóa dữ liệu trước khi đọc lại; 401, 403, 404, 503, provenance không khớp, logout và phản hồi muộn không được giữ hồ sơ cũ. Logout gọi endpoint hiện hữu; trạng thái đăng xuất lỗi không tuyên bố đã thu hồi phiên.
- Hiển thị provenance từng hàng: revision/Git blob/SHA-256 thật do Core trả. OpenAI và 6 Kho dùng dữ liệu Core trong bản mount. Snapshot vẫn được ghi rõ là snapshot.
- Đào tạo theo nguyên bản `training-basic-v1.json` đã ghim hash: 5 bài, 12 bài thực hành, 6 hướng nâng cao. Dấu đã đọc nằm ở trình duyệt; không chứng nhận năng lực hoặc cấp quyền.
- Bổ sung khoảng chạm và safe-area cho iPhone. Chưa có xác minh render/browser hoặc iPhone thật.

## Mount vào môi trường hiện hữu

1. Build `node build.mjs` tại `hub69/ui`.
2. Chủ Core phục vụ nội dung `core-dist/` tại một đường dẫn review cùng origin, qua chính HTTP/runtime hiện hữu. Không tạo host/API mới hoặc cross-origin proxy. Không mount mặc định vào `/69` production.
3. Origin đó đã phục vụ `/registry-client.js`, `/api/core/**`, `/api/logout` và `/p2` của Codex 1 đúng pin. Cấu hình nguồn Registry server-only theo bàn giao Codex 1; service chỉ cần quyền đọc checkout ghim.
4. Đăng nhập bằng phiên kiểm thử hiện hữu tại `/p2`, mở đường review và đối chiếu executable SHA, Registry revision và owner-private access. Không thêm quyền hoặc chuyển production để kiểm.

Không có môi trường HTTPS riêng tư hoặc browser được hỗ trợ được cấp trong lượt này. Các test HTTP dùng server loopback sống trong từng ca test, client Core nguyên bản và DOM stub; không phải Preview chạy liên tục, WebKit, Safari hay nghiệm thu iPhone.

## Phạm vi dữ liệu

Core pin ở `integration/source-pins.json` trả 224 tham chiếu từ nguồn hiện hữu: 99 quốc gia + 99 AI-country + 20 developer + 6 AI. Chỉ 26 hàng là named developer/AI bindings. Danh sách 91 REVIEW ONLY không được nhập vào runtime hoặc tính tỷ lệ phủ 26/91.

Chuỗi OpenAI là `911 → 6911 → 69118 → 691181`. HSTDN tham chiếu giữ ID/Parent/DID/Canonical riêng ở null; hold nhánh Hoa Kỳ, quyền, đánh giá, partnership và 6-vault sync không được nâng trạng thái.

## Evidence và nghiệm thu còn thiếu

Kết quả thực thi và manifest có tại `evidence/INTEGRATION-UNIT.tap`, `evidence/INTEGRATION-HTTP.tap` và bản ghi bàn giao cùng tên. Source pins và hash tách khỏi Evidence revision. Không nhận ACK thay ReviewSI.

- Cần chủ môi trường cung cấp đường HTTPS staging riêng tư đã được phép, cấu hình mount cùng origin, tài khoản kiểm thử và deployment readback.
- Cần công cụ browser được hỗ trợ/thiết bị iPhone để nghiệm thu desktop, Safari, navigation/back/reload, zoom/touch và owner/anonymous ACL.
- Binding pair/HSTDN thật do Registry custodian/Human Governance cung cấp; thiếu binding không cản trở việc review giao diện và contract đã chuẩn bị.

Sites hiện chỉ có đường triển khai production; việc save version không tạo URL. Không gọi deploy, đổi quyền, activate, merge hoặc ghi Registry trong lượt này. HOLD ACTIVATION • HUMAN REVIEW • PRODUCTION NO-GO.
