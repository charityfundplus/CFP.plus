# 6789 • Open Super Quantum Z • Lõi dùng chung (SANDBOX)

**SANDBOX PRACTICE GO • HOLD ACTIVATION • PRODUCTION NO-GO**

Siêu Lượng Tử ⚛️ • SI 🤖 AI 🤖 • Siêu Phần Mềm. Mọi kết quả là **MÔ PHỎNG trên CPU cổ điển**; không có QPU thật, không tuyên bố lợi thế lượng tử.

| Thành phần | Mô-đun | Trạng thái |
| --- | --- | --- |
| Core: mạch trung lập, giới hạn an toàn (≤20 qubit, ≤5000 cổng, ≤100000 shots) | `sqz/circuit.py` | PASS |
| Bộ mô phỏng nội tại (chuẩn đối chiếu) | `sqz/backends` • `numpy` | PASS |
| Google Cirq | `cirq` | PASS |
| IBM Qiskit (+ Aer khi có) | `qiskit` | PASS |
| PennyLane | `pennylane` | PASS |
| NVIDIA CUDA-Q | `cudaq` (target `qpp-cpu`) | PASS trên CPU |
| NVIDIA cuQuantum | `cudaq` target `nvidia` | NOT AVAILABLE (không có GPU) |
| Google OR-Tools CP-SAT (MaxCut, có vét cạn kiểm chứng) | `sqz/optimize.py` | PASS |
| FastAPI + CMP Work Order | `sqz/api.py` | PASS |
| MCP (stdio) | `sqz/mcp_server.py` | PASS |
| Worker • Scheduler (Bell self-test định kỳ) • Heartbeat • lease tự phục hồi | `sqz/worker.py`, `sqz/store.py` | PASS |
| Audit nối chuỗi băm • Emergency Stop • token fail-closed | `sqz/store.py`, `sqz/api.py` | PASS |
| ID Số 5 Nhóm • 10 Chương • Con • Cháu • Siêu Bộ Tam 4/5/6+ số | `sqz/ids.py` | PASS |
| Docker + healthcheck, CI 3 job (core có PostgreSQL) | `Dockerfile`, `.github/workflows/sandbox-6789-super-quantum-z.yml` | xem CI |
| Adapter mở (`register()`, entry point `sqz.backends`) + lane QPU TẮT | `sqz/backends` | PASS |
| Phân loại `CLASSICAL` • `QUANTUM_SIMULATION` • `HYBRID_SIMULATION` • `QPU` | mọi kết quả | PASS |
| OR-Tools phân công nhiệm vụ cho Team • QAOA lai trên Cirq | `sqz/optimize.py` | PASS |
| API dùng chung `/trio/{id}` • review độc lập 6788 • `/evidence` cho 6776 | `sqz/api.py` | PASS |
| PostgreSQL (`SQZ_DATABASE_URL`) | `sqz/store.py` | CI |

Đặc tả đầy đủ: `SPEC.md`.

## Cài đặt và chạy

1. Python 3.11+ (đã kiểm 3.12 trong CI, 3.13 cục bộ). Không cần GPU hay QPU.
2. Chỉ lõi: `pip install -r requirements.txt` (numpy, OR-Tools, FastAPI, MCP, SQLAlchemy).
3. Thêm adapter lượng tử: `pip install -r requirements-quantum.txt` (Cirq, Qiskit + Aer, PennyLane, CUDA-Q CPU).
4. Kiểm thử: `pip install -r requirements-dev.txt && python -m pytest -q`.
5. API: `SQZ_API_TOKEN=… SQZ_ADMIN_TOKEN=… uvicorn sqz.api:app_from_env --factory --port 8000`.
6. MCP cho Claude Code / Codex: `python -m sqz.mcp_server` (stdio).
7. Docker: `docker build -t sqz-6789 . && docker run -p 8000:8000 -e SQZ_API_TOKEN=… -e SQZ_ADMIN_TOKEN=… sqz-6789`.

Biến môi trường: `SQZ_API_TOKEN`, `SQZ_ADMIN_TOKEN` (bắt buộc; thiếu thì API từ chối) • `SQZ_DATABASE_URL` (PostgreSQL, Cloud) hoặc `SQZ_DB_PATH` (SQLite) • `SQZ_WORKER` • `SQZ_SELFTEST_INTERVAL_S` • `SQZ_QPU_ENABLED` (mặc định tắt).

## Quy ước

- Bitstring và statevector: q0 là bit trái nhất trên mọi backend (đã kiểm tra chéo).
- `owner_id` phải là ID Số hiện hữu; lõi không cấp ID mới.
- Emergency Stop chặn nhận Job, worker và công cụ MCP; mọi bật/tắt ghi audit.
