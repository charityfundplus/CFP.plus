## Bàn giao Codex 2 • Chương 0 / Mạng xã hội • 03/11/2026

Codex 2 đảm nhận cả backend và giao diện, tiếp tục source `ca743c30947387435ab1d67a078a07b232e77bac`; tích hợp khung Website từ PR#189 (`488439a856e860037c3f6d8e94f938b7eda652ae`). Không tạo repo, Registry hay database App riêng. Nhánh review: `codex/product-social-20261103`.

**Đường chạy trực tiếp trong cùng sandbox server:** `/website/` (khung Website), `/app/#intake` (ưu tiên Chương0, nhập hồ sơ và giao nhiệm vụ), `/app/#social` (Mạng xã hội, không phải tài liệu điều phối), `/app/#forum` (tiếp nhận/phản hồi/Evidence). Đây là các route nội bộ, **chưa có URL HTTPS Preview/Staging công khai được phê duyệt**. Không dùng `cfp.plus` Production làm Preview mới.

- Hồ sơ thủ công Siêu Bộ Đôi/CMP1–CMP9/chủ đề dùng bảng records hiện hữu. Nhãn CMP là thông tin chờ kiểm chứng; Canonical/Parent/DID luôn null. Sau khi kiểm tra trọn luồng Chương0, các mapping nhập chủ đề Chương1..9 được kiểm tra; chưa tuyên bố có đầy đủ nội dung Canonical cho các chương.
- Luồng đã kiểm thử qua UI/API thật: hồ sơ Chương0 → nhiệm vụ gắn đúng profile_key → tài khoản nhận độc lập ACK/phản hồi → tải Evidence văn bản và đọc lại SHA256/task_key → tải lại vẫn tồn tại.
- Mạng xã hội: đăng nhập → bài đăng → bình luận từ phiên độc lập → tải lại. Cộng Đồng, Chi Hội, Diễn Đàn SI AI, Diễn Đàn Siêu Bộ Đôi có grant riêng; không được tự cấp từ HTTP. Viewer không được ghi; workspace khác không đọc được. Forum cũ cũng áp dụng grant SI AI. Root audit là projection được cấp quyền, backend vẫn kiểm tra full chain. Backup toàn workspace cần admin và đủ4 grant đọc.
- Worker thử nghiệm là tiến trình Python thật, chỉ xử lý `sha256-text`, không shell/network/model/plugin. Nhận nhiệm vụ được giao, ACK bằng tài khoản kỹ thuật, ghi RECEIVED/RUNNING/COMPLETED hoặc FAILED, Evidence, heartbeat và cảnh báo. Tick lại không chạy trùng. Heartbeat mới không phải bằng chứng trực24/7 hay ACK của SI AI bên ngoài. Tất cả trung tâm mạng xã hội ngoài giữ **NOT VERIFIED**.
- Website tái sử dụng PR189, sửa nhãn nhóm theo Master Map thành V/0/135/246/789, giữ nguyên ID số;10chương/100vị trí được ghi rõ là cấu trúc chờ xác minh. Không mượn hồ sơ cha cho ID không tồn tại, không tự gán vị trí thành Canonical.
- HTTPS cục bộ đã kiểm tra CA và hostname, cookie Secure, auth/role, đọc/ghi/sync/restore và Forum. Đây không phải staging được triển khai. `staging-config.mjs` chỉ tạo cấu hình build HTTPS/exact-origin được chỉ định, từ chối Production/loopback và không đổi default. APK default vẫn chưa nối endpoint ngoài được duyệt. Thiết bị thật BLOCKED.

```sh
# từ hub69/ui, build và chạy toàn bộ check hiện hữu + bổ sung
CFP_PRODUCT_EVIDENCE_DIR=/tmp/cfp-product-evidence python3 integration/run-product-checks.py
# từ pilots/spacex, dữ liệu chỉ trong sandbox hiện hữu
python3 operations_server.py --state-dir /workspace/.cfp-env/spacex-operations --port 8765 --provision-demo
# terminal riêng, bật worker kỹ thuật cục bộ có giới hạn rõ ràng
python3 software_worker.py --state-dir /workspace/.cfp-env/spacex-operations --poll-seconds 5 --provision-worker
```

Lỗi UI đã tái hiện và sửa: một lần đọc chậm sau ghi có thể giữ bảng tin trống dù backend đã commit. UI hiện cập nhật từ biên nhận server đã commit và vô hiệu hóa kết quả đọc cũ; test giữ chậm response thật chứng minh FAIL trước/PASS sau, rồi reload xác nhận dữ liệu thực. Không hạ assertion hoặc giả lập dữ liệu PASS.

