# CFP+ • Phương án Preview Review Vòng 1 trình phê duyệt

Ngày 13/10/2026. **HUMAN REVIEW • PRODUCTION NO-GO • PENDING APPROVAL**.
Đây là cấu hình đề xuất, chưa được áp dụng và chưa tạo tài nguyên tính phí.

## Chọn bản và giữ bằng chứng

Theo chỉ đạo CFP+, ưu tiên `f3be4842d973e2e882102ed16376a57954d87d63`; giữ `2814b357d8b31385aff530ca37eb8606674b608e` làm đối chiếu, không xóa/ghi đè. Quyết định mới này thay vai trò ưu tiên trong bàn giao cũ, không sửa bằng chứng lịch sử.

| Vai trò | Gói đã có | SHA-256 ZIP theo biên nhận nguồn |
|---|---|---|
| Review ưu tiên, 73 runtime files | [f3be4842](https://drive.google.com/file/d/1lYR4xCDcpq8O9yunswAVxOR74_n3VyGn/view) | `920f92627e545c117ee20eba10ec06598f72927fbd0ebb8ccc131d1bfb243de3` |
| Đối chiếu, 64 runtime files | [2814b357](https://drive.google.com/file/d/1i3wmDKK4140PWYiKoUHW-iL7pZsS-mtq/view) | `b6d0294970e4962bf45a58cd9b296d2fed3c8c5ff6ed9b6daf1886aa8c014f69` |

Điều hướng ưu tiên: Link Mẫu → Đăng ký → Xác minh → Học tập → Thực hành → Nhận việc → Evidence. Dùng các luồng hiện hữu; xác minh vẫn pending, yêu cầu nhận việc không tự cấp quyền. Không tạo Core/navigation/Link Mẫu thứ hai.

Nguồn đã đọc: [bàn giao ghim f3be4842](https://github.com/charityfundplus/CFP.plus/blob/f3be4842d973e2e882102ed16376a57954d87d63/drafts/si-office/docs/PREVIEW_REPLAY_HANDOFF.md), [hồ sơ Notion hiện hữu](https://app.notion.com/p/3f8caac9a55781f794dcc175b857057c). Hash và kết quả QA trên là từ biên nhận lịch sử; lượt này không tải lại ZIP, không chạy lại suite, không xác nhận URL đang hoạt động hoặc iPhone/Safari PASS.

## Bảng giá và điều kiện trần

Phương án đề xuất: DigitalOcean Basic Regular tại Singapore nếu plan sẵn có; một máy Node 24 + SQLite, không HA. Giá chính thức kiểm tra ngày 13/10/2026, không tính credit khuyến mại.

| Khoản | Cấu hình đề xuất | USD/tháng |
|---|---|---:|
| Host | 1 vCPU, 1 GiB RAM, 25 GiB SSD, 1.000 GiB transfer gồm trong plan | 6,00 |
| Storage ngoài máy | Spaces Standard, 250 GiB storage và 1 TiB outbound gồm trong plan | 5,00 |
| Backup máy | Percentage-based weekly: 20% × 6 USD | 1,20 |
| HTTPS/phần mềm | Caddy + ACME; không mua certificate hoặc license | 0,00 |
| Domain | Dùng subdomain thuộc domain hiện có, không mua domain mới | 0,00 phát sinh dự kiến |
| **Tổng niêm yết** | | **12,20** |
| **Dự phòng trong trần** | Thuế/phí và phát sinh được duyệt | **2,80** |
| **Trần tổng** | | **15,00** |

Nguồn: [Droplets pricing](https://www.digitalocean.com/pricing/droplets), [Spaces pricing](https://www.digitalocean.com/pricing/spaces-object-storage), [Backups pricing](https://docs.digitalocean.com/products/backups/details/pricing/).

Điều kiện: 12,20 USD là trước thuế. Chỉ được tạo tài nguyên khi tổng sau thuế/phí đã xác định ≤15 USD; nếu chỉ có thuế thì dư địa tương đương tối đa khoảng 22,95%. Không bảo đảm hard cap bằng billing alert. Không autoscale, không thêm VPS/volume/database/load balancer/snapshot trả phí. Máy tắt nguồn vẫn có thể tính phí. Không dựa vào thao tác xóa tài nguyên tự động để kiểm soát trần.

Giới hạn ứng dụng đề xuất thấp hơn quota tính phí: dữ liệu sống ≤5 GiB; toàn bộ backup/evidence Spaces ≤50 GiB; outbound host ≤100 GiB/tháng, Spaces ≤100 GiB/tháng. Giới hạn export/upload, rate limit và tắt nhận thao tác mới khi đạt giới hạn; kiểm tra cả egress/log của host vì giới hạn ứng dụng không phải hard cap của nhà cung cấp. Cảnh báo dự kiến ở 12/13/14 USD, owner xử lý trước 15 USD. Giá overage Spaces là 0,02 USD/GiB storage và 0,01 USD/GiB transfer; không cho phép vượt quota rồi thanh toán mặc nhiên.

## Cấu hình HTTPS và runtime đề xuất

- Một hostname sandbox cố định do CFP+ cấp quyền; không dùng apex, không đổi canonical `https://cfp.plus/69`. Không tạo DNS/tunnel trong lượt này. DNS/TLS chỉ cấu hình sau phê duyệt riêng cho sandbox.
- Caddy terminate TLS bằng chứng chỉ công khai ACME tự gia hạn; HTTP chuyển HTTPS, chỉ mở 80 cho redirect/ACME và 443. Không dùng chứng chỉ localhost trên điện thoại. Backend chỉ bind loopback, không public cổng Node.
- Node 24, một process SQLite writer; build sẵn bên ngoài máy 1 GiB. Không chia sẻ DB qua NFS/object storage hoặc chạy hai writer. Mỗi revision có thư mục release riêng, read-only đối với service; launcher phải kiểm tra manifest/hash trước chạy.
- Origin HTTPS chính xác và Host allowlist tại ứng dụng; cấu hình forwarded headers chỉ tin reverse proxy local. Giữ Secure/HttpOnly/SameSite cookie, chống cross-origin, quyền server theo workspace/pair và thu hồi phiên. Không sửa các kiểm soát này để chạy qua proxy.
- State ở `/var/lib/cfp-preview/f3be4842/`, không nằm trong source/webroot. DB/credentials mode 0600, thư mục 0700, tài khoản service không root. Chưa có state từ runtime cũ trong hai ZIP: chỉ provision tài khoản synthetic mới, không tuyên bố khôi phục học viên/audit cũ.
- Chỉ f3be4842 phục vụ Review ưu tiên. 2814b357 giữ trong archive riêng; nếu cần chạy đối chiếu, dùng DB/origin riêng và chuyển lịch có kiểm soát, không overlay source/state. Không tạo host thứ hai mặc nhiên.

## Storage, backup và phục hồi đề xuất

- Một Spaces subscription cho các bucket/prefix private của archive, evidence và backup; public ACL/CDN tắt. ZIP gốc giữ theo revision/hash, không ghi đè. Export chỉ qua API có quyền hoặc URL có hạn ngắn nếu cơ chế này được reviewer chấp thuận.
- Backup ứng dụng mỗi ngày và trước thay đổi: dùng chức năng backup SQLite nhất quán hiện hữu sau khi kiểm tra entrypoint chính xác; không copy riêng file DB đang mở hoặc bỏ WAL. Chụp state/audit/evidence nhất quán, manifest SHA-256 và timestamp/revision; mã hóa trước upload bằng khóa phục hồi do owner giữ ngoài host.
- Giữ 7 bản ngày + 4 bản tuần; archive hai revision giữ hết Review và chờ quyết định retention. Xóa backup theo retention chỉ sau owner duyệt, không ảnh hưởng ZIP nguồn. Cảnh báo dung lượng tại 40 GiB, chặn upload mới ở 50 GiB.
- Weekly image backup là lớp phục hồi máy, không thay cho SQLite-consistent backup. RPO mục tiêu ≤24h nếu job thành công; RTO mục tiêu 4h, chưa được kiểm chứng. Restore vào DB/thư mục mới, xác minh hash và thu hồi session, giữ state gốc. Rehearsal dùng cùng host trong maintenance sau phê duyệt, không tạo máy tính phí khác.
- Backup khác bucket cùng provider không phải WORM hoặc custodian độc lập. Audit/WORM vẫn finding riêng. Nhật ký backup không chứa token/password/dữ liệu nhạy cảm; owner nhận cảnh báo thất bại, xác nhận readback/restore trước mở review.

## Quyền truy cập đề xuất

- Billing/host owner do CFP+ chỉ định, MFA bắt buộc. Codex không nhận quyền thanh toán hay token production trong lượt này.
- SSH bằng key, chỉ IP admin được phép, tắt password/root login. App service không có quyền cloud-admin; khóa Spaces tối thiểu theo bucket/scope được provider hỗ trợ, không dùng khóa toàn tài khoản. Khóa backup tách khóa phục hồi, không đưa vào GitHub/Notion/ZIP.
- Mỗi reviewer có tài khoản synthetic riêng trong workspace review, vai trò viewer/editor/reviewer tách biệt; viewer không ghi, người thực hành không tự review. Tài khoản cấp riêng, thu hồi sau review. Không ghi ACK thay reviewer.
- Không mở adapter thật/thanh toán/dữ liệu thật hoặc quyền production. MCP/CMP giữ ngoại lệ riêng; không probe lại hay ghi synced. ID/Parent/DID/Canonical/Audit History và bằng chứng Routing giữ nguyên.

## Nội dung cần Human Governance phê duyệt

1. Chọn phương án một host 6 USD + Spaces 5 USD + backup tuần 1,20 USD, tổng sau thuế/phí ≤15 USD/tháng.
2. Chỉ định billing/host owner, backup custodian, hostname sandbox thuộc domain hiện có và quyền DNS; xác định tài khoản billing/quốc gia thuế.
3. Duyệt reviewer roster, access/retention nêu trên và thời hạn Review; không suy thành production approval.
4. Sau phê duyệt, provision sandbox và kiểm tra đúng phần thay đổi host: manifest/revision, HTTPS/Host/Origin/cookie, cô lập state/quyền, backup/readback/restore và iPhone/Safari thực tế. Không chạy lại suite Core/intake/course/Routing không bị ảnh hưởng.

Chưa tạo tài nguyên, cấu hình DNS, triển khai hoặc chạy QA. Đây là tài liệu trình duyệt local; chưa cập nhật hồ sơ GitHub/Notion/Google và không phải receipt đồng bộ năm kho.

## Tiếp nhận phê duyệt có điều kiện • 13/10/2026

CFP+ chấp thuận về nguyên tắc lựa chọn revision, ngân sách cơ sở và các kiểm soát; chưa phê duyệt cuối việc tạo tài nguyên/thanh toán. Trạng thái hiện tại: **CONDITIONAL APPROVAL • PAYMENT PENDING • PRODUCTION NO-GO**. Báo cáo điều kiện và cơ chế còn thiếu tại [READINESS_VI.md](/workspace/cfp-preview-preactivation/READINESS_VI.md); cổng kích hoạt vẫn đóng trong [activation-gate.json](/workspace/cfp-preview-preactivation/activation-gate.json). Giữ nội dung dự toán trước đây như hồ sơ lịch sử; báo cáo bổ sung phân biệt cấu hình đề xuất với cơ chế đã có bằng chứng.
