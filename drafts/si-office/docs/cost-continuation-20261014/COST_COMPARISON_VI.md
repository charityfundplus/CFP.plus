# CFP+ • Bảng chi phí đầy đủ • 14/10/2026

**CONDITIONAL APPROVAL • HOLD ACTIVATION • PRODUCTION NO-GO.**
Baseline đánh giá giữ `b75b780eb64430355f0b51a4b58b9e5269e0db43`.
Một Preview; DigitalOcean ưu tiên xác minh, Render đối chiếu; chưa chọn mua.
Đọc nguồn công khai trong lượt này, không checkout, truy cập Billing tài khoản,
liên hệ support hay gọi API provider. Giá công khai không phải quote tài khoản.

| Khoản / USD mỗi tháng | DigitalOcean bundled | Render Hobby + external Spaces | Trạng thái thực tế |
|---|---|---|---|
| Compute, một instance | Basic Regular 1 vCPU / 1 GiB, 6.00 [1] | 0.5 CPU / 512 MB, 7.00 [2] | List estimate; actual SKU/region/quantity/account chưa xác minh |
| Lưu trữ ứng dụng | 25 GiB SSD đã trong 6.00; không cộng lần hai | Disk 1 GB ở /var/data, 0.25 [3] | Actual size/config chưa có |
| Lưu trữ backup off-host | Spaces Standard 5.00, 250 GiB dùng chung bucket [4] | Cùng external Spaces 5.00; subscription riêng DO | Không mặc định một subscription mới hoặc quota trống; inventory/ACL còn thiếu |
| Backup hệ thống | Percentage weekly 20% × 6 = 1.20 [5] | Không cộng DO image backup vào Render | Image/snapshot không thay backup SQLite nhất quán |
| Backup ứng dụng | Snapshot SQLite + sidecar + account receipt mã hóa vào Spaces; storage thuộc quota trên | Cùng quy trình; disk snapshots hằng ngày không phải bản backup DB off-host [6] | CPU/transfer/version retention và custodian restore chưa có số thực |
| **Base estimate** | **12.20** | **12.25** | Trước thuế/phí/overage; không phải gross |
| Thuế compute/disk/backup | Theo team tax location/VAT status [7]; UNKNOWN | Thuế Render UNKNOWN; thuế external Spaces theo tài khoản DO riêng | Không áp thuế DO cho Render hoặc suy billing location từ Singapore |
| Ví dụ thuế DO Vietnam | Chỉ nếu VAT 10% áp cả 12.20: 13.42 | Không tính scenario gross Render khi tax Render thiếu | Ví dụ, không invoice CFP+; miễn thuế cần evidence tài khoản |
| Droplet public outbound | Full-cycle plan allowance 1,000 GiB, accrual theo thời gian và pool team; vượt pool 0.01/GiB [8] | Không áp allowance Droplet cho Render | Remaining team quota/accrued/pending UNKNOWN |
| Render public outbound | Không áp | Hobby 5 GB/workspace; vượt 0.15/GB; cả responses và upload backup tới Spaces [9] | Quota shared; Spaces không nằm trong ngoại lệ same-region S3/GCS |
| Spaces outbound | 1,024 GiB/subscription shared; vượt 0.01/GiB [4] | Cùng giá, restore từ Spaces tới Render có thể dùng quota này | Droplet→Spaces upload tính pool Droplet; hai meters khác nhau |
| Storage overage / retention | Spaces vượt 250 GiB: 0.02/GiB-month [4]; versions/backups cũ cần inventory | Cùng Spaces; disk tăng theo provisioned size 0.25/GB-month | Không cho retention/quota UNKNOWN = 0 |
| Build pipeline | Build local/on-host trong compute đã quote; build/CI khác nếu có phải tính riêng | Hobby 500 Starter minutes shared; overage supplementary purchase, giới hạn chỉ pipeline [10] | Rate/pack/limit thực account UNKNOWN; auto-deploy OFF là đề xuất |
| Phí thanh toán / FX | Provider/card/bank/FX/rounding UNKNOWN | Tách hai provider, hai invoice, payment/FX UNKNOWN | Không dùng credit khuyến mại để chứng minh ngân sách |
| Khoản phát sinh khác | Extra disk/snapshot/IP/resource/support/CDN/worker/log export/API thật nếu có: inventory + giá riêng | Workspace nâng plan/extra instance/job/worker/database/API thật: inventory + giá riêng | Không được tạo; absence cần readback inventory trước khi ghi 0 |
| Phí sau đóng admission | Droplet vẫn bill khi power-off; Spaces còn bill nếu bucket giữ [1][4] | Chỉ stop app không ngừng service; suspend không xóa accrued usage/disk/Spaces [3] | Residual tới billing-end UNKNOWN; không tự destroy/cancel |
| **Gross tài khoản / upper bound** | **UNKNOWN** | **UNKNOWN** | **Hard cap tổng 15 USD chưa chứng minh** |

