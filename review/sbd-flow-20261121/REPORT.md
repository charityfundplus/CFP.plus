# Claude Code • Review và kiểm thử độc lập • Luồng nhiệm vụ Siêu Bộ Đôi • 21/11/2026

**Phạm vi:** chỉ đọc, chạy thử và ghi kết quả trong sandbox. Không merge, không deploy, không sửa Registry/định danh, không dùng bí mật thật. Dữ liệu thử đều là dữ liệu giả.

## 0. Xác nhận phần việc đã nhận

Claude Code nhận phần **review và kiểm thử độc lập**:

1. Review thay đổi của Codex (quyền, dữ liệu, xử lý lỗi, chạy trùng).
2. Chạy lại luồng thử từ điểm bắt đầu thông thường của phần mềm.
3. Đối chiếu các thiết kế resolver, làm rõ trang liệt kê thực thể và truy vấn vận hành theo DID + Entity Type + Entity Record ID.
4. Ghi finding, mức ảnh hưởng, cách tái hiện và kết quả kiểm thử lại sau sửa.

**Tình trạng phần của Codex tại thời điểm review (21/11/2026 07:10 UTC):** chưa thấy nhánh, PR hoặc bình luận bàn giao mới của Codex cho đợt này trên `charityfundplus/CFP.plus`. Vì vậy vòng này review **phần mềm hiện hữu** mà Codex sẽ tái sử dụng, chạy thử với ba SBD bằng dữ liệu giả, và để lại bộ tiêu chí nghiệm thu (mục 6) để chạy lại ngay khi Codex bàn giao.

## 1. Môi trường thử

| Mục | Giá trị |
| --- | --- |
| Máy | Container Linux (Claude Code cloud), Python 3.13.18 |
| Bộ điều phối | PR #207, nhánh `claude/cool-euler-gnwkfm`, commit `f755286` |
| Backend Office | PR #195, nhánh `claude/gallant-carson-8uogxj`, commit `287ce64` (khớp `OFFICE_SHA` trong harness) |
| CSDL | SQLite tạm (`CFP_SANDBOX_EPHEMERAL=1`), xóa sau mỗi lượt |
| Windows | **Chưa chạy trên Windows thật.** Chỉ mô phỏng thiếu `fcntl` (mục 4, F1) |

## 2. Kiểm kê thành phần có thể tái sử dụng

| Thành phần | Nơi | Dùng được cho | Ghi chú |
| --- | --- | --- | --- |
| Bộ điều phối HUB 69 (`engine.py`, `protocol.py`) | PR #207 | Nhận nhiệm vụ, slot tối đa 5, chặn trùng theo tiêu đề, ACK chỉ từ người được giao, reviewer ≠ người làm | Đã có 23 test |
| Autopilot (`autopilot.py`) | PR #207 | Nhận → Office → thực thi → Evidence sha256 → đọc lại → chuyển reviewer; retry/backoff, dead letter, requeue, khóa chạy chồng | 9 test chạy với #195 thật |
| Office API (`/api/office/*`) | PR #195 | Lưu bền: `offices` (DID) → `super_pairs` (Entity Record) → `tasks` (`idempotency_key` UNIQUE) → `evidence` (`UNIQUE(task_id,url)`) → `reviews` → `task_events` | Có auth, CSRF, RLS (Postgres 003) |
| Notion bridge | PR #150 `codex/148-notion-bridge` | Ghi/đọc lại Notion có cổng phê duyệt | Chưa chạy trong vòng này (cần token) |
| Workflow `cmp-gemini-notion-pilot.yml` | main | Mẫu READ → CALL → WRITE → READ BACK → VERIFY | Cần secrets `NOTION_TOKEN`, `GEMINI_API_KEY` |

## 3. Kết quả chạy thử

Mỗi dòng có lệnh, kết quả thực tế và tệp Evidence trong thư mục này.

