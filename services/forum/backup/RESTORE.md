# CFP+ • Sao lưu và khôi phục kho Diễn Đàn / Văn Phòng / Worker

Trạng thái: **SANDBOX • chờ SecuritySI + Human Governance**. Không áp cho production khi chưa được phê duyệt.

## Thành phần

| Tệp | Vai trò |
| --- | --- |
| `services/forum/sql/006_backup_role.sql` | Role `cfp_backup_ro`: chỉ USAGE + SELECT, phiên read-only, BYPASSRLS (Văn Phòng bật FORCE RLS). Chạy lại sau mỗi migration mới. |
| `services/forum/backup/backup_drill.sh` | Kiểm tra phủ quyền → `pg_dump` → chụp số dòng + md5 → khôi phục vào database tạm → so sánh → `manifest.json`. |
| `.github/workflows/forum_office_p0_ci.yml` | Mỗi PR: chạy diễn tập trên Postgres 17 trong CI (không secrets). |
| `.github/workflows/forum_backup_nightly.yml` | Hằng đêm: sao lưu Supabase sandbox, diễn tập, mã hóa bằng khóa công khai, lưu artifact 30 ngày. |

Bản sao lưu **bỏ dữ liệu** `cfp_forum_auth.sessions` (phiên đăng nhập; sau khi khôi phục người dùng đăng nhập lại).

## Việc người có quyền phải làm một lần (Claude không tự làm)

1. Áp `006_backup_role.sql` lên Supabase. Sau đó chạy `ALTER ROLE cfp_backup_ro LOGIN PASSWORD '<mật khẩu dài>';`.
2. Tạo secret `SUPABASE_BACKUP_DB_URL`. Dùng Session Pooler, user dạng `cfp_backup_ro.<project_ref>`, thêm `sslmode=require`.
3. Người giữ khóa khôi phục tạo cặp khóa OpenPGP **ngoài GitHub**, rồi đặt khóa **công khai** vào variable `BACKUP_GPG_PUBLIC_KEY`. Khóa bí mật chỉ người giữ khóa có; nên giữ thêm một bản dự phòng theo quy trình kế nhiệm (#211).

## Khôi phục

1. Tải artifact `cfp-backup-<run_id>`. Kiểm tra mã băm: `sha256sum -c SHA256SUMS`.
2. Giải mã: `gpg --output cfp.dump --decrypt cfp-backup-*.dump.gpg`.
3. Luôn khôi phục vào **database mới** trước, không ghi đè kho đang chạy:
   `createdb cfp_restore && pg_restore -d cfp_restore --no-owner --no-privileges --exit-on-error cfp.dump`
4. Đối chiếu số dòng và md5 từng bảng với `manifest.json`. Có thể dùng chính `backup_drill.sh`, trỏ nguồn về database vừa khôi phục.
5. Chỉ khi khớp và có quyết định của Human Governance mới chuyển ứng dụng sang database đã khôi phục.

## Giới hạn

- Đây là sao lưu logic hằng ngày: điểm khôi phục tốt nhất là lần chạy gần nhất (RPO tới 24 giờ).
- Artifact của repo công khai có thể tải được bởi người khác, nhưng chỉ ở dạng **đã mã hóa**. Runner không bao giờ có khóa giải mã.
- Lịch hằng đêm chỉ chạy khi workflow nằm trên nhánh mặc định (main).
