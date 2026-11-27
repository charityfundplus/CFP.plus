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
| Docker + healthcheck, CI 3 job | `Dockerfile`, `.github/workflows/sandbox-6789-super-quantum-z.yml` | xem CI |

## Chạy

```bash
pip install -r requirements.txt -r requirements-quantum.txt -r requirements-dev.txt
python -m pytest -q
SQZ_API_TOKEN=... SQZ_ADMIN_TOKEN=... uvicorn sqz.api:app_from_env --factory --port 8000
python -m sqz.mcp_server   # MCP stdio cho Claude Code / Codex
```

Biến môi trường: `SQZ_API_TOKEN`, `SQZ_ADMIN_TOKEN` (bắt buộc; thiếu thì API từ chối), `SQZ_DB_PATH`, `SQZ_WORKER`, `SQZ_SELFTEST_INTERVAL_S`.

## Quy ước

- Bitstring và statevector: q0 là bit trái nhất trên mọi backend (đã kiểm tra chéo).
- `owner_id` phải là ID Số hiện hữu; lõi không cấp ID mới.
- Emergency Stop chặn nhận Job, worker và công cụ MCP; mọi bật/tắt ghi audit.
