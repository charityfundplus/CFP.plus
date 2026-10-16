# Kiến trúc ID Chương và Ba Quỹ

## Trạng thái

Baseline Candidate

## Phiên bản

v0.1

## Ngôn ngữ chuẩn

Tiếng Việt

## Mục đích

Tài liệu này chuẩn hóa cách định vị Bộ Tam, CFPU, CFPT và Ba Quỹ trong kiến trúc số của CFP+.

Mục tiêu là:

1. Mỗi ID có ý nghĩa rõ ràng.
2. Số đầu tiên xác định chương.
3. Các khái niệm toàn hệ thống chỉ có một Canonical ID.
4. Các Quỹ theo cơ quan, doanh nghiệp, tổ chức và chi hội được nhận biết theo chương và ngữ cảnh vận hành.
5. Các chương khác tham chiếu về Canonical Link thay vì tạo lại định nghĩa.

## 1. Quy tắc số đầu tiên

Trong ID bốn chữ số, chữ số đầu tiên xác định chương.

Ví dụ:

| ID | Ý nghĩa |
|---|---|
| 1331 | Quỹ 1 trong phạm vi Chương 1 |
| 2331 | Quỹ 1 trong phạm vi Chương 2 |
| 3331 | Quỹ 1 trong phạm vi Chương 3 |
| 5331 | Quỹ 1 trong phạm vi Chương 5 |
| 7331 | Quỹ 1 trong phạm vi Chương 7 |

Công thức nhận biết:

| Công thức | Ý nghĩa |
|---|---|
| X331 | Quỹ 1 thuộc Chương X |
| X332 | Quỹ 2 thuộc Chương X |
| X333 | Quỹ 3 thuộc Chương X |

Trong đó X là số chương.

## 2. Ba Quỹ theo chương

Ba Quỹ là các cấu phần vận hành độc lập của cơ quan, doanh nghiệp, tổ chức, cộng đồng hoặc chi hội.

Ba Quỹ cần mang ID theo chương để:

1. Nhận biết ngay phạm vi quản lý.
2. Phân biệt các Quỹ thuộc các loại hình khác nhau.
3. Hỗ trợ tìm kiếm, điều hướng và kiểm tra bằng con người hoặc AI.
4. Tránh nhập nhằng khi cùng một loại Quỹ xuất hiện trong nhiều chương.

Ví dụ tại Chương 1:

| ID | Nội dung |
|---|---|
| 1331 | Quỹ 1 |
| 1332 | Quỹ 2 |
| 1333 | Quỹ 3 |

Ví dụ tại Chương 3:

| ID | Nội dung |
|---|---|
| 3331 | Quỹ 1 |
| 3332 | Quỹ 2 |
| 3333 | Quỹ 3 |

## 3. Bộ Tam

Bộ Tam chỉ có một Canonical ID độc lập trong toàn bộ CFP+.

Bộ Tam chỉ được trình bày và định nghĩa đầy đủ tại Chương 3.

Các chương, cơ quan, doanh nghiệp, tổ chức và chi hội khác không tạo lại ID hoặc định nghĩa Bộ Tam.

Khi cần sử dụng, các tài liệu chỉ dẫn Canonical Link về tài liệu Bộ Tam tại Chương 3.

## 4. CFPU

CFPU có một Canonical ID độc lập.

CFPU chỉ được trình bày và định nghĩa đầy đủ tại Chương 3.

CFPU không thay đổi ID theo chương.

Các vị trí khác chỉ tham chiếu đến Canonical Link của CFPU.

## 5. CFPT

CFPT có một Canonical ID độc lập.

CFPT chỉ được trình bày và định nghĩa đầy đủ tại Chương 3.

CFPT không thay đổi ID theo chương.

Các vị trí khác chỉ tham chiếu đến Canonical Link của CFPT.

## 6. Phân biệt hai loại thực thể

### 6.1 Thực thể Canonical toàn hệ thống

Các thực thể sau chỉ có một Canonical ID và được trình bày tại Chương 3:

1. Bộ Tam
2. CFPU
3. CFPT

### 6.2 Thực thể vận hành theo ngữ cảnh

Các thực thể sau mang ID theo chương:

1. Quỹ 1
2. Quỹ 2
3. Quỹ 3

Các Quỹ có thể thuộc cơ quan, doanh nghiệp, tổ chức, cộng đồng hoặc chi hội cụ thể.

## 7. Quy tắc tham chiếu

1. Không sao chép định nghĩa Bộ Tam, CFPU hoặc CFPT sang chương khác.
2. Không tạo Canonical ID mới cho cùng một khái niệm.
3. Các tài liệu khác sử dụng Canonical Link dẫn về Chương 3.
4. Ba Quỹ theo từng chương có ID riêng để quản lý đối tượng vận hành cụ thể.
5. Tài liệu Quỹ có thể dẫn về định nghĩa nền tại Chương 3 khi cần giải thích quan hệ với Bộ Tam.

## 8. Nguyên tắc kiến trúc

Kiến trúc này tuân thủ các nguyên tắc:

1. Một khái niệm toàn hệ thống chỉ có một Canonical ID.
2. Reference First.
3. Canonical Meaning.
4. Số đầu tiên xác định chương.
5. Mỗi cấp chỉ sử dụng các chữ số từ 0 đến 9.
6. Mở rộng bằng tầng sâu hơn, không vượt quá mười mục ngang hàng.
7. GitHub không tự xác lập Canonical Status.
8. Human Governance là thẩm quyền phê duyệt cuối cùng.

## 9. Các ID còn chờ Human Governance xác định

Tài liệu này chưa tự gán ID cụ thể cho:

1. Bộ Tam
2. CFPU
3. CFPT

Ba ID này phải được Human Governance xác định trong khung Chương 3 trước khi chuyển trạng thái từ Baseline Candidate sang Canonical.

## 10. Quy tắc thay đổi

Tài liệu chỉ được sửa đổi thông qua Governance Decision.

Mọi thay đổi liên quan đến công thức X331, X332, X333 hoặc Canonical ID của Bộ Tam, CFPU và CFPT phải được đánh giá tác động trước khi phê duyệt.