Mạng sau publish: CFP+/HUB69/GitHub API trả200; Canva Preview được nhận diện đúng “Prototype ứng dụng CFP+”, nhưng script/CDN `static.canva.com` còn bị proxy chặn; edit link yêu cầu đăng nhập. Không sao chép tài sản Canva hoặc xác nhận khớp thiết kế khi chưa render được. PublicHUB69 còn nhãn000 khác Master Map; chỉ ghi nhận, chưa sửa Production.

**Đề xuất cần Human Governance (chưa thực hiện):**1 VM/container Staging riêng trong Cloud project hiện hữu,1 persistent disk để giữ chính SQLite, HTTPS trên hostname staging riêng, tài khoản thử hạn chế; tắt demo/provisioning công khai. Cần phê duyệt project/chi phí, hostname+TLS, quyền tối thiểu quản lý VM/disk/snapshot đúng staging và runtime service account đã chỉ định. Không xin Owner/Editor toàn project, không dùng DB/DNS/IAM Production, không lấy secret trong chat. Cloud connections hiện rỗng; chưa có deployment/host hợp lệ, không tạo URL giả.

Mã, ảnh, log và manifest của lần bàn giao ở `evidence/product-20261103/`. APK là debug review, không phải phát hành hoặc nghiệm thu native kết nối đầy đủ. Owner thực hiện: Codex2; ReviewSI/SecuritySI/Human Governance vẫn phải review trước phát hành. Các receipt cũ bên dưới giữ nguyên phạm vi lịch sử.

---

## App CFP+ • bàn giao tích hợp 02/11/2026

Tiếp tục PWA hiện hữu tại `codex2/p0-pwa-sandbox` (`94261742b76f6550e7bcb9f8fa4d02b76548bcae`) trên backend SpaceX đã có; nhánh bàn giao `codex2/p0-app-integration-20261102`. Đảm nhận cả backend và giao diện theo yêu cầu khi Codex 1 bên ngoài tạm dừng. Không tuyên bố các phiên/đơn vị bên ngoài đã ACK.

**Chạy từ repo hiện hữu:**

```sh
cd hub69/ui
npm ci --cache /workspace/.cfp-env/npm-cache
npm run build
cd ../../pilots/spacex
python3 operations_server.py --state-dir /workspace/.cfp-env/spacex-operations --port 8765 --provision-demo
```

Trên máy chạy server, Website ở `/`, App ở `/app/` cùng origin. Không có staging công khai được xác minh. Cờ demo chỉ tạo tài khoản kỹ thuật thử nghiệm (xem `DEMO_PASSWORD` trong backend), không phải danh tính CFP+ hoặc credential thật. Không mở bản demo ra Internet.

- App dùng lại thiết kế/token, PWA, các màn hình ID/HUB 69/5 Nhóm/10 Chương hiện hữu. Bản Canva được yêu cầu là https://canva.link/urtcevo11xn75tp và https://www.canva.com/d/QK0AJCFDfj-Ofe9; cả hai đang bị proxy CONNECT403. Chưa đối chiếu hoặc sao chép thiết kế/tài sản Canva mới; giao diện hiện tại không được gọi là bản chuyển đổi chính xác từ Canva.
- Registry đọc qua `/api/app/registry` từ **tệp Registry gốc hiện hữu**, kiểm tra Git blob pin trước phản hồi. Không thêm Registry/DB App, không dùng snapshot fallback khi hết phiên/mất mạng, không đổi ID/Parent/DID/Canonical. Tìm ID giữ nguyên số0.
- Giao diện Vận hành dùng cùng session/API/source SQLite với Website qua same-origin view. Ghi từ App đọc được trên Website và ngược lại. Đồng bộ replica vẫn chỉ bao phủ bản ghi vận hành; Forum nằm chung source DB và backup, chưa có cơ chế replica riêng cho Forum.
- Diễn đàn nối API thật: tạo nhiệm vụ cho tài khoản kỹ thuật trong workspace, đúng người tiếp nhận, phản hồi append-only, tải Evidence UTF-8 tối đa32KiB và đọc lại đúng task_key/SHA256. Notifications là nhiệm vụ được giao trong App, **chưa phải push**. Không biến technical ACK thành ACK của một SI AI bên ngoài.
- Backend giữ nguyên xác thực/role/workspace, transaction data+audit, idempotency; thêm bảng Forum trong chính SQLite hiện hữu. Backup/restore sao chép và kiểm chứng cả Forum/Evidence; phục hồi vẫn tạo **bản sao dữ liệu riêng**, chưa khôi phục toàn bộ dịch vụ/auth/outbox hoặc ghi đè nguồn.

