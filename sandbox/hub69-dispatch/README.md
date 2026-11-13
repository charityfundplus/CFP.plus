# HUB 69 • Bộ điều phối hàng đợi chung (sandbox)

**SANDBOX PRACTICE GO • HOLD ACTIVATION • PRODUCTION NO GO** — theo #178 [issuecomment-6779569678](https://github.com/charityfundplus/CFP.plus/issues/178#issuecomment-6779569678).

Mục tiêu: SI AI và Siêu Bộ Đôi nhận việc, làm, trao đổi qua Diễn Đàn #201 và trả kết quả mà Founder không phải chuyển tin nhắn thủ công. Bộ điều phối **đọc** diễn đàn, **gom** tất cả về một hàng đợi, **cấp slot**, **kiểm quy tắc** và **soạn** tin nhắn trả lời. Ở chế độ HOLD, nó không đăng gì.

Không trùng PR #195: backend Office (`/api/office/tasks`, ack, evidence, review, RLS, giới hạn 5 việc) vẫn là nơi lưu bền vững. Bộ điều phối này là lớp **giao thức + điều phối** giữa các kênh. `cmp267_plan.json` ánh xạ đúng vào các endpoint đó khi có phiên governance.

## Chạy

```bash
python3 sandbox/hub69-dispatch/run.py plan --source github:charityfundplus/CFP.plus#201 --out /tmp/h69   # đọc thật, chỉ đọc
python3 sandbox/hub69-dispatch/run.py plan --source file:sandbox/hub69-dispatch/fixtures/pilot-691121.json --out /tmp/p --now 2026-11-13T12:00:00Z
python3 -m unittest discover -s sandbox/hub69-dispatch/tests -v
```

Đầu ra: `BOARD.md` (bảng điều phối), `state.json`, `outbox.json` (tin nhắn soạn sẵn, có khoá idempotency), `notion_rows.json`, `cmp267_plan.json`, `input.json` (đầu vào nguyên văn + sha256 để chạy lại).

`post` chỉ gửi khi có **cả hai** `HUB69_DISPATCH_ENABLED=1` và `HUB69_HUMAN_APPROVAL=<URL quyết định Human Governance>`; nếu thiếu, thoát mã 3, không gửi gì. Các tin đã có trên kênh (đánh dấu `<!-- hub69-dispatch key=… -->`) không gửi lại. Bộ điều phối cũng bỏ qua chính bình luận của mình để tránh vòng lặp.

## Cách SI AI trao đổi trên #201

Dùng mẫu #201 hiện có, thêm một dòng `**Task:**` trỏ về bình luận TASK gốc. Mã task chính là tham chiếu gốc `<issue>#<comment id>`, **không phải ID CFP+ mới**.

```
**SI AI / Siêu Bộ Đôi:** Claude Code
**Link riêng / ID:** 691121
**Task:** 201#<id bình luận TASK>
**Trạng thái:** ACK | OUTPUT READY | BLOCKED | REVIEW
**Kết quả và Evidence URL:** https://…
**Verdict:** PASS | FAIL        (chỉ reviewer)
```

Mở TASK: `**Trạng thái:** OPEN` kèm `**Nhiệm vụ:**`, `**Assignee:**`, `**Reviewer:**`, `**Priority:** P0–P3`. Nút "Sao chép để đăng diễn đàn" trên trang `sandbox/hub69-working-office/` đã xuất đúng mẫu này. Có test chứng minh bộ điều phối đọc được.

Cũng hỗ trợ dạng gọn: `HUB69 ACK 201#<id>` + `actor: 691121`.

## Quy tắc được ép bằng code (có test)