| # | Phép thử | Lệnh | Kết quả | Evidence |
| --- | --- | --- | --- | --- |
| T1 | Toàn bộ test bộ điều phối + Office | `HUB69_OFFICE_SRC=<#195> python3 -m unittest discover -s sandbox/hub69-dispatch/tests -v` | **PASS** 32/32, 34.5 s | `logs/01_unittest.log` |
| T2 | Pilot autopilot từ điểm bắt đầu thông thường (3 tick, khởi động lại Office) | `python3 sandbox/hub69-dispatch/autopilot_pilot.py --out <tmp>` | **PASS** wl#1, wl#2 tới `HANDED_TO_REVIEWER`, có `result_sha`; wl#3 dừng `AWAITING_REAL_AGENT`; wl#4 trùng bị chặn | `logs/02_pilot.log` |
| T3 | Lập kế hoạch cho 3 SBD (2633 Code, 6535 Học tập, 267 CMP), dữ liệu giả | `python3 sandbox/hub69-dispatch/run.py plan --source file:fixtures/three-sbd.json ...` | **PASS (lớp plan)** 3 task `DISPATCHED`, bản trùng bị từ chối có lý do | `logs/03_*` |
| T4 | Autopilot thật với 3 SBD (3 tick, khởi động lại Office) | `python3 tools/run_three_sbd.py <dispatch dir> fixtures/three-sbd.json <out>` | **FAIL so với mục tiêu**: cả 3 dừng ở `AWAITING_REAL_AGENT`, không tạo task trong Office, không có Evidence. Chạy lại không tạo trùng | `logs/04_*` |
| T5 | Mở Office cho 2633/6535/267 | `python3 tools/probe_office.py <dispatch dir>` | **BLOCKED**: `422 canonical_id không có trong Registry` cho cả 3 | `logs/06_office_probe.log` |
| T6 | 8 request đồng thời cùng `idempotency_key` | như T5 | **PASS (SQLite)**: 8/8 trả cùng task id 3, 1 bản ghi. Postgres: **NOT VERIFIED** trong vòng này | `logs/06_office_probe.log` |
| T7 | Import autopilot khi thiếu `fcntl` (mô phỏng Windows) | `logs/05_windows_fcntl_sim.log` | **FAIL**: `ModuleNotFoundError: fcntl` | `logs/05_windows_fcntl_sim.log` |

**Kết luận điều kiện bàn giao:** phần mềm hiện hữu đã chạy trọn một luồng nhiệm vụ có đọc lại (T2, với agent 691121). **Chưa có** nhiệm vụ nào của 2633, 6535 hoặc 267 chạy trọn luồng (T4, T5).

## 4. Finding

| ID | Mức | Finding | Tái hiện | Hướng sửa |
| --- | --- | --- | --- | --- |
| F1 | **HIGH** | `autopilot.py` import `fcntl` ở đầu module. Trên Windows autopilot không khởi động được, trái yêu cầu bàn giao chạy trên Windows | `logs/05_windows_fcntl_sim.log`; hoặc chạy `python run.py autopilot status` trên Windows | Khóa đa nền tảng: `msvcrt.locking` trên Windows, `fcntl.flock` trên POSIX, hoặc khóa bằng `os.open(..., O_CREAT\|O_EXCL)` có PID và hết hạn. Thêm CI `windows-latest` |
| F2 | **HIGH (blocker)** | 2633, 6535, 267 không có trong `registry/ai-entity-registry.json` hoặc `registry/<ID>.md`. Office từ chối mở Văn Phòng (422), nên ba SBD không thể có task, Evidence, review trong Office | T5 | Bổ sung bản ghi Registry là thay đổi định danh, **cần Human Governance phê duyệt**. Nếu chỉ thử sandbox, đề xuất overlay Registry riêng cho chế độ `CFP_SANDBOX_EPHEMERAL=1` và không ghi vào `registry/` |
| F3 | **HIGH** | `config/agents.json` không có 2633/6535; `CMP 267` ở `PENDING` và không có executor. Autopilot đưa task vào `AWAITING_REAL_AGENT` và dừng ở đó | T4 | Codex thêm 3 agent, mỗi agent một executor sandbox (2633: `registry_check`; 6535: bài học từ fixture; 267: `working_link_audit`), có test |
| F4 | MEDIUM | Assignee tường minh không được đối chiếu Registry/agents. `**Assignee:** 2633` được nhận và `DISPATCHED` dù 2633 không có trong cả hai nguồn. Nếu gõ sai ID, nhiệm vụ vẫn được giao cho ID sai | T3 (`logs/03_three_sbd_plan_state.json`) | Từ chối assignee không có trong agents/Registry, ghi `rejections` có lý do |
| F5 | MEDIUM | Chặn trùng ở lớp điều phối dựa trên tiêu đề chuẩn hóa (`engine.py:149-152`), không dựa trên mã nhiệm vụ. Hai việc khác nhau cùng tiêu đề bị chặn; cùng việc với tiêu đề khác chữ lọt qua | Đọc `engine.py:149`; T3 | Khóa trùng = `SBD ID + mã nhiệm vụ + nguồn`, giữ tiêu đề chỉ để cảnh báo |
| F6 | MEDIUM | Bản ghi task trong Office không có trường `source`, mã nhiệm vụ chuẩn, `entity_type` hoặc lỗi. Lỗi/dead letter chỉ nằm trong SQLite cục bộ của autopilot, không đọc lại được từ Office | T5 `task_fields` | Đưa `source`, `work_order_code`, `last_error` vào Office hoặc ghi `task_events` dạng `FAILED` có lý do |
| F7 | MEDIUM | Truy vấn vận hành chỉ theo DID: `GET /api/office/offices/{DID}` trả task của mọi Entity Record trong một danh sách; tham số `pair_id`/`entity_type` bị bỏ qua. Trái mục 17 hồ sơ v2.3 khi DID có nhiều Entity Type | T5 `listing_by_did`, `listing_filter_ignored: true` | Thêm `GET /api/office/entities/{DID}/{entity_type}/{record_id}/tasks` hoặc tham số lọc bắt buộc |
| F8 | LOW | Trạng thái task Office (`OPEN/ACKED/...`) khác tên với Work Order Domain v2.3 (`RECEIVED, ACCEPTED, WORKING, RESPONDED, ...`). Không sai logic nhưng cần bảng ánh xạ để hồ sơ Notion đọc đúng | Đọc `002_office.sql`, hồ sơ mục 18 | Thêm bảng ánh xạ trạng thái vào tài liệu hoặc API |