**Kiểm thử đã chạy:**105 unit PWA PASS;45 test Python backend/HTTP/Forum PASS; browser thực tế qua Chromium mô phỏng chạm320/390/768/1440px xác nhận Registry API, shared App/Website persistence, offline/reconnect, viewer, logout và nhiệm vụ→người nhận độc lập→ACK→phản hồi→Evidence/readback. Chưa có iPhone Safari/Android vật lý hoặc review bảo mật bên ngoài. Log, ảnh và manifest ở thư mục `evidence/app-20261102/`.

```sh
# từ hub69/ui
npm test
CFP_APP_EVIDENCE_DIR=/tmp/cfp-app-browser python3 integration/app-shared-browser.py
# từ pilots/spacex
python3 -m unittest -v test_pilot test_operations test_operations_http test_app_bridge test_forum
```

**Đóng gói:**Capacitor8.6.0 được pin bằng lockfile và giấy phép MIT được giữ trong THIRD_PARTY_NOTICES.txt/bundle. Đã chạy `cap add android`, `cap add ios`, `cap sync`. Có source Android/iOS cùng appId kỹ thuật đề xuất `plus.cfp.app`, không phải CFP Canonical ID hay đăng ký store. `npm run package:review` tạo gói ZIP chạy thử cục bộ; manifest/checksum của artifact được lưu riêng. APK Android debug đã build thành công; chữ ký v2 được kiểm tra và SHA256 nằm trong receipt Android. Chưa cài/chạy trên thiết bị thật; build binary không phải nghiệm thu native kết nối đầy đủ. iOS build/signing cần Xcode/macOS và quyền ký được phê duyệt. Không nhúng production URL/secret: bản native mặc định có thể mở UI nhưng **chưa nối backend HTTPS được duyệt**. Chưa phải nghiệm thu App native hoàn chỉnh.

Không deploy production, đổi DNS/quyền hệ thống hoặc phát hành store. Cần cấp quyền mạng đã lưu (`canva.link`, `www.canva.com`, `cfp.plus`, `api.github.com`) để tiếp tục đối chiếu Canva/public và tạo PR/comment qua API. Không yêu cầu gửi mật khẩu/token qua chat. Nghiệm thu Production thuộc Human Governance.

---

### Các receipt trước đây (giữ nguyên phạm vi lịch sử)

> **Issue #156 • Shared Design 1.1.0 continuation:** xem [baseline, phạm vi, API seam, blockers và checklist thiết bị](ISSUE156-SHARED-DESIGN.md), [bàn giao theme Google Sites cho Gemini](GOOGLE-SITES-DESIGN-HANDOFF.md) và [bảng URL thực tế](evidence/shared-design/URLS.md). Các receipt cũ bên dưới chỉ chứng minh revision riêng của chúng. HOLD ACTIVATION • PRODUCTION NO-GO.

# HUB 69 • Codex 2 • Giao diện P0

## HSTDN Việt Nam mẫu → Hoa Kỳ → toàn cầu • 19/10/2026