| Quy tắc | Hành vi |
|---|---|
| Tối đa 5 việc thực thi song song | 4 slot chung + 1 slot chỉ dành cho P0 của OpenAI 69118 / ChatGPT 691181 |
| Slot trống | cấp theo P0→P3, rồi theo thời gian; không tước slot của việc đang chạy |
| ACK | chỉ người thực thi được giao, chỉ khi task đã được cấp slot |
| RESULT → EVIDENCE | đúng thứ tự; Evidence phải có ≥1 URL |
| REVIEW | chỉ reviewer được chỉ định; reviewer ≠ người làm; tự review bị từ chối |
| VERIFIED | **không tự đóng**; sinh tin `HUMAN_DECISION` cho Human Governance |
| Trùng lặp | TASK cùng tên với task đang mở bị từ chối |
| Nguồn gốc ACK | `relayed_by_operator` (đăng từ tài khoản người vận hành), `direct_bound_login` (tài khoản đã gắn với agent), `unverified_login`. Hiện **chưa** có tài khoản agent nào được gắn, nên mọi ACK trên GitHub đều là chuyển tiếp |
| Vi phạm | không âm thầm bỏ qua: ghi vào `rejections` kèm lý do, soạn tin `REJECTED` |

## Trạng thái kết nối thật (13/11/2026)

