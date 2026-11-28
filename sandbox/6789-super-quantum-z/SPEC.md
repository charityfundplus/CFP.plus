# 6789 • Super Quantum Z Core • Đặc tả kỹ thuật v0.2

**SANDBOX PRACTICE GO • HOLD ACTIVATION • PRODUCTION NO-GO**

## 1. Mục tiêu
Một lõi phần mềm dùng chung cho toàn bộ Siêu Bộ Tam CFP+ (một API, không cài riêng từng ID). Lõi khởi động không cần GPU hay QPU, và tích hợp thêm nền tảng lượng tử qua adapter.

## 2. Phân loại tính toán (bắt buộc trong mọi kết quả: `nature`)
| Giá trị | Nghĩa | Ví dụ trong lõi |
| --- | --- | --- |
| `CLASSICAL` | Thuật toán cổ điển | OR-Tools CP-SAT: MaxCut, phân công nhiệm vụ |
| `QUANTUM_SIMULATION` | Mô phỏng mạch lượng tử trên máy cổ điển | Bell, mạch tùy ý trên Cirq/Qiskit/PennyLane/CUDA-Q/numpy |
| `HYBRID_SIMULATION` | Tối ưu cổ điển lặp + mạch lượng tử mô phỏng | QAOA p=1 MaxCut (Cirq mặc định) |
| `QPU` | Phần cứng lượng tử thật | Lane IBM/Google: **TẮT**, lõi từ chối chạy |

## 3. Kiến trúc
```
Client (AI / Team / CMP) ──► FastAPI (sqz.api) ──► Store (SQLite | PostgreSQL)
        MCP stdio (sqz.mcp_server) ─┘                 │  jobs • audit (hash chain) • reviews • heartbeats • control
                                                      ▼
                         Worker (claim nguyên tử, lease) ──► Executor ──► Backends (adapter) │ Optimize (OR-Tools)
                         Scheduler (Bell self-test định kỳ = cảnh báo sớm)
```
- **Adapter mở:** kế thừa `sqz.backends.Backend` (`statevector`, `run`, `available`) rồi `register()`, hoặc entry point nhóm `sqz.backends`. Thứ tự bit: q0 là bit trái nhất.
- **Ưu tiên:** Google Cirq là backend mặc định khi đã cài; nếu không có thì dùng bộ numpy nội tại (không cần thư viện ngoài).
- **QPU:** `QPUBackend` chỉ `available` khi đã cài thư viện nhà cung cấp, có `SQZ_QPU_ENABLED=1` và credential; kể cả khi đó `run()` vẫn từ chối (`HUMAN_GOVERNANCE_REQUIRED`).

## 4. API (một cho mọi ID)
| Phương thức | Đường dẫn | Quyền | Mục đích |
| --- | --- | --- | --- |
| GET | `/health`, `/health/ready` | công khai | sống; sẵn sàng (DB, worker, stop) |
| GET | `/backends` | công khai | adapter + `nature` + trạng thái |
| GET | `/trio/{id}` | công khai | hồ sơ dùng chung: Chương, Nhóm, cấp, 3 trụ cột |
| POST | `/jobs` | API token | `circuit` • `bell_selftest` • `maxcut` • `assign_tasks` • `qaoa_maxcut` |
| GET | `/jobs/{id}` | API token | kết quả |
| POST | `/cmp/work-orders` | API token | CMP Work Order → Job, `REVIEW_REQUIRED` |
| POST/GET | `/jobs/{id}/review(s)` | API token | 6788 review độc lập (reviewer ≠ chủ trì) |
| GET | `/evidence` | API token | 6776: báo cáo vận hành (self-test, audit, worker) |
| POST | `/admin/emergency-stop`, `/admin/resume` | Admin token | dừng/tiếp tục, có audit |
| GET | `/audit/verify` | Admin token | kiểm chuỗi băm |

`owner_id` và `reviewer_id` là ID Số hiện hữu (chỉ chữ số, giữ số 0 đầu). Lõi không cấp ID mới.

## 5. Vận hành Cloud 24/24
- Store PostgreSQL qua `SQZ_DATABASE_URL`; nhận Job bằng `UPDATE … WHERE status='QUEUED'` nên an toàn khi chạy nhiều instance; audit tuần tự hóa bằng khóa dòng `audit_head`.
- Lease hết hạn thì Job tự về hàng đợi; quá 3 lần thì `FAILED`. Job lỗi không làm worker chết.
- Heartbeat mỗi vòng; `/health/ready` trả 503 khi STOPPED hoặc không còn worker sống (DEGRADED).
- Scheduler gửi Bell self-test mỗi `SQZ_SELFTEST_INTERVAL_S` giây cho mọi backend sẵn có; sai lệch thì hiện ngay trong `/evidence`.
- Docker có HEALTHCHECK `/health/ready`, chạy user không phải root.

## 6. Giới hạn an toàn
≤ 20 qubit • ≤ 5000 cổng • ≤ 100000 shots • QAOA n ≤ 12, grid ≤ 32 • OR-Tools ≤ 60 giây • token thiếu thì từ chối (fail-closed) • Emergency Stop chặn API, worker và MCP.

