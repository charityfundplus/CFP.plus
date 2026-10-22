# Issue #156 • Website / App / Google Sites review

**HOLD ACTIVATION • PRODUCTION NO-GO.**

## Baseline đã đọc trước khi sửa

| Nguồn | Branch / PR | Full SHA đã đọc |
| --- | --- | --- |
| UI kế thừa | `codex2/integration-readiness` / Draft #141 | `07f317888d2fac98da2a912329aaa86b170053e7` |
| Base của UI #141 | `codex2/hub69-p0-ui-20261016` / Draft #140 | `6daec1ca72a65f542392aeb70592a7ed9b5453f6` |
| main / snapshot Registry | `main` | `835616308111f6851c0387fa9f5eda60c9ffa624` |
| Core | Draft #124 | `06f386b1ba52358779cec6bc26c2d88f6a33664a` |
| Contract | Draft #157 | `383ffcf5fa3a229d442393a86fa189e52bc09289` |

GitHub connector và `git ls-remote` cùng trả UI HEAD 07f3178 và main 8356163.
Checkout đầy đủ nhánh UI, trạng thái sạch trước khi tạo `codex2/issue156-shared-design`.
Không tìm thấy AGENTS.md trong checkout. Draft mới base là nhánh UI #141 để
review riêng delta này, giữ nguyên các PR #110/#124/#140/#141/#157.
Mã và bằng chứng chỉ nằm dưới `hub69/ui/`; không thay runtime mount/Registry.

## Thay đổi

- Design Tokens **1.1.0** làm nguồn chung của CSS: màu, font, cỡ chữ, spacing,
  radius, focus, touch target và layout. Bundles snapshot/Core/offline dùng cùng CSS.
- Navigation mobile thu gọn có label, `aria-expanded`, keyboard focus và đóng sau
  khi chọn route. Không có JavaScript thì navigation vẫn hiện để đọc liên kết.
- Bổ sung nội dung/đường đi cho 10 Chương; ưu tiên Chi Hội, SI/AI/Robot/Công Nghệ,
  HSTDN và Quốc gia. Giữ cây Parent nguồn hiện hữu.
- Danh mục nhà cung cấp, bên mua, bên bán: lọc Việt Nam/Hoa Kỳ và vai trò.
  **6 mẫu minh họa**, toàn bộ ID/Parent/DID/Canonical để null; không là 6 đối tác thật.
- 8682 TMTC và 8882 TTTC có trang tham chiếu PENDING REVIEW; URL được nhắc tới
  hiển thị dạng text. Chưa mở liên kết Canonical khi binding chưa được xác minh.
- `#app` là browser App shell chạy chung Website. Chưa có native binary/PWA
  installation, service worker hoặc App production. Offline không thu mật khẩu.
- [Bàn giao Google Sites](GOOGLE-SITES-DESIGN-HANDOFF.md) ghi rõ phần Sites
  hỗ trợ, phần gần đúng và receipt cần Gemini trả trong Issue #156.

## Luồng và component dùng chung

HUB 69 là cửa ngõ của cả Website và browser App shell. Hai giao diện dùng cùng
router, tra cứu ID, hồ sơ, chapter tree, country/role filter, catalog cards,
Evidence fields, status panel, button và Design Tokens. API vẫn là Core hiện hữu.

| Luồng | Component / nguồn | Ranh giới |
| --- | --- | --- |
| Website / browser App → UI | `app.js`, `workspace.js`, `p0.js` | Cùng màn hình và router; không có Registry mới |
| UI → Core | `core-binding.js` → `/registry-client.js` của Core #124 | Core bundle chưa mount; same-origin, source pins, không fallback snapshot |
| Core → Registry | Core #124 `registry-read-model.mjs` | Nguồn và revision hiện hữu, đọc-only |
| Google Sites → nội dung bổ trợ | Theme mapping + URL preview do Gemini bàn giao | Không nhúng cookie/token; public facade #157 vẫn disabled |

Đã đọc `openapi.json`, `API_CONTRACT.md` tại Contract SHA nêu trên và actual
Core client tại SHA #124. Contract có GET Registry/detail, phiên same-origin và
các route public đề xuất đang disabled. Không kết nối route mới hoặc adapter.
**Blocker đã thấy:** Core server/contract nhận ID tới 256 chữ số, nhưng UI và
`projectCoreRecord` của Core client vẫn giới hạn 80. Không sửa client của Codex 1
hoặc mở rộng quyền để vượt kiểm thử; cần bản client tương thích đã review.
Claim-level Evidence HSTDN, publication authorization và độc lập review vẫn chờ.

