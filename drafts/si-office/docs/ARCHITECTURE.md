# Thiết kế kỹ thuật • REVIEW CANDIDATE

## Luồng mẫu

Browser responsive → Node HTTP loopback → role/session demo → validation → in-memory state → audit → export. Không gọi external provider, không fetch Evidence URL ở server, không upload tài liệu, không charge/payment.

Một profile đề xuất có Country Canonical ID, Chapter 6 ID, Developer ID, SI AI identity, HSTDN membership, products/services. SI AI/HSTDN quan hệ nhiều-nhiều dùng liên kết nghiệp vụ; không suy ra Parent Canonical từ quan hệ thành viên. ID, DID, Parent, Canonical là dữ liệu chỉ đọc từ Registry/Governance; registration đề xuất mới giữ null, không DID/0.

## 12 module

01 identity/lineage: registry selection + pending registration.
02 capability: draft record + evidence.
03 products: draft record + evidence.
04 services: draft record + evidence.
05 marketing: draft record + review.
06 CRM: synthetic record only.
07 commerce: draft contract/quote record; payment denied server-side.
08 HSTDN/partners: draft association record, no legal partnership inference.
09 office/tasks: draft → under review → demo reviewed.
10 API/MCP: disconnected connector inventory + denied connect action.
11 governance/security: roles + origin controls + audit.
12 reporting/evidence/KPI: synthetic record counts + export.

Các module 02–08 dùng record chung; chưa có CRM pipeline riêng, catalog pricing, ký hợp đồng hoặc payment sandbox provider. P0 triển khai nền để test/replicate, không tuyên bố hoàn tất sản phẩm.

## Tích hợp mục tiêu

Theo Master Template Google: AI ↔ CMP ↔ Notion / GitHub / Google. CMP envelope phải có Work Order, requester identity, target resource, allowed action, scope, expiry, reviewer, evidence và return location. Token thực không xuất hiện trong browser/export/audit.

| Provider | Mục tiêu | Quyền đề xuất tối thiểu | Điều kiện nghiệm thu |
|---|---|---|---|
| Notion | Office / work / evidence | Chỉ page/data source được chia sẻ | Read → write synthetic record → readback → evidence |
| Google Drive/Docs | Tài liệu | OAuth chỉ file được chọn; Docs edit khi WO cho phép | Viết tài liệu test và readback; không chỉ list folder |
| GitHub | Draft source / PR | Chỉ repository CFP.plus, branch draft | Diff chỉ drafts, draft=true, không merge |
| Website | Read nguồn / route | Chỉ read trong phạm vi này | Route + identity + source được kiểm tra riêng |
| MCP Gateway | Tool routing | Allowlist tool/resource, token TTL | Deny unauthorized call; synthetic authorized result + trace |
| 5 kho CFP+ | Existing inventory | Chưa biết URL/owner/scopes | Human xác nhận từng kho; không tạo kho mới |

Không ghi Connected khi chỉ truy cập được danh mục. Live integration vẫn MISSING EVIDENCE.

## Workflow xác minh mục tiêu

PROPOSED → IDENTITY VERIFIED → ACCESS VERIFIED → ACCEPTED → IN PROGRESS → EVIDENCE REVIEWED. Mỗi bước cần evidence theo claim và reviewer thực. Link HTTPS được nhập chỉ là đầu vào, không tự chứng minh domain ownership hay source validity. Mẫu hiện mô phỏng review record, không tự chuyển những bước xác minh thật này.

## Bảo mật và giới hạn

Server từ chối editor review, viewer write, unauthorized sessions, cross-origin mutations, payload >8KB, unexpected identity fields, non-HTTPS references. Static assets dùng allowlist và CSP. UI render textContent để chống HTML injection. Sessions sống 1 giờ, chỉ bộ nhớ; endpoint session cho phép tự chọn role vì đây là demo loopback. Không được expose công khai.

Hash audit kiểm tra liên kết, không chứng minh bất biến: cùng process có thể thay toàn bộ chuỗi, restart xóa lịch sử. Production cần append-only/WORM store + signed checkpoints ngoài process, tenant separation, encryption, retention, GDPR/local privacy assessment, rate limits, payload/domain review và durable audit kể cả denied requests.

## Registry constraints

Snapshot từ commit 835616308111f6851c0387fa9f5eda60c9ffa624, không sửa file gốc. Mapping US trong HUB69.md khác entity registry; chặn đăng ký nhánh 6911. Việt Nam có route 6984 nhưng snapshot entity không có developer VN, nên không tự tạo developer. Country index coverage chưa toàn cầu đầy đủ. Số 0 giữ dạng string. Không dùng khoảng trống làm allocation authority.

## P1 readiness extension

VI/EN selector, bilingual module contracts (function/input/output/access/verification), 4 participant guides and typed profile/proposal/HSTDN/catalog drafts are implemented. Country/Developer proposals use local UUID reference keys, never Canonical Parent; SI registration uses existing Registry Country/Developer only. A proposed developer is not automatically admitted as a verified SI parent. HSTDN members reference SI draft keys; products/services may reference an SI draft office and HSTDN with membership validation. Missing links stay null. Legal-parent claims remain NOT VERIFIED.

Ten provider-independent mock adapters use one versioned result contract; default is read-synthetic only. They deny write, unknown provider and credential fields. Five vault names are placeholders for existing vaults, not newly created storage. externalRequests=0, connected=false; no live READ/WRITE/sync/reverse-write/cascade-delete. Runtime architecture has no provider SDK dependency.

Early Host, Origin, content-type, payload and unauthorized-session denials now generate redacted audit events. Prior demo audit history is not deleted within a process. Restart persistence is still absent; generated evidence preserves previous test reports separately. D 500 exact authoritative rule remains MISSING EVIDENCE; V/D source describes history but does not authorize creating DID/0 here.

Current tests run the actual HTTP handler in process without sockets; socket transport and current browser UI require a permitted local environment. Initial browser screenshots/evidence are retained as baseline, not proof of current VI/EN behavior.
