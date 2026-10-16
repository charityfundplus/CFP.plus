# CFP+ • HUB 69 • Tiếp tục thực hiện • 14/10/2026

HOLD ACTIVATION • PRODUCTION NO-GO.

Approved review runtime remains **b75b780eb64430355f0b51a4b58b9e5269e0db43**.
Evidence Pack/77-file manifest is unchanged. Development source inspected:
690b711316fd1dc41d7bee328609d471f1ddafb9 on Draft PR #124.
This handoff is not an approval to substitute 690b711,42e8bae,f3be or any new head
for the pinned preview. No paid resources or preview were activated.

## 1. Hai thư mục backup — đối chiếu chỉ đọc

| Kho | Parent | Nội dung thấy ngày 14/10 | Quyền metadata |
|---|---|---|---|
| [Encrypted-Backups-HOLD](https://drive.google.com/drive/folders/1FyEKdgVwS8LZwxRJ07cyDXydXqnr5c2q) | My Drive root |3 tệp: encrypted transport drill11649B, receipt646B, readiness10949B |shared=false; một user owner|
| [Restricted Synthetic Backup](https://drive.google.com/drive/folders/15Rg4eNnrJUEc22GTqOnTMmhkIJawvAgS) |Collaboration Workspace1JxTGabFVepUW22TwyyeUEV0ZBCpszr9Z|2 tệp: synthetic backup .fernet95672B, activation-gates.zip7568B|shared=false; một user owner|

Đề xuất thư mục chính thức: **1FyEKdgVwS8LZwxRJ07cyDXydXqnr5c2q**, vì nằm ngoài
cây Collaboration và hiện có bộ receipt/readiness kèm drill. Đây là đề xuất,
chưa phải CFP+ đã chỉ định custodian hoặc thông qua ACL vận hành. Cả hai folder
metadata trả cùng owner; không tự gán trách nhiệm operator/billing/custodian.

Giữ thư mục15Rg4 làm hồ sơ synthetic lịch sử. Không xóa, di chuyển, đổi sharing,
rename hay gộp hai backup. Cập nhật nhận định cũ “thư mục15Rg4 trống”: hiện có 2 file.
Các payload khác định dạng/kích thước; không kết luận byte-identical hoặc chứa
cùng state. Không giải mã và không chạy lại drill đãPASS. Key tạm của transport
drill đã được nguồn báo xóa; không coi file đó là recovery point vận hành có khóa.

Chi tiết file ID/size/parent/role có trong BACKUP_FOLDER_COMPARISON.json. Metadata
hiện không chứng minh quota, retention, key custody, inherited future ACL, WORM,
operator/custodian acceptance hoặc đã restore state/audit preview cũ.

## 2. Chi phí theo cấu hình — giá công khai và phần còn thiếu

Nguồn chính thức live HTTP200 đọc14/10/2026. Không tính credits/khuyến mại.
Đây là các cấu hình đề nghị, không phải inventory/checkout đã tạo.

| Khoản | DigitalOcean | Render + Spaces | Render + Drive hiện có |
|---|---:|---:|---:|
| Host |6.00: Basic Regular bundled s-1vcpu-1gb, 1 vCPU / 1 GiB / 25 GiB SSD|7.00:1 instance 0.5 CPU / 512 MB|7.00|
| Disk ứng dụng |đã trong25GiB SSD|0.25:1 GB persistent disk|0.25|
| Off-host storage |5.00: Standard Spaces subscription|5.00: Standard Spaces subscription|UNKNOWN: quota/plan/free space/phí tăng thêm chưa xác nhận|
| Image backup tuần |1.20: 20% × 6.00|không cộng DO image backup vào Render|không cộng|
| Workspace/HTTPS/certificate |0 thêm: không LB/domain mua thêm; Certbot/NGINX|Hobby 0; onrender.com TLS 0|Hobby 0; TLS 0|
| **Base trước thuế/phí** |**12.20**|**12.25**|**7.25 + backup tăng thêm UNKNOWN**|
| **Thuế tài khoản thực tế** |**MISSING EVIDENCE**|**MISSING EVIDENCE**|**MISSING EVIDENCE**|
| **Tổng sau thuế/phí thực tế** |**MISSING EVIDENCE**|**MISSING EVIDENCE**|**MISSING EVIDENCE**|

Human Governance xác nhận trong phiên này: chưa xác minh tax location của cả hai
tài khoản; chưa có checkout chính thức có VAT/ưu đãi/phí. Không coi UNKNOWN=0,
không chọn tax rate từ vị trí datacenter Singapore.

DigitalOcean công bố VAT10% nếu tax location Vietnam. **Chỉ là scenario**, chưa
áp vào tài khoản CFP+:12.20×1.10=13.42 USD; còn1.58 USD trong mục tiêu15 trước
payment/FX/overage. Nếu có validVATID, DO hướng dẫn thêm vào team để xử lý tax;
không tự xác nhận CFP+ cóVATID/đủ miễn thuế. Singapore9% là scenario khác nếu
đúng billing location. Render chưa xác minh public/account-specific tax rate;
không tự áp VAT10% cho Render chỉ vì đọc tài liệu DO.

Overage: DO Droplet0.01USD/GiB trên transfer pool thực; Spaces0.02USD/GiB storage,
0.01USD/GiB outbound ngoài quota. Droplet transfer pool accrues over runtime và
dùng chung team, không nhận ngay đủ1000 GiB lúc tạo. Spaces base gồm250 GiB / 1 TiB.
Render Hobby5 GB outbound/500 standard build minutes dùng chung workspace;
overage0.15 USD/GB và standard build5USD/1000 phút bổ sung.
Tổng gross=(billable subtotal +overage +backup tăng thêm)*tax thực + payment/FX thực,
theo tax scope trên invoice. Khoản chưa biết vẫnMISSING EVIDENCE. Billing alerts,
pipeline spend limit hoặc app/kernel egress guard không chứng minh hardcap gross15.

### Phí khi dừng — không nhầm dừng app với hết phí

| Thao tác | DO cấu hình12.20 | Render+Spaces cấu hình12.25 |
|---|---|---|
| Dừng nhận bài/tắt app/HTTPS |Droplet/Spaces/backup chưa hủy tiếp tục tính theo quy tắc|service chưasuspend, disk/Spaces và usage trước dừng vẫn có thể tính|
| Power-off Droplet |vẫn bill6USD host; Spaces 5; backup enabled dự trù 1.20. Không ghi 0 USD|không phải thao tác Render|
| Suspend Render đã readback |không phải thao tác DO|compute dự kiến dừng sau suspend; dự trù disk 0.25+Spaces 5=5.25 USD/tháng nếu giữ. Disk billing exact suspended-state cần Billing/support xác nhận|
| Xóa host/service sau duyệt riêng |Droplet compute kết thúc khi destroy; Spaces còn5USD nếu còn bucket. Backup/image/volume/snapshot/reservedIP phải inventory riêng|compute kết thúc khi service deletion confirmed; Spaces còn5USD nếu cònbucket; disk/assets/invoice phải kiểm lại|
| Dừng hẳn mọi khoản |không chỉ tắtmáy: cần separately-approved teardown inventory và hủy Spaces khi destroy tất cảbucket|cần separately-approved service/disk teardown và hủy Spaces nếu chọn phương án này|

Các con số residual là dự trù đủtháng cho tài nguyên được giữ, trước thuế/phí,
không phải invoice cuối. Usage/accrued charges/overage trước dừng không được xóa;
retained image/snapshot/subscription khác chưa biết không bỏ qua. Spaces bill
prorated hourly và kết thúc khi tất cảbucket trong subscription đượcdestroy.
Không thực hiện destroy/cancel/move data trong lượt này.

## 3. Human Governance kiểm tra Billing không Create

1. DigitalOcean: đăng nhập trực tiếp [Billing Settings](https://cloud.digitalocean.com/account/billing/settings).
Đọc tax location/rate, address và VAT status của team hiện hữu; không gửi address
đầy đủ hoặcVATID lên chat. Đọc Billing usage/pending charges và Spaces/backup
subscription inventory. Không clickCreateDroplet/CreateSpace hoặc nhập thẻ.
2. Render: vào [Dashboard](https://dashboard.render.com/)→chọn đúngworkspace→Billing
và Workspace Settings. Đọc plan/inventory/quota used/pending usage; tax/invoice
summary nếu có. Nếu UI chưa hiển thị tax trước tạo, hỏi Billing support để lấy
estimate/pre-create quote; không tạo service chỉ để khám phá mức thuế.
3. Thông tin không nhạy cảm cần ghi vào hồ sơ: provider/team/workspace label,
tax country/rate hoặc explicitUNKNOWN, baseSKU, quota còn lại, requiredextras,
thuế/phí, costwhenstopped và quote time. Có thể dùng screenshot đãredact.
Không yêu cầu sốthẻ, mật khẩu, sessioncookie, APIkey, secret hay VATID đầy đủ.
4. Xác nhận payment/FX với phương thức thanh toán hiện hữu mà không đưa thông tin
nhạy cảm vào hồ sơ. Grossmonthly<=15 phải có evidence, không suy từbase12.20.

## 4. HTTPS DigitalOcean không sửa DNS

Phương án chuẩn bị: HTTPS trực tiếp **IP public của Droplet được duyệt**, chứng
chỉIP công khai Let’sEncrypt, Certbot>=5.4 vớiprofile shortlived, HTTP-01 webroot,
NGINX terminateTLS và backend localhost. Không apex/subdomain CFP+, không
Cloudflare/DNS-01/tunnel. IP chưa cấp; không công bố IP ví dụ làURL đang chạy.

Let’sEncrypt công bốIP certificates GA,160 hours(~6 days). Certbot 5.3 cóipflag;
5.4 hỗ trợwebroot IP. NGINX/Apache installerplugin chưa hỗ trợIP nên dùngcertonly
và loadcertfiles thủ công; deployhook phải validate config và reloadNGINX sau
renew. Stagingcert không trustpublic; không dùng chứng chỉselfsigned để ghi
iPhonePASS. Template HTTPS_DO_IP_NGINX.conf.example chỉ đểreview, chưa áp dụng.

Sau approval: kiểm soátIP/ACME reachability80;443 public review;SSH 22 chỉ admin được
chỉ định. DefaultHost bị từchối, backendkhông public. Exact origin=https://IP thật
cho createReviewSandbox b75; giữHost/Origin/Secure/HttpOnly/SameSiteStrict.
ACME account/TLSprivate key chỉhost secretstorage, tách recoveryprivatekey.
Dailycheck renewaltimer/expiry; ngừngreview trước expiry nếu renewal lỗi.
Quiesce/backend/systemd/watchdog cấu hình sau approval, không autoactivate.

Gate kiểm thử sau kích hoạt được duyệt: issuer chain+IP SAN, revisionheader b75,
POSTlogin/authrole, renewal+reload trênhost, externaliPhone/Safari, certificate
expiry và rollback mới. Không chạy lại toàn bộCore/intake/course/Routing đãPASS.

## 5. Operator/custodian/key custody

Quy trình tại OPERATOR_CUSTODIAN_KEYS_VI.md, tất cảngười/contacts/roster hiện
PENDING OFFICIAL ASSIGNMENT. Folder owner không tự trở thànhcustodian; không
gán syntheticreviewer làmcloudoperator hoặc giữkey.

## 6. Tiếp tục kỹ thuật trong sandbox hiện hữu

Đã thêm sidecar **practice-evidence-review.mjs** cho export thực hành hiện hữu:
kiểmtra taskKey/pair/track/workspace trùng hoặc sai, output digest, checks,
reviewer khácowner, outputsynthetic và deliverable bindings. Genericreflection
không thànhadvanced competency; missingtaskKey lịch sử giữnull; assessor
authority/prerequisites vẫn cầnngười được chỉ định.

Đây là prepare reviewpacket, không thayCore state/grants/curriculum/runtime b75
hoặc oldaudit. Không chạycohort cũ để tạo lại evidence. 3 kiểm thử mới cófixtures
synthetic cho sidecarPASS; không gọiprovider/không mởHTTPpreview.
5 bài / 12 bài / 6 track đã có tiếp tục theo TRAINING_HSTDN_WORKBOOK_VI_EN.md.
HSTDNcaseworksheet mới tại HSTDN_PRACTICE_ADDENDUM_VI_EN.md giúp review nguồn,
Country/Developer/declaredParent và authority; không tự đổiID/Parent/DID/Canonical.

## Nguồn

- https://www.digitalocean.com/pricing/droplets
- https://www.digitalocean.com/pricing/spaces-object-storage
- https://docs.digitalocean.com/products/backups/details/pricing/
- https://docs.digitalocean.com/products/droplets/details/pricing/
- https://docs.digitalocean.com/products/spaces/details/pricing/
- https://docs.digitalocean.com/platform/billing/taxes/vnm/
- https://render.com/pricing
- https://render.com/docs/faq
- https://render.com/terms-update
- https://api-docs.render.com/reference/suspend-service-1
- https://letsencrypt.org/2026/01/15/6day-and-ip-general-availability
- https://letsencrypt.org/2026/03/11/shorter-certs-certbot

HOLD ACTIVATION • PRODUCTION NO-GO. Không xóa backup, không đổiACL/DNS, không
tạo tài nguyêntrảphí/Preview, không merge/deployproduction hoặc auto-adopthead.
