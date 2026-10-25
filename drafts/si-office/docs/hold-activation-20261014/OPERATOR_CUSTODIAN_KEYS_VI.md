# Operator • Custodian • Key custody • Chờ chỉ định

HOLD ACTIVATION. Approved runtime b75b780 remains frozen. This is an operating
procedure to review, not a roster acceptance or permission grant.

| Vai trò | Trách nhiệm | Quyền tối thiểu đề nghị | Hiện trạng |
|---|---|---|---|
| Human Governance/billing owner |tax/quote/gross<=15, chọnprovider và expiry, phê duyệtactivation/teardown|billingread; write/create chỉ sau approval rõ|chưa chỉ định người/liên hệ|
| Operator |revisionhash/hosthealth, snapshot+encrypt+upload/readback, closeadmission/expiry|hostservice scope và đúngbackupfolder; không giữrecoveryprivatekey|PENDING|
| Backup custodian |off-hostdownload/hash, giải mã/restore riêng, kiểm auditprefix/session và kýreceipt|backupfolderread, privatekey trongkeystore riêng|PENDING|
| Key custodian/recovery deputy |publickeyfingerprint/rotation/recovery và breakglass|recoverykey vault; không quyềndeploy mặc nhiên|PENDING|
| Training assessor |evidence/prerequisites/capability decision|scopepair/task đãcấp; khôngcloudadmin|PENDING|

Nếu CFP+ chỉ định một người giữnhiều vai trò, ghi rõ sựkiêmnhiệm và rủi ro thiếu
phân tách trách nhiệm. Không tựđặtcontact/email hay xác nhận ACK.

## Handover trước phiên

1. Governance ghi provider/resource scope, exactfull SHA b75, budgetquote/date,
approvedexpiry và recipients. Operator/custodian xácnhậnđọc bằng chứng qua
Task Board #130; ACKnêu scope/time, không thayphêduyệtkíchhoạt.
2. Custodian tạo recoverykey trênthiếtbị riêng/keystore đãđượcchọn. Chỉpubkey và
fingerprint đi tớioperator; xácnhậnfingerprint qua kênh thứhai đượcchấpnhận.
Không khóaprivate, passwordreceipt, APIkey/cookie lênGitHub/Notion/chat.
3. Phânbiệt khóa: cloudaccess/SSH, TLS/ACME, recoveryprivate, backupdestination
credential và syntheticappaccounts. Không táisửdụng; servicekhôngđượccloudadmin.
Approle viewer/editor/reviewer khônggrantmaintainer chooperator.
4. Chỉ cấp đúngfolder1FyEK... sau designation; không public/linksharing/domainwide,
không owner transfer trong lượt này. Quota/storageplan/inheritedACL phảiđọc thật.
Không tải recoveryprivatekey vàoDrivebackuparchive hoặc Renderdisk.

## Backup — vận hành chờ approval

Quiesce authorizedwrites/maintenancelease→SQLiteconsistent snapshot→integrity/audit
checkpoint→manifestrevision/UTC/sequence/hash→archiveaccountreceiptmode0600→
encrypt bằngpubrecipient đã xácnhận→upload đúngprivatefolder→download vàSHA match.
Custodian offhost decrypt vào thưmục mới, verifysha/compat/auditprefix,
P2Sandbox.restore destination mới, revokeoldsessions, giữNEW GENERATION event;
đăngreceiptnonsensitive. Khôngoverwrite DB gốc hoặc lịch sử.

Backup trước/sauphiên, ít nhất 24h cóthayđổi và trước redeploy/rollback; retention
≥7 verified points+rollbackmốc, giữ nguồn/Evidence Pack ghim. Khôngxóa/prune lúc này.
Đọc checkpoint/audit khônglog passwordreceipt hoặc sessiontoken.
Drill đãPASS giữreceipt; chưa chạyoffhostCore restore mới nếuroles/keys chưa được giao.
RPO/RTO là mục tiêu chođếnkhiđothật, không dùng historicalsyntheticPASS đểcertify.

Nếuquota/auth/keyfingerprint/hash/restorefail: đánh dấubackupFAILED, giữbảncũ,
đóngadmission khi policyyêucầu, báoGovernance/custodian; không tự giảm kiểm tra hoặc
đổirecipient. Envelope hiện hữu có32MiBpayload/48MiBenvelope limit: vượtthìHOLD,
không tựbỏgiớihạn hoặc claimstreaming đãsẵn.

## Khóa và khi dừng

Ghi keyfingerprint/version/time/scope, không key value. Rotation thêmrecipientmới
sauverify, vẫn giữkhóacũ chohistoricalarchives đếnkhi migration/recoveryđượcduyệt.
Breakglass cầnGovernance và designatedcustodian/deputy; localrestore bảnmới,
logreceipt/authority, khôngvượtHumanGovernance.

Kếthoặcincident: closeadmission, finish/captureinflighttasks, backupreadback,
expiry/providerreadback và invoiceinventory. Dừngapp/poweroff khôngđồngnghĩa0USD.
Suspend/teardown chỉ dùng quyền đúng target đãđượcduyệt; khôngautoCreate/resume/destroy.
Thu hồiappreviewaccounts/cloudtokens khiđượcchỉ định; giữencryptedbackup vàkeys
theo retention. Khôngmấtkhóacũ rồi tuyênbốbackup vẫnrestoređược.
