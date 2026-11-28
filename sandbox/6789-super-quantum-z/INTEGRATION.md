# Tích hợp lõi Siêu Bộ Tam (6789 • 6788 • 6776) trên mọi nền tảng

Một API và một bộ công cụ MCP dùng chung cho mọi ID Số. Không cài riêng từng ID. Mọi kết quả lượng tử là MÔ PHỎNG; QPU tắt.

## 1. Danh tính và quyền (bắt buộc)
Cấp cho mỗi AI hoặc Team một token riêng qua `SQZ_CLIENTS_JSON`. Định dạng tương thích `CFP_MCP_CLIENTS_JSON` của cfp-gateway:
```json
{"clients": [
  {"ai_id": "SI_6788", "name": "6788 Siêu Trí Tuệ", "token_sha256": "<sha256 của token>",
   "scopes": ["read", "review"], "act_as": ["6788"]},
  {"ai_id": "CLAUDE_CODE", "token_sha256": "<…>", "scopes": ["read", "submit"], "act_as": ["6789"]}
]}
```
- `scopes`: `read`, `submit`, `review`, `operate`, `admin`.
- `act_as`: danh sách ID Số mà token này được đại diện. Lõi chỉ kiểm định dạng ID, không cấp ID mới.
- Review: token phải có scope `review`, có `reviewer_id` nằm trong `act_as`, reviewer phải khác chủ trì, và không phải chính token đã gửi Job.
- Token gốc chỉ trao trực tiếp cho từng AI; trên server chỉ lưu `token_sha256`. Hai danh tính dùng chung một token thì lõi từ chối khởi động.

## 2. Gọi từ từng nền tảng
| Nền tảng | Cách nối | Ghi chú |
| --- | --- | --- |
| Claude Code, Codex, Claude Desktop | MCP stdio: `python -m sqz.mcp_server` | 8 công cụ `sqz_*` |
| ChatGPT, Gemini (custom MCP/OAuth) | Qua cfp-gateway (`/mcp-chatgpt`, `/mcp-gemini`), gateway gọi REST của lõi | Lane Gemini: patch `0001-…` |
| Notion Agent, Perplexity, script | REST + `Authorization: Bearer <token>` | Xem bảng API trong `SPEC.md` |
| CMP | `POST /cmp/work-orders` (`work_order_id` làm khóa idempotency) | Trả `REVIEW_REQUIRED`; `GET /cmp/work-orders/{job}/gateway-format` để chuyển tiếp |

## 3. Quy trình mẫu (một nhiệm vụ, một chủ trì)
1. Chủ trì gửi Job: `POST /jobs {owner_id, kind, payload, priority, idempotency_key}`.
2. Worker nhận Job, có lease và fencing token; nếu worker chết, Job tự quay lại hàng đợi; một Job chỉ được chốt đúng một lần.
3. 6788 kiểm chứng: `POST /si/verify/{job}` để chạy lại độc lập, hoặc `POST /jobs/{job}/review` để ghi kết luận thủ công.
4. Chọn reviewer thứ hai: `GET /si/next-reviewer?owner_id=&pool=&history=` (thay phiên SI AI).
5. 6776 vận hành: `GET /ops/watchdog`, `GET /evidence`, `GET /ops/backup`; kiểm báo cáo bằng `POST /evidence/validate`.
6. Tra ID Số Sống: `GET /ids/{id}/resolve` qua `SQZ_GATEWAY_URL`. DID chỉ có khi Registry cung cấp.

## 4. Phân công Team
- Job `form_teams {trio_ids, n_teams, min_size, max_teams_per_trio}` dùng OR-Tools.
- `scripts/run_team_formation.py` chạy trên kiểm kê thật của 87788 và ghi `evidence/team_formation.json`.
- Job `route_tasks {tasks, teams}` giao nhiệm vụ theo ưu tiên, năng lực và sức chứa.

## 5. Thêm nền tảng lượng tử mới
Kế thừa `sqz.backends.Backend`, rồi gọi `register()` hoặc khai entry point nhóm `sqz.backends`. Bắt buộc qua test chéo statevector với bộ `numpy` (fidelity > 1 − 1e-6) và Bell self-test.

## 6. Giới hạn đã biết
- Thêm cột mới chưa có migration tự động (chưa dùng Alembic): DB đã có từ v0.3 trở về trước cần tạo lại hoặc migrate tay.
- Lane QPU luôn từ chối chạy.
- Render free không đạt 24/24.
- Danh sách chính thức 1.115 ID chưa có trong repo. Test hiện bao phủ toàn bộ 1.110 ID 1–3 chữ số và 104 ID trong kiểm kê.
