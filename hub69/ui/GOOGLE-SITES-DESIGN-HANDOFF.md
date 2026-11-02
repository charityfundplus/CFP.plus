# CFP+ HUB 69 • Design System 1.1.0 • bàn giao Gemini

**DRAFT • HOLD ACTIVATION • PRODUCTION NO-GO.** Issue [#156](https://github.com/charityfundplus/CFP.plus/issues/156).
Đây là gói ánh xạ giao diện để review. Chưa xác nhận Gemini đã nhận hoặc áp dụng.

Nguồn duy nhất: `public/design-tokens.json` phiên bản **1.1.0**. `build.mjs`
sinh `design-tokens.css`; Website, App shell, bản Core chưa mount và HTML offline
dùng cùng dữ liệu tokens và cùng component. Không thêm Registry hoặc API.
1.1.0 bổ sung typography, spacing, layout, focus và touch target; giữ paper/ink/green/lime,
làm đậm muted/amber để tăng tương phản. Phiên bản 1.0.0 vẫn có trong lịch sử Git.

## Ánh xạ trong Google Sites

| Thành phần | Token / giá trị | Cách áp dụng để Gemini review |
| --- | --- | --- |
| Nền trang | paper `#f5f5ef` | Custom theme → Colors / section background |
| Nền thẻ | surface `#fffef9` | Màu nền section; độ bo/gap chỉ gần đúng theo layout Sites |
| Chữ chính | ink `#143b32` | Text styles và màu chữ theme |
| Chữ phụ | muted `#4f665a` | Text styles, kiểm tra tương phản trên nền thực tế |
| Nút chính / điều hướng | green `#174c3c`, chữ trắng | Buttons và Navigation trong custom theme |
| Điểm nhấn | lime `#d8ed91`, chữ ink | Section/callout; không dùng lime làm chữ trên nền trắng |
| Trạng thái chờ | amber `#805317`, nền `#f4ebda` | Nhãn bằng văn bản + màu; không dùng dấu xác nhận |
| Body | Arial, 16px, line height 1.6 | Chọn Arial hoặc font được Sites hỗ trợ; cỡ chữ gần nhất có thể đọc |
| Heading | 32–48px responsive | Ánh xạ Title/Heading; kiểm tra phone preview để tránh cắt chữ |
| Spacing | 4 / 8 / 12 / 16 / 24 / 32 / 48px | Section, layout, spacer gần nhất; không cam kết chính xác từng pixel |
| Nút / focus | target ≥44px, outline 3px | Kiểm tra kích thước/focus thực tế; ghi ngoại lệ nếu Sites hạn chế |
| Navigation | HUB 69 → 5 Nhóm → 10 Chương | Dùng Pages/Subpages; link về HUB 69 trên từng trang |
| Responsive | phone ≤700px, tablet ≤1100px | Đây là breakpoint Web/App; Sites quản lý reflow riêng, phải review thực tế |

Google Sites hỗ trợ custom themes cho màu, text styles, buttons, links, site width
và navigation. [Google Sites Help](https://support.google.com/sites/answer/6372865?hl=en)
là nguồn khả năng nền tảng đã đọc. Các dòng "gần đúng" ở trên là đề xuất áp dụng,
không phải khả năng import JSON/CSS tự động. Gói này không chạy script trong Sites,
không nhúng Core token/cookie, không publish và không thay quyền chia sẻ.

## Sitemap giao diện để đối chiếu

| Màn hình Website/App | Route review | Google Sites cần Gemini đối chiếu |
| --- | --- | --- |
| HUB 69 | `#home` | Cửa ngõ hiện hữu; không tạo HUB thứ hai |
| Master Hub | `#master` | Trang Master hiện hữu |
| ID | `#id` | Trang ID hiện hữu |
| 5 Nhóm | `#group/V`, `000`, `135`, `246`, `789` | Pages/subpages đúng sitemap được bàn giao |
| 10 Chương | `#chapter/0` … `#chapter/9` | Chương 0–9; giữ nguyên mọi ID/Parent |
| Chi Hội | `#chapter/5` | Tham chiếu nguồn Notion Chi Hội trong Issue #156 |
| SI/AI/Robot/Công Nghệ | `#chapter/6`, `#technology` | SI/AI/Robot, nguồn công nghệ, đào tạo |
| HSTDN | `#chapter/7`, `#hstdn/vn`, `#hstdn/us` | Việt Nam/Hoa Kỳ, nguồn và trường còn thiếu |
| Quốc gia | `#chapter/9` | Bối cảnh quốc gia; không gán binding mới |
| Nhà cung cấp / mua / bán | `#partners` | Mẫu minh họa; không xác nhận đối tác thật |
| 8682 / 8882 | `#reference/8682`, `#reference/8882` | Tham chiếu PENDING REVIEW; chờ Registry và nội dung tuyến |
| App shell | `#app` | Website dùng chung UI; Google Sites là kênh bổ trợ |

Sitemap gốc Gemini và URL Google Sites Preview chưa được định vị trong nguồn
đã đọc của đợt này. Các URL Sites cũ hiển thị trong Master Hub chỉ là tham chiếu,
không phải Evidence Preview của revision mới. **Không dùng `https://cfp.plus/69`
thay thế Google Sites Preview.**

## Receipt cần Gemini trả tại Issue #156

1. URL sitemap/file gốc + version; xác nhận phần mapping đã review.
2. URL Google Sites Preview thực tế trong quyền truy cập được duyệt; thời điểm,
   phiên bản theme 1.1.0 và mô tả revision nội dung.
3. Ảnh desktop/phone Preview; đường đi HUB 69 → Chương 5/6/7/9 → quay về HUB.
4. Ngoại lệ nền tảng về typography, spacing, focus hoặc navigation và cách xử lý.
5. Receipt áp dụng/readback của chính Gemini. Posting của Codex không phải ACK Gemini.

Chỉ chỉnh bản nháp khi được giao quyền hiện hữu. Không publish, deploy, thay DNS,
quyền, ID/Parent/DID/Canonical hoặc kích hoạt adapter.
