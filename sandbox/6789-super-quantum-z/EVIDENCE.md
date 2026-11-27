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

---

# v0.2 • Evidence • 2026-11-27

`pytest`: **38 passed, 1 skipped** cục bộ (test PostgreSQL chạy trong CI có service Postgres 16).

Mới trong v0.2:
- **Adapter mở:** `register()` + entry point; plugin thử nghiệm chạy Bell PASS; tên trùng bị từ chối.
- **Lane QPU** (IBM, Google): mặc định `available=false`; API trả **403** khi chọn QPU; `run()` luôn từ chối.
- **Phân loại:** MaxCut và phân công nhiệm vụ là `CLASSICAL`; Bell là `QUANTUM_SIMULATION`; QAOA là `HYBRID_SIMULATION`.
- **Cirq mặc định.**
- **Store SQLAlchemy:** SQLite/PostgreSQL; audit phát hiện cả sửa dòng lẫn xóa dòng cuối; lease quá 3 lần → FAILED.

Chạy thật lần 2 (uvicorn + worker + scheduler 5 giây):
- `assign_tasks` (owner 87728): `CLASSICAL`, `OPTIMAL`, chi phí 8, khớp vét cạn.
- `qaoa_maxcut` 5 đỉnh trên Cirq: `HYBRID_SIMULATION`, tỉ lệ xấp xỉ kỳ vọng 0.817; mẫu tốt nhất đạt cut 5 = tối ưu OR-Tools.
- 6788 review độc lập: APPROVED (reviewer ≠ chủ trì).
- `/trio/87788` → Nhóm 789, `SIEU_BO_TAM_5_SO`, 3 trụ cột.
- `/evidence`: 27 Job DONE; Bell self-test 5/5 PASS trên cả 5 backend; audit hợp lệ 56 bản ghi; `/health/ready` READY.

---

# v0.3 • 6788 Siêu Trí Tuệ + 6776 Siêu Phần Mềm • 2026-11-27

`pytest`: **66 passed, 2 skipped** cục bộ. Hai test bị skip là test PostgreSQL, chạy trong CI.

**6788** (bài nghiệm thu: danh tính, trích nguồn, song ngữ)
- Câu trả lời mẫu đúng đạt cả 5 điểm kiểm.
- 6 câu trả lời lỗi, mỗi câu bị bắt đúng ở điểm kiểm tương ứng: sai ID, nguồn ngoài danh sách, thiếu nguồn hợp lệ, chỉ một ngôn ngữ, "đã chạy trên QPU, đạt lợi thế lượng tử", "I am a superintelligence".
- Kiểm chứng độc lập đủ 5 loại Job: APPROVED. Kết quả bị sửa (cut sai; Bell ra 01/10) → REJECTED.

**6776** (bài nghiệm thu: schema Evidence, dữ liệu hợp lệ và không hợp lệ)
- 1 báo cáo hợp lệ được chấp nhận; 13 báo cáo không hợp lệ đều bị từ chối, lỗi chỉ đúng trường.
- Watchdog: OK → bật Emergency Stop thì WARNING → sửa audit thì CRITICAL kèm đề nghị dừng; không có worker thì CRITICAL.
- Sao lưu → khôi phục: chuỗi audit giữ nguyên head và tiếp tục ghi được; Store đích có dữ liệu thì từ chối ghi đè; bản sao lưu bị sửa thì sha256 báo lỗi.

**Chạy thật** (uvicorn + worker + scheduler 5 giây)
- `assign_tasks` (87728) → `/si/verify`: APPROVED (vét cạn 8 = 8), review 6788 đã ghi.
- Bell self-test → `/si/verify`: APPROVED, TVD 0.004 ≤ 0.06.
- Bell self-test 3/3 PASS trên mỗi backend trong 5 backend.
- `/ops/watchdog`: OK, 0 cảnh báo.
- `/ops/backup`: sqz-backup-v1, 16 Job, 2 review, 35 audit.
- Diễn tập khôi phục vào Store mới: audit hợp lệ 35/35.
