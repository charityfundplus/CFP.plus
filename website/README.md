# CFP+ Website

**Only Plus+ For Life**

## Trạng thái

Baseline Candidate

## Ngôn ngữ chuẩn

Tiếng Việt là ngôn ngữ Canonical.

Bản tiếng Anh và các ngôn ngữ khác chỉ được tạo từ bản tiếng Việt đã hoàn thành review, được Human Governance phê duyệt và khóa Canonical.

## Source of Truth

Notion hiện là Source of Truth của nội dung Website.

GitHub là Canonical Repository công khai dành cho review, bằng chứng, lịch sử thay đổi và phát hành tài liệu đã được phê duyệt.

## Kiến trúc điều hướng

Homepage

V

0

1

2

3

4

5

6

7

8

9

## Năm nhóm

V

000

135

246

789

## Quy tắc ID

Mỗi cấp chỉ dùng các chữ số từ 0 đến 9.

Mỗi cấp không vượt quá 10 mục ngang hàng.

Khi cần mở rộng, tạo cấp sâu hơn.

Mỗi ID có một ý nghĩa chuẩn và không được tái sử dụng gây nhập nhằng.

Không dùng số âm.

## Cấu trúc thư mục

`home` chứa Homepage.

`V` chứa Governance và điều hướng cấp V.

`0` đến `9` chứa 10 chương Website.

Mỗi chương có Hub và tối đa 10 mục cấp trực tiếp theo dải 0 đến 9.

`registry` chứa danh mục Canonical ID, Canonical Link và nguồn Notion.

`sources` chứa bản ghi nguồn và trạng thái nhập tài liệu.

## Nguyên tắc công bố

Không Evidence thì không xác nhận Completion.

Không Human Governance phê duyệt thì không gắn Canonical Status.

Không sao chép định nghĩa chuẩn giữa nhiều tài liệu. Các tài liệu khác phải tham chiếu Canonical ID và Canonical Link.
