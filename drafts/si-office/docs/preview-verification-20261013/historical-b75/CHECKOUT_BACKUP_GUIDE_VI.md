# Render Preview — hướng dẫn Human Governance

Không bấm Create Web Service, Apply Blueprint, Deploy hoặc xác nhận nâng workspace.
Không nhập/sao chép bí mật vào ChatGPT, GitHub, Notion hoặc ảnh evidence.

## Kiểm tra tài khoản và checkout

1. Đăng nhập trực tiếp dashboard.render.com bằng tài khoản owner. Chọn đúng workspace;
   ghi plan và kỳ thanh toán. Không đổi sang Pro/Scale. Mở Billing, chụp phần plan,
   usage/quota hiện tại, pending charges/estimated invoice và currency nếu hiển thị.
2. Trong Workspace Settings → Build Pipeline, ghi tier, quota đã dùng và spend limit.
   Nếu muốn đặt extra spend limit 0, chỉ thực hiện khi UI giải thích rõ phạm vi và
   không tạo tài nguyên/nâng plan; ghi bằng chứng giá trị đã lưu. Đừng coi đây là cap
   bandwidth, disk hoặc toàn hóa đơn.
3. Mở biểu mẫu New → Web Service, chọn charityfundplus/CFP.plus. Chỉ điền để xem giá:
   root drafts/si-office; Singapore; Node native; 0,5 CPU/512 MB; một instance;
   auto-deploy OFF; disk 1 GB /var/data. Không dùng auto-preview tạo thêm service.
   Nếu chọn repo/branch chưa sinh tài nguyên, kiểm tra revision bằng manual specific
   commit sau này; head PR hiện tại không phải SHA đã được duyệt.
4. Ghi các dòng giá compute/disk, workspace fee, tổng dự kiến, quota bandwidth/build,
   đơn giá vượt quota, thuế và phí nếu có. Không đi qua bước xác nhận thanh toán để
   tìm thuế. Nếu UI không hiện thuế/phí cuối, đánh dấu CHƯA XÁC MINH và hỏi Billing
   support/account owner; không coi thuế bằng 0. Phí thẻ/đổi tiền kiểm tra với bên
   thanh toán riêng, không cung cấp thông tin thẻ cho Codex.
5. Che email, địa chỉ, tax ID, số thẻ, API token, mật khẩu, deploy hook và dữ liệu
   cá nhân. Giữ lại tên dòng sản phẩm, region, specs, số tiền, quota, spend-limit,
   thời điểm UTC; có thể dùng nhãn workspace thay tên thật.
6. Tìm bằng chứng giới hạn tổng chi phí: phạm vi gồm compute/disk/build/bandwidth,
   thuế và phí? Khi chạm trần có tự ngừng? Độ trễ usage? Chi phí còn sau suspend?
   Nếu chỉ có cảnh báo hoặc pipeline cap thì tổng cap vẫn CHƯA XÁC MINH.
7. Cung cấp các ảnh đã che thông tin tại cuộc trao đổi này. Chưa bấm Create.
   Khi tất cả evidence đủ, Codex lập hồ sơ cuối cho Human Governance quyết định.

## Rủi ro ngân sách

7,25 USD là dự toán trước thuế/phí, không phải giá checkout xác nhận. Nguồn #130
đã ghi compute 7 + disk 0,25; lần đọc pricing hiện tại không trả bảng giá động nên
không xác nhận lại số đó như checkout. Render docs xác nhận Hobby 500 phút build,
5 GB bandwidth/workspace và public egress vượt quota 0,15 USD/GB. Quota dùng chung.
Chỉ bandwidth thêm 52 GB đã thêm 7,80 USD, khiến dự toán 7,25 thành 15,05 trước
thuế/phí. Backup và response bị từ chối cũng có thể tiêu thụ bandwidth.
Ngưỡng cảnh báo 10/đóng 12 USD và bandwidth 4 GB chỉ là biện pháp dự phòng.
Chưa bảo đảm <=15 USD: không kích hoạt trả phí theo chỉ đạo Human Governance.

