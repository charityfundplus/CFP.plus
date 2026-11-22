# CFP+ • Cập nhật nội dung Website không cần sửa mã nguồn

Mỗi trang mới = **một file Markdown** trong thư mục này. Không cần sửa HTML, CSS, nginx hay Dockerfile.

## Cách thêm hoặc sửa một trang

1. Sao chép `_TEMPLATE.md` thành `<ID>.md` (ví dụ `691187.md`). Tên file phải trùng `id`.
2. Điền phần đầu file (front matter) và viết nội dung bằng Markdown.
3. Mở Pull Request. CI **Website Content** tự kiểm tra; lỗi sẽ được báo rõ dòng nào.
4. Human Governance review và merge. Khi `main` thay đổi, hệ thống triển khai hiện có tự build lại;
   trang xuất hiện tại `https://cfp.plus/<ID>/`.

Có thể làm toàn bộ trên giao diện web GitHub, kể cả trên iPhone: *Add file → Create new file*.

## Front matter

| Khóa | Bắt buộc | Ý nghĩa |
|---|---|---|
| `id` | có | ID số đã được Registry cấp. Giữ nguyên mọi chữ số và số 0. |
| `title` | có | Tiêu đề trang. |
| `parent` | có | ID trang cha **đã tồn tại** (Nhóm/Chương/HUB 69…). |
| `description` | không | Mô tả ngắn cho Google và mạng xã hội. |
| `lang` | không | Mặc định `vi`. Mã ngôn ngữ cho trang dịch (`en`, `fr`…). |
| `status` | không | Nhãn trạng thái hiển thị, ví dụ `ĐANG BỔ SUNG/REVIEW`. |
| `updated` | không | Ngày cập nhật, ví dụ `2026-11-20`. |
| `draft` | không | `true` = kiểm tra nhưng chưa xuất bản. |

## Quy tắc an toàn (build tự chặn nếu vi phạm)

- Công cụ **không cấp ID, không đổi Parent, không sửa Registry**. Chỉ hiển thị ID đã có.
- **Không ghi đè** trang HTML viết tay hiện có. Muốn chuyển một trang cũ sang Markdown phải xóa HTML cũ trong cùng một PR được review.
- Cấm namespace cũ `66666`.
- HTML/script trong Markdown bị vô hiệu hóa (hiển thị như chữ). Link chỉ chấp nhận `https://`, `mailto:` hoặc đường dẫn bắt đầu bằng `/`.
- Trang con tự hiện trong mục **Trang Con** của trang cha (mở rộng Con • Cháu).

## Kiểm tra trên máy

```
python3 tools/build_pages.py --check
```
