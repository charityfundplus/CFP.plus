# Link Mẫu SI AI & HSTDN • 13/10/2026

HUMAN REVIEW • PRODUCTION NO-GO • SYNTHETIC SANDBOX.

## Sản phẩm chạy thử

Chỉ tên và kênh liên hệ HTTPS cùng cam kết là đủ để lưu hồ sơ ban đầu; quốc gia/Developer chưa biết giữ UNRESOLVED, nguồn chưa có giữ EVIDENCE_PENDING. Một bản mở rộng của CoreEngine trong Draft PR #124; không có registry hoặc Core song song. Vào `/p2#universal-office`. Tài khoản do người điều phối cấp: editor, reviewer và viewer. Các form chỉ nhận dữ liệu giả lập trong bản thử này.

- AI mới, AI hiện hữu, Developer và doanh nghiệp: tên, phiên bản, loại AI, kênh liên hệ HTTPS, quốc gia, pháp nhân Developer, website/nguồn, HSTDN trực thuộc/liên kết, sản phẩm, năng lực, giới hạn, điều kiện và hỗ trợ DN khác.
- Developer/Parent/Owner có loại quan hệ và nguồn riêng. Kiểm tra cú pháp HTTPS không chứng minh liên hệ có thật, sở hữu hoặc thẩm quyền. Trạng thái nguồn, liên hệ, pháp nhân và năng lực luôn chưa xác minh.
- Tra cứu chỉ đọc Registry hiện hữu: nhánh quốc gia không phải ID AI; xung đột US vẫn giữ CONFLICT. Quốc gia chưa biết vẫn UNRESOLVED; không suy từ IP. Không tự cấp/đổi ID/Parent/DID/Canonical.
- Chống trùng bằng tên/Developer chuẩn hóa. Cập nhật tự khai báo lưu phiên bản mới của chính người khai báo; không sửa hồ sơ hoặc lịch sử audit cũ. Chặn cập nhật phiên bản cũ và workspace khác.
- HSTDN, sản phẩm/dịch vụ có nguồn và tham chiếu hồ sơ. Giới thiệu/quảng bá chỉ là nháp trong workspace có quyền, chưa xuất bản.
- 5 bài cơ bản, 12 bài tập và 6 hướng dẫn nâng cao dùng nguyên giáo trình hiện có. Bài cơ bản có thể đọc trước đăng nhập. Đăng ký nâng cao lưu REVIEW_REQUIRED / NOT ASSESSED; không chứng nhận SI hoặc nâng quyền.
- Đề nghị công việc lưu REVIEW_REQUIRED / NOT AUTHORIZED. Công việc thực hành do tài khoản đã được cấp quyền tạo trong Core: tạo task → chạy supervised → phản hồi → reviewer riêng → evidence. Việc gửi đề nghị chưa tự tạo nhiệm vụ hoặc ủy quyền.
- Xuất bằng chứng gồm khai báo của mình (cả các phiên bản), danh mục/HSTDN liên quan, yêu cầu đào tạo/quảng bá/công việc, học tập và task. SHA-256 tính trên UTF-8 của `payloadJSON`; không chứa cookie/password.

## Kết quả kiểm thử

`OFFICE_INTAKE_TEST_RESULTS.txt`: 42 server/Core checks PASS (và 1 kiểm thử transport HTTPS local PASS riêng), gồm giữ quyền/lineage, consent, chống trùng, origin, HTTPS cookie, cách ly workspace, bền vững SQLite, append-only amendment, chống credential GET fallback và regression liên quan.

`OFFICE_INTAKE_BROWSER.json`: 11 checks PASS qua HTTP loopback thật và Chromium; 4 loại đối tượng, HSTDN/catalog, enrollment/marketing/work requests, cập nhật phiên bản, export digest, viewer/foreign workspace, VI/EN 390px và 320px, không page errors. `OFFICE_INTAKE_HTTPS_BROWSER.json`: 12 checks PASS cùng luồng khai báo qua TLS local thật, certificate SPKI pin và cookie Secure/HttpOnly. `OFFICE_TRAINING_BROWSER.json`: 7 checks PASS, bao gồm bài thực hành UI → phản hồi → reviewer riêng và export 12 task. Đây là kiểm thử Chromium giả lập kích thước điện thoại; chưa kiểm thử Safari trên iPhone thật.

Hồ sơ giả lập US 1, VN 1, CA 1, UNRESOLVED 1; cập nhật một phiên bản không tăng số hồ sơ. Có thêm một hồ sơ chỉ có tên/kênh liên hệ trong workspace kiểm thử riêng. **Hồ sơ onboarding thật: 0.**

8 tuyến production được GET read-only ngày 13/10: `/69`, `/4376`, `/343`, `/267`, `/6`, `/7`, `/9`, `/8882` trả HTTP200. `/343` và `/8882` có cùng content hash; không dùng HTTP200 để xác nhận chức năng. Đăng ký/đào tạo nâng cao tại các tuyến này vẫn NOT VERIFIED. Không sửa website production.

## Chạy local