ACK chỉ đạo [PR #157, comment 6276298491](https://github.com/charityfundplus/CFP.plus/pull/157#issuecomment-6276298491).
Nguồn review duy nhất cho gói mới là [hồ sơ Notion hiện hữu](https://app.notion.com/p/3fecaac9a5578132a41fec206bfb0552),
last edit `2026-10-19T20:08:51.750Z`. Tuyên bố VERIFIED trong bàn giao GrokSI
chưa phải kết luận kiểm chứng độc lập. Không sao chép thành hồ sơ Registry.

Tiếp tục chính nhánh `codex2/integration-readiness` / Draft PR #141 trên HEAD
`47be3310421c14e6de413189f2aad0839d18e78b`. Có một presenter dùng chung
Website/App web, dùng nguyên Design Tokens 1.0.0 và component hiện hữu:

- `#hstdn/vn/starlink`: mẫu Việt Nam với thông tin bàn giao về Starlink được
  gắn nguồn và trạng thái theo trường; tên pháp lý/số giấy phép chưa VERIFIED.
- Đổi chủ thể trong select: Starlink, SpaceX, Tesla/Optimus, xAI/Grok, X,
  Neuralink, The Boring Company/Loop. Đây là danh sách chủ đề của nguồn,
  không xác lập các chủ thể có cùng loại, Parent hoặc chủ sở hữu.
- `#hstdn/us/<subject>` và `#hstdn/global/<subject>` tái sử dụng cùng khung;
  đổi thị trường giữ chủ đề đang chọn nhưng không mang tên pháp lý/giấy phép
  Việt Nam sang Hoa Kỳ hoặc quốc gia khác. `global` là ngữ cảnh UI, không là
  Canonical ID hoặc tuyên bố phủ thị trường.
- Mỗi trường có giá trị được bàn giao, nguồn/loại nguồn, ngày nguồn, ngày
  sự kiện nếu có, trích đoạn, nguồn gốc còn thiếu, trạng thái và bước kiểm chứng.
  BLOCKED có thể áp dụng riêng giấy phép/sở hữu trong khi trường tên tham
  chiếu vẫn NOT VERIFIED. Không có verdict VERIFIED cho toàn hồ sơ.
- Nhãn VERIFIED có chú giải nhưng **0 trường được nâng VERIFIED**. URL,
  boolean, nhãn của nguồn hoặc chuỗi receipt tự nhập không tạo thẩm quyền.
  Receipt độc lập/mapping chưa có được để chờ; Codex 2 không thay Claude.
- API HTTP do nguồn đề xuất chỉ là văn bản; không tạo link hoặc gọi endpoint.
  Pháp nhân, thương hiệu, segment, sản phẩm và sở hữu doanh nghiệp tách khỏi
  ID/Parent/DID/Canonical/country ID; toàn bộ binding mới vẫn null.

### Schema đã đọc và điểm nối còn BLOCKED

Đã đọc [bàn giao schema–Registry của Codex 1](https://github.com/charityfundplus/CFP.plus/pull/157#issuecomment-6276360601).
Đây là proposal review, chưa phải contract mới được phê duyệt. Đối chiếu
OpenAPI/API_CONTRACT tại HEAD PR157 mới
`383ffcf5fa3a229d442393a86fa189e52bc09289`: Evidence hiện có
`additionalProperties:false`; không đưa field/date/excerpt/status mới vào
response hiện hành hoặc giả `verifiedAt`. Các enum type giữ nguyên.
Không chạy review/test lại candidate LOW/P3 trong lượt phát triển giao diện này.

| Nguồn tại full SHA | Điều đã kiểm tra | Cách tái sử dụng / phụ thuộc |
|---|---|---|
| UI `47be3310421c14e6de413189f2aad0839d18e78b`, `profile.schema.json` | Projection bắt buộc numeric `id`, `name`, `type`; chưa có field-level evidence contract | Giữ nguyên schema; review notes không được nhập thành Registry record có ID tự tạo |
| Core `06f386b1ba52358779cec6bc26c2d88f6a33664a`, `public/registry-client.js` | Same-origin read client, projection `hstdn:null`; endpoint HSTDN OpenAI riêng | Giữ client/endpoint và fail-closed hiện hữu; chưa nối gói mới vào Core |
| Cùng Core SHA, `docs/p0-20261016/openai-profile.json` | Mẫu `hstdn-reference` giữ ID/Parent/DID/Canonical null, nguồn và blocker riêng | Tái sử dụng nguyên tắc reference-only, không coi file snapshot là generic API schema |
| Notion snapshot nêu trên | Đề xuất trường JSON-like chưa phải contract được phê duyệt | Codex 1 cần xác nhận mapping legal_entity/brand/segment/product và receipt theo trường trước nối API |

`public/hstdn-review.js` là presenter và ghi chú nguồn phục vụ review, không là
hợp đồng API, Registry hoặc nguồn thẩm quyền mới. Tài liệu bàn giao được cập
nhật ngay trong README này và comment ACK hiện hữu, không mở hồ sơ cạnh tranh.
Receipt/log mới: `evidence/HSTDN-REVIEW-20261019.json` và `.tap`; logs lượt P0
trước giữ nguyên. Chạy `node build.mjs`, mở `HUB69-review.html` hoặc dùng cùng
asset trong `dist/` và `core-dist/` sau mount được duyệt.

Phần presenter có thể review offline. **BLOCKED** cho nối API mới (Codex 1
xác nhận contract/mapping), dữ liệu VERIFIED (nguồn gốc + reviewer độc lập),
browser responsive/Safari iPhone thật (browser hỗ trợ + staging riêng tư,
mount, tài khoản thử và device Evidence). Native App binary chưa được build.
Theo Sites workflow, thiếu `$control-browser` phải bỏ qua browser QA, không
dựng một đường điều khiển khác. HOLD ACTIVATION • PRODUCTION NO-GO.

## Website/App P0 • 19/10/2026

### Tiếp nhận Evidence theo trường • candidate chưa publish

#### Xác nhận tiếp nhận và nguồn còn thiếu • 19/10/2026

Đã đọc lại GitHub UI `beb5d432b776f40ef9f5acf16743fc76c97a10a1`, contract/
Registry `383ffcf5fa3a229d442393a86fa189e52bc09289`, cùng [Notion nguồn](https://app.notion.com/p/3fecaac9a5578132a41fec206bfb0552)
(last edit `2026-10-19T20:08:51.750Z`). Receipt hiện hữu có cả nội dung local và
remote; **8/8** file nguồn khớp Git blob và byte local trong phiên kiểm tra.
Điều này không chứng minh một workspace/phiên khác đã nhận file.

Nếu workspace khác trống, đọc các URL GitHub ghim SHA bên trên và file
`hub69/ui/evidence/HSTDN-REVIEW-20261019.json` trước; dữ liệu tiếp nhận ở
`intakeVerification20261019`, ma trận trước ở `fieldComparisonFollowup20261019`.
Không cần tạo hồ sơ/Registry mới hoặc chờ có bản local mới bắt đầu đọc URL.
Phiên hiện tại dùng `/workspace/scratch/dc9ff82e0956/CFP.plus-candidate`;
đường dẫn local này không phải địa chỉ dùng chung cho các phiên khác.

**Phân biệt:** đã đọc bản tóm lược GrokSI và candidate; gói chứng từ gốc với
manifest/URL/trích đoạn từng trường vẫn chưa đầy đủ. PASS chỉ áp dụng phạm vi
ghi trên từng dòng, không tự cấp VERIFIED hoặc đóng authority/binding.

Nguồn bổ sung Bộ KH&CN mô tả giấy phép **tần số**; không thay thế bản giấy phép
viễn thông **57/GP-CVT** đang lệch ngày. SEC Exhibit 2.1 mô tả X.AI Holdings,
chưa đủ cầu nối pháp nhân tới SpaceXAI LLC hiện tại. Điều khoản/báo giá Megapack
riêng theo dự án vẫn thiếu; không lấy menu/hợp đồng Powerwall để điền.
Các URL gốc, phiên bản, trường thiếu và việc tiếp theo đã ghi trong receipt.

Lượt này chỉ cập nhật README/receipt; code/schema/API/Registry/ID/Parent/DID
không đổi. Không chạy lại test không thay đổi và không claim một test PASS mới.
Notion đọc được; chưa thử ghi lại sau lần trước trả 403 insufficient_access.
**HOLD ACTIVATION • PRODUCTION NO-GO.**

Code được kiểm thử: `7752326b66f205b1bf9f31bae1560fccff737b23`, tiếp nối
`7a3061ee5b9f0bac59cb680791ce9ecc69abba86`. Presenter hiện hữu bổ sung phần
**Trường → Nguồn đã đọc → Khớp / Sai lệch / Chưa xác minh → Cách xử lý**.
Kết quả đọc nguồn của Codex khác với VERIFIED độc lập; chưa có receipt Claude.
Giữ riêng ngày bàn giao, ngày công bố/cập nhật nguồn, ngày đọc và ngày sự kiện.
Không có ngày nguồn hoặc trích đoạn thì để thiếu; không dùng ngày đọc thay thế.

Starlink VN giữ cả ngày giấy phép nguồn bàn giao (03/03/2026) và thông báo chính
quyền (13/02/2026); chưa chọn giá trị thay thế trước bản gốc. Pháp nhân Grok,
tên thương mại, bên bán bundle, thuê bao hiện hữu, phí API, Parent pháp lý và
Parent CFP+ có trường/ghi chú riêng. Megapack giữ điều kiện của chú thích đã
đọc, chờ claim/hợp đồng gốc. Trường nguồn không đọc được bị chặn riêng.

Ma trận, URL, ngày và giới hạn xem property
`fieldComparisonFollowup20261019` trong receipt hiện hữu
`evidence/HSTDN-REVIEW-20261019.json`. Lịch sử 73-test/log phía trước giữ nguyên.
Lượt mới chạy **18/18** kiểm thử ảnh hưởng (12 kế thừa + 6 mới), 0 fail/skip;
không chạy lại các suite không đổi. `node build.mjs` PASS, vẫn 26 bản ghi, blob
Registry không đổi. Hai file code/test đã đọc lại remote khớp byte trước bàn giao.
Không có browser/HTTPS/iPhone/native App/CI hoặc kiểm thử API thật trong lượt này.
Schema/API/Registry/binding chưa sửa; mọi trạng thái VERIFIED vẫn bằng 0.

**HOLD ACTIVATION • PRODUCTION NO-GO.** Nhánh Draft hiện hữu; chưa publish.

**ACK cả hai P0** từ [Issue #156](https://github.com/charityfundplus/CFP.plus/issues/156#issuecomment-6271840896)
và [Evidence Inbox hiện hữu](https://app.notion.com/p/3fecaac9a5578117a3a6c3d079f70aff?pvs=204).
Tiếp tục nhánh `codex2/integration-readiness`, Draft PR #141, trên baseline
`8ca11c26fbe3ba76db75ae1aa62b204744233d85`. Đây là prototype để review trên
cùng UI; chưa nghiệm thu staging, Safari hoặc native App. Các mục bàn giao
phía dưới giữ phạm vi lịch sử của từng revision.

Sau `node build.mjs`, mở `HUB69-review.html` trực tiếp bằng trình duyệt, không
cần server, tài khoản, API hoặc mạng để dùng điều hướng nội bộ. Liên kết ngoài
chỉ mở khi người review chọn. Dùng cùng component ở `dist/` và `core-dist/`;
bản Core tiếp tục bắt đầu với `records:[]` và cần mount được duyệt.

| Luồng review | Chức năng | Nguồn / giới hạn |
|---|---|---|
| `#chapters` → `#group/789` → `#chapter/7` → `#hstdn` | Lọc quốc gia Việt Nam / Hoa Kỳ / chưa có phạm vi; mở hồ sơ thương hiệu | Hai hồ sơ được ghi **MINH HỌA**, không phải doanh nghiệp thật; không gán ID/Parent/DID |
| `#brand/sample-vn`, `#brand/sample-us` | Bố cục pháp nhân, thương hiệu, sản phẩm, nguồn, chất lượng, hàng tại quốc gia và giao tại chỗ | Tồn kho, giao hàng, chứng nhận, liên hệ và quyền media đều chờ Evidence |
| `#commerce` → `#brand/amazon` → `https://cfp.plus/8682` | Danh mục sàn tham chiếu; mở trang sàn gốc hoặc cổng TMTC | Amazon được nêu trong [nguồn 8682](https://app.notion.com/p/3decaac9a55781be8616d39de9978bce); quốc gia phục vụ chưa xác minh, bộ lọc VN/US trả rỗng |
| `#chapter/6` → `#technology` | Phân khu Quantum / Space / Future Technologies | 6 nguồn được dẫn từ Evidence Inbox + 2 hướng nghiên cứu được ghi là đề xuất; không suy binding HSTDN/country hoặc tích hợp |

Các slug `vn`, `us`, `sample-vn`, `amazon` là khóa điều hướng UI, **không phải
Canonical ID mới**. Prototype không gửi dữ liệu, tạo giao dịch, gọi API mới,
sao chép Registry hoặc kích hoạt adapter. Các tham chiếu công khai/đề bài vẫn
đọc được khi Core lỗi; bản ghi Core cũ được xóa theo controller hiện hữu.

### Design Tokens 1.0.0 và Google Sites

`public/design-tokens.json` xuất lại đúng 7 biến màu `:root` hiện hữu của
PR #141. Kiểm thử bắt buộc đối chiếu từng giá trị với `public/style.css`.
Không đổi palette hoặc tạo Design System thứ hai.

| Token / quy tắc | Website / App web | Áp dụng thủ công cho Google Sites |
|---|---|---|
| `--paper`, `--ink`, `--green` | Nền, chữ, nút chính hiện hữu | Màu nền section, chữ và theme accent tương ứng |
| `--muted`, `--line`, `--lime`, `--amber` | Chú thích, viền, callout, trạng thái chờ | Màu văn bản phụ, đường chia, nền section/callout theo khả năng trình biên tập |
| Typography | Inter / Segoe UI / Arial / sans-serif; body 15px, line-height 1.6 | Chọn font sans-serif gần nhất được hỗ trợ; ghi rõ sai khác |
| Touch / form | Nút tối thiểu 44px; select 16px; focus-visible | Đối chiếu bản mobile; không giả định chỉnh được CSS hoặc pixel chính xác |
| Catalog | 3 cột lớn, 2 cột ≤1100px, 1 cột ≤700px | Dùng layout section thích ứng sẵn có, kiểm tra preview riêng |

Gemini giữ trách nhiệm đối chiếu Google Sites và cung cấp Preview URL/receipt
của chính mình. Chưa có thao tác Google Sites, publish hoặc thay quyền.

### Kiểm thử và nghiệm thu P0 mới

`node --test tests/*.test.mjs` chạy các test kế thừa và
`tests/website-p0.test.mjs`: deep links, lọc quốc gia, empty state, nguồn tham
chiếu, escaping, trạng thái Core lỗi, tokens, hai bundle và responsive source
guards. Log/receipt của lượt này ở `evidence/WEBSITE-P0-20261019.*` sau bàn giao.

**Responsive source PASS chỉ kiểm các quy tắc CSS**, gồm viewport/safe-area,
1 cột trên mobile, target 44px, form 16px, wrapping và focus/reduced motion.
Chưa đo layout, overflow, contrast hoặc touch thực tế trên browser.
Theo Sites skill, thiếu `$control-browser` trong managed environment phải bỏ
qua browser QA; không dựng preview server hoặc dùng đường điều khiển khác.
File HTML chạy độc lập là đầu ra prototype, không phải ảnh chụp render.

**Safari iPhone / HTTPS staging: BLOCKED.** Chủ môi trường cần bàn giao URL
HTTPS riêng tư hiện hữu được duyệt, mount cùng origin đúng SHA, tài khoản thử
và readback. Checklist thiết bị: Safari thật; 320/375/390/430px và landscape;
text zoom 200%; không tràn ngang; tất cả route/back/reload; bộ lọc quốc gia;
nút/link chạm được; VoiceOver/keyboard; Core 401/403/404/503/logout; anonymous
không đọc được hồ sơ riêng tư. Mỗi receipt cần SHA, URL, thiết bị/iOS/Safari,
thời điểm, ảnh/video và người review. Chưa đánh dấu PASS cho các bước này.

HOLD ACTIVATION • PRODUCTION NO-GO. Chờ review độc lập và Human Governance.

Tiếp tục giao diện HUB 69 hiện hữu từ source `6d2fd6f0c19ebaa0fcbfa53850bcce1b5bf7287f`. Module này đưa mã giao diện về repository CFP.plus để review và tích hợp; không tạo Site, HUB, Registry hay Core API mới. Site review hiện hữu giữ nguyên định danh và quyền truy cập. **HOLD ACTIVATION • PRODUCTION NO-GO.**

## Sử dụng bản review

Tại thư mục `hub69/ui`:

```bash
npm run build
npm test
```

Mở file được build `HUB69-review.html` để tra cứu offline; file chứa toàn bộ CSS/JS/dữ liệu. `dist/` là cùng giao diện dùng khi đóng gói Site. Chưa có URL HTTPS hoạt động. Không chạy server/API, adapter hoặc đồng bộ thật.

## Các chức năng đã triển khai

- Giữ giao diện Tổng quan, Master Hub, tra cứu ID, lưu mục và sao chép link mục.
- Thêm điều hướng đúng 5 nhóm **V • 000 • 135 • 246 • 789** và 10 chương 0–9. Nhóm điều hướng tách khỏi Canonical ID: `0`, `000` và `V` không được thay thế cho nhau.
- Cây **Chương → Con → Cháu** dùng chữ số đầu để phân loại Chương và `parent_id` được ghi trong nguồn để nối các bản ghi. Ví dụ có nguồn: **Chương 6 → OpenAI 69118 → ChatGPT 691181**. Việc đặt nhà phát triển dưới Chương trong giao diện không ghi thêm Parent vào Registry.
- Mỗi ID trong snapshot có hồ sơ riêng. Nhận biết trùng ID, Parent thiếu, vòng lặp, sai chương và quan hệ liên chương; giữ nguyên dữ liệu khi có finding.
- Khung Link Mẫu Chung hỗ trợ Siêu Bộ Đôi, phần mềm, SI, AI, Robot, nhà phát triển, HSTDN, doanh nghiệp, quốc gia, tổ chức và thực thể CFP+.
- Thành phần **Làm Dự Án tại ChatGPT** cho Siêu Bộ Đôi: tên, phạm vi, trạng thái, liên kết có receipt xác minh. Giữ ID của Siêu Bộ Đôi; không cấp ID dự án hoặc tạo URL. Hiện chưa có Siêu Bộ Đôi/project thật trong snapshot; xem cấu trúc tại `#template`.
- `#openai` là góc nhìn của Link Mẫu, tách OpenAI nhà phát triển và ChatGPT sản phẩm/AI. ID HSTDN, SI/Siêu Bộ Đôi liên quan và hợp tác chưa có nguồn được để chờ; không tạo thực thể HSTDN mới.
- `#vaults` trình bày 6 Kho, Evidence, lỗi/dữ liệu còn thiếu và thời điểm đồng bộ. GitHub chỉ là snapshot đọc được; Lượng Tử là RESEARCH; không có claim kết nối hoặc đồng bộ runtime.
- URL CFP+/Google Sites chưa được xác minh hiển thị bằng văn bản, không phát sinh link hoạt động. Link dự án chưa đủ receipt hoặc thuộc private không được xuất.

## Nguồn dữ liệu

Đọc trực tiếp **Registry hiện hữu** `registry/ai-entity-registry.json`, commit `835616308111f6851c0387fa9f5eda60c9ffa624`; build kiểm Git blob `1f18068d66379ce90bb079dc56c77b4c4d66dcdf` trước khi dùng. SHA-256: `a63c5e0b8af157b0938014d51da94ea924b9721acd0a11a9107f5deea3c6f507`.

**26 bản ghi nguồn = 20 nhà phát triển + 6 AI. 0 danh tính hoặc operator được thành phần này tự xác minh.** Không coi đây là Master Registry 91 Siêu Bộ Đôi. Snapshot và các trạng thái Review/Conflict không được nâng thành VERIFIED/ACTIVE. Khi export sang Site, bản sao evidence là đầu vào build đã ghim hash, không phải Registry có quyền ghi.

## Kiểm thử và giới hạn

Mốc lịch sử: 39/39 kiểm thử Node/VM PASS (14 nguồn/baseline, 19 P0 và 6 trạng thái ứng dụng với DOM stub). Bàn giao tích hợp mới được ghi riêng tại `INTEGRATION-READINESS.md`. Có kiểm tra các hash route/link nội bộ, dữ liệu nguồn, ba tầng, dự án/riêng tư, OpenAI và trạng thái kho. Đây không phải browser rendering hay iPhone acceptance.

Browser/CSS rendering, screenshots mới, Safari/WebKit, iPhone thật, HTTPS/quyền truy cập và E2E Core API trên môi trường HTTPS **chưa kiểm thử**. Phiên này không có `$control-browser`; Sites skill yêu cầu bỏ qua browser QA trong trường hợp đó, không khởi chạy một đường điều khiển trình duyệt khác.

Chỉ thêm `hub69/ui/**`; không sửa `/69`, `/id`, Registry, nhánh Codex 1, Core API hoặc Draft PR #124. Tích hợp lên cổng chính và nghiệm thu thiết bị là bước tiếp theo sau khi Codex 1 bàn giao read model/authority và môi trường được phê duyệt.

## Tiếp tục integration-readiness

Nhánh `codex2/integration-readiness` kế thừa PR140 ở `6daec1ca72a65f542392aeb70592a7ed9b5453f6`. Có màn hình đào tạo 5/12/6 từ Codex 1 và bản build `core-dist/` để mount cùng miền với Core hiện hữu. `dist/` và `HUB69-review.html` vẫn là bản snapshot; `core-dist/registry.js` bắt đầu với danh sách rỗng, không dùng snapshot khi Core lỗi. Không chạy Core thứ hai.

Core dùng `/registry-client.js` của Codex 1 ở revision trong `integration/source-pins.json`. Client phải được phục vụ đúng từ Core hiện hữu; mở `core-dist` trên một host tĩnh khác không tự tạo kết nối. Xem `INTEGRATION-READINESS.md` cho contract, giới hạn và Evidence mới.

Kiểm HTTP + trạng thái UI với checkout Codex 1 đúng pin:

```bash
CFP_CODEX1_SOURCE=/absolute/path/to/pinned-CFP.plus node --test integration/core-http.test.mjs
```

Màn hình `#training` và `#lesson/security` có nội dung bài học, 12 bài thực hành có giám sát và 6 hướng nâng cao. Dấu đã đọc chỉ lưu trên trình duyệt, không nộp assessment, không đổi Registry hoặc cấp quyền.

## Mẫu Website Chung • 26/10/2026

Xem [bảng tái sử dụng, sơ đồ, demo, cấu hình và giới hạn](COMMON-TEMPLATE-20261026.md). Mở `HUB69-review.html#template` sau build. Khung 10 mục và Văn Phòng 7 Link con dùng UI hiện hữu; diễn đàn mới ở mức thiết kế, chưa có thread/reply/ACK thật. HOLD ACTIVATION • PRODUCTION NO-GO.