## Chạy và kiểm tra lại

```bash
cd hub69/ui
node build.mjs
node --test --test-reporter=tap tests/*.test.mjs
CFP_CODEX1_SOURCE=/path/to/exact-core-checkout node --test integration/core-http.test.mjs
CFP_PLAYWRIGHT_MODULE=/path/to/playwright/index.mjs CFP_AXE_PATH=/path/to/axe-core/axe.min.js CFP_QA_OUTPUT=/path/to/output node integration/browser-review.mjs
```

Core checkout phải đúng SHA 06f386b1 và các hash trong `integration/source-pins.json`.
Core integration dùng account/SQLite synthetic tạm và loopback, xóa khi hoàn tất.
Nó không thử staging, TLS, tài khoản thật hoặc nguồn cấp quyền thật.
Browser QA chạy HTML local, không server/deploy; phone viewport Firefox không
thay Safari/iPhone. `browser-results.json` giữ các lỗi/axe incompletes để review.

`HUB69-review.html` là Preview tự chứa mở offline sau build, không là URL staging.
Chỉ giữ PASS trong phạm vi log/receipt. Browser screenshot và video phải ghi engine,
viewport và source hash; không gắn nhãn "kiểm thử iPhone" cho ảnh mô phỏng.

## Blockers và owner

| Hạng mục | Trạng thái / điều kiện mở chặn | Owner |
| --- | --- | --- |
| HTTPS staging | Thiếu URL riêng tư hiện hữu được duyệt, mount cùng origin, deploy SHA, tài khoản thử và rollback | Chủ môi trường + Human Governance |
| Safari iPhone thật | Thiếu thiết bị/session và URL HTTPS nói trên | QA thiết bị + chủ môi trường |
| Google Sites | Thiếu sitemap gốc định vị được, Preview URL và receipt áp dụng theme của Gemini | Gemini |
| API live / App auth | Contract/runtime chưa được nghiệm thu, client 80/256 cần tương thích; không có native identity contract | Codex 1 + reviewer |
| Registry bindings | Chi Hội/HSTDN/nhà cung cấp/8682/8882 thiếu hàng có thẩm quyền và Evidence | Custodian + Human Governance |
| Nội dung đầy đủ | Chưa có roster Chi Hội/đối tác thật; mẫu minh họa và research không thay nội dung đã xác minh | Chủ nội dung + reviewer |
| Browser render local | Firefox launch được nhưng tạo page timeout 15s; WebKit thiếu shared libraries, install-deps không thực hiện được setgroups/setuid | Chủ môi trường QA |
| Independent acceptance | Tác giả tự kiểm thử; không ghi verdict/ACK thay Claude, Gemini hoặc reviewer khác | Reviewer độc lập |

## Checklist Safari iPhone / HTTPS sau khi được bàn giao

- Ghi model iPhone, iOS/Safari, thời điểm, exact HTTPS URL, UI SHA, Core SHA và
  deployment revision. Chụp TLS/origin và màn hình HOLD ở đầu video.
- Chạm HUB → nhóm 135 → Chương 5; nhóm 246 → Chương 6; nhóm 789 → Chương 7/9.
- Lọc HSTDN Việt Nam/Hoa Kỳ, lọc nhà cung cấp/mua/bán; mở 8682/8882 tham chiếu
  và quay lại HUB. Không coi HTTP 200 là đúng hồ sơ hoặc VERIFIED.
- Nhập `000`, ID đã có nguồn, ID thiếu và route lỗi; kiểm tra không mất số 0.
- Portrait/landscape, tăng chữ 200%, VoiceOver, thứ tự focus/menu, touch ≥44px,
  không scroll ngang/cắt nội dung; kiểm tra contrast trong màn hình thực tế.
- Session Core 401, logout/revoke, 404, 503: xóa dữ liệu cũ, không fallback snapshot.
- Ghi screenshot/video gốc, URL + SHA, PASS/FAIL từng ca; không sửa quyền để pass.

## Rollback và phạm vi bảo toàn

Delta chỉ thay UI và tài liệu. Rollback bằng revert commit UI trên nhánh thử nghiệm,
build lại; chưa có migration, persisted server state hoặc deployment để rollback.
Không thực thi rollback trên môi trường nào trong đợt này. Source Registry, Core,
contract, ID, Parent, DID, Canonical, IAM/DNS và năm adapter disabled được bảo toàn.