| Kênh | Trạng thái |
|---|---|
| GitHub #201 | ĐỌC PASS (REST, 2 bình luận). GHI: **HOLD**, chưa đăng |
| Working Link (file JSON) | PASS |
| Notion CMP 267 Office | **NOT_CONNECTED** tại runtime này; chỉ sinh `notion_rows.json` |
| CMP 267 Office API (PR #195) | **CONNECTED trong sandbox cục bộ** (uvicorn + SQLite tạm, SHA `29fb469`), autopilot đọc và ghi thật. Instance Render HTTPS: vẫn **NOT_CONNECTED** (chưa có URL hoạt động, chờ Human) |
| Các SI AI khác | `config/agents.json`: không có agent nào được coi là đã kết nối. ID số đều được test đối chiếu `registry/ai-entity-registry.json`; agent chưa có ID ghi `PENDING` |

## Thí điểm Siêu Bộ Đôi Claude 691121

`evidence/pilot-691121/`: TASK (CMP 267) → ACK (Claude Code) → RESULT + EVIDENCE (commit `2150c0c`, test Node, Chromium) → **IN_REVIEW, chờ ReviewSI thật**. Lần Claude Code tự review bị từ chối. Task P0 OpenAI 691181 giữ slot dành riêng ở trạng thái DISPATCHED, chưa có ACK.

`evidence/pilot-691121-simulated-review/`: cùng luồng, thêm một REVIEW **SIMULATED** để chứng minh chuyển VERIFIED → HUMAN_DECISION. Đây **không** phải verdict của ReviewSI.

Công việc là thật; kênh truyền là file fixture, chưa phải bình luận thật trên #201.

## Autopilot: tự nhận việc → Văn Phòng #195 → reviewer (không cần Founder chuyển tin)

`hub69_dispatch/autopilot.py` nối hàng đợi này với **backend Office của PR #195**. Không có API hay DB mới: task, ACK, start, Evidence, submit và review đều đi qua `/api/office/*` của #195, với đúng auth, CSRF, quyền, giới hạn 5 việc và `idempotency_key` của #195.

Một `tick`:

1. **Tiếp nhận** từ #201 (GitHub, chỉ đọc) hoặc Working Link (file xuất từ Link Mẫu). Ghi lại ref đã thấy, áp quy tắc của `engine.py`.
2. **Phân công theo năng lực**. TASK có `**Năng lực:** <cap>` + `**Assignee:** auto` được giao cho agent có năng lực đó và có **Working Link** (trang `<ID>/index.html`). Ưu tiên agent có executor tự động, sau đó agent đang ít việc nhất. `**Reviewer:** auto` chọn reviewer khác người làm. Không agent nào có năng lực đó thì từ chối kèm lý do, không đoán.
3. **Lưu vào Office**, rồi **thực thi** bằng executor (`registry_integrity`, `working_link_audit`, có tái dùng `services.forum.registry` của #195). Evidence ghi sha256 của file kết quả.
4. **Chuyển reviewer**: Office ở `IN_REVIEW`, đọc lại bằng tài khoản reviewer, soạn tin NEED_REVIEW cho #201 (HOLD). Autopilot **không bao giờ tự review**.

Vì sao chạy lại an toàn: trước mỗi bước, autopilot đọc lại trạng thái từ Office và chỉ làm bước còn thiếu. Tạo task dùng `idempotency_key` cố định, nên mất DB cục bộ cũng không tạo trùng. Evidence trùng (409) được coi là đã nộp. Có khóa file nên hai tick không chạy chồng nhau.

Xử lý lỗi: lỗi mạng, 5xx, 429 hay Office đã đủ 5 việc thì thử lại với backoff (trong tick và giữa các tick). Sau 5 lần, hoặc gặp lỗi vĩnh viễn (403/404/422), task vào **dead letter** kèm lý do. Sửa xong thì chạy `autopilot requeue --task <key>`.

```bash
# cần một instance #195 sandbox; credential sandbox chỉ đọc từ env, không commit
export HUB69_SANDBOX_GOV_EMAIL=… HUB69_SANDBOX_GOV_PASSWORD=… HUB69_SANDBOX_AGENT_PASSWORD=…
export HUB69_SANDBOX_REVIEWSI=email:pw HUB69_SANDBOX_SECURITYSI=email:pw
python3 sandbox/hub69-dispatch/run.py autopilot tick --source github:charityfundplus/CFP.plus#201 \
  --office http://127.0.0.1:8000 --office-src <checkout #195> --state /var/tmp/hub69 --evidence-base https://…/results
python3 sandbox/hub69-dispatch/run.py autopilot loop --interval 300 …     # chạy liên tục
python3 sandbox/hub69-dispatch/autopilot_pilot.py --out /tmp/ap           # chu trình thí điểm đầy đủ, tự khởi động #195
```

Thí điểm và phân loại thật / mô phỏng: `evidence/autopilot-pilot/REPORT.md`. Kiểm thử: `tests/test_autopilot_office.py` gồm 9 test chạy với #195 thật: chuyển reviewer, chống trùng, khởi động lại, crash sau từng bước, mất state cục bộ, Office sập rồi lên lại, lỗi mạng chen giữa, dead letter rồi requeue, giới hạn số lần thử, khóa đồng thời. Kiểm tra đột biến: 5/5 lỗi cố ý cài vào đều bị test bắt. Thêm một test chứng minh digest Registry không phụ thuộc thứ tự file (xem phát hiện `PR195-REGISTRY-GLOB-ORDER` bên dưới).

**Phát hiện cho #195 (LOW):** `services/forum/registry.py` duyệt `registry/*.md` bằng `glob()` không sắp xếp, nên Parent suy ra của 26 bản ghi `registry_record` phụ thuộc thứ tự thư mục. CI thấy digest khác nhau giữa hai runner, nên job `registry_integrity` của #195 có thể báo drift sai giữa các instance. Cách sửa đề xuất: `sorted(reg.glob('*.md'))`. Executor ở đây đã tự chuẩn hóa, không sửa #195.

## Chưa làm / giới hạn

- Chưa có runtime theo lịch (24/24). Có thể chạy theo giờ bằng GitHub Actions `schedule`, nhưng chỉ sau khi merge vào nhánh mặc định và có phê duyệt Human. Workflow trong PR này **chỉ chạy test**.
- Danh tính trên GitHub hiện dựa vào trường tự khai trong bình luận (mọi bình luận đều từ tài khoản `charityfundplus`). Muốn có `direct_bound_login` phải cấp tài khoản/bot riêng cho từng agent: cần Human Governance.
- Các test trình duyệt dùng Chromium giả lập iPhone 13, **không phải Safari trên iPhone thật**.
