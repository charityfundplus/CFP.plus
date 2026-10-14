# CFP+ • Bảng quyết định duy nhất • 14/10/2026

**HOLD ACTIVATION • PRODUCTION NO-GO.** Đây là hồ sơ để Human Governance xem xét,
không phải yêu cầu checkout hoặc lệnh kích hoạt. Chỉ báo cáo thay đổi/ngoại lệ mới.

| Quyết định | Phương án đã chuẩn bị | Bằng chứng hiện có | Còn thiếu / trách nhiệm | Kết luận hiện tại |
|---|---|---|---|---|
| Revision đánh giá triển khai |b75b780eb64430355f0b51a4b58b9e5269e0db43|CFP+ giữ mốc này; Evidence Pack ghim|Phê duyệt riêng nếu muốn thay revision sau này|Giữ nguyên; commit phát triển không thay pin|
| Ngân sách mục tiêu |≤15 USD/tháng gồm thuế/phí/phát sinh và phí còn lại khi dừng|Giá công khai và bảng chi phí đã bàn giao99dcdf3|Tax location, thuế/miễn thuế, FX/payment fees, pending usage và quote tài khoản đều chưa có|MISSING EVIDENCE; không checkout|
| DigitalOcean |Basic Regular bundled1 vCPU / 1 GiB / 25 GiB: 6  + Spaces: 5 + weekly backup: 1.20 =12.20 USD trước thuế/phí|Nguồn DO chính thức đã ghim; power-off vẫn tính phí|Billing owner xác minh đúng SKU/quota/kỳ tính phí/gross/retained resources; chưa có người được chỉ định|Phương án so sánh; chưa chọn/mua|
| Render |Hobby, một instance 0.5 CPU / 512 MB: 7  + disk 1 GB: 0.25 + Spaces: 5 =12.25 USD trước thuế/phí|Nguồn Render/Spaces đã ghim|Tax/gross và residual disk/storage thực cần Billing; Drive thay Spaces thì phí tăng thêm/quota vẫnUNKNOWN|Phương án so sánh; chưa chọn/mua|
| Thuế |DO Vietnam VAT 10% chỉ là scenario nếu đúng tài khoản:12.20→13.42USD|DO công bố tax rate; HG xác nhận chưa biết billing location|Không suy tax location từdatacenter Singapore; không áp DO rate choRender|Tổng thực sau thuế/phí vẫnMISSING EVIDENCE|
| Chi phí dừng |DO power-off không hết phí; Render chỉ tắt app không hết phí; storage/backup/accrued usage cần inventory|Bảng residual trong 99dcdf3|Suspend/readback/teardown đều cần scope và approval riêng; chưa chứng minh tổng phí đã dừng|Không tự suspend/destroy/cancel|
| Kiểm soát tiền |Một resource, expiry, theo dõi và close-admission đã có thiết kế|Alerts/pipeline/appmeter không phải hardcap gross 15|Provider-level usage, độtrễ, shutdown authority và kiểm chứng thực còn thiếu|Không bảo đảm hardcap; tiếp tụcHOLD|
| HTTPS DO không DNS |PublicIP cert Let’sEncrypt, Certbot≥5.4 shortlived, NGINX/loopback và renew/reload|Thiết kế có nguồn chính thức; không cần đổiDNS|IP/ACME authority/renewal/hostreadback/iPhone chưa có; không yêu cầu cấp chứng chỉ|DESIGN READY; không kích hoạtPreview|
| HTTPS Render |onrender.com mặc định/exactHost-Origin/Securecookie|Thiết kế trênexportcreateReviewSandbox b75|Chưa chọnservice/hostname hoặc kiểmTLS/renewal/iPhone thực|DESIGN READY; chưa deploy|
| Hai thư mục backup |Giữ1FyEKdgVwS8LZwxRJ07cyDXydXqnr5c2q và15Rg4eNnrJUEc22GTqOnTMmhkIJawvAgS|Metadata/fileinventory đã bàn giao|Theo chỉ đạo hiện tại, chưa thư mục nào được chỉ định chính thức; không đổiACL/quota/custody|Không chuyểnroot, khôngmove/delete|
| Operator |Principle vận hành riêng, quyền đúnghost/expiry/snapshot/transfer|Runbook sẵn; syntheticreviewer không phảioperator|HG chỉ định người/contact/deputy, scope và receipt nhận nhiệm vụ|PENDING OFFICIAL ASSIGNMENT|
| Custodian |Off-host readback/decrypt/isolatedrestore, receipt khôngbí mật|Synthetic backupPASS lịch sử được giữ, không rerun|HG chỉ định người/destination/quota/retention; independentCore restore thực chưa có|PENDING OFFICIAL ASSIGNMENT|
| Khóa vận hành |Recovery private key off-host; chỉpublic key/fingerprint tớioperator; TLS/cloud/appkeys tách|Keyprocedure đã soạn|Keystore/recipientfingerprint/recovery deputy/rotation/breakglass chưa giao|Không tạo/cấp/chuyểnkhóa trong lượt này|
| Năng lực SI/AI–HSTDN |5 bài / 12 bài / 6 track và worksheet; evidence bind realtask/pair/subject|Luồng hiện hữu; bộ đọc export mới kiểmhash/binding|Assessorauthority/prerequisites/realexecutiondeliverables cần nguồn; draftreview không thayassessment|NOT ASSESSED; không cấp quyền|

