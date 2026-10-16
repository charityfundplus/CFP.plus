# Codex → OpenSI • Link Mẫu và thương mại synthetic • 14/10/2026

Source/execution `275c6b11559216404537c752a706e1b2eef1d0b7`; parent `310a6b6f0aa413259363fae935a8b46aa931035e`. Baseline đánh giá `b75b780eb64430355f0b51a4b58b9e5269e0db43` giữ nguyên. Owner thực hiện: Codex local. Review nội bộ có source/readback; OpenSI kiểm toán độc lập chưa ACK. PR124 Draft/unmerged; HOLD ACTIVATION • PRODUCTION NO-GO.

## Đã thực hiện

- Tái sử dụng Link Mẫu Notion đã chỉ định, CoreEngine và 12 Office modules. UI VI trước/EN, chín phân hệ điều hướng; metadata nhóm V/000/135/246/789, chương0–9, ba tầng details. Slot0 là vị trí mở rộng, không cấp ID/DID hoặc suy Parent. Bản nguồn Notion native-unverified, edited2026-10-14T02:47:12.504Z; checksum là enhanced-Markdown snapshot, không native immutable revision/authority.
- Existing Office intake hỗ trợ declaration Software; mọi identity/capability/legal claim vẫn unbound/NOT VERIFIED. Chỉ record mới được gắn subject từ server actor; record lịch sử thiếu owner không được suy gán.
- Hồ sơ doanh nghiệp/HSTDN → product/service → name search → nhu cầu buy/sell/partner/invest → score/reasons deterministic synthetic → opportunity DRAFT/UNDER REVIEW/CLOSED và readback. Không LLM/live SI call, liên hệ thật, thanh toán, hợp đồng thật hoặc công nhận affiliation. Matching giữ matcherVersion, query/inquiry/catalog/target hashes và target snapshot; không nhận score do client nhập.
- Idempotency create + semantic duplicate denial, owner requester profile, private inquiries/opportunities theo subject/workspace/pair, viewer/RBAC/grants và forbidden contact/payment fields. Catalog là thông tin synthetic chia sẻ trong workspace được cấp; không tuyên bố toàn bộ Office có user-private isolation. Enrollment/marketing/work-request cũ vẫn cho tham chiếu profile khác cùng workspace; đó là declared/shared-reference scope, không owner/authority verification và chưa đóng ngoại lệ rộng này.
- Schema3 cho checkpoint có commercial data; predecessor b381 reader thực tế từ chối để tránh mất/lộ dữ liệu qua route cũ. Restore kiểm latest audit→record hash và toàn bộ retained record; missing/tamper/downgraded schema bị chặn. Metadata upgrade/rollback và SQLite backup/reopen/restore giữ dữ liệu. Actual executable process switch, host restore/RPO/RTO/off-host custody chưa thử; rollback phải chọn reader/checkpoint tương thích schema3.
- Existing export chỉ lấy commercial records riêng đã được server lọc, kiểm auditLink/recordHash với final state readback, chặn pair/subject/workspace/build đổi giữa chừng. Giữ training envelope/digest/source flags; không biến export checksum thành authority/execution attestation.

## Evidence và cách chạy

`node tests/commercial-evidence-flow.mjs /tmp/NEW-commercial-receipt.json`

Chạy từ source checkout/Git objects đúng pin275c6b1, Node>=22. Output create-only; nếu thiếu Git/mã drift thì dừng trước khi ghi source PASS. Đây là một trace synthetic mới, không lệnh cohort cũ; không chạy lại khi chỉ cần đọc Evidence đã bàn giao. Không socket/browser và không mở Preview.

COMMERCIAL_E2E_RECEIPT.json: **38 assertions** qua real HTTP handler + SQLite, bao gồm zero/no-match, invalid input, duplicate/idempotency conflict, unauthorized access, viewer, tenant/user/pair isolation, audit linkage, forbidden realcontact/payment. Seed local keys, API responses/statuses, expected/observed, match scores/reasons/source hashes và final state được giữ. Seed keys là UUID record trong fixture, không Registry IDs.

ONBOARDING_AFFECTED_RECEIPT.json: **17 assertions**, new source275c profile/HSTDN →5study ACK→1task mới→feedback→separate synthetic draft review→export. Chạy vì owner stamping/Core/export thay đổi; không relabel receipt17 cũ ở b381 hoặc rerun12exercise cohort. Task mới `57d079ec-df81-4392-87c8-b35637348d88` vẫn NOT ASSESSED.

10 tests mới PASS (3commercial flow +3retention/ownership/software +4export callback VM mocked transport);4 affected regressions PASS (3assessment retention +1task receipt). VM không phải browser. Source26files remote readback chính xác;852untouched blobs giữ nguyên. BUILD_MANIFEST.json có70runtime files, byte digest đúng4d1fd0b6b8ce54854e67a97ba8b9e5e1a0ddac88454051f2eee8e7cf93473be3. Nội bộ CR1–3 đã đóng đúng source scope; không giả ACK/kết luận OpenSI.

## Trạng thái 9 phân hệ

| Phân hệ | Trạng thái | Điều kiện còn thiếu |
|---|---|---|
| Danh tính | PARTIAL: declaration/source lookup | Registry binding/owner/grants thật; không cấp ID |
| Giới thiệu | PARTIAL: nội dung/capability/products/limits tự khai báo | Nguồn và authority xác minh |
| Đăng ký | PARTIAL: existing intake + Software và pending review | CMP live receipt; canonical URL thực tế |
| Đào tạo | PARTIAL: giữ5/12/6, study/task/evidence workflow | Standard v0.2, assessor/prerequisite/roster authority |
| Công việc | PARTIAL: assigned synthetic task/output/review/export | Real SI/AI/team/operator bindings |
| Thương mại | DONE backend/code/local synthetic trace; UI runtime pending | Browser flow và approved host; real operations không được phép |
| Evidence | DONE local source/manifest/export/audit handoff | Independent OpenSI readback/assessment |
| Quản trị | DONE changed local safety; host scope BLOCKED | Actual host/access/custody/executable rollback/cost bound |
| Liên kết | PARTIAL:9anchors/5groups/10chapters/3levels | Actual69/4376/267/CMP readback và per-ID authorized pages |

## BLOCKED rõ ràng

Không approved current HTTPS URL/deployed SHA; Chromium bị EPERM/SIGTRAP nên không ảnh, mobile/browser PASS hoặc Safari iPhone receipt. Test renderer đã chuẩn bị cho môi trường được phép; chưa thực thi thành công. Ba URL Canonical đọc qua web tool không accessible; không suy website down hoặc chức năng hoạt động. Template checksum/14test/38assertions không chứng minh iPhone, identity, hợp tác, năng lực hay tổng chi phí≤15USD.

Source Standard v0.2, authenticated assessor/roster/operator và host/billing/custody giữ ngoại lệ trước. Không paid resource, DNS, real grants, merge, deploy, activation, ID/Parent/DID/Canonical/Audit History rewrite. Mỗi thực thể chỉ được nhân rộng theo Registry binding và quyền thật, không tạo Registry/Core/HUB song song. GitHub comment không tự tạo phiên agent chạy liên tục.
