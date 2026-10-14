# CFP+ • Rehearsal / tài khoản / rollback • 14/10/2026

**PLAN READY • HOST EXECUTION BLOCKED • HOLD ACTIVATION • PRODUCTION NO-GO.**
Baseline `b75b780eb64430355f0b51a4b58b9e5269e0db43` giữ nguyên. Source phát
triển của PR không tự thành release được phép. Checklist bổ sung runbook hiện
hữu, không thay lịch sử PASS, không giao người/quyền hoặc ghi ACK thay họ.

## Quyền và danh tính phải xác thực

| Vai trò | Quyết định hiện hữu | Evidence cần | Quyền tối thiểu / điều cấm |
|---|---|---|---|
| Human Governance | Billing/backup; admin@cfp.plus email quản trị chính thức | Account membership readback đúng provider/Drive, verified contact và scope authority; access hiện CHƯA XÁC MINH | Phê duyệt riêng budget/runtime/host/lease/rehearsal; không suy email thành operator/custodian |
| Operator + dự phòng | Chờ named assignment riêng | Principal/account ID, verified identity/lineage, receipt nhận nhiệm vụ, ca trực/contact, MFA và expiry UTC; không gửi secret | Đúng một host, SSH key/admin CIDR được duyệt, snapshot/encrypted upload/process switch đã cấp scope; không billing owner/cloud admin mặc định |
| Reviewer / assessor | Chờ verified authority/prerequisites | Account principal riêng learner/operator, đúng subject/workspace/pair grants, assessor scope và nhận review thực | Đọc evidence/review đã cấp; không self-review, mutate grants/ID hoặc chứng nhận ngoài scope |
| Observer độc lập | Chờ assignment | Kênh ngoài host và receipt quan sát/time/scope | Đo closure/HTTPS từ ngoài; không arm/reopen hoặc provider admin |
| Recovery custodian + dự phòng | Chờ chỉ định riêng | Private destination/ACL/quota/retention, recipient public fingerprint, keystore custody và recovery receipt | Private key off-host; isolated decrypt/restore; operator chỉ nhận public recipient |
| Codex kỹ thuật dưới CFP+ | Local prep/dev được phép | Scope đang thực hiện + artifact/revision/log | Không tạo resource, checkout, DNS, deploy, merge, adapter thật |

Tài khoản synthetic editor/reviewer/viewer dùng test local không phải tài khoản
operator/assessor thật; không grant maintainer. Owner Drive giữ nguyên;
admin@cfp.plus designation không chứng minh quyền Render/DO/Drive. Không yêu cầu
password/token/SSH private key/card/recovery key trong GitHub/Notion/chat.

## Trước rehearsal host — tất cả chờ evidence

- [ ] Host hiện hữu/môi trường được HG cấp quyền cụ thể; không tự tạo paid host.
- [ ] Chọn một provider, full runtime SHA, release/manifest và scope lease UTC; baseline đánh giá b75 không đổi.
- [ ] Tài khoản operator/deputy/reviewer/observer/custodian xác thực và nhận nhiệm vụ; least privilege/readback grants.
- [ ] Gross/upper bound, shared inventory/quota, D/R, residual budget và quyền closure được phê duyệt riêng.
- [ ] Off-host destination/ACL/public recipient/custody, >=7 valid points; không prune khi backup thất bại.
- [ ] Original DB/audit/checkpoints bất biến, snapshot nhất quán, compatible recovery release; new assessment field có risk downgrade mất dữ liệu chưa chứng minh.
- [ ] Admission CLOSED, real adapters DISABLED, auto-deploy OFF; SSH admin CIDR, cloud+guest firewall IPv4/IPv6 readback, app loopback, đúng Host/Origin/TLS/cookie.

## Ca host mới, chỉ chạy sau quyền riêng

| Ca | Expected / bằng chứng bắt buộc | Khi lỗi |
|---|---|---|
| Identity / grants | Viewer write/self-review/foreign workspace/pair denied trên account và cấu hình host mới; backend không public | CLOSED, revoke đúng scope; không lặp toàn suite local cũ |
| Meter / closure | NIC/namespace/IPv4/IPv6/direct Spaces/proxy bypass coverage; stale-meter, expiry, active stream và bytes/time overshoot đo từ observer ngoài | CLOSED latch; không tự reopen; money cap vẫn NOT PROVEN |
| Crash / disk full / reboot | Controller chết, storage full, mất clock/lease giữ fail-closed, boot không tự arm; admin recovery path còn | Ghi finding và retained state; chưa đủ authority thì không fault injection |
| Backup | Consistent SQLite+audit+sidecar/account receipt → encrypt → private off-host upload/download → digest readback → custodian decrypt | Không prune hoặc overwrite bản tốt trước |
| Restore | Isolated new generation, audit/checkpoints + assessment sidecar preserved; revoke restored sessions; measure actual RPO/RTO | Giữ DB gốc và CLOSED |
| Rollback / process switch | Quiesce writes → previous compatible executable + atomic pointer → restart → source/hash/HTTPS readback; assessment fields và grants/history không mất | Thiếu compatible release thì STOP/CLOSED; không downgrade b75 trên DB mới để thử may rủi |
| Billing after closure | Target-specific closure readback + inventory pending/storage/compute/retention phí còn tiếp tục | Không suy HTTPS stop = billing stop; destroy/cancel cần quyền riêng |

Rollback ưu tiên phục hồi executable tương thích với schema hiện tại. Nếu release
cũ không giữ assessment field, không ghi vào DB hiện tại: tạo bản isolated phục
hồi có migration/sidecar bảo toàn đã review, hoặc giữ CLOSED đến khi có release
tương thích. Không gán host PASS từ prototype/mock/loopback.

Mỗi receipt: case, expected, observed, status PASS/FINDING/BLOCKED, full source
SHA/config hash, started/ended UTC, artifact+SHA256, actual executor principal,
reviewer/observer receipt, finding/owner/next step và rollback pointer/backup hash.
Không copy secrets hoặc reset lịch sử. RPO/RTO hiện null; host cases BLOCKED.
Chỉ ca có thay đổi liên quan được chạy; historical PASS giữ nguyên.
Rehearsal PASS không cấp activation/Production hoặc DNS authority.
