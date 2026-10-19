# HUB 69 • Codex 2 • Giao diện P0

## Website/App P0 • 19/10/2026

**ACK cả hai P0** từ [Issue #156](https://github.com/charityfundplus/CFP.plus/issues/156#issuecomment-6271840896)
và [Evidence Inbox hiện hữu](https://app.notion.com/p/3fecaac9a5578117a3a6c3d079f70aff?pvs=204).
Tiếp tục nhánh `codex2/integration-readiness`, Draft PR #141, trên baseline
`8ca11c26fbe3ba76db75ae1aa62b204744233d85`. Đây là prototype để review trên
cùng UI; chưa nghiệm thu staging, Safari hoặc native App. Các mục bàn giao
phía dưới giữ phạm vi lịch sử của từng revision.

Sau `node build.mjs`, mở `HUB69-review.html` trực tiếp bằng trình duyệt, không
cần server, tài khoản, API hoặc mạng để dùng điều hướng nội bộ. Liên kết ngoài
chỉ mở khi người review chọn. Dùng cùng component ở `dist/` và `core-dist/`;
bản Core tiếp tục bắt đầu với `records:[]` và cần mount được duyệt.

| Luồng review | Chức năng | Nguồn / giới hạn |
|---|---|---|
| `#chapters` → `#group/789` → `#chapter/7` → `#hstdn` | Lọc quốc gia Việt Nam / Hoa Kỳ / chưa có phạm vi; mở hồ sơ thương hiệu | Hai hồ sơ được ghi **MINH HỌA**, không phải doanh nghiệp thật; không gán ID/Parent/DID |
| `#brand/sample-vn`, `#brand/sample-us` | Bố cục pháp nhân, thương hiệu, sản phẩm, nguồn, chất lượng, hàng tại quốc gia và giao tại chỗ | Tồn kho, giao hàng, chứng nhận, liên hệ và quyền media đều chờ Evidence |
| `#commerce` → `#brand/amazon` → `https://cfp.plus/8682` | Danh mục sàn tham chiếu; mở trang sàn gốc hoặc cổng TMTC | Amazon được nêu trong [nguồn 8682](https://app.notion.com/p/3decaac9a55781be8616d39de9978bce); quốc gia phục vụ chưa xác minh, bộ lọc VN/US trả rỗng |
| `#chapter/6` → `#technology` | Phân khu Quantum / Space / Future Technologies | 6 nguồn được dẫn từ Evidence Inbox + 2 hướng nghiên cứu được ghi là đề xuất; không suy binding HSTDN/country hoặc tích hợp |

Các slug `vn`, `us`, `sample-vn`, `amazon` là khóa điều hướng UI, **không phải
Canonical ID mới**. Prototype không gửi dữ liệu, tạo giao dịch, gọi API mới,
sao chép Registry hoặc kích hoạt adapter. Các tham chiếu công khai/đề bài vẫn
đọc được khi Core lỗi; bản ghi Core cũ được xóa theo controller hiện hữu.

### Design Tokens 1.0.0 và Google Sites

`public/design-tokens.json` xuất lại đúng 7 biến màu `:root` hiện hữu của
PR #141. Kiểm thử bắt buộc đối chiếu từng giá trị với `public/style.css`.
Không đổi palette hoặc tạo Design System thứ hai.

| Token / quy tắc | Website / App web | Áp dụng thủ công cho Google Sites |
|---|---|---|
| `--paper`, `--ink`, `--green` | Nền, chữ, nút chính hiện hữu | Màu nền section, chữ và theme accent tương ứng |
| `--muted`, `--line`, `--lime`, `--amber` | Chú thích, viền, callout, trạng thái chờ | Màu văn bản phụ, đường chia, nền section/callout theo khả năng trình biên tập |
| Typography | Inter / Segoe UI / Arial / sans-serif; body 15px, line-height 1.6 | Chọn font sans-serif gần nhất được hỗ trợ; ghi rõ sai khác |
| Touch / form | Nút tối thiểu 44px; select 16px; focus-visible | Đối chiếu bản mobile; không giả định chỉnh được CSS hoặc pixel chính xác |
| Catalog | 3 cột lớn, 2 cột ≤1100px, 1 cột ≤700px | Dùng layout section thích ứng sẵn có, kiểm tra preview riêng |

Gemini giữ trách nhiệm đối chiếu Google Sites và cung cấp Preview URL/receipt
của chính mình. Chưa có thao tác Google Sites, publish hoặc thay quyền.

### Kiểm thử và nghiệm thu P0 mới

`node --test tests/*.test.mjs` chạy các test kế thừa và
`tests/website-p0.test.mjs`: deep links, lọc quốc gia, empty state, nguồn tham
chiếu, escaping, trạng thái Core lỗi, tokens, hai bundle và responsive source
guards. Log/receipt của lượt này ở `evidence/WEBSITE-P0-20261019.*` sau bàn giao.

**Responsive source PASS chỉ kiểm các quy tắc CSS**, gồm viewport/safe-area,
1 cột trên mobile, target 44px, form 16px, wrapping và focus/reduced motion.
Chưa đo layout, overflow, contrast hoặc touch thực tế trên browser.
Theo Sites skill, thiếu `$control-browser` trong managed environment phải bỏ
qua browser QA; không dựng preview server hoặc dùng đường điều khiển khác.
File HTML chạy độc lập là đầu ra prototype, không phải ảnh chụp render.

**Safari iPhone / HTTPS staging: BLOCKED.** Chủ môi trường cần bàn giao URL
HTTPS riêng tư hiện hữu được duyệt, mount cùng origin đúng SHA, tài khoản thử
và readback. Checklist thiết bị: Safari thật; 320/375/390/430px và landscape;
text zoom 200%; không tràn ngang; tất cả route/back/reload; bộ lọc quốc gia;
nút/link chạm được; VoiceOver/keyboard; Core 401/403/404/503/logout; anonymous
không đọc được hồ sơ riêng tư. Mỗi receipt cần SHA, URL, thiết bị/iOS/Safari,
thời điểm, ảnh/video và người review. Chưa đánh dấu PASS cho các bước này.

HOLD ACTIVATION • PRODUCTION NO-GO. Chờ review độc lập và Human Governance.

Tiếp tục giao diện HUB 69 hiện hữu từ source `6d2fd6f0c19ebaa0fcbfa53850bcce1b5bf7287f`. Module này đưa mã giao diện về repository CFP.plus để review và tích hợp; không tạo Site, HUB, Registry hay Core API mới. Site review hiện hữu giữ nguyên định danh và quyền truy cập. **HOLD ACTIVATION • PRODUCTION NO-GO.**

## Sử dụng bản review

Tại thư mục `hub69/ui`:

```bash
npm run build
npm test
```

Mở file được build `HUB69-review.html` để tra cứu offline; file chứa toàn bộ CSS/JS/dữ liệu. `dist/` là cùng giao diện dùng khi đóng gói Site. Chưa có URL HTTPS hoạt động. Không chạy server/API, adapter hoặc đồng bộ thật.

## Các chức năng đã triển khai

- Giữ giao diện Tổng quan, Master Hub, tra cứu ID, lưu mục và sao chép link mục.
- Thêm điều hướng đúng 5 nhóm **V • 000 • 135 • 246 • 789** và 10 chương 0–9. Nhóm điều hướng tách khỏi Canonical ID: `0`, `000` và `V` không được thay thế cho nhau.
- Cây **Chương → Con → Cháu** dùng chữ số đầu để phân loại Chương và `parent_id` được ghi trong nguồn để nối các bản ghi. Ví dụ có nguồn: **Chương 6 → OpenAI 69118 → ChatGPT 691181**. Việc đặt nhà phát triển dưới Chương trong giao diện không ghi thêm Parent vào Registry.
- Mỗi ID trong snapshot có hồ sơ riêng. Nhận biết trùng ID, Parent thiếu, vòng lặp, sai chương và quan hệ liên chương; giữ nguyên dữ liệu khi có finding.
- Khung Link Mẫu Chung hỗ trợ Siêu Bộ Đôi, phần mềm, SI, AI, Robot, nhà phát triển, HSTDN, doanh nghiệp, quốc gia, tổ chức và thực thể CFP+.
- Thành phần **Làm Dự Án tại ChatGPT** cho Siêu Bộ Đôi: tên, phạm vi, trạng thái, liên kết có receipt xác minh. Giữ ID của Siêu Bộ Đôi; không cấp ID dự án hoặc tạo URL. Hiện chưa có Siêu Bộ Đôi/project thật trong snapshot; xem cấu trúc tại `#template`.
- `#openai` là góc nhìn của Link Mẫu, tách OpenAI nhà phát triển và ChatGPT sản phẩm/AI. ID HSTDN, SI/Siêu Bộ Đôi liên quan và hợp tác chưa có nguồn được để chờ; không tạo thực thể HSTDN mới.
- `#vaults` trình bày 6 Kho, Evidence, lỗi/dữ liệu còn thiếu và thời điểm đồng bộ. GitHub chỉ là snapshot đọc được; Lượng Tử là RESEARCH; không có claim kết nối hoặc đồng bộ runtime.
- URL CFP+/Google Sites chưa được xác minh hiển thị bằng văn bản, không phát sinh link hoạt động. Link dự án chưa đủ receipt hoặc thuộc private không được xuất.

## Nguồn dữ liệu

Đọc trực tiếp **Registry hiện hữu** `registry/ai-entity-registry.json`, commit `835616308111f6851c0387fa9f5eda60c9ffa624`; build kiểm Git blob `1f18068d66379ce90bb079dc56c77b4c4d66dcdf` trước khi dùng. SHA-256: `a63c5e0b8af157b0938014d51da94ea924b9721acd0a11a9107f5deea3c6f507`.

**26 bản ghi nguồn = 20 nhà phát triển + 6 AI. 0 danh tính hoặc operator được thành phần này tự xác minh.** Không coi đây là Master Registry 91 Siêu Bộ Đôi. Snapshot và các trạng thái Review/Conflict không được nâng thành VERIFIED/ACTIVE. Khi export sang Site, bản sao evidence là đầu vào build đã ghim hash, không phải Registry có quyền ghi.

## Kiểm thử và giới hạn

Mốc lịch sử: 39/39 kiểm thử Node/VM PASS (14 nguồn/baseline, 19 P0 và 6 trạng thái ứng dụng với DOM stub). Bàn giao tích hợp mới được ghi riêng tại `INTEGRATION-READINESS.md`. Có kiểm tra các hash route/link nội bộ, dữ liệu nguồn, ba tầng, dự án/riêng tư, OpenAI và trạng thái kho. Đây không phải browser rendering hay iPhone acceptance.

Browser/CSS rendering, screenshots mới, Safari/WebKit, iPhone thật, HTTPS/quyền truy cập và E2E Core API trên môi trường HTTPS **chưa kiểm thử**. Phiên này không có `$control-browser`; Sites skill yêu cầu bỏ qua browser QA trong trường hợp đó, không khởi chạy một đường điều khiển trình duyệt khác.

Chỉ thêm `hub69/ui/**`; không sửa `/69`, `/id`, Registry, nhánh Codex 1, Core API hoặc Draft PR #124. Tích hợp lên cổng chính và nghiệm thu thiết bị là bước tiếp theo sau khi Codex 1 bàn giao read model/authority và môi trường được phê duyệt.

## Tiếp tục integration-readiness

Nhánh `codex2/integration-readiness` kế thừa PR140 ở `6daec1ca72a65f542392aeb70592a7ed9b5453f6`. Có màn hình đào tạo 5/12/6 từ Codex 1 và bản build `core-dist/` để mount cùng miền với Core hiện hữu. `dist/` và `HUB69-review.html` vẫn là bản snapshot; `core-dist/registry.js` bắt đầu với danh sách rỗng, không dùng snapshot khi Core lỗi. Không chạy Core thứ hai.

Core dùng `/registry-client.js` của Codex 1 ở revision trong `integration/source-pins.json`. Client phải được phục vụ đúng từ Core hiện hữu; mở `core-dist` trên một host tĩnh khác không tự tạo kết nối. Xem `INTEGRATION-READINESS.md` cho contract, giới hạn và Evidence mới.

Kiểm HTTP + trạng thái UI với checkout Codex 1 đúng pin:

```bash
CFP_CODEX1_SOURCE=/absolute/path/to/pinned-CFP.plus node --test integration/core-http.test.mjs
```

Màn hình `#training` và `#lesson/security` có nội dung bài học, 12 bài thực hành có giám sát và 6 hướng nâng cao. Dấu đã đọc chỉ lưu trên trình duyệt, không nộp assessment, không đổi Registry hoặc cấp quyền.
