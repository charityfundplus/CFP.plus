# CFP+ • Rehearsal host HTTPS • chỉ chuẩn bị

CONDITIONAL APPROVAL • HOLD ACTIVATION • PRODUCTION NO-GO.

Hai profile tại configs/provider-preparation.json: DO12,20 ưu tiên xác minh,
Render12,25 đối chiếu (service7+disk0,25+Spaces5), đều trước thuế/phí. Accountquote,
tax/FX/pending/shared usage vẫn null. provider-preflight.mjs chỉ tạo báo cáo local,
không gọi API/checkout hoặc cho phép activation kể cả fixture đầy đủ.

Human Governance quản lý thanh toán/backup; Codex kỹ thuật dưới CFP+ giám sát.
Phân công vai trò không cấp SSH/API/custody hoặc final permission. Cần quyết định
riêng cho môi trường/host/revision/lease. Không tự Create, thêm thẻ, Apply, đổiDNS,
merge hoặc Production. Không chạy lại6kernel/8ledger/8proxy PASS cũ nếu không đổi.

## Trước được cấp host

Chốt một provider, full SHA được duyệt, UTCexpiry, admin/IP/key/operator/backup
recipient/destination/retention và bảng giá tài khoản đã redact. Giữ nguồn P1/
f3be4842/2814b357/các draft đúng revision, không overlay state hoặc gán source mới
dưới SHA cũ. Quote và control checklist không chứng minh authority; cần HG xác nhận.

## Khi có quyền và host, giữ admission CLOSED

1. Đối chiếu actual plan/region/account/quantity với profile; Node24, source
manifest, private SQLite0700/0600, một writer và server grants. DO cần NIC list và
firewall cả IPv4/IPv6; Render cần actual serviceId/ownerId/name/type/controller
scope. Không dùng cùng metadata/command suspend giữa hai provider.
2. HTTPS đúng public origin/Host/Secure cookie; đóng backend direct; owner-only
lease arm. Đo NIC/kernel/proxy/backup/Spaces/error/ACME/bypass và pending usage,
không coi guest namespace meter là toàn bộ billing. Giới hạn theo accrued quota.
3. Trigger quota/expiry/stale meter/forecast; outer stopCaddy/firewall(DO) hoặc
validated suspend+readback(Render); external observer xác nhận unreachable và
active streams dừng. Fault crash/reboot/disk-full không auto-rearm; giữ admin path.
4. Xác nhận residual compute/disk/storage/backup/workspace/pending fees sau close;
Suspend/poweroff/SpendAlert/buildcap không chứng minh tổng bill hardcap15USD.
Không teardown/xóa backup nếu chưa có quyền riêng và restore receipt.
5. SQLite-consistent backup+sidecar+account receipt→public-recipient encryption→
private off-host upload/download/hash→custodian decrypt→new DB restore; giữ gốc/
audit, NEWGENERATION và old-session denial. Đo RPO/RTO; ≥7valid points, không prune
khi backup lỗi. Không dùng source ZIP làm runtimebackup.
6. Rollback cần previous compatible bundle, quiescent, retained-current backup,
pointer/process-switch/HTTPS readback. Field assessment mới phải được bảo toàn;
old runtime có thể bỏ field khi save nên chưa được chứng minh downgrade. Không
restore in-place hoặc tự downgrade về2814. Lỗi thì CLOSED, giữ state/evidence.

Receipt phải ghi thời điểm/host/revision/configdigest/quote scope, triggers và byte
counts/overshoot, external close observation, residual fees, backuphash/generation/
session revocation và RPO/RTO đo được. Chỉ đọc lại đúng phép kiểm tra bị ảnh hưởng.
Public Review/iPhone và assessor/identity/legal acceptance vẫn có gate riêng.