Render dùng Drive hiện hữu thay Spaces là phương án riêng **7.25 + backup tăng thêm UNKNOWN**,
không mặc định free quota hoặc 0 chi phí. Owner Drive hiện tại giữ
charityfundplus@gmail.com; admin@cfp.plus là email điều phối backup/billing đã
được HG chỉ định, **access chưa xác minh**. Không chuyển owner/ACL.

## Cách tính và phân bổ

Gross định kỳ = compute + disk + backup/storage cố định + thuế từng invoice +
payment/FX + metered usage + khoản khác được xác nhận. Giữ đơn vị GB của Render
và GiB của DO riêng, quy đổi bytes theo định nghĩa billing đã xác minh.
Headroom trước khoản chưa biết: DO 2.80, Render 2.75. Ví dụ synthetic:
Render 12.25 + 19 excess GB × 0.15 = 15.10 trước thuế/phí; không là usage thực.

`cost-bound.mjs` tính **F + U + D + R + S**, integer cents grossUSD, cùng scope/kỳ:
F fixed gross; U accrued/pending chưa nằm trong F; D phát sinh tăng thêm trong
độ trễ closure; R residual chưa nằm F/U/D; S sai số định lượng. Ví dụ nếu F đã
bao compute/storage cả tháng thì R không được cộng lại cùng chi phí đó; R phải
ghi phần tăng thêm/qua kỳ hoặc giữ UNKNOWN nếu chưa phân bổ được. Từng group
cần evidenceRef, và allocationEvidenceRef chứng minh không đếm đôi. Reference
chỉ là locator, calculator không xác thực nội dung/authority. Thiếu group hoặc
amount=null giữ UNKNOWN; tổng không đủ dữ liệu giữ null, không suy 0.
Arithmetic ≤1500c không cấp approval và không chứng minh provider hard cap.

## Receipt cần bổ sung trước activation

HG/admin@cfp.plus lấy bằng chứng đã che thông tin nhạy cảm từ tài khoản hiện
có khi được phép: team/workspace, inventory đầy đủ, SKU/region/kỳ/quantity,
quote từng dòng, tax location/rate/exemption, fee/FX thời điểm, remaining shared
quota, accrued/pending, retention/cancel/minimum và billing-end. Theo lệnh hiện
tại **không checkout**, không Create/Pay/Apply/Deploy, không nhập thẻ hay gửi
secrets; quote thiếu thì tiếp tục HOLD. Access admin email chưa được xác minh.
Độ trễ closure, active streams, tốc độ/bytes, external observer và residual
authority còn thiếu nên D/R không có upper bound đáng tin.

DO Spend Alerts là thông báo, không giới hạn spending [11]. Pipeline limit
Render chỉ giới hạn phút build [10]. Không có evidence tổng-money hard cap.

## Nguồn chính thức / giới hạn nguồn

1. https://www.digitalocean.com/pricing/droplets ; https://docs.digitalocean.com/products/droplets/details/pricing/
2. https://render.com/pricing — open trong lượt này chỉ trả shell, không hiện bảng compute; search index chính thức vẫn ghi 7.00. Giữ list estimate đã ghim profile4e6e11a, cần account quote xác nhận lại.
3. https://render.com/articles/how-much-does-cloud-application-hosting-cost-for-small-businesses — xác nhận cost model và disk0.25, workspace/compute/bandwidth/build riêng; exact suspended-disk invoice cần Billing.
4. https://docs.digitalocean.com/products/spaces/details/pricing/
5. https://docs.digitalocean.com/products/backups/details/pricing/
6. https://render.com/docs/disks
7. https://docs.digitalocean.com/platform/billing/taxes/ ; https://docs.digitalocean.com/platform/billing/taxes/vnm/
8. https://docs.digitalocean.com/platform/billing/bandwidth/
9. https://render.com/docs/outbound-bandwidth
10. https://render.com/docs/build-pipeline
11. https://docs.digitalocean.com/platform/billing/spend-alerts/

Không chứng nhận cloud configuration, quota thực, gross hoặc billing đã dừng.
