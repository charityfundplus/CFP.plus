# Kho HUB 69 SpaceX • vận hành sandbox hiện hữu

Ưu tiên ứng dụng và vận hành theo Issue #174. Tiếp tục chính pilot này từ nhánh `pilot/spacex-reproducible-20261028`, commit `edb0016243d050b5974ccbad4dba933792518ffc`; không tạo repo hoặc diễn đàn mới. Bản bàn giao: `codex2/p0-spacex-operations-20261102`.

Kho thuộc CFP+, không phải hệ thống chính thức của công ty SpaceX. Thiết kế chính giữ theo [Canva vận hành](https://canva.link/nkzsml955cov73v); [Canva nghiên cứu](https://canva.link/website-nghien-cuu-spacex) là bản tham chiếu. Hai URL chưa truy cập được trong môi trường này do proxy CONNECT 403, nên chưa có đối chiếu trực quan hay xác nhận thay đổi Canva. [HUB 69](https://cfp.plus/69) vẫn là trung tâm điều hướng duy nhất.

## Bản chạy thử hiện tại

Python 3.9+ với SQLite và `hashlib.scrypt`, không thêm dependency runtime. Từ thư mục `pilots/spacex`:

```sh
python3 operations_server.py --state-dir /workspace/.cfp-env/spacex-operations --port 8765 --provision-demo
```

Máy chủ chỉ bind loopback. Giao diện và API chạy cùng origin, không phải URL staging công khai. `--provision-demo` là lựa chọn rõ ràng để tạo các tài khoản giả lập `editor`, `viewer`, `admin` (workspace alpha) và `foreign` (beta); mật khẩu thử nghiệm được định nghĩa bởi `DEMO_PASSWORD` trong `operations.py`, không phải credential thật. Cờ này lặp lại an toàn và không đổi mật khẩu tài khoản đã có. Không chạy cấu hình demo trên dịch vụ được công bố. Trạng thái lưu ngoài checkout tại thư mục chỉ định; process phải khởi động lại sau khi môi trường được phục hồi.

- Giao diện vận hành dùng `/api/session`, `/api/state`, `/api/records`, `/api/sync`, `/api/backup`, `/api/restore`, `/api/logout`, với cookie HttpOnly/SameSite, TTL, role và workspace phía server. API không nhận role/tenant từ client.
- 5 Nhóm `V • 0 • 135 • 246 • 789`, 10 Chương và liên kết số hiện hữu theo `website/WEBSITE_MASTER_MAP_VI.md`. Không dùng `000` thay Group `0`, không cấp ID/Parent/DID/Canonical mới. UUID bản ghi chỉ là mã vận hành cục bộ.
- Ghi nguồn SQLite và outbox trong một transaction cùng audit. Đồng bộ một chiều sang SQLite đích cục bộ; retry idempotent, mất đích vẫn giữ hàng đợi qua restart, xung đột giữ nguyên dữ liệu thay vì ghi đè. Đây chưa phải đồng bộ tới bất kỳ dịch vụ cloud nào.
- Backup chứa dữ liệu và audit của workspace, không sao chép mật khẩu/session. Phục hồi tạo **bản sao dữ liệu riêng có kiểm chứng**, không thay thế kho nguồn hoặc phục hồi toàn bộ dịch vụ/auth/outbox. UI và biên nhận ghi rõ giới hạn này.
- Chuỗi hash audit và checksum phát hiện các thay đổi đã kiểm thử; chưa phải kho audit WORM hoặc bảo vệ trước người đã chiếm quyền máy chủ. Nội dung được render như text, không thực thi HTML người dùng nhập.
- UI kiểm tra heartbeat cục bộ, báo mất kết nối và khóa ghi khi không xác minh được API. Chưa có runtime Siêu Bộ Đôi trực 24/7, cảnh báo ngoài hệ thống hoặc ACK của ReviewSI/SecuritySI. Phân công trên UI là trách nhiệm được yêu cầu, không phải bằng chứng các bên đã nhận việc.
- Importer Registry cũ giữ nguyên whitelist, pin checksum và cấm ghi ngược. Snapshot offline và các nút DEMO cũ vẫn có nhãn riêng; không tính chúng là nghiệp vụ được xác thực.

## Kiểm thử và bằng chứng vận hành

```sh
python3 -m unittest -v test_pilot test_operations test_operations_http
# Browser optional: Python Playwright + /usr/bin/chromium
CFP_SPACEX_EVIDENCE_DIR=/tmp/cfp-spacex-browser python3 check-operations.py
```

Đã chạy: **29 kiểm thử Python PASS** (12 importer cũ, 11 backend, 6 HTTP độc lập) và **9 nhóm kiểm thử vận hành qua Chromium PASS**. Kiểm thử HTTP dùng socket thật và SQLite tạm; kiểm thử mất đích làm đường dẫn SQLite thực sự không mở được, giữ trạng thái qua restart rồi đồng bộ bù. Test phục hồi mở tệp tạo lại và so sánh bản ghi thực tế, không chỉ kiểm tra biên nhận. Kiểm thử trình duyệt ở 320/390/1440px gồm ghi, tải lại, đồng bộ, mất mạng/kết nối lại, phiên độc lập, phân quyền, backup/restore và XSS. Đây là mô phỏng viewport, **chưa chạy iPhone/Safari vật lý**.

Bằng chứng trong thư mục hiện hữu `evidence/`: `operations-tests.txt`, `operations-browser.json`, `operations-mobile.png`, `operations-overview-mobile.png`, `operations-evidence.json` và `operations-url-results.json`. Manifest gắn commit mã được kiểm thử và checksum các bằng chứng.

Lỗi đã tái hiện và sửa trong lần tích hợp: JSON lưu trữ sai cấu trúc ban đầu bị trả HTTP 400 như lỗi input; backend hiện trả 503 `RECORD_INTEGRITY_FAILURE` / `AUDIT_INTEGRITY_FAILURE`, không trả dữ liệu hỏng. Replica hỏng được đánh dấu riêng; nguồn hợp lệ vẫn đọc được. Source state dùng transaction đọc nhất quán; kho đích mất kết nối không ngăn khởi động lại kho nguồn.

**ĐỌC PASS • GHI PASS • ĐỒNG BỘ PASS • PHỤC HỒI BẢN SAO PASS • BẢO VỆ PASS**, chỉ trong các ca sandbox cục bộ nêu trên. Chưa nghiệm thu toàn kho: các kết nối Notion, GitHub sync, Google Drive, Canva, Cloud, Supabase và HubSpot đều BLOCKED vì chưa có binding được cấp quyền và kiểm thử. Đọc/push mã GitHub thành công không chứng minh connector đồng bộ hoạt động. Chưa có staging được xác minh. Network draft đã có `canva.link`, `cfp.plus`, `api.github.com`; cần lưu/apply trong Environment settings để kiểm tra tiếp URL và tạo PR/comment qua API. Không cần gửi token hoặc mật khẩu qua chat.

Không merge/deploy, đổi DNS hoặc quyền hệ thống. Nghiệm thu và Production thuộc Human Governance. Bàn giao qua nhánh repository hiện hữu; không tuyên bố Codex 1 bên ngoài hay ReviewSI/SecuritySI đã ACK.

---

## Lịch sử pilot offline (giữ nguyên phạm vi của các kết quả cũ)

# HUB 69 / SpaceX offline pilot

Independent operational sandbox, no new canonical identity, no SpaceX affiliation.
HOLD ACTIVATION • PRODUCTION NO-GO. Do not deploy or wire this fixture to production.

## Run (Python 3.9+, no Python dependencies)

```sh
cd pilots/spacex
python3 -m unittest -v
python3 pilot.py --enable
python3 -m http.server 8765 --bind 127.0.0.1 --directory ui
```

Open http://127.0.0.1:8765 on the same machine, or open `ui/index.html` directly
where browser policy allows. The checked-in snapshot.js already contains adapter
output, so the static UI works without an API. Search, section navigation, audit
viewer and blocked-writeback UI are interactive. `python3 pilot.py --reverse`
exits nonzero with WRITEBACK_BLOCKED before destination I/O. Import without
`--enable` fails with KILL_SWITCH_OFF.

`registry.json` is a public Registry snapshot from CFP.plus base
835616308111f6851c0387fa9f5eda60c9ffa624, copied without modifying the source.
Only existing ChatGPT 691181 → OpenAI 69118 → 6911 → 911 is verified for the
fixture. This is NOT a SpaceX allocation or feed approval. The import accepts a
single fixed identity and fixed status; additional fields, identity changes,
duplicate IDs and arbitrary text fail validation. It has no network client.
SQLite import and audit share a transaction; duplicate input is idempotent.

## Evidence (2026-10-28 UTC)

- `evidence/tests.txt`: 12 Python tests PASS, including audit-failure rollback,
  source unchanged, validation, duplicate rejection, symlink DB rejection,
  idempotency, kill switch and writeback blocked before I/O.
- `evidence/import.json`: sanitized sample + snapshot and payload digests.
- `evidence/writeback.txt`: actual reverse CLI failure.
- `evidence/ui-tests.json`: Chromium 390×1000 and 1440×1000, 22 assertions each
  (44 PASS): adapter record rendering, overflow, search empty/match, reverse UI
  feedback, page errors, section navigation, six requested surfaces, safe demo text,
  demo ACK/DECLINE, disabled activation and session reset. Screenshots alongside logs.
- JS syntax: `node --check ui/app.js` PASS.
- Browser reproduction: Playwright package + Chromium required; run
  `node check-ui.cjs` with local server on 8765. Script uses /usr/bin/chromium.
  Initial file:// navigation blocked by browser policy; HTTP loopback retest PASS.

## Limits / review requirements

Local fixture proof only. No live API, source IAM proof, secret credential,
production integration, external security review, Safari physical device test,
HTTP verification of external links or factual source verification. Official
URLs are research entry points, not verified claims. Review against Issue #174,
#178, #156 and PR #177. No ACK attributed to any other SI AI.

The Python module is trusted local code, not a hardened multi-user service.
The CLI fixes input/output paths under its directory. A caller using the module
can select another output path and must supply a disposable sandbox; OS-level
permissions enforce isolation. Do not run it with production write permissions.
No concurrent-writer ordering, signed snapshots or live version transitions are
implemented. Rollback for this disposable fixture: stop the static server,
remove sandbox/, rerun the importer. No production or source rollback is needed.

The UI button is illustrative; the Python negative tests prove the implemented
adapter boundary. A compromised host/modified Python program is outside this
proof. No claim of infrastructure-level one-way enforcement is made.

## Follow-up review

Actual files are pilot.py, test_pilot.py, registry.json, ui/index.html and
ui/app.js; no adapter.mjs/server.mjs/test.mjs exists in this PR. The static
server is Python's read-only file server, not a live CFP+/SpaceX API.

The copied registry.json is fixture material, not an authoritative Registry.
Its bytes are pinned to SHA256 in pilot.py; tampered snapshots fail before use.
That pin establishes integrity against the reviewed snapshot, not a signed live
feed or independent source authentication. Import supports schema_version=1
only; missing IDs, unknown versions and extra fields fail before destination I/O.

Directory, discussion, tasks/ACK, evidence and governance surfaces are present.
Discussion and ACK/DECLINE are explicitly DEMO, held only in DOM memory and
cleared by reload. No authenticated forum, durable queue or administrative
operation is implemented. Activation is disabled. All external participation
remains unconfirmed until actual authenticated receipt.

Rechecked original receipts 6481751819 (#174) and 6481756290 (#178): both exist
and were authored by charityfundplus. No separate Codex identity is established.
Status: DRAFT • CHƯA NGHIỆM THU. Physical iPhone Safari and independent
SecuritySI/ReviewSI review remain NOT RUN; Chromium mobile viewport is not Safari.
