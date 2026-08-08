# CFP+ Website Master Map

**Trạng thái:** Baseline Candidate — aligned to Release 1

**Ngôn ngữ chuẩn:** Tiếng Việt

## 1. Mục đích

Tài liệu này xác lập khung Website CFP+ cho Release 1 và phải được đọc cùng các baseline đã khóa. Việc sửa file này chỉ đồng bộ lớp triển khai công khai; không mở lại Foundation hoặc Architecture.

Thứ tự triển khai bắt buộc:

1. Giữ nguyên khung Website đã được Human Governance chốt.
2. Định danh và định vị ID.
3. Kiểm tra không thiếu và không trùng ID.
4. Nhập nội dung theo Source of Truth.
5. Review, link audit, responsive QA và Evidence Package trước release.

## 2. Năm nhóm Website — Release 1

| Nhóm | Vai trò khung |
|---|---|
| V | Public Gateway • Cổng công khai |
| 0 | Chương 0 • Foundation / nền tảng tham chiếu |
| 135 | Chương 1, Chương 3, Chương 5 |
| 246 | Chương 2, Chương 4, Chương 6 |
| 789 | Chương 7, Chương 8, Chương 9 |

**Canonical Release 1 group set:** `V • 0 • 135 • 246 • 789`.

- Không tạo Group Landing `D` trong Release 1.
- Không dùng `000` thay cho Group `0` trong navigation hoặc inventory Release 1.
- CMP thuộc Chương 0 theo quyết định hiện hành; Chương 6 chỉ tham chiếu vai trò liên quan theo nguyên tắc Reference First.

## 3. Mười chương

| Chương | Phạm vi ID chính | Nhóm |
|---|---|---|
| 0 | 00 đến 09 | 0 |
| 1 | 10 đến 19 | 135 |
| 2 | 20 đến 29 | 246 |
| 3 | 30 đến 39 | 135 |
| 4 | 40 đến 49 | 246 |
| 5 | 50 đến 59 | 135 |
| 6 | 60 đến 69 | 246 |
| 7 | 70 đến 79 | 789 |
| 8 | 80 đến 89 | 789 |
| 9 | 90 đến 99 | 789 |

## 4. Release 1 inventory contract

Release 1 gồm đúng các bề mặt chính sau:

- 1 Homepage.
- 5 Group Landing Pages: `V`, `0`, `135`, `246`, `789`.
- 10 Chapter Landing Pages: `0–9`.
- 100 Core Page routes: `00–99`.
- Header, Footer, Primary Navigation, Menu và Breadcrumb.
- Website Tree, Canonical ID Mapping và Canonical URL Mapping.
- Responsive QA, Link Audit, Evidence Package và Release Package.

Không mở rộng portal hoặc namespace ngoài phạm vi trên nếu chưa có Human Governance Decision.

## 5. Quy tắc định vị

1. Chữ số đầu tiên của ID nội dung xác định chương.
2. Mỗi chương có tối đa 10 nội dung chính, dùng chữ số 0 đến 9.
3. Mở rộng bằng tầng sâu hơn, không tăng quá 10 mục ngang hàng.
4. ID là định danh ổn định; tên nội dung có thể được review và hoàn thiện sau.
5. Mỗi ID chỉ có một Canonical Link.
6. Tài liệu nội dung phải tham chiếu đến ID đã được xác lập trước.
7. `V` là Group Landing / Public Gateway, không phải ID nội dung 00–99.
8. CMP và các nội dung dùng chung tuân theo Reference First; không tạo bản sao Canonical chỉ để phục vụ navigation.

## 6. Chương 3 và các thực thể độc lập

Bộ Tam, CFPU và CFPT có Canonical ID độc lập, chỉ được trình bày đầy đủ tại Chương 3.

Các chương khác không tạo bản sao mà chỉ dẫn Canonical Link về Chương 3.

Ba Quỹ là các thực thể vận hành theo chương và theo cơ quan, doanh nghiệp, tổ chức, cộng đồng hoặc chi hội.

Công thức ID bốn chữ số:

| Công thức | Ý nghĩa |
|---|---|
| X331 | Quỹ 1 thuộc Chương X |
| X332 | Quỹ 2 thuộc Chương X |
| X333 | Quỹ 3 thuộc Chương X |

Ví dụ Chương 1:

| ID | Nội dung |
|---|---|
| 1331 | Quỹ 1 |
| 1332 | Quỹ 2 |
| 1333 | Quỹ 3 |

## 7. Ranh giới tài liệu

Website Master Map xác lập kiến trúc triển khai và định vị. Nội dung chi tiết, mô tả, tiêu chuẩn, quy trình và hồ sơ được đưa vào theo từng tài liệu, có review và evidence riêng.

## 8. Change Rule

Mọi thay đổi đối với bộ năm nhóm `V • 0 • 135 • 246 • 789`, phạm vi `00–99`, công thức ID hoặc vị trí chương phải có Governance Decision của Human Governance.

## 9. Change Record

- 2026-08-08: đồng bộ Baseline Candidate với CMP-14 Release 1; bỏ Group `D`, chuẩn hóa `000` thành Group `0`, giữ CMP trong Chương 0 và Reference First cho Chương 6.
