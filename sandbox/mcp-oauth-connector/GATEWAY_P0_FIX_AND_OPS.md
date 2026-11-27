# CFP+ • HUB 69 • P0 • Sửa quyền tối thiểu, lane Gemini OAuth, dữ liệu và vận hành 24/24

**SANDBOX • HOLD ACTIVATION • PRODUCTION NO-GO** • 2026-11-25 • Claude Code
Nguồn: `charityfundplus/cfp-gateway` @ `f530739` (chỉ đọc). Không redeploy, không merge, không chi phí.

## 1. Commit Railway ổn định gần nhất

- `main` @ `f530739` (2026-09-19, "Add controlled Claude MCP end-to-end test") là commit mới nhất trên `main` và là commit Railway deploy thành công cuối cùng.
- **ĐÃ XÁC MINH (commit status Railway):** `f530739` deploy SUCCESS 2026-09-20T03:37Z ở **2 project**: `splendid-liberation` và `intelligent-comfort`. Project thứ hai chưa được nêu trong báo cáo trước: cần Founder kiểm tra trạng thái, chi phí và domain của nó.
- Hệ quả: nếu `f530739` đang chạy, Production đã cấp scope rộng (mục 2) từ khi deploy.

## 2. Sửa 2 FAIL • nguyên tắc quyền tối thiểu

**Nguyên nhân gốc (mã sai, test đúng):** `ChatGPTOAuthProvider.authorize()` tự động thêm mọi `OPERATIONAL_SCOPES` (`read propose execute_approved write_noncanonical`) vào yêu cầu, dù client không xin. Đây là leo thang quyền ngầm.

**Bản sửa** (patch `patches/0001-…patch`, commit cục bộ `331d6cc` trên nhánh `claude/p0-least-privilege-gemini-oauth` của `cfp-gateway`):
- Mặc định ChatGPT: `read`, `propose`.
- `execute_approved`, `write_noncanonical` chỉ được công bố và cấp khi Human Governance liệt kê trong biến Railway `CFP_CHATGPT_OAUTH_ELEVATED_SCOPES` **và** client xin rõ ràng.
- Không sửa test. Kết quả: 20/20 test hiện hữu PASS (trước: 18/20).

## 3. Lane Gemini OAuth (quyền `read`)

- `gemini_oauth.py`: kế thừa `ChatGPTOAuthProvider`; issuer/resource `https://mcp.cfp.plus/mcp-gemini`; AI `691141`; scope `read` (+ `offline_access`).
- Tắt Dynamic Client Registration. Client đăng ký sẵn nạp lúc khởi động từ `CFP_GEMINI_OAUTH_CLIENT_ID` / `CFP_GEMINI_OAUTH_CLIENT_SECRET` (biến Railway riêng, không commit).
- Redirect URI khớp chính xác (`CFP_GEMINI_OAUTH_REDIRECT_URIS`, mặc định URI Gemini đã cung cấp).
- Consent `/oauth/gemini/consent` dùng `CFP_GEMINI_OAUTH_ADMIN_TOKEN` riêng, không fallback secret chung.
- **Cách ly token:** trạng thái OAuth lưu dưới tiền tố `gemini:` trong `oauth_state`; ChatGPT giữ tiền tố rỗng nên dữ liệu cũ vẫn hợp lệ.
- `CFP_GEMINI_OAUTH_TOKEN_AUTH_METHOD` (`client_secret_post` mặc định, đổi sang `client_secret_basic` nếu kiểm thử thật cho thấy Gemini gửi Basic): CHƯA XÁC MINH với Gemini.

**Kiểm thử (9 case, tiến trình riêng):** metadata chỉ `read`; không có registration endpoint; `/register` bị từ chối; chưa xác thực → 401 + `resource_metadata`; redirect URI sai bị từ chối; xin scope ngoài `read` → `invalid_scope` trước consent; mã quản trị sai → 403; PKCE S256 đầy đủ → token `read offline_access`; token Gemini dùng được ở `/mcp-gemini`, **bị từ chối 401 ở `/mcp-chatgpt`**; scope nâng cao tắt mặc định, chỉ nhận từ allowlist.

**Tổng:** `pytest` 21 PASS (20 hiện hữu + bộ Gemini).

## 4. PostgreSQL • OAuth • Audit • Work Order • Queue

