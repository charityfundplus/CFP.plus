# CFP+ HUB 69 — Tin Tức • Quan Sát Toàn Cầu Theo Ngày

**Status:** REVIEW CANDIDATE  
**Governance Approved:** NO  
**Canonical Locked:** NO  
**Phạm vi:** HUB 69 • Website tiếng Việt • Tin tức AI tổng hợp đa quốc gia

## 1. Mục đích

HUB 69 có một hệ Tin Tức • Quan Sát Toàn Cầu do nhiều AI 🤖 hỗ trợ tổng hợp từ nhiều quốc gia, nhiều nguồn và nhiều lĩnh vực. Mỗi ngày có một trang chính duy nhất, bao quát các diễn biến quan trọng và tổ chức theo 10 Chương CFP+ từ 0 đến 9.

Tin tức không tạo một hệ phân loại cạnh tranh với CFP+. Tin tức phải tuân theo cấu trúc Chương, Evidence, Reference First, Governance và pháp luật áp dụng.

## 2. Công thức Time ID

**`69YYYYMMDD`**

Trong đó:

- `69` = HUB 69
- `YYYY` = năm
- `MM` = tháng
- `DD` = ngày

Ví dụ ngày 13/08/2026:

**`6920260813`**

Đây là Time ID duy nhất của trang Tin Tức • Quan Sát Toàn Cầu ngày 13/08/2026.

## 3. Một ngày • Một ID • Một trang chính

Mỗi ngày chỉ tạo một Time ID và một trang chính. Không cấp Canonical ID riêng cho từng tin, từng Chương hoặc từng tầng nội dung bên trong trang ngày.

Time ID đã hình thành không đổi, không renumber và không tái sử dụng. Nội dung có thể được bổ sung, sửa lỗi và thêm Evidence theo Governance mà không thay đổi Time ID.

## 4. 10 Chương là 10 thể loại tin chính

Bên trong trang ngày, tin tức được phân loại theo chính 10 Chương CFP+:

- `0` — CFP+ • Nền tảng • Quản trị • Tổng hợp
- `1` — Sự Sống
- `2` — Con Người
- `3` — Ba Quỹ • Tài chính và nội dung liên quan
- `4` — Tôn Giáo
- `5` — Cộng Đồng
- `6` — AI 🤖 • Công Nghệ • Khoa Học
- `7` — Doanh Nghiệp
- `8` — Tổ Chức
- `9` — Quốc Gia • Chính sách • Quan hệ quốc tế

Một sự kiện xuyên Chương có một Chương chính và có thể dẫn chiếu đến các Chương liên quan. Không cần sao chép toàn bộ nội dung.

## 5. Ngoại lệ dùng dấu `/` dành riêng cho Tin Tức

Các Canonical Link CFP+ thông thường tiếp tục dùng ID số liền nhau theo quy tắc hiện hành. Thiết kế Tin Tức không thay đổi quy tắc đó.

**Riêng hệ Tin Tức • Quan Sát Toàn Cầu theo ngày**, khi cần phân tầng nội dung bên trong một Time ID, dùng dấu `/`.

Ví dụ:

- `6920260813` — trang chính ngày
- `6920260813/6` — Content Path Chương 6
- `6920260813/6/4` — tầng nội dung tiếp theo
- `6920260813/0/4/6` — ba tầng Content Path

Phần sau dấu `/` **không phải Canonical ID mới**. Đây chỉ là **Content Path** để định tuyến và tổ chức nội dung.

## 6. Công thức tổng quát

**`69YYYYMMDD/[0-9]/[0-9]/[0-9]...`**

Trong đó:

- `69YYYYMMDD` = Time ID duy nhất của ngày
- mỗi `/[0-9]` = một tầng Content Path
- mỗi tầng có tối đa 10 nhánh `0–9`
- chỉ mở thêm tầng khi nội dung thực tế cần
- không tạo trước hàng loạt ID trống

Như vậy có thể giữ nguyên logic 10 × 10 × 10 của nội dung CFP+ mà không làm tăng số Canonical ID.

## 7. Tin đa quốc gia và nhiều AI 🤖

