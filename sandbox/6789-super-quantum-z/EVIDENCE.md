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

---

# v0.4 • Nền tảng Siêu Bộ Tam dùng chung • 2026-11-27

`pytest` cục bộ: **83 passed, 4 skipped**. Có 4 test PostgreSQL chỉ chạy trong CI: mất kết nối, restart, đa worker, khôi phục.

| Hạng mục | Kết quả |
| --- | --- |
| Danh tính thực | Claude Code gửi thay 6788 → 403. 87783 mạo danh 6788 để review → 403. Thiếu scope → 403. 6788 thật → 200. Cùng token tự review → từ chối. Token trùng hoặc ID sai → không khởi động |
| Fencing | Worker chậm bị thu hồi lease thì không chốt được (fence cũ); không chốt hai lần |
| Đa worker | 8 luồng × 120 Job: mỗi Job thực thi **đúng 1 lần**, audit hợp lệ |
| Idempotency | 16 luồng cùng khóa → 1 Job; CMP gửi lại → cùng Job |
| Đa tiến trình | **Lỗi thật phát hiện được:** 2 instance trên SQLite làm chuỗi audit rẽ nhánh tại seq 23. Đã sửa bằng compare-and-swap + `BEGIN IMMEDIATE`; test 4 tiến trình × 192 bản ghi đạt |
| Chạy thật 2 instance | 90 request đồng thời → 90×202, 60 Job riêng biệt (30 lần gửi lại không tạo trùng); 130 Job DONE, 0 chốt trùng, audit hợp lệ |
| Gateway | Tra ID: GATEWAY_VERIFIED / NOT_FOUND / LOCAL_FORMAT_ONLY khi gateway sập (mock HTTP). Trường Work Order khớp `main.py` của cfp-gateway |
| 1.110 ID nền tảng | 10 Chương + 100 Con + 1.000 Cháu, cùng 104 ID kiểm kê: `/trio/{id}` đều 200; "0", "00", "000" là ba ID khác nhau |
| 115 Team | Kiểm kê thật 104 Siêu Bộ Tam → 115 Team × 33 (FEASIBLE, 60 giây); mỗi Siêu Bộ Tam tối đa 37 Team (= mức tối thiểu lý thuyết 3795/104); mọi Team đủ 4 Nhóm. `evidence/team_formation.json` |
| Ưu tiên, chia sẻ, thay phiên | Ưu tiên cao chạy trước; hạn mức theo owner; 9 lượt review chia đều 3/3/3, không ai review hai lượt liền |

Giới hạn: danh sách chính thức 1.115 ID chưa có trong repo; DID chưa được Registry cấp nên luôn ở trạng thái `NOT_ASSIGNED`; staging chưa triển khai.

---

# v0.5 • P0 khẩn cấp 6776 • Work Order MCP-DDB8FF1A5BD9 • 2026-11-27

**Gateway đo trực tiếp** (`https://mcp.cfp.plus`):
- `/health` → 0.4.3, lưu trữ postgres, `auto_worker: disabled`.
- `/api/id/69` → 200 CURRENT; `/api/id/6776`, `1127`, `0229` → 404.

**Nguyên nhân gốc của NOT_FOUND (đã xác minh trong mã):** trong `cfp-gateway/main.py` (dòng 391), `CANONICAL_IDS` là dict viết cứng chỉ có 3 ID (69, 6984, 6911). Resolver không đọc Registry hay Notion nào khác. Lỗi không nằm ở quyền truy cập hay đồng bộ.

**Bản sửa Gateway** (patch `../mcp-oauth-connector/patches/0002-…`, commit cục bộ `668777f`):
- Nạp thêm `config/core_registry.json`; 3 ID gốc không bị ghi đè; giữ nguyên trạng thái `INVENTORY_REVIEW` (không tự nâng lên Canonical); giữ số 0 đầu; loại khóa không phải chữ số; thêm `/api/registry/status` (sha256, số lượng).
- Snapshot 104 ID tạo từ kiểm kê 87788 (`scripts/build_core_registry.py`, 0 ID bị loại).
- Kết quả: 6776, 6789, 87788, 0, 000 → 200 INVENTORY_REVIEW. 1127, 0229 → 404, đúng vì kiểm kê chưa có hồ sơ cho hai ID này, không tự tạo.
- `pytest` gateway: 25 passed (gồm 4 test mới).

**Validator ID Số Sống** `sqz/idformula.py`: chỉ áp dụng R1–R6 trích từ Mẫu Chung 366. Phần chưa xác minh (Parent, Registry) trả về trạng thái `pending`.
- Đã kiểm thử:
  - số 0 đầu: "0", "00", "000" là ba ID khác nhau; số nguyên bị từ chối;
  - "10" là hai cấp;
  - phân tầng và Nhóm;
  - 366 MMDD khớp lịch thật năm nhuận 2024; Daily Record 0229 chỉ năm nhuận, gồm cả các năm 1900, 2000, 2100;
  - phát hiện DDMM cũ (2711 → 1127);
  - kiêm nhiệm hợp lệ; bản trùng sau chuẩn hóa; xung đột tên cùng ID; khóa idempotency ổn định.
- API: `/ids/{id}/validate`, `/ids/validate-batch`, `/ids/mmdd?year=`.

**Chuỗi tự động** `sqz/pipeline.py`:
- Tiếp nhận → Phân công → Thực thi → Kiểm tra → Bàn giao. Bật bằng `SQZ_AUTO_HANDOVER=1`.
- Sau khi Job DONE, 6788 kiểm chứng độc lập, tạo báo cáo Evidence theo schema v1 và ghi audit `HANDOVER`. Job lỗi không được tự bàn giao.

`pytest` lõi: **91 passed, 4 skipped** cục bộ (4 test PostgreSQL chạy trong CI).

**Còn chặn:**
- Push `cfp-gateway` (phiên chỉ có quyền đọc).
- Gateway production vẫn chạy `f530739`, còn lỗi cấp quyền OAuth rộng hơn mức đã kiểm thử: cần duyệt deploy patch 0001.
- `auto_worker` đang tắt (bật là kích hoạt vận hành).
- Snapshot là kiểm kê, chưa phải Core Registry đầy đủ.