## Backup ngoài Render — phương án đề xuất, chưa chọn nơi lưu

Ưu tiên kho object storage riêng thuộc CFP+ với endpoint HTTPS, ACL private,
versioning, quota/chi phí đã xác nhận, retention >=7 mốc; không tự tạo kho tính phí.
Nếu CFP+ đã có máy/kho riêng được quản lý, dùng receiver SFTP được xác nhận host key,
ACL owner-only và thư mục riêng. Dell chỉ là một ứng viên nếu được xác nhận sau.
Google Drive evidence ZIP hiện hữu chứa source/evidence, không phải backup runtime.

Đề xuất mã hóa bằng age với public recipient trên Render; private recovery key
chỉ trong password manager/keystore do backup custodian quản lý ngoài Render,
và bản dự phòng riêng do người thay thế giữ theo quy trình CFP+. Không đặt private
key trong archive, app, GitHub/Notion hay cuộc hội thoại. Test hiện tại dùng AES-256-GCM
và key ngẫu nhiên trong bộ nhớ; chưa chứng minh age/key custody thực tế.

Luồng: maintenance lease → VACUUM INTO → audit/hash + integrity_check → manifest
và receipt synthetic 0600 (receipt có mật khẩu nên phải ở trong archive mã hóa) →
encrypt → transfer → remote SHA/readback → decrypt/restore drill vào thư mục riêng
→ xác nhận audit prefix, NEW GENERATION và revoke sessions. Không restore đè DB đang dùng.
Chỉ prune sau mốc mới đạt readback; giữ ít nhất 7 mốc hợp lệ và bản trước rollback.
Chặn mở Preview nếu backup lỗi/quá hạn. RPO24h/RTO60min là mục tiêu chờ đo thực tế.

Cần owner + người thay thế, region/endpoint, ACL/readback, lịch/retention, dung lượng,
chi phí, key custody và drill từ đúng nơi lưu ngoài Render. Test receiver cục bộ
không thay thế bằng chứng đó. Không gửi bí mật để hoàn thành các xác nhận.

## Phạm vi đã kiểm thử và việc tiếp theo

26 Git blobs tải bằng connector khớp byte tại SHA b75b780; đây là tập phụ thuộc cần
cho diễn tập, không phải checkout đầy đủ hoặc kiểm lại 77 manifest lịch sử.
4 nhóm test mới PASS tại Node24.19.0. Test rollback dùng hai package cùng runtime
đã chốt, kiểm cơ chế checkpoint/pointer/restore; không chứng minh nâng schema,
chuyển tiến trình Render hoặc rollback Production.
Giới hạn request và policy guard hiện là prototype ngoài app, chưa gắn launcher;
chưa giới hạn byte phản hồi, toàn egress, disk đầy hoặc thử transport Render.
Suspend dùng callback giả lập và bắt buộc readback; không gọi Render API.

PR124 Draft/unmerged head f3be4842d973e2e882102ed16376a57954d87d63 là hậu duệ
6 commit của b75b780; Link Mẫu universal intake được thêm sau SHA chốt.
Giữ test training/UI đã PASS tại revision tương ứng. Không chạy lại suite lịch sử.
Chuẩn bị kiểm thử thực tế bản đã duyệt gồm /p2, 5 bài, 12 bài thực hành, 6 hướng dẫn
nâng cao và HSTDN draft; universal intake mới chưa thuộc SHA được duyệt trên Render.
Không tự chứng nhận assessment hoặc đưa bản head vào Preview đã pin.

Nguồn: https://github.com/charityfundplus/CFP.plus/issues/130
https://github.com/charityfundplus/CFP.plus/pull/124
https://render.com/docs/build-pipeline
https://render.com/docs/outbound-bandwidth
https://render.com/docs/disks

CONFIGURATION APPROVED • PAID RESOURCE PENDING • PRODUCTION NO-GO.