Trang ngày không thuộc riêng một quốc gia. Nhiều AI có thể tổng hợp, kiểm tra và review thông tin từ nhiều quốc gia và nhiều nguồn.

Mô hình:

**Nhiều AI 🤖 → Nhiều nguồn → Nhiều quốc gia → 10 Chương → Một trang ngày**

Khi tin liên quan đến Country, Developer, AI hoặc thực thể Canonical đã tồn tại, ưu tiên dẫn Canonical Link tương ứng.

## 8. Reference First và tài liệu lịch sử

Nếu tài liệu hoặc bản tin cũ đã có link, ưu tiên dẫn link thay vì sao chép toàn bộ nội dung.

**Tin hiện tại → Link lịch sử → Evidence gốc → Canonical Source**

Cấu trúc này cho phép HUB 69 hình thành kho Quan Sát Toàn Cầu theo thời gian mà không làm trùng lặp dữ liệu.

## 9. Mẫu tối thiểu cho mỗi tin

Mỗi tin nên có:

1. Tiêu đề
2. Thời gian
3. Quốc gia / khu vực
4. Chương chính
5. Chương liên quan
6. Tóm tắt
7. Điều gì thay đổi
8. Vì sao quan trọng với Sự Sống
9. Dependency / mối liên hệ
10. Early Warning nếu có
11. Evidence và nguồn
12. Canonical Links liên quan
13. Tài liệu / bản tin lịch sử liên quan
14. Điều cần tiếp tục theo dõi

## 10. Governance

Tin tức phải tôn trọng pháp luật áp dụng tại quốc gia và khu vực liên quan. Ưu tiên nguồn chính thức, nguồn gốc và bằng chứng có thể kiểm tra. AI không được trình bày suy luận như sự kiện đã xác nhận; thông tin chưa chắc chắn phải ghi rõ trạng thái.

Ngoại lệ `/` chỉ áp dụng cho Content Path của hệ Tin Tức theo ngày. Nó không được dùng để thay đổi Canonical ID hoặc Canonical Link rules của các hệ CFP+ khác.

## 11. Các câu hỏi bắt buộc cho vòng Review

1. `69YYYYMMDD` có đủ rõ và bền vững lâu dài không?
2. Có collision hoặc ambiguity nào với namespace Country → Developer → AI hiện tại của HUB 69 không?
3. Có cần metadata bắt buộc `ID Type = TIME` để máy phân biệt không?
4. Ngoại lệ `/` có gây xung đột routing với website hiện tại không?
5. Quy tắc “phần sau `/` là Content Path, không phải ID” đã đủ rõ chưa?
6. Mô hình Một Ngày • Một ID • Một Trang có phù hợp khi quy mô tin tăng mạnh không?
7. Cấu trúc 10 Chương 0–9 có đủ để phân loại toàn bộ tin xuyên lĩnh vực không?
8. Cần giới hạn bao nhiêu tầng `/` để URL vẫn dễ đọc và vận hành?
9. Cần Evidence fields tối thiểu nào để nhiều AI cùng đóng góp nhưng vẫn audit được?
10. Cần cơ chế version/history nào để sửa tin cũ mà không làm mất bằng chứng trước đó?

## 12. Chuẩn phản hồi Review

Mỗi AI Reviewer phản hồi theo:

**Finding → Evidence → Analysis → Recommendation → Severity → Closure Criteria → PASS / PASS WITH CHANGES / FAIL**

Reviewer không tự thay đổi Canonical ID, không tự Governance Approve và không tự Canonical Lock.

## 13. Tóm tắt đề xuất

**HUB 69**

↓

**`69YYYYMMDD` = một ngày • một Time ID • một trang chính**

↓

**`/0` đến `/9` = 10 Chương dưới dạng Content Path**

↓

**`/[0-9]/[0-9]...` = mở rộng nội dung khi cần, không sinh Canonical ID mới**

↓

**Nhiều tin • Nhiều AI 🤖 • Nhiều quốc gia • Nhiều lĩnh vực • Nhiều Evidence**

**Only Plus+ For Life**
