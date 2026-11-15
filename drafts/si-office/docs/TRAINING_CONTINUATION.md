# HUB 69 • Training continuation • 2026-10-13

Base: `340e4206c1ad676bb8532587cf30821bf48d200f`, Draft PR124.
Coordination: https://cfp.plus/69 • Task Board: https://github.com/charityfundplus/CFP.plus/issues/130
SYNTHETIC SANDBOX • HUMAN REVIEW • PRODUCTION NO-GO.

## Hướng dẫn VI

1. Từ HUB69 mở Link Mẫu Chuẩn và Basic Training. Đọc quy tắc danh tính/lineage, đạo đức/governance, công cụ, bảo mật và bằng chứng.
2. Đầu mối cấp tài khoản sandbox sau khi xác định workspace/pair. Tài khoản demo không chứng minh Registry hoặc thẩm quyền thật. Trong `/p2`, chọn đúng pair; hồ sơ và HSTDN chỉ là nháp nghiên cứu chưa gắn ID chính thức.
3. Ghi nhận từng bài học bằng tài khoản của mình. Chọn một trong 12 bài tập → Chuẩn bị nhiệm vụ → xác nhận dữ liệu giả lập → tạo task → Run supervised.
4. Lưu phản hồi cho đúng task. Reviewer dùng tài khoản riêng đọc output và checks, sau đó chấp nhận hoặc từ chối nháp. Một bài chỉ được chỉ báo hoàn tất khi mẫu bài tập khớp, 18 checks đạt, phản hồi gắn proposalHash và reviewer khác chủ task chấp nhận nháp. Đây là chỉ báo UI, không phải enforcement hoặc chứng nhận năng lực.
5. Lộ trình tính riêng theo người học và pair. Đủ 5 bài học và 12 bài đã review cho phép đề nghị đánh giá nâng cao; sáu chương trình có bước VI/EN và yêu cầu bằng chứng. Chưa có kết quả đánh giá nâng cao hoặc tự nâng quyền.
6. Nhận nhiệm vụ trong scope server đã cấp; task mới có idempotency key. Chọn Export evidence để lưu task/output/checks/review/feedback và audit liên quan. Digest tính trên UTF-8 của chuỗi `payloadJSON` trong gói; không trên JSON đã format lại. Gói không chứa cookie/password và không chứng nhận revision; đối chiếu revision bằng build manifest.
7. Bàn giao qua Task Board130 với revision, digest, kỳ vọng/thực tế và ngoại lệ. Không ghi ACK cho thành viên khác. Danh tính chính thức, quyền thật và quyết định production/bảo mật/pháp lý/dữ liệu thật qua Human Governance.

## English guide

1. Enter through HUB69's Standard Entry and Basic Training links. Read identity/lineage, ethics/governance, tools, security and evidence lessons.
2. Obtain a coordinator-issued sandbox account with workspace/pair grants. Demo accounts do not verify Registry identity or real authority. Select the authorized pair in `/p2`; profile and HSTDN registration remain unbound research drafts.
3. Record your own study observations. Select one of twelve exercises → Prepare task → confirm synthetic data → create → Run supervised.
4. Save feedback for the correct task. A separate reviewer inspects output/checks and accepts or rejects the draft. UI progress requires matching exercise input, eighteen passing checks, feedback tied to proposalHash and a reviewer other than the owner. It is a display indicator, not enforcement or competence certification.
5. Progress is scoped to subject and pair. Five study records and twelve reviewed drafts permit requesting advanced assessment. Six tracks now include VI/EN steps and evidence prerequisites; actual advanced assessments remain pending with no automatic privileges.
6. Receive work within existing server grants. Export task/output/checks/review/feedback and related audit before handoff. Verify SHA-256 over the UTF-8 bytes of the packet's `payloadJSON` string. Export excludes cookies/passwords and does not certify revision; use the build manifest to establish revision.
7. Submit revision, digest, expected/observed outcomes and exceptions through Task Board130. Never acknowledge for another member. Human Governance controls official identity and real production/security/legal/data changes.

## Concurrent teams

Run `node scripts/training-teams.mjs` from `drafts/si-office`.
Three services/databases overlap while their adapters run; each team exercises three existing pair templates through the same Core implementation. Separate synthetic editor/reviewer accounts; foreign service token denial; retained checkpoint after reopen. Temporary fixtures are removed after the rehearsal.

For interactive teams, provision a separate synthetic DB and loopback port per team with the existing provisioning/HTTP tools. Each service keeps its existing single-writer/BUSY contract; serialize commands within that service or retry a BUSY response after the in-flight operation completes. Do not run multiple HTTP processes against one DB. This rehearsal is not multi-process/shared-DB certification or acceptance by any named SI/AI.

## New verification

- `TRAINING_TEAMS_RESULTS.json`: three concurrent services × three pairs; nine reviewed draft tasks; foreign-token denials; checkpoint/reopen matches.
- `TRAINING_CONTINUATION_RESULTS.txt`: existing basic exercise mapping test and five affected Round1 integrations PASS; unchanged full historical suites not rerun.
- `TRAINING_CONTINUATION_BROWSER.json`: eight changed-scope checks PASS in Chromium; UI practice/feedback/separate review, download digest, own-subject progress, foreign workspace, VI/EN390, existing HUB links/ten chapters and no page errors. Local preview only; both servers stopped.
- Fixed digest text overflow at390px; no authentication, permission, DB schema or existing Core changes.

## Operational exceptions and synchronization

| Scope | Actual status | Required next evidence |
|---|---|---|
| GitHub draft source | Updated only after branch write and readback | Exact commit/tree/file hashes |
| Existing Notion review page | Update/readback recorded separately | https://app.notion.com/p/3f8caac9a55781f794dcc175b857057c |
| Website production | Not deployed; draft source only | Human Governance approval and deployment owner |
| Five operational vaults | All disconnected; identities/URLs/scopes not supplied | Per-vault owner, verified URL, allowed scope, receipt/hash/readback |
| Public HTTPS preview | Host/tunnel owner not supplied | Approved Node/SQLite host and access policy |
| Advanced competence | Six guided tracks; assessments pending | Actual trainee evidence and verified assessor decision |
| Real team members | Pending verified roster and acceptance | Identity/lineage/access/receipt per member |
| Audit independence | Local durable chains; not external WORM | Independent custodian/checkpoint |
| Legacy HUB69 EN | Prior prose still partially translated | Remaining source-faithful translation/review |

GitHub/Notion coordination is not five-vault synchronization. Existing Drive P1 evidence is preserved, not replaced. Locked ID, Parent, DID, Canonical, prior audit history and historical manifests are unchanged. No DID/0, production deployment, real adapter/payment/customer data or named member ACK.
