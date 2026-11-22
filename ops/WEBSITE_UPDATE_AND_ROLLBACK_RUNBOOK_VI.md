# Website CFP+ • Quy trình cập nhật và khôi phục (rollback)

Áp dụng sau khi Human Governance phê duyệt PR pipeline nội dung (#235, #176).

## A. Cập nhật nội dung (hằng ngày, không cần lập trình)

1. Trên GitHub (máy tính hoặc iPhone), mở `content/pages/`, chọn *Add file → Create new file*, đặt tên `<ID>.md`, theo mẫu `_TEMPLATE.md`.
2. Chọn *Create a new branch… and start a pull request*. Không commit thẳng vào `main`.
3. Đợi CI **Website Content** báo xanh. Nếu đỏ, đọc dòng lỗi (ví dụ `parent 999 does not exist`), sửa file và CI sẽ tự chạy lại.
4. Reviewer kiểm tra nội dung, sau đó Human Governance merge.
5. Cloud Build tự build và deploy sau khi `main` thay đổi.
6. **Kiểm chứng đã lên live** bằng hai bằng chứng độc lập:
   - `https://cfp.plus/<ID>/` trả về 200 và có tiêu đề mới.
   - Sau khi `.dockerignore` được merge, `/.git/` không còn công khai, nên SHA production được xác minh qua workflow **GCP Read-only Evidence** (`revisions.json`, `builds-*.json`). Trước đó, có thể dùng `https://cfp.plus/.git/FETCH_HEAD` (cách này sẽ ngừng hoạt động khi lỗ hổng được đóng).

## B. Khôi phục

| Tình huống | Cách khôi phục | Ai làm | Thời gian |
|---|---|---|---|
| Nội dung sai nhưng site vẫn chạy | GitHub *Revert* PR → merge → tự deploy lại | Biên tập + Human Governance | Vài phút |
| File nội dung lỗi | Không cần làm gì: build thất bại, revision cũ vẫn phục vụ | (tự động) | 0 |
| Revision mới lỗi (5xx) | Chuyển traffic về revision trước (lệnh bên dưới), rồi revert trên GitHub | Người có `run.developer`/`run.admin` | Khoảng 1 phút |

```bash
gcloud run revisions list --service cfp-plus --region asia-southeast1 --project abiding-robot-507708-i3 --limit 5
gcloud run services update-traffic cfp-plus --region asia-southeast1 --project abiding-robot-507708-i3 \
  --to-revisions <REVISION_TRUOC>=100
# Sau khi revert trên main và deploy lại thành công:
gcloud run services update-traffic cfp-plus --region asia-southeast1 --project abiding-robot-507708-i3 --to-latest
```

Lưu ý: sau khi chuyển traffic về revision cũ, deploy mới **không tự nhận traffic** cho tới khi chạy `--to-latest`.

## C. Lịch sử chỉnh sửa

- Mọi thay đổi nội dung = commit Git, có người viết, thời điểm, diff và PR review. Đây là "lịch sử phiên bản" của CMS.
- Mỗi deploy = một Cloud Run revision bất biến, có thể quay lại bất kỳ lúc nào.
