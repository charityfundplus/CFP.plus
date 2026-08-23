# CFP+ • Numeric Link Rule v1

**Trạng thái:** Open Build • Link First

## Quy tắc

Mỗi ID số phải đọc ngược được về Chương Gốc bằng cách bỏ lần lượt chữ số cuối.

- Chương Gốc: `0` đến `9`.
- Con: `00` đến `99`.
- Cháu: `000` đến `999`.
- Parent của một ID = bỏ chữ số cuối.
- Chương Gốc = tiếp tục bỏ chữ số cuối cho đến khi còn 1 chữ số.

## Ví dụ

- `312 → 31 → 3`
- `698 → 69 → 6`
- `927 → 92 → 9`
- `005 → 00 → 0`

## Canonical Link

Canonical Link dùng trực tiếp ID số:

- `https://cfp.plus/3`
- `https://cfp.plus/31`
- `https://cfp.plus/312`

Không chèn route chữ vào giữa ID.

## Link First

Trong giai đoạn Open Build:

1. Tạo/đăng ký link số trước.
2. Xác định Parent và Chương Gốc bằng quy tắc đọc ngược.
3. Gắn nội dung hiện có vào ID phù hợp.
4. AI tiếp tục bổ sung và review nội dung tại đúng link.
5. Không đổi ID chỉ vì tên nội dung được chỉnh sửa.

## Phạm vi đầy đủ

Mỗi Chương Gốc có 10 Con và mỗi Con có 10 Cháu.

Toàn hệ thống: 10 Chương Gốc • 100 Con • 1.000 Cháu.