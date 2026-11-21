# Evidence • SEC-195-03c / 03d • RLS 003: bất biến GHI + chống ghi trùng task_events

**Phạm vi:** SANDBOX. Chỉ sửa mã và chạy kiểm thử trên Postgres cục bộ và CI. **Không** áp Supabase, không merge, không deploy.
**Gốc:** head PR #195 `a801627b607db4c0781afd61fa2b49c707c5e2d6`. Phản biện gốc: https://github.com/charityfundplus/CFP.plus/pull/195#issuecomment-7021451128
**Commit:** xem SHA của commit chứa thư mục này (báo cáo trong Draft PR); bước 03c đầu tiên: `fe697374ce6d70f8584c8be6dd8cd10dcb202f33`.

| Tệp | sha256 (16 ký tự đầu) |
|---|---|
| `services/forum/sql/003_office_rls.sql` | `e2b9fc22f44fff6e` |
| `services/forum/sql/003_office_rls_down.sql` | `4a2d564dec378185` |
| `tests/forum/rls_write_invariants.sql` (SQL tái lập) | `908599f16d245d0b` |

## Kết quả (PostgreSQL 16.15 cục bộ)

| Log | Nội dung | Kết quả |
|---|---|---|
| `before_a801627.log` | cùng bộ 49 ca, chạy trên 003 @ a801627 | **26 FAIL**: 23 lỗ hổng thật (C1–C1e, C2a–C2f, G3, G3b, G5, G4–G4d, G4f, D1–D4) + 3 ca D5–D7 chưa có đối tượng (bảng/hàm token chưa tồn tại) |
| `after_003c.log` | 49 ca: 30 tấn công + 19 đối chứng hợp lệ | **49/49 PASS**, rollback sạch |
| `rls_task_transitions.log` | SEC-195-03b máy trạng thái | 56/56 PASS |
| `migration.log` | #193 → 002 → 003 → 004, mỗi bước ×2, down → up | OK; office_tables=15, office_rls_forced=15 |
| `upgrade_002_to_003.log` | nâng cấp 002 → 003 khi có nhiệm vụ dở dang | 23/23 PASS |
| `pytest_postgres_003.log` | pytest Postgres có 003 | 181 passed, 1 skipped (ca chỉ chạy SQLite) |
| `playwright.log` | E2E Văn Phòng (iPhone 13) + Diễn Đàn | 31/31 • 17/17 |
| `worker_runtime.log` | Worker P0 chạy thật | WORKER_RUNTIME=PASS |

Kiểm tra bổ sung cục bộ (không lưu log riêng): pytest SQLite 144 passed; chế độ chỉ 002 pytest 162 passed, 20 skipped;
áp 003 mới **đè lên** 003 cũ (@a801627 và @fe69737) → 49/49 + 56/56.

## Thay đổi

- **C1, C1b** • `links` INSERT: hai đầu `ref_visible` + `can_link_from(from_ref)` (giống `add_link()`). Khác app có chủ đích: nguồn `task:` chỉ cần xem được nhiệm vụ, vì app tự ghi link bài học/thảo luận cho mọi người tham gia (kể cả reviewer).
- **C2 (tạo), G3, G5** • `tasks` INSERT: `QUEUED`, `assignee_id` = lead Siêu Bộ Đôi, `reviewer_id <> assignee_id`, reviewer có vai trò reviewer/governance, `review_round = 0`.
- **C2 (Closure)** • `enforce_task_transition`: ACCEPTED → CLOSED đòi Review ACCEPT của reviewer được chỉ định (khác người thực thi) trong đúng vòng hiện tại.
- **G4** • `task_events` INSERT: `task_event_ok` (khớp trạng thái thật + đúng người cho bước chuyển).
- **03d chống ghi trùng** • bảng nội bộ `task_transition_tokens` (office_app không có quyền nào; FORCE RLS, không policy). Trigger SECURITY DEFINER phát 1 token cho mỗi lần tạo nhiệm vụ / đổi trạng thái thật; trigger AFTER INSERT trên `task_events` buộc mỗi sự kiện không phải COMMENT tiêu thụ đúng 1 token của cùng giao dịch. Không cần sửa app.
- Đổi người thực thi / reviewer: office_app vốn chỉ có quyền UPDATE `status, updated_at` (03b) → không đổi được; `review_round` chỉ trigger ghi.

## Tương thích (Supabase sandbox, đọc chỉ bằng SELECT ngày 2026-11-19)

PostgreSQL 17.11 • role `postgres` có BYPASSRLS (003 yêu cầu) • 003 **chưa áp** (rls_user_policies=0, 14 bảng) • 0 nhiệm vụ • có event trigger `ensure_rls` (bảng token đã tự bật + FORCE RLS). `pg_current_xact_id` / `xid8` cần PostgreSQL ≥ 13. CI chạy Postgres 17.

## Giới hạn còn lại

- Không chống kẻ đã chiếm credential office_app (có thể tự đặt `cfp.user_id`) — giống mô hình tin cậy của 003.
- Ở tầng DB, bình luận (COMMENT) vẫn ghi lặp được (đúng chủ đích); `forum:` ref không kiểm quyền đọc diễn đàn ở DB (kho khác).
- Chưa có thẩm định độc lập của SecuritySI / ReviewSI. Tác giả **không** tự nghiệm thu.

## Tái lập

```bash
PGUSER=<superuser> tests/forum/setup_pg.sh cfp_ci
psql -v ON_ERROR_STOP=1 -d cfp_ci -f tests/forum/rls_write_invariants.sql   # SEC195_03C pass=49 fail=0 rollback_clean=t
```
