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