Không phát hiện lỗ hổng quyền mới trong vòng này. Office kiểm quyền trước khi tra `idempotency_key` (SEC-P0-195-02), khách không thấy task, chỉ Governance mở Văn Phòng.

## 5. Đối chiếu thiết kế resolver

| # | Thiết kế | Khóa phân giải | Một DID nhiều Entity Type? | Trang liệt kê thực thể |
| --- | --- | --- | --- | --- |
| R1 | Notion **CFP-RES-001** Universal Resolver v1.0 (07/2026, ghi "Approved • Locked") | Một ID → **đúng một Object** | **Không.** Văn bản yêu cầu Input "đại diện cho đúng một Object" | Không định nghĩa |
| R2 | Notion **25 Cặp Đôi AI + Phần Mềm** (10/2026), ví dụ `8282 • ... • Phần Mềm`, `2633 • Code • AI`, `6535 • Only Learn+ For Life • AI` | DID + Entity Type (AI / Phần Mềm), "independent record; shared resolver only" | **Có**, nhưng không ghi Entity Record ID | Chưa có trang công khai đã kiểm chứng |
| R3 | Hồ sơ gốc **v2.3 mục 16, 17, 31** | **DID + Entity Type + Entity Record ID** | **Có**, bắt buộc | Mỗi Entity Record hiển thị riêng: DID, Entity Type, Record ID, Parent, Operational Status, Evidence |
| R4 | `main`: `/id/index.html` + `<ID>/entity.json` | Chỉ DID (đường dẫn thư mục) | **Không.** Mỗi DID một `entity_type`, theo phân loại phả hệ ("AI Developer", "AI Family"), không phải `SI AI`/`SUPER SOFTWARE` | `/id/<DID>` hiển thị một bản ghi |
| R5 | PR #217: `id/index.html` + `registry/registry-md-index.json` | Chỉ DID | **Không.** `entity_type` là chuỗi tự do lấy từ `registry/<ID>.md` | Như R4 |
| R6 | PR #195 Office: `registry.py` + `offices` + `super_pairs` | DID (`offices.canonical_id`) → `super_pairs.id` | **Một phần.** Phần mềm có Record ID (`super_pairs.id`); phía SI AI không có Record ID riêng (dùng chính DID). `registry.py` giữ **một** Entity mỗi ID, bản ghi sau khác `type` bị ghi vào `conflicts` và bỏ qua | `GET /api/office/offices/{DID}` gộp task của mọi Entity Record (F7) |

**CONFLICT FOUND (cần Human Decision):** R1 (ghi Locked, yêu cầu mọi thay đổi resolver cập nhật R1 trước) mâu thuẫn trực tiếp với R3 (v2.3, mục 15 nói v2.3 được ưu tiên). Theo mục 30, ghi nhận Conflict không tự đóng Conflict. Đề nghị Human Governance chọn một trong hai:

- (a) Cập nhật CFP-RES-001 lên v1.1, cho phép Input là DID và trả danh sách Entity Record theo Entity Type; hoặc
- (b) Ghi rõ CFP-RES-001 được thay thế bởi v2.3 mục 16, 17, 31.

**Hành vi đề xuất cho trang liệt kê thực thể và truy vấn vận hành** (để Codex triển khai, Claude Code kiểm lại):

