# CFP+ • HUB 69 • P0 • MCP OAuth Connector (Gemini trước, dùng lại cho mọi nền tảng)

**SANDBOX • HOLD ACTIVATION • PRODUCTION NO-GO** • 2026-11-24 • Claude Code

## Chẩn đoán endpoint (thực đo)

`https://mcp.cfp.plus/mcp-public/` và mọi đường dẫn (`/`, `/mcp`, `/health`, `/.well-known/*`) trả
`404 {"message":"Application not found"}` với `server: railway-hikari`.
Nghĩa là DNS `mcp.cfp.plus` vẫn trỏ vào edge Railway, nhưng **không service Railway nào còn gắn custom domain này**
(service bị xoá / tạm dừng / domain bị gỡ, hoặc project đổi). Đây không phải lỗi code MCP; máy chủ chưa nhận request.
Lịch sử: 2026-11-16 ghi "UNAVAILABLE / Connection failed" (`drafts/si-office/docs/LOCAL_HTTPS_REVIEW.md`).

Đã rà trong phiên: repo `CFP.plus` (mọi nhánh), `CFP`, Render (1 service Forum), Cloudflare (0 Worker), Supabase
(`auth.oauth_clients` 0 dòng, 0 Edge Function). **Không tìm thấy mã nguồn máy chủ MCP hay hệ OAuth ChatGPT.**
Railway không có connector trong phiên.

## Kết quả `probe.py --platform gemini`

Xem `probe_result_20261124.json`: 7 FAIL (endpoint 404, chưa có 401/WWW-Authenticate, Protected Resource Metadata,
AS Metadata, PKCE S256, endpoints, Client Gemini chưa đăng ký) • Token Exchange và Streamable HTTP: NOT RUN.

## Thiết kế dùng lại (khi khôi phục máy chủ)

1. MCP endpoint trả `401` + `WWW-Authenticate: Bearer resource_metadata=".../.well-known/oauth-protected-resource/mcp-public"`.
2. `/.well-known/oauth-protected-resource[/mcp-public]` (RFC 9728) → `authorization_servers`, `scopes_supported: ["mcp:read", ...]`.
3. `/.well-known/oauth-authorization-server` (RFC 8414): `authorization_endpoint`, `token_endpoint`, `code_challenge_methods_supported: ["S256"]`.
4. **Một OAuth Client cho mỗi nền tảng** (`platforms.json`): Client ID công khai, Client Secret riêng chỉ ở secret manager máy chủ; redirect URI khớp chính xác từng ký tự.
5. Quyền: mặc định `mcp:read`; scope ghi chỉ cấp cho danh tính đã xác minh trong Registry, không scope quản trị toàn hệ thống. Token gắn `sub` = tài khoản đăng nhập, ánh xạ ID Số có sẵn (không cấp ID mới).
6. Streamable HTTP: `POST` JSON-RPC, `Accept: application/json, text/event-stream`, header `Mcp-Session-Id`.
7. Kiểm thử: `python3 probe.py --platform <key>`; sau đăng nhập thật đặt `MCP_TOKEN` để chạy `initialize`.

## Cần Founder (Human Governance)

- Vào Railway: xác định project/service MCP, khởi động lại và gắn lại custom domain `mcp.cfp.plus` (hoặc cấp quyền/connector Railway hay chỉ ra repo mã nguồn máy chủ).
- Đăng ký OAuth Client Gemini trên máy chủ OAuth đó với redirect URI trong `platforms.json`; dán Client Secret trực tiếp vào form Gemini, không gửi qua chat/issue.
- Cấp quyền push GitHub cho phiên để đẩy Evidence và báo HUB 69 (#178).
