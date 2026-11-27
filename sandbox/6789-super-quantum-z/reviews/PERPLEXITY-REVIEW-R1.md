# CFP+ 6789 • Open Super Quantum Z — Kiểm tra chéo độc lập Perplexity • Vòng 1

- Người kiểm tra: Perplexity (Team Siêu Bộ Tam, vai trò kiểm chứng độc lập)
- Ngày truy cập/kiểm tra: 2026-11-26 (America/New_York) • 2026-11-27 (UTC)
- Phạm vi: mã tại commit `1701a94` (v0.2) và `1d2c75a` (v0.3) trên PR [#253](https://github.com/charityfundplus/CFP.plus/pull/253)
- Trạng thái: SANDBOX PRACTICE • QPU TẮT • không phát sinh chi phí • không merge/deploy/đổi ID
- Kết luận ngắn: phần toán học và mô phỏng ĐÚNG (đã đo độc lập). Phần quản trị Job/review/audit có 5 lỗi cần vá trước khi gọi là "kiểm chứng độc lập". Bản vá v0.3.1 kèm 17 test mới nằm trên nhánh `pplx/6789-v0.2.1-review-r1`.

---

## 1. Kiểm tra độc lập kết quả Claude Code

### 1.1 Tái lập CI và test

| Hạng mục | Kết quả Claude Code | Perplexity chạy lại | Ghi chú |
|---|---|---|---|
| CI run [45921963844](https://github.com/charityfundplus/CFP.plus/actions/runs/45921963844) | 3 job xanh | Xác nhận: core 31 passed (có PostgreSQL 16), full 38 passed 1 skipped, Docker READY | Log Docker có cảnh báo `mkdir -p failed for path /home/sqz/.config/matplotlib: Permission denied`; worker báo version `0.1.0` |
| Test cục bộ `1701a94` | 36 passed, 1 skipped | 36 passed, 1 skipped | skip = CUDA-Q (không có GPU/cudaq) |
| Test cục bộ `1d2c75a` + bản vá | 66 passed (+2 PG) | 81 passed, 2 skipped | 66 cũ + 17 mới, toàn bộ test cũ vẫn qua |

### 1.2 Kiểm tra toán học (độc lập với test của Claude Code)

| Phép thử | Phương pháp | Kết quả |
|---|---|---|
| QAOA p=1 MaxCut | So với công thức giải tích (Wang, Hadfield, Jiang, Rieffel 2018) trên đồ thị ngẫu nhiên | sai số tối đa 2.9e-14 — ĐÚNG (mạch lõi cài exp(+iγC), lưới quét đủ chu kỳ) |
| Fuzz mạch | 30 mạch ngẫu nhiên 6 qubit × 60 cổng, fidelity so với numpy tham chiếu tự viết | Cirq 0.99999972, Qiskit/PennyLane ≈ 1.0 |
| Thứ tự bit | X trên q0 | mọi backend trả `"100"` — nhất quán |
| Hiệu năng QAOA n=12, lưới 32×32 | đo trên 2 vCPU | Cirq 9.11 s • numpy lõi 3.07 s • numpy chéo hóa (đề xuất §5.2) 0.49 s, cùng E=17.581283 |

### 1.3 Lỗi phát hiện (tái hiện được bằng test)

| Mã | Mức | Mô tả | Tái hiện tại 1701a94 / 1d2c75a | Bản vá v0.3.1 |
|---|---|---|---|---|
| F1 | CAO | Danh tính reviewer/owner tự khai, dùng chung 1 token. Owner 87728 có thể tự duyệt Job của mình với danh nghĩa "6788" (HTTP 200); ID không tồn tại `000000000001` được chấp nhận; một reviewer review nhiều lần | `test_identity_mode_blocks_reviewer_spoofing`, `test_shared_token_mode_...` FAIL trên mã gốc | `SQZ_IDENTITY_TOKENS="id:token,..."` gắn token với ID → 403 khi mạo danh; cờ `identity_verified`; mỗi reviewer 1 lần (409); `/si/verify` gọi lặp không lỗi 500 |
| F2 | CAO | Không gia hạn lease/heartbeat khi Job dài. Lease 0.2 s → worker thứ hai nhận lại cùng Job, worker đầu bị từ chối khi hoàn tất (attempts=2); heartbeat cũ → `/health/ready` DEGRADED → Docker unhealthy (ngưỡng 30 s < giới hạn OR-Tools 60 s) | `test_long_job_keeps_lease_and_heartbeat` FAIL | luồng keepalive gia hạn lease + heartbeat mỗi min(lease/3, 10 s) |
| F3 | CAO | Audit chain không bao phủ kết quả Job: sửa `result` thành `{"cut":999}` vẫn được phục vụ, `verify_audit` vẫn OK; viết lại toàn chuỗi với digest tính lại vẫn qua (không có khóa HMAC/neo ngoài). Backup 6776 cũng tự tính sha256 nên cùng giới hạn | `test_result_tampering_detected` FAIL | `result_sha256` ghi vào sự kiện `JOB_DONE`; `/jobs/{id}` trả `integrity`; còn lại: HMAC + neo head ra ngoài (§7.3) |
| F4 | TRUNG BÌNH | Payload chỉ kiểm ở worker: cạnh sai, thiếu costs → 202 rồi FAILED; `time_limit="nan"` → DONE; lưới QAOA 0/-5 → DONE với approximation_ratio -1/-0.33; payload 2000×200 nhận 202; không giới hạn body | 7 ca `test_bad_payload_rejected_at_submit` + `test_oversize_body_rejected` FAIL | `sqz/validate.py` kiểm tại submit (422); `SQZ_MAX_BODY_BYTES` mặc định 1 MB (413) |
| F5 | TRUNG BÌNH | `work_order_id` trùng tạo 2 Job; `REVIEW_REQUIRED` chỉ là nhãn | `test_work_order_is_idempotent` FAIL | khóa control `wo:<id>` → gửi lại trả đúng Job cũ |
| L1–L9 | THẤP | version 0.1.0 ở v0.2; công cụ MCP `bell` đánh dấu readOnly nhưng ghi audit; Bell self-test seed cố định 6789; scheduler chạy trùng khi nhiều instance; job/audit tăng vô hạn, `/evidence` chạy `verify_audit` O(N); SQLite đa tiến trình nên `BEGIN IMMEDIATE`; Postgres claim nên `FOR UPDATE SKIP LOCKED`; requirements không ghim phiên bản; uvicorn `0.0.0.0` không TLS, `/backends` công khai; kiểm ID chỉ theo định dạng | — | đã vá: version, readOnlyHint, Dockerfile. Còn lại: §7 |

Kiểm chứng ngược: chạy file test mới trên mã gốc `1701a94` → 14 failed, 2 passed (2 test toán học qua vì phần toán đúng). Như vậy test mới bắt đúng lỗi chứ không phải test rỗng.

---

## 2. Thành tựu lượng tử mới nhất (đến 2026-11-26)

| Đơn vị | Thành tựu | Nguồn |
|---|---|---|
| Google Quantum AI | "Quantum Echoes" (OTOC) trên chip Willow nhanh hơn Frontier ~13.000 lần, công bố trên Nature, dạng lợi thế lượng tử kiểm chứng được; mốc tiếp theo là qubit logic sống lâu | [Google blog](https://blog.google/innovation-and-ai/technology/research/quantum-echoes-willow-verifiable-quantum-advantage/), [Google Research](https://research.google/blog/a-verifiable-quantum-advantage/) |
| Google Quantum AI | Kiểm tra tính ngữ cảnh (contextuality) ở quy mô tới 105 qubit, Science 19/11/2026: 98,3% so với giới hạn cổ điển 88,9% | [Google blog](https://blog.google/innovation-and-ai/models-and-research/quantum-computing/putting-one-of-quantum-mechanics-deepest-features-to-test-at-scale/) |
| IBM Quantum | QDC 2026: Nighthawk r2 >7.500 phép toán trên 120 qubit, 100k mẫu/s (25× Heron); r3 10.000 phép toán 520 qubit; 2027 nối hai chip → 1.040 qubit; Starling 2029: 100 triệu phép toán, 200 qubit logic; workflow SQD nhanh hơn 5× | [IBM QDC 2026](https://ibm.com/quantum/blog/qdc-2026), [Path to Starling](https://ibm.com/quantum/blog/path-to-ibm-quantum-starling) |
| IBM Quantum | SC26: SQD cho cụm Fe4S4 trong phạm vi 4,3 mHa so với DMRG; QRMI (Rust, giao diện tài nguyên trung lập nhà cung cấp); Quantum Advantage Tracker | [IBM SC26](https://ibm.com/quantum/blog/sc26), [IBM dev tools](https://ibm.com/quantum/blog/dev-tools-qdc-2026), [Tracker](https://quantum-advantage-tracker.github.io/) |
| NVIDIA | CUDA-Q mở rộng cho tính toán chịu lỗi (CUDA-Q Logical, 14/9/2026); NVQLink, cudaq-realtime, máy chủ giải mã CUDA-Q QEC 0.9, CUDA-Q Pulse | [NVIDIA press](https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Expands-Open-Source-CUDA-Q-Platform-for-Fault-Tolerant-Quantum-Computing/default.aspx), [CUDA-Q blog](https://nvidia.github.io/cuda-quantum/blogs/blog/category/cuda-q/) |
| Microsoft Azure Quantum | Majorana 2 (2/6/2026): vật liệu nền chì, thời gian sống parity >20 s, mục tiêu 2029; giới khoa học vẫn hoài nghi | [Microsoft](https://quantum.microsoft.com/en-us/insights/blogs/majorana-2-scalable-quantum-processor), [Science](https://www.science.org/content/article/doubling-down-controversial-claims-microsoft-accelerates-quantum-computing-plans), [Reuters](https://www.reuters.com/business/microsoft-give-darpa-hands-on-access-to-quantum-system-new-maryland-site-2026-09-22/) |
| Amazon Braket / AWS | Chip Ocelot (cat qubit, 2/2025); Braket thêm agent + AWS MCP server trong notebook (19/11/2026), giới hạn chi tiêu (spending limit), program sets; TN1 đã ngừng | [Amazon Science](https://www.amazon.science/blog/amazon-announces-ocelot-quantum-chip), [Braket doc history](https://docs.aws.amazon.com/braket/latest/developerguide/doc-history.html), [AWS blog Mitiq](https://aws.amazon.com/blogs/quantum-computing/error-mitigation-on-amazon-braket-with-program-sets-and-mitiq/) |
| D-Wave | Advantage2, bộ giải lai Stride; hướng gate-model dual-rail; Q3/2026: NTT DOCOMO giảm 65% tín hiệu, simulator gate-model beta | [SEC 8-K](https://www.sec.gov/Archives/edgar/data/1907982/000190798226000016/a993annealing-gate.htm), [SEC Q3 2026](https://www.sec.gov/Archives/edgar/data/1907982/000190798226000180/d-wavequantum3q26earning.htm) |
| Mã nguồn mở | Mitiq 1.x API ổn định (ZNE, PEC, DDD, LRE, CDR, REM), 1.1.0 thêm debiasing | [Mitiq changelog](https://mitiq.readthedocs.io/en/stable/changelog.html) |

Lưu ý phản biện: các thuật toán cổ điển liên tục cải thiện và đôi khi rút ngắn khoảng cách "lợi thế lượng tử" (ví dụ [tóm tắt tranh luận](https://contentlora.com/events/quantum-echoes-experiment-2025)). Vì vậy 6789 phải luôn báo kèm baseline cổ điển (§5.1).

## 3–4. Đối chiếu nền tảng và SDK (phiên bản PyPI kiểm tra 2026-11-26)

| SDK | Phiên bản mới nhất | 6789 đang dùng | Khuyến nghị |
|---|---|---|---|
| Cirq (cirq-core) | 1.7.0 | có (backend chính) | giữ; dùng làm backend kiểm chéo |
| Qiskit / Aer / IBM Runtime | 2.6.2 / 0.18.4 / 0.52.1 | Qiskit + Aer | thêm mô hình nhiễu Aer cho bài giảm sai số (§5.3); Runtime chỉ khi Human Governance duyệt |
| PennyLane | 0.45.1 | có | giữ làm backend thứ ba |
| CUDA-Q | 0.17.0 | adapter, skip khi không có GPU | giữ adapter; PR [#256](https://github.com/charityfundplus/CFP.plus/pull/256) của Codex đưa kernel vào API — cần áp cùng validate/identity |
| cuQuantum | — | không | chỉ bật khi có GPU sẵn có; không thuê GPU |
| OR-Tools | 9.15.6755 | CP-SAT cho maxcut/assign_tasks | giữ làm baseline bắt buộc |
| Amazon Braket SDK / D-Wave Ocean | 1.128.2 / 9.5.0 | không | chỉ adapter TẮT; LocalSimulator/ dimod ExactSolver miễn phí có thể dùng để đối chiếu |
| qiskit-addon-sqd | 0.14.1 | không | ứng viên cho bài hóa học (SQD) ở vòng sau |
| FastAPI / MCP / SQLAlchemy | 0.165.0 / 2.3.0 / 2.1.9 | không ghim | ghim bằng lockfile có hash (§7.5) |

Ghi chú: `pip index` báo mitiq 0.25.0 trong khi tài liệu chính thức ghi 1.1.0 — CHƯA XÁC MINH nguyên nhân, cần kiểm tra trước khi thêm phụ thuộc.

---

## 5. Giải pháp lai, tối ưu, giảm sai số, tiết kiệm tài nguyên (đo được)

### 5.1 Quy tắc "baseline cổ điển bắt buộc"
Mọi Job lượng tử (QAOA, Bell, …) trả thêm `classical_baseline` (CP-SAT/brute force) và `approximation_ratio = E_qaoa / OPT`. Tiêu chí PASS: ratio ∈ (0, 1], OPT do OR-Tools chứng minh tối ưu. Bản vá đã chặn lưới ≤ 0 (trước đây cho ratio âm).

### 5.2 QAOA chéo hóa (tiết kiệm ~6× CPU, ~18× so với Cirq)
Pha chi phí của MaxCut là đường chéo: tính `cuts[z]` một lần cho 2^n trạng thái, pha = `exp(+iγ·cuts)`; mixer RX(2β) áp từng trục bằng tensordot. Không dựng mạch trong vòng lặp lưới. Sau khi tìm (γ, β) tốt nhất, chạy lại MỘT lần trên Cirq/Qiskit để kiểm chéo.

Đo trên n=12, 30 cạnh, lưới 32×32, 2 vCPU: 0.49 s vs 3.07 s (numpy lõi) vs 9.11 s (Cirq), cùng E=17.581283 (Cirq 17.581285). Mã tham khảo: phụ lục A. Bước tiếp: thay lưới bằng `scipy.optimize.minimize(method="COBYLA")` khởi tạo từ lưới thô 8×8 → giảm số lần đánh giá ~10×.

### 5.3 Giảm sai số (chỉ mô phỏng)
Thêm kind `zne_demo`: mạch Bell/GHZ + mô hình nhiễu khử cực (Aer `NoiseModel` hoặc `cirq.depolarize`), Mitiq ZNE (Richardson, hệ số gấp 1/3/5) và REM. Chỉ số: `gain = |E_noisy − E_ideal| / |E_mitigated − E_ideal|`. PASS khi gain > 1 với ≥ 95% seed. Không gọi QPU.

### 5.4 Tiết kiệm tài nguyên
- Mặc định backend numpy/Cirq CPU; CUDA-Q/cuQuantum chỉ khi `nvidia-smi` có sẵn.
- Giới hạn qubit theo bộ nhớ: statevector 2^n × 16 byte (n=24 ≈ 256 MB) → giữ trần n ≤ 20 cho API công khai.
- Cache `cuts` theo hash đồ thị; giới hạn kích thước payload (đã vá, 1 MB).

## 6. Vận hành Cloud 24/24 bằng tài nguyên hiện có (đề xuất, CHƯA kích hoạt)

| Lớp | Tài nguyên hiện có | Đề xuất | Chi phí mới |
|---|---|---|---|
| Giám sát tổng hợp | GitHub Actions (repo công khai → runner chuẩn miễn phí) | workflow `schedule` mỗi 6 giờ: chạy test + Bell self-test, đăng digest audit head vào artifact | 0 — cần duyệt vì là tác vụ định kỳ |
| Dịch vụ API | Railway đang chạy cfp-gateway + Postgres | thêm service `sqz` dùng chung Postgres, 1 instance, `SQZ_RUN_WORKER=1` | có thể phát sinh theo gói Railway → cần Human Governance |
| Nhiều instance | Postgres | leader scheduler bằng `pg_try_advisory_lock(6789)` (§7.4) | 0 |
| Sao lưu | `/ops/backup` (6776) + pg_dump | đẩy sha256 snapshot vào Evidence (GitHub) mỗi ngày | 0 |
| QPU | — | giữ lane TẮT; nếu một ngày được duyệt: Braket spending limit + phê duyệt từng Job | không |

## 7. Rà soát bảo mật, PostgreSQL, API, MCP, CMP, DID, Work Order

7.1 API: token theo danh tính (đã vá, tùy chọn bật). Bước tiếp: rate limit theo `owner_id`; `/backends` và `/evidence/*` nên sau token khi chạy ngoài sandbox; chạy sau reverse proxy TLS.

7.2 MCP: công cụ ghi (bell, verify) phải `readOnlyHint=False` (đã vá bell); công cụ MCP nên gọi qua cùng `validate_payload` và cùng danh tính như HTTP.

7.3 Audit/Evidence: thêm `SQZ_AUDIT_HMAC_KEY` → `digest = HMAC(key, prev || payload)`; định kỳ neo `audit_head` (seq, digest) vào Evidence trên GitHub. Khi đó viết lại chuỗi không thể khớp neo ngoài. Test đề xuất: sửa một dòng + tính lại toàn bộ digest không khóa → `verify_audit(anchor=...)` phải FAIL.

7.4 PostgreSQL:
```sql
-- claim an toàn nhiều worker
UPDATE jobs SET status='RUNNING', lease_owner=:w, lease_until=:t, attempts=attempts+1
WHERE id = (SELECT id FROM jobs WHERE status='QUEUED' OR (status='RUNNING' AND lease_until < :now)
            ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1)
RETURNING *;
-- chỉ một scheduler
SELECT pg_try_advisory_lock(6789);
```
Retention: xóa Job self-test > 7 ngày sau khi neo checkpoint audit; `verify_audit` chạy tăng dần từ checkpoint thay vì O(N) mỗi lần gọi `/evidence`.

7.5 Chuỗi cung ứng: `requirements.lock` sinh bằng `pip-compile --generate-hashes`, CI cài `--require-hashes`; Dockerfile chạy user không root (đã có) + HOME hợp lệ (đã vá).

7.6 CMP/DID/Work Order: hiện chưa có DID trong mã. Đề xuất theo lộ trình: (1) registry allowlist ID thật thay vì chỉ kiểm định dạng; (2) mỗi ID có khóa Ed25519, review được ký (`sig` trên `job_id|result_sha256|verdict`), định danh dạng `did:web:cfp.plus:id:6788`; (3) Work Order idempotent (đã vá) và trạng thái `REVIEW_REQUIRED → APPROVED` chỉ chuyển khi có ≥1 review `identity_verified=true` từ ID khác chủ trì.

## 8. Mã nguồn, thuật toán, test, bản vá để Claude Code và Codex triển khai

- Nhánh: `pplx/6789-v0.2.1-review-r1` (dựa trên `1d2c75a`), một commit, 8 tệp, ~400 dòng.
- Tệp mới: `sqz/validate.py`, `tests/test_sqz_v3_independent_review.py` (17 test), báo cáo này.
- Cách áp: `git fetch origin pplx/6789-v0.2.1-review-r1 && git cherry-pick <sha>` rồi `pytest -q`.
- Việc chia cho vòng 2:
  - Claude Code: HMAC + neo audit (§7.3), `classical_baseline` (§5.1), QAOA chéo hóa (§5.2).
  - Codex: áp `validate_payload` + identity cho kind CUDA-Q trong PR #256; `FOR UPDATE SKIP LOCKED` + advisory lock (§7.4); lockfile có hash.
  - Gemini 691141 / ChatGPT 691181 / Team 87783: chạy lại `pytest -q tests/test_sqz_v3_independent_review.py` trên commit mới, báo PASS/FAIL + SHA commit tại HUB 69 #178.

## 9. Ứng dụng cho 1.115 Siêu Bộ Tam và ID 4, 5, 6 số trở lên

- Con số 1.115 Siêu Bộ Tam: CHƯA XÁC MINH trong repo ở vòng này; cần registry chính thức làm nguồn.
- Kiến trúc đề xuất: MỘT lõi dùng chung, không cài riêng cho từng ID. Mỗi Siêu Bộ Tam là một bản ghi cấu hình (3 ID: chủ trì, kiểm chứng, vận hành) giống bộ 6789/6788/6776 hiện có; API `/trio/{id}` đọc từ registry.
- Phân loại ID: lõi đã phân loại 4, 5, 6+ chữ số theo định dạng; cần thêm allowlist từ registry để phân biệt "đúng định dạng" và "tồn tại".
- Tài nguyên: self-test chạy theo backend, không theo ID → chi phí không tăng tuyến tính theo 1.115 bộ; tải thực tế điều tiết bằng hàng đợi + rate limit theo `owner_id`.
- Phân công: `assign_tasks` (CP-SAT) dùng được để chia việc cho các bộ; đo thời gian giải với 1.115 tác vụ × 3 vai trò là việc của vòng 2.

## 10. Kế hoạch kiểm tra chéo nhiều vòng

| Vòng | Ai | Việc | Tiêu chí đo |
|---|---|---|---|
| R1 (xong) | Perplexity | báo cáo này + bản vá + 17 test | 81 passed, 2 skipped; 14/16 test mới FAIL trên mã gốc |
| R2 | Claude Code, Codex | triển khai §8, mở commit mới | CI xanh, không giảm số test |
| R3 | Gemini, ChatGPT, Team 87783 | chạy lại độc lập, báo PASS/FAIL + SHA | ≥ 2 bên PASS cùng SHA |
| R4 | Perplexity | kiểm lại HMAC/neo, đo hiệu năng | test giả mạo chuỗi FAIL đúng kỳ vọng |

---

## Phụ lục A — QAOA chéo hóa (tham khảo)

```python
def fast_qaoa_grid(n, edges, grid):
    cuts = np.array([cut_value([int(c) for c in format(i, f"0{n}b")], edges) for i in range(2**n)], float)
    plus = np.full(2**n, 2**(-n/2), complex); best = (-1, 0, 0)
    for gi in range(grid):
        g = math.pi * gi / grid
        phased = plus * np.exp(1j * g * cuts)          # khớp mạch lõi exp(+iγC)
        for bi in range(grid):
            b = math.pi / 2 * bi / grid; c, s = math.cos(b), -1j * math.sin(b)
            psi = phased.reshape((2,) * n)
            for q in range(n):                          # RX(2β) trên từng qubit
                psi = np.moveaxis(psi, q, 0)
                psi = np.stack([c * psi[0] + s * psi[1], s * psi[0] + c * psi[1]])
                psi = np.moveaxis(psi, 0, q)
            e = float(np.abs(psi.reshape(-1)) ** 2 @ cuts)
            if e > best[0]: best = (e, g, b)
    return best
```
(γ, β) tối ưu có thể khác lõi khi có nhiều điểm hòa do đối xứng; E tối ưu trùng nhau.

CFP+ • Charity Fund Plus • Phục Vụ Vô Vụ Lợi