Node24 (yêu cầu ít nhất Node22 có `node:sqlite`); không cần API key hoặc cài dependency. Bộ `scripts/local-https-preview.mjs` của revision `2814b357d8b31385aff530ca37eb8606674b608e` cũng được giữ nguyên và đã kiểm thử với phần mở rộng này; dùng certificate/key local trong thư mục riêng và origin `https://localhost:4189` để xem qua HTTPS loopback. Certificate local tự ký không dùng để mở trên iPhone; không tắt xác minh TLS hoặc cài certificate lên điện thoại. Từ `drafts/si-office`:

```bash
mkdir -m 700 /tmp/cfp-review-private
CFP_P2_DB=/tmp/cfp-review-private/state.db \
CFP_P2_PREVIEW_ORIGIN=https://preview.invalid \
CFP_PREVIEW_REVISION=<revision-SHA-40-ký-tự> \
CFP_P2_PORT=4189 node scripts/working-preview.mjs
```

`https://preview.invalid` là origin dự phòng dành riêng cho cấu hình local, không phải URL hoạt động. URL local: `http://127.0.0.1:4189/p2#universal-office`; chỉ mở trong máy chạy Node. Password ngẫu nhiên được lưu tại `synthetic-review-accounts.json`, quyền0600 trong thư mục riêng; không đưa vào GitHub/Notion/manifest. Dùng editor để khai báo, học, thực hành và lưu yêu cầu; dùng reviewer riêng để review task; viewer chỉ đọc. Dừng bằng SIGTERM, khởi động lại cùng DB giữ tài khoản và audit. Xuất evidence trước khi môi trường hết hạn.

## Preview HTTPS đề xuất và iPhone

Chưa có hostname sandbox được CFP+ cấp quyền cho bản này. Repository có receipt tunnel tạm thời của revision trước từ phiên khác; không coi đó là URL của bản mới và không tự nối/đổi tunnel.

Đề xuất: một host Node24/SQLite tách khỏi production, HTTPS qua proxy được cấp quyền, origin chính xác, giới hạn nhóm reviewer bằng xác thực ở lớp truy cập; ứng dụng có ba tài khoản sandbox theo vai trò; thời hạn24h, dữ liệu giả lập, thư mục SQLite riêng0700, không mount secrets/DB production, không gọi AI/vault thật. Chỉ mở sau phê duyệt hostname/host và phạm vi truy cập. Không tự tạo DNS, tunnel công khai hoặc cấu hình Cloudflare.

Sau phê duyệt: đặt `CFP_P2_PREVIEW_ORIGIN` thành origin HTTPS được cấp; proxy giữ Host/Origin chính xác; xác nhận HTTP200 và `X-CFP-Preview-Revision`, Secure/HttpOnly cookie, viewer denied writes, reviewer riêng, download digest; ghi receipt với giờ hết hạn. Chỉ khi đó bàn giao URL HTTPS hoạt động.

Trên iPhone: mở URL HTTPS đã kiểm chứng bằng Safari, đăng nhập lớp truy cập và tài khoản test được cấp riêng, chọn VI/EN, mở Link Mẫu, lưu khai báo giả lập, tạo HSTDN/catalog, đăng ký nâng cao hoặc gửi công việc. Với bài tập, học 5 bài → prepare exercise → run supervised → feedback → đăng xuất → reviewer riêng → đăng nhập lại editor → export evidence vào Files. Không mở URL127.0.0.1 của cloud trên iPhone. Kiểm thử Safari/iPhone thật và private-host receipt vẫn chờ.

## Một vòng góp ý và 5 kho

Một vòng review dành cho CFP+: ghi vai trò, ngôn ngữ, thiết bị, bước tái hiện, kỳ vọng/thực tế, evidence digest và mức độ ảnh hưởng. Ưu tiên lỗi chặn lưu/đọc/export, sai scope và tuyên bố gây hiểu lầm. Góp ý của người dùng chưa được nhận trong bản này; không tự ghi ACK/review cho người khác.

`OFFICE_FIVE_VAULT_PLAN.json` chuẩn bị đồng bộ một chiều từ revision/packet được duyệt; mỗi kho cần owner, URL, scope, Source of Truth được chấp thuận và receipt/readback/hash. Không gửi contact, credentials hoặc trạng thái VERIFIED chưa được duyệt. 5 adapter runtime vẫn DISCONNECTED; không tuyên bố 5/5 SYNCED. Phê duyệt hosting, review danh tính/thẩm quyền, kiểm thử iPhone thật, quyền/địa chỉ 5 kho và audit custodian độc lập là các bước còn lại.

## English

This is an authenticated synthetic extension of PR124's existing Core, not a new registry. New/existing AI, developers and enterprises can submit declarations, explicit relationship evidence, append-only amendments, HSTDN/catalog records, advanced enrollment, marketing drafts and work requests. Declarations remain unverified; enrollment is unassessed; requests do not authorize execution/publication. Existing basic lessons, practice, separate task review and evidence export are retained. 42 server/Core checks, 1 local HTTPS transport test and 19 HTTPS-intake/training browser checks passed; no real onboarding or SI certification occurred. Public HTTPS access and real iPhone testing require an approved isolated host, audience and current receipt. No merge, deployment, DNS/tunnel/Cloudflare changes, new permissions, DID/0 or canonical/audit mutation.