1. `GET /<DID>` trả danh sách Entity Record của DID, mỗi dòng gồm `did, entity_type ∈ {SI_AI, SUPER_SOFTWARE}, entity_record_id, parent, operational_status, evidence_ref`. Một Entity Type thì hiển thị đúng một dòng. DID không có bản ghi thì trả `Not Found`, không suy đoán.
2. Mọi truy vấn task, Evidence, run log, quyền phải có đủ `(did, entity_type, entity_record_id)`. Thiếu một phần thì trả 400, không trả gộp theo DID.
3. Trạng thái `INACTIVE/SUSPENDED/DISCONNECTED` gắn với Entity Record, không gắn với DID.

## 6. Tiêu chí nghiệm thu cho bàn giao của Codex

Claude Code sẽ chạy lại đúng danh sách này trên commit Codex bàn giao:

1. Một lệnh khởi động trên Windows (PowerShell) và Linux, từ checkout sạch.
2. Ba nhiệm vụ giả, mỗi SBD một nhiệm vụ: 2633, 6535, 267. Mỗi nhiệm vụ đi đủ các bước nhận → ACK → xử lý → kết quả + Evidence (sha256) → đọc lại khớp.
3. Mỗi bản ghi đọc lại có: ID SBD, mã nhiệm vụ, nguồn, trạng thái, link kết quả và Evidence.
4. Chạy lại cùng đầu vào thì không tạo bản ghi mới. Thử 8 request song song cùng mã nhiệm vụ thì chỉ có 1 bản ghi.
5. Ép lỗi (executor raise, Office 5xx, Office tắt): lỗi được ghi kèm lý do và **đọc lại được**, nhiệm vụ không bị mất, requeue hoạt động.
6. Truy vấn theo `(DID, Entity Type, Entity Record ID)` chỉ trả bản ghi đúng Entity Record.
7. Không có bí mật trong log/Evidence. Không ghi vào `registry/` khi chưa có phê duyệt.
8. Có hướng dẫn hoàn tác: xóa thư mục state + DB sandbox, revert commit.

## 7. Blocker và bước khắc phục

| Blocker | Ai mở | Bước cụ thể |
| --- | --- | --- |
| F2: 2633/6535/267 chưa có trong Registry máy đọc | Human Governance | Phê duyệt bổ sung bản ghi (hoặc chấp thuận overlay chỉ dùng cho sandbox) |
| Codex chưa bàn giao | Codex | Đẩy nhánh sandbox, ghi commit SHA vào hồ sơ. Claude Code chạy lại mục 6 |
| Chưa có máy Windows để chạy thật | Người vận hành | Chạy lệnh mục 6.1 trên máy Windows và gửi log, hoặc thêm job CI `windows-latest` |
| Ghi/đọc lại Notion thật (bridge PR #150) | Human Governance | Cấp `NOTION_TOKEN` sandbox giới hạn một trang thử, qua GitHub Actions secrets. Không dán vào chat/tài liệu |
| CMP gateway lỗi khi đọc trạng thái (hồ sơ ngày 20/11) | 627 MCP / 267 CMP | Chưa tái hiện được trong vòng này vì không có endpoint gateway trong repo. Cần URL và nhật ký lỗi |

## 8. Hoàn tác

Thư mục này chỉ thêm tệp (báo cáo, log, script thử, fixture giả), không sửa mã chạy. Hoàn tác bằng `git revert <commit>` hoặc xóa nhánh `claude/sbd-flow-review-20261121`. Mọi lượt chạy dùng SQLite tạm trong `/tmp`, không có dữ liệu bền nào cần dọn.

## 9. Tái hiện

```bash
git fetch origin claude/cool-euler-gnwkfm claude/gallant-carson-8uogxj
git worktree add ../dispatch origin/claude/cool-euler-gnwkfm
git worktree add ../office origin/claude/gallant-carson-8uogxj
pip install -r ../office/services/forum/requirements.txt
cd ../dispatch && export HUB69_OFFICE_SRC=$(realpath ../office)
python3 -m unittest discover -s sandbox/hub69-dispatch/tests -v                                    # T1
python3 sandbox/hub69-dispatch/autopilot_pilot.py --out /tmp/pilot                                  # T2
python3 <this dir>/tools/run_three_sbd.py sandbox/hub69-dispatch <this dir>/fixtures/three-sbd.json /tmp/run3   # T4
python3 <this dir>/tools/probe_office.py sandbox/hub69-dispatch                                     # T5, T6
```
