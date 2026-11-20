# Runbook • Render `cfp-forum-office-sandbox-p0` ↔ Supabase `cfp-plus-forum-sandbox` (lưu bền vững)

**SANDBOX • chưa thực hiện • cần Human Governance phê duyệt từng bước có đánh dấu 🔒.** Tài liệu này không chứa secret.

## Hiện trạng đã kiểm (chỉ đọc, 20/11/2026)

| Hạng mục | Giá trị |
|---|---|
| Render service | `srv-dblo01nf3r2c73e74jq0`, gói **free**, region oregon, `autoDeploy: no`, nhánh `claude/gallant-carson-8uogxj` |
| Bản đang chạy | `396c1d8` (deploy 08/11), chế độ **ephemeral-sqlite** (dữ liệu mất khi restart) |
| Health check trên Dashboard | **trống** (`render.yaml` ghi `/api/health`; service không tạo từ Blueprint) |
| Supabase | gói **Free**, Postgres 17, `ACTIVE_HEALTHY` |
| Migration đã áp | `#193 schemas_up` (20261103203246), `002_office` (20261104043050), `drop_rls_probe_20261120` (chỉ xóa bảng thử) |
| Vai trò | 3 role diễn đàn `LOGIN`, conn limit 20 • `office_app` **NOLOGIN** • `anon`/`authenticated` không có USAGE trên `cfp_*` |
| Dữ liệu | Văn Phòng 0 dòng. Schema diễn đàn chưa có bảng (app tạo khi khởi động lần đầu) |
| Security advisor | 0 cảnh báo |

## Các bước (theo thứ tự)

1. 🔒 **Mật khẩu role.** Chạy trong SQL Editor: `sql/set_passwords_sandbox.sql` (3 role diễn đàn) và `sql/set_password_office_sandbox.sql` (bật LOGIN cho `office_app`). Mật khẩu sinh trên server; chỉ chép URL vào secret Render, không dán vào GitHub/chat. Host Session pooler phải lấy từ Dashboard → Connect.
2. 🔒 **Biến môi trường Render** (Dashboard → Environment, đánh dấu secret):

   | Biến | Giá trị |
   |---|---|
   | `CFP_FORUM_AUTH_DB`, `CFP_FORUM_DB_SIEU_BO_DOI`, `CFP_FORUM_DB_SI_AI_HSTDN`, `CFP_OFFICE_DB` | URL từ bước 1 (`postgresql+psycopg://<role>.gmnsmggqvbwlgluvscfh:…@<pooler>:5432/postgres?sslmode=require`) |
   | `CFP_SANDBOX_EPHEMERAL` | **xóa** (không được để cùng các URL trên; app từ chối khởi động nếu trộn) |
   | `CFP_BOOTSTRAP_*` | xóa (chỉ dùng cho chế độ tạm) |
   | `CFP_FORUM_TRUST_PROXY=1`, `CFP_FORUM_TRUSTED_PROXY_HOPS=1`, `CFP_FORUM_COOKIE_SECURE=1` | giữ |
   | `CFP_EMBED_ORIGINS` | chỉ đặt **sau** khi chốt kết quả phản biện chế độ nhúng; không thêm `null` nếu không bắt buộc |
   | `CFP_WORKER_DB` | để trống tới khi 004 được duyệt |
3. 🔒 **Health check path** `/api/health` trên Dashboard.
4. 🔒 **Deploy thủ công** commit đã duyệt (Manual Deploy → commit cụ thể). Ghi lại deploy id.
5. **Tài khoản governance/reviewer sandbox:** đăng ký qua `/api/auth/register`, rồi cấp vai trò bằng `python -m services.forum.admin grant-office-role governance|reviewer <email>` với `CFP_OFFICE_ADMIN_DB` (URL quản trị chỉ dùng trên máy người vận hành, không đặt trên Render).
6. **Kiểm tra sau deploy** (GitHub Actions → *Render sandbox smoke* → Run workflow):
   - `/api/health`: `storage` ≠ `ephemeral-sqlite`, `auth_db`/`office` = `postgresql`.
   - Có `SMOKE_GOV_EMAIL`, `SMOKE_REVIEWER_EMAIL`, `SMOKE_PASSWORD` → chạy luồng đầy đủ task → ACK → Evidence → Review.
   - **Restart service** (Dashboard → Restart) rồi chạy lại smoke: bài và nhiệm vụ cũ phải còn.

## Khôi phục / rollback

- **Ứng dụng:** Render → Deploys → *Rollback* về `396c1d8`, đặt lại `CFP_SANDBOX_EPHEMERAL=1`.
- **Dữ liệu:** gói Free **không có** bản sao lưu tải về hay PITR. Dùng bản sao lưu logic `tests/forum/backup_drill.sh` (pg_dump dữ liệu mọi schema `cfp_*`, khôi phục vào DB mới, so khớp số dòng + md5 từng bảng + số policy RLS). Diễn tập cục bộ ngày 20/11 đạt PASS ở cả trạng thái 002 và 003+004. Chạy định kỳ trên Supabase cần URL quản trị (secret) và nơi lưu **mã hóa**: tệp có email + mã băm mật khẩu. 🔒 Cần quyết định nơi lưu.
- **Migration:** 003/004 **chưa áp**. Phản biện 19/11 và kiểm chứng chéo 20/11 xác nhận 003 còn 6 lỗ hổng (C1, C1b, C2, G3–G5): không áp cho tới khi có bản sửa đã review.

## Giới hạn của gói miễn phí

Render Free ngủ khi không có truy cập (lần gọi đầu chậm khoảng 30–60 s, không chạy 24/24). Supabase Free có thể tạm dừng dự án sau một thời gian không hoạt động. Nâng gói là quyết định chi phí 🔒.
