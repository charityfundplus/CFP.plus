# Staging • phương án (chưa triển khai)

Mọi bước dưới đây cần Human Governance duyệt trước. Claude Code không tự triển khai, không phát sinh chi phí.

| Lựa chọn | Tài nguyên hiện có | Chi phí | 24/24 | Ghi chú |
| --- | --- | --- | --- | --- |
| A. Render free | Workspace Render đang có 1 service Forum | 0 | Không (instance ngủ khi rảnh) | Hợp cho staging kiểm thử; `deploy/render.staging.yaml` |
| B. Railway `splendid-liberation` | Đã có Postgres + volume | Theo gói Railway (Trial đã hết) | Có | Dùng lại Postgres của Gateway, mỗi ứng dụng một schema/database riêng |
| C. Supabase `cfp-plus-forum-sandbox` | Postgres đang ACTIVE | Theo gói hiện tại | DB có; compute đặt ở A hoặc B | Đặt `SQZ_DATABASE_URL` trỏ vào database riêng `sqz` |

Đề xuất: **A + C** cho staging không phát sinh chi phí, chuyển **B** khi Railway được khôi phục.

Kiểm tra sau triển khai:
1. `GET /health/ready` → READY.
2. `GET /ops/watchdog` → OK.
3. Bell self-test PASS trên mọi backend trong `/evidence`.
4. Diễn tập `/admin/emergency-stop` và `/admin/resume`.
5. `/ops/backup` → khôi phục thử vào DB tạm.
6. Ghi Evidence theo schema `/evidence/schema`.
