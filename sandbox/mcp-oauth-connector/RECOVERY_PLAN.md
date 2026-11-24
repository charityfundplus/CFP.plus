# CFP+ • HUB 69 • P0 • Phương án khôi phục MCP Gateway và tích hợp Gemini OAuth

**Trạng thái:** DRAFT • SANDBOX • HOLD ACTIVATION • PRODUCTION NO-GO • 2026-11-24
**Nguyên tắc:** kế thừa `cfp-gateway`, không xây lại • không xoá dữ liệu • không đổi Canonical ID • không push thẳng `main` (Auto Deploy đang bật).

## Dữ kiện

| Dữ kiện | Nguồn | Trạng thái |
| --- | --- | --- |
| Railway project `splendid-liberation`, service `cfp-gateway`, PostgreSQL + `postgres-volume` | Founder, 2026-11-24 | Founder xác nhận |
| Cả 2 service offline, Railway báo **Trial expired** | Founder | Founder xác nhận |
| Nguồn: `charityfundplus/cfp-gateway` @ `main`, Auto Deploy bật | Founder | Founder xác nhận |
| `mcp.cfp.plus/*` → `404 Application not found` (`server: railway-hikari`) | `probe_result_20261124.json` | Đã kiểm chứng (khớp với service bị dừng do hết Trial) |
| Mã nguồn MCP, OAuth, Registry, phân quyền | repo riêng tư | **CHƯA ĐỌC • thiếu quyền GitHub** |

## Giai đoạn A • Bảo toàn (trước mọi kích hoạt) • Founder thực hiện

1. **Railway → Settings của service `cfp-gateway`:** tắt Auto Deploy (hoặc đổi nhánh deploy sang `release/gateway-restore`) trước khi nâng gói, để lúc khôi phục không tự build lại commit mới nhất của `main`.
2. **Nâng gói** từ Trial lên Hobby/Pro (Billing là việc của Human Governance). Không xoá project, service hay volume; không đổi biến môi trường.
3. **Sao lưu Postgres ngay khi chạy lại:** dùng Railway Backups (nếu gói hỗ trợ) hoặc `pg_dump` qua `DATABASE_URL` vào kho riêng tư. Ghi ngày giờ, kích thước, sha256 vào Evidence. Không commit dump hay `DATABASE_URL`.
4. Ghi lại cho Evidence: danh sách **tên** biến môi trường (không ghi giá trị), commit SHA đang deploy, custom domain, healthcheck path.

## Giai đoạn B • Khôi phục nguyên trạng

5. Redeploy **đúng commit SHA đã chạy trước khi hết Trial** (Railway → Deployments → Redeploy), không deploy commit mới.
6. Kiểm tra custom domain `mcp.cfp.plus` vẫn gắn với service; DNS không đổi.
7. Chạy `python3 sandbox/mcp-oauth-connector/probe.py`. Điều kiện đạt: endpoint ≠ 404, phản hồi 401 kèm `WWW-Authenticate`, discovery có mặt. Nếu Gateway chưa từng có OAuth cho đường dẫn `mcp-public`, ghi rõ nguyên trạng, không coi là lỗi khôi phục.
8. Dùng ChatGPT đọc lại một tool chỉ đọc (READBACK), để xác nhận hệ OAuth ChatGPT hiện hữu hoạt động lại.

## Giai đoạn C • Tích hợp Gemini OAuth (sau khi đọc được mã)

9. Rà `cfp-gateway`: cách lưu OAuth client (bảng/biến), luồng authorize/token, PKCE, scope, ánh xạ danh tính ↔ Registry, metadata `/.well-known/*`, transport Streamable HTTP.
10. Thêm Gemini là **client thứ hai** theo đúng cơ chế đang dùng cho ChatGPT: Client ID riêng, secret riêng (sinh trên máy chủ, lưu trong Railway Variables hoặc bảng có mã hoá), redirect URI khớp chính xác:
    `https://oauth-redirect.googleusercontent.com/r/user_bound_custom-mcp-db6be1542137b3a9ae65fd92`
11. Quyền: mặc định `mcp:read`; scope ghi chỉ dành cho danh tính đã xác minh trong Registry; không scope quản trị toàn hệ thống; không cấp ID mới.
12. Thay đổi đi qua **nhánh `claude/gateway-gemini-oauth` → Draft PR → 87783 review → Founder merge**. Có test: discovery, PKCE S256, redirect URI sai bị từ chối, token Gemini bị từ chối ở client ChatGPT và ngược lại, chỉ đọc khi chưa có scope ghi.
13. Migration (nếu cần bảng client) chỉ được thêm dữ liệu, không xoá hay sửa dòng cũ, và đi kèm script rollback.

## Giai đoạn D • Kiểm thử thực tế và nghiệm thu

14. Founder nhập vào Gemini: MCP URL, Client ID, Client Secret (dán trực tiếp vào form, không qua chat/issue).
15. Kết nối từ Gemini với tài khoản Founder, gọi một tool chỉ đọc. Evidence: ảnh chụp/ghi log có thời gian, log Gateway khớp `client_id` Gemini, kết quả `probe.py` có `MCP_TOKEN` (token chỉ dùng tạm, không lưu).
16. Lưu Evidence vào GitHub (Draft PR) và Link Mẫu 87788, báo HUB 69 #178. Giữ HOLD ACTIVATION cho đến khi 87783 review và Founder duyệt.

## Rollback

- Lỗi tại B: redeploy lại SHA trước đó; dữ liệu đã có bản sao lưu ở bước 3.
- Lỗi tại C/D: thu hồi client Gemini (vô hiệu hoá, không xoá dòng), revert PR; client ChatGPT không bị ảnh hưởng vì dùng secret riêng.

## Cần Founder

- Cấp quyền GitHub cho `cfp-gateway` (claude.ai/connect-github + Claude GitHub App) rồi mở phiên mới chọn repo đó.
- Bước 1–4 trên Railway (Auto Deploy, Billing, sao lưu).
