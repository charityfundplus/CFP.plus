# 6789 • Evidence thực thi • 2026-11-27

Môi trường: Python 3.13.18, Linux x86_64, 4 CPU, **không GPU**. Thư viện: numpy 2.5.5, cirq 1.7.0, qiskit 2.6.2, qiskit-aer 0.18.4, pennylane 0.45.1, CUDA-Q 0.17.0 (`qpp-cpu`), ortools 9.15.6755, fastapi 0.165.0, mcp 2.3.0.

## Kiểm thử tự động
`pytest`: **26 passed**.
- Statevector 5 backend so với bộ nội tại trên mạch ngẫu nhiên 4 qubit × 30 cổng: fidelity > 1 − 1e-6 (Cirq tính float32 nên đạt ≈ 0.9999999).
- Bell self-test mọi backend: chỉ ra 00/11, mỗi trạng thái 50% ± 5%.
- Thứ tự bit q0 trái nhất trên mọi backend.
- OR-Tools CP-SAT MaxCut khớp lời giải vét cạn ở 5 đồ thị ngẫu nhiên.
- Audit phát hiện sửa dòng; nhận Job độc quyền; lease hết hạn tự trả về hàng đợi; Emergency Stop chặn worker; lỗi Job không làm chết worker.
- API: thiếu token → 401; ID sai, mạch quá giới hạn → 422; CMP Work Order → `REVIEW_REQUIRED`; Emergency Stop chỉ admin.

## Chạy thật (uvicorn + worker + scheduler 5 giây)
- `/health/ready` → `READY`, 1 worker sống, heartbeat < 1 giây.
- Scheduler tự gửi Bell self-test: 15 Job DONE, PASS trên cả 5 backend (numpy, cirq, qiskit, pennylane, cudaq).
- MaxCut 6 đỉnh qua API → `DONE`, cut 18, `OPTIMAL`.
- Diễn tập Emergency Stop: gửi Job → **423**, readiness → **503**; resume OK.
- `audit/verify` → ok, 35 bản ghi nối chuỗi.
- MCP stdio: 4 công cụ; `sqz_bell_selftest(qiskit)` PASS.

## Chưa làm được • giới hạn
- cuQuantum GPU: NOT AVAILABLE (không GPU).
- Docker image: không build được cục bộ (không có Docker daemon) → CI job `docker`.
- Chưa triển khai thường trực; 24/24 chỉ xác nhận khi có log vận hành thật sau khi được duyệt.
