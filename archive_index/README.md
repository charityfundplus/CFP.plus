# CFP+ • Chỉ mục liên kho • P0 REVIEW

Đây là bộ khung **thực thi thử nghiệm**, không phải chứng nhận rằng sáu kho đã được đồng bộ. Không thay đổi Registry hoặc cấp ID mới.

## Mục đích
- Phân loại tài sản theo 5 Nhóm, 10 Chương; không tự suy diễn nhóm hoặc ID.
- Giữ một nguồn chính, nhiều đường dẫn bản sao và bằng chứng.
- Gắn cửa tra cứu MM-DD (366 cửa, gồm 02-29) mà không giới hạn năm.
- Phân biệt dữ liệu VERIFIED và PENDING; lưu mốc thời gian thật.

## Thử nhanh
```sh
python3 archive_index/validate_index.py archive_index/sample.json
python3 -m unittest discover -s archive_index/tests -v
```

## Các bước chưa thực hiện
Kiểm kê thực tế GitHub, Notion, Google, Cloud, Web, Quantum; xây adapter đọc chỉ mục; đối chiếu dữ liệu thực; phân quyền, hash và lịch sử; read-back xuyên kho; CI và phê duyệt. Các kết nối phải được xác minh và chỉ đọc trước.

**Quy tắc:** asset_key là khóa kỹ thuật, không phải Canonical ID. ID số chỉ được gắn khi đã xác minh trong Registry. Không tự động di chuyển, xóa hoặc ghi đè dữ liệu.