## Cách Human Governance hoàn thiện dữ liệu mà không checkout

DigitalOcean: Billing→Settings trong tài khoản hiện hữu, đọc tax location/rate/
VATstatus; Billingusage/inventory/quota và invoice/estimate nếu đãcó.
Render: đúngworkspace→Billing/WorkspaceSettings, đọc plan, pendingusage/quota/
tax/invoice. Nếu thuế chưahiện, lấy thông tin từ Billing support sau khi HG tự
thực hiện; không tạo resource để khám phá giá. Không yêu cầu sốthẻ/CVV/password/
APIkey/sessioncookie/fullVATID/địa chỉ đầyđủ. Trong lượt này không liên hệ support.

HG có thể ghi quyết định riêng từngrow cùng authority/time/evidenceURL.
Không coi bảng này là approval, không suy silence=consent và không cấp một
approval bao trùm cả provider/budget/keys/activation/production.
Hiện chưa có ngoại lệ mới đủ bằng chứng để mở activation.

## Thay đổi kỹ thuật miễn phí của lượt này

Bổ sung **training-export-worksheet.mjs** đọc chính định dạng
cfp-training-evidence-v1 từ UI hiện hữu. Xác minh SHA256 payloadJSON bytes,
subject/pair/task/feedback và ánh xạ bài tập theo trườngexercise hiện có; không
nhận chỉ một journey.basicDraftReady tự khai làm bằng chứng. Kiểm đúng template task,
18 checks vàreviewer riêng; tạo worksheet VI/EN/read-only cho5 bài / 12 bài / 6 track và
declaration/HSTDN. Không thayUI/Core/grants/curriculum hoặc runtime b75.

**Ngoại lệ giữ rõ:** export hiện hữu ghi sourceRevision bằng nhãn “SEE BUILD
MANIFEST; EXPORT DOES NOT CERTIFY REVISION”. Hash xác nhận bytes, không tự chứng
minh provenance. Worksheet mới giữ sourceRevisionVerified=false và yêu cầu
Build Manifest readback, không điền revision b75 thay nguồn thực tế.

8/8hash của file addendum 99dcdf3 khớp theo đường dẫnrepo đãnormalize; không đổi
manifest cũ có package-relative docs paths. Chỉ3 test mới choadapter export chạy;
không rerun training/Core/backup/browser/hostingPASS và không dựng cohort mới
để lấp mất evidence lịch sử.

Nguồn ghim: [bàn giao99dcdf3](https://github.com/charityfundplus/CFP.plus/blob/99dcdf3f170a8e65bdc60275b733aad4cc79e498/drafts/si-office/docs/hold-activation-20261014/HOLD_ACTIVATION_HANDOFF_VI.md).
GiữDraftPR124, TaskBoard130, hai backupfolders vàb75/ID/Parent/DID/Canonical/
AuditHistory. Khôngcheckout/pay/resource/DNS/merge/Preview/Production.