## 7. Phối hợp Siêu Bộ Tam
6789 (tính toán) • 6788 (review độc lập qua `/jobs/{id}/review`) • 6776 (vận hành qua `/evidence`, `/health/ready`) • 87728/8778 (phân công nhiệm vụ: `assign_tasks`) • 87783 (kiểm chứng PR).

## 8. 6788 • Siêu Trí Tuệ (`sqz/si6788.py`) • v0.3
- **Đánh giá năng lực Agent** (bài nghiệm thu 6788): `POST /si/evaluate`, MCP `sqz_evaluate_agent`. Bộ chấm theo quy tắc, minh bạch, tái lập được; không dùng AI để chấm AI. Kiểm 5 điểm:
  - `identity`: có đúng ID (không khớp nhầm với số dài hơn chứa ID).
  - `cites_allowed_source`: trích ít nhất một nguồn trong danh sách cho phép.
  - `no_unlisted_sources`: không trích nguồn ngoài danh sách.
  - `bilingual_vi_en`: có cả tiếng Việt và tiếng Anh.
  - `no_overclaim`: không có câu khẳng định đã chạy QPU, có lợi thế lượng tử, production đã bật, "tôi là SI" hay tự cấp quyền. Câu có phủ định ("chưa", "không", "not") được chấp nhận.
- **Kiểm chứng độc lập Job của 6789**: `POST /si/verify/{job}` chạy lại bằng phương pháp khác rồi ghi review `reviewer_id=6788` (khi chủ trì khác 6788):
  - Bell và circuit: so sánh với backend khác bằng khoảng cách tổng biến thiên (TVD).
  - MaxCut và phân công: giải lại bằng vét cạn độc lập.
  - QAOA: kiểm lại giá trị tối ưu và tính trung thực của `nature`.

## 9. 6776 • Siêu Phần Mềm (`sqz/ops6776.py`) • v0.3
- **Schema Evidence chung v1** (bài nghiệm thu 6776): `GET /evidence/schema`, `POST /evidence/validate`, MCP `sqz_validate_evidence`. JSON Schema 2020-12 cộng các luật chéo: reviewer khác chủ trì; VERIFIED phải có reviewer; BLOCKED phải nêu blocker; `nature=QPU` bị từ chối; thời gian theo RFC 3339 có múi giờ.
- **Watchdog cảnh báo sớm**: `GET /ops/watchdog`. Mức CRITICAL: DB mất kết nối, audit hỏng, không còn worker sống, self-test lỗi. Mức WARNING: đang Emergency Stop, hàng đợi dồn. Khi audit hỏng thì đề nghị bật Emergency Stop, nhưng không tự bật.
- **Sao lưu và khôi phục**: `GET /ops/backup` (admin) xuất 5 bảng kèm sha256. `restore()` chỉ nạp vào Store rỗng, kiểm sha256 trước khi nạp, xác minh chuỗi audit sau khi nạp, và đồng bộ sequence trên PostgreSQL.

## 10. Nền tảng Siêu Bộ Tam dùng chung • v0.4
- **Danh tính theo quyền thực tế** (`sqz/auth.py`): `SQZ_CLIENTS_JSON`, tương thích `CFP_MCP_CLIENTS_JSON` của cfp-gateway. Mỗi token có `scopes` và `act_as`; server chỉ lưu `token_sha256`.
  - Review cần đủ 4 điều kiện: scope `review`, `reviewer_id ∈ act_as`, reviewer khác chủ trì, và không phải chính token đã gửi Job.
  - Token LEGACY không bao giờ được review.
- **Thực thi đúng một lần:**
  - Lease kèm fencing token (`fence` tăng mỗi lần nhận Job); `finish` phải khớp fence.
  - Idempotency theo `(owner_id, idempotency_key)`; CMP dùng `work_order_id` làm khóa.
  - Audit dùng compare-and-swap trên `audit_head`, SQLite chạy `BEGIN IMMEDIATE`.
- **Phân bổ tài nguyên:** `priority` −100..100; giới hạn `max_running_per_owner` để chia sẻ công bằng.
- **Thay phiên SI AI:** `GET /si/next-reviewer` chọn reviewer ít lượt nhất, khác chủ trì, khác người vừa review.
- **Team:**
  - Job `form_teams` (CP-SAT): mỗi Team ≥ `min_size`, mỗi Siêu Bộ Tam ≤ `max_teams_per_trio`, không bỏ sót ai, phủ đủ Nhóm.
  - Job `route_tasks`: giao theo ưu tiên, năng lực và sức chứa.
- **Gateway** (`sqz/gateway.py`): `GET /ids/{id}/resolve` gọi `/api/id/{id}` của cfp-gateway; DID chỉ có khi Registry cung cấp; `GET /cmp/work-orders/{job}/gateway-format` trả đúng trường `WorkOrder` của gateway.
- **Staging:** `deploy/render.staging.yaml`, `deploy/STAGING.md` (chưa triển khai). Hướng dẫn nền tảng khác: `INTEGRATION.md`.