| Mã | Mức | Phát hiện | Đề xuất |
| --- | --- | --- | --- |
| STORAGE_FALLBACK | HIGH | Thiếu `DATABASE_URL` → SQLite `/tmp`, mất dữ liệu khi restart mà vẫn báo `status: ok` | Kiểm tra `/health` có `storage: postgres` trước nghiệm thu |
| HEALTH_NO_DB | MEDIUM | `/health` không kiểm tra kết nối DB → Railway không phát hiện DB chết | Thêm `/health/ready` chạy `SELECT 1` |
| CLAIM_RACE | MEDIUM | `claim_next()` đọc-sửa-ghi không khóa → 2 worker/instance có thể nhận trùng Work Order | Cập nhật có điều kiện (`WHERE status='RECEIVED'`) hoặc `SELECT … FOR UPDATE SKIP LOCKED` |
| NO_MIGRATIONS | LOW | Chỉ `metadata.create_all` → thêm bảng được, đổi cột thì không | Alembic khi cần đổi schema |
| AUDIT_NOT_CHAINED | LOW | `audit_log` có sha256 từng dòng, không nối chuỗi → khó chứng minh không bị xóa dòng | Thêm `prev_digest` (hash chain) |
| OAUTH_STATE_GROWTH | LOW | Token/code hết hạn chỉ bị bỏ qua khi đọc, không dọn | Job dọn `expires_at < now` |

**Khôi phục dữ liệu:** dữ liệu nằm ở 5 bảng (`work_orders`, `reviews`, `audit_log`, `executors`, `oauth_state`) trên `postgres-volume`. Sau khi Founder khôi phục gói: `pg_dump --format=custom` → lưu riêng tư, ghi sha256; kiểm thử `pg_restore` vào DB tạm trước mọi thay đổi. Chính sách giữ volume khi hết Trial: CHƯA XÁC MINH.

## 5. Siêu Phần Mềm • vận hành 24/24 • tự phục hồi • cảnh báo sớm (phương án, chưa bật)

1. **Healthcheck 2 tầng:** `/health` (sống) + `/health/ready` (DB + session manager) làm Railway healthcheck path; restart policy `ON_FAILURE`.
2. **Giám sát ngoài:** GitHub Actions `schedule` mỗi 15 phút chạy `probe.py` + `GET /health/ready` (miễn phí trong hạn mức Actions); lỗi 2 lần liên tiếp → mở/ghi issue HUB 69 có nhãn `P0-ALERT`.
3. **Cảnh báo chi phí và gói:** cảnh báo khi Railway gần hết hạn mức (do Founder đặt trên Railway; Claude không thay đổi Billing).
4. **Tự phục hồi trong quyền:** Work Order `CLAIMED` quá hạn lease → trả về `RECEIVED` (sau khi sửa CLAIM_RACE); không tự redeploy.
5. **Sao lưu định kỳ:** `pg_dump` hằng ngày vào kho riêng tư, giữ 7 bản; diễn tập khôi phục hằng tháng.
6. **Mỗi bước bật** đi qua Draft PR + 87783 review + Founder duyệt.

## 6. Phân công Siêu Bộ Tam (đề xuất, không giao trùng)

| Team | Việc |
| --- | --- |
| 6776 Siêu Phần Mềm | Chủ trì mục 5 (healthcheck, giám sát, backup) |
| 6788 SI AI | Kiểm thử kết nối Gemini/ChatGPT thật sau khi Gateway chạy |
| 6789 Siêu Lượng Tử | Tối ưu hàng đợi (CLAIM_RACE, lease) |
| 8778 • 87728 | Điều phối, quyền tối thiểu từng nền tảng |
| 87783 | Review độc lập bản sửa này và PR #253 |

## 7. Cần Founder

1. Chốt SHA đang deploy trên Railway; quyết định gói (chi phí).
2. Cấp quyền ghi `cfp-gateway` cho phiên Claude Code (hiện chỉ đọc) để mở Draft PR từ nhánh `claude/p0-least-privilege-gemini-oauth`; hoặc Codex áp patch `patches/0001-…patch`.
3. Đặt biến Railway: `CFP_GEMINI_OAUTH_CLIENT_ID`, `CFP_GEMINI_OAUTH_CLIENT_SECRET`, `CFP_GEMINI_OAUTH_ADMIN_TOKEN` (sinh mới, không dùng lại secret ChatGPT). Không đặt `CFP_CHATGPT_OAUTH_ELEVATED_SCOPES` trừ khi Human Governance duyệt.
4. Sau khi deploy được duyệt: nhập vào Gemini URL `https://mcp.cfp.plus/mcp-gemini`, Client ID, Client Secret; kiểm thử thật và ghi Evidence.
