# CFP+ HUB69 • Báo cáo tổ chức nguồn và đồng bộ • 13/10/2026

Đã hoàn thành kiểm kê và tổ chức bằng danh mục chức năng, giữ đường dẫn đang hoạt động, tạo snapshot có kiểm soát và xác minh khôi phục. GitHub là nguồn chuẩn mã chạy/lịch sử; Drive lưu bản bàn giao; Notion điều phối/liên kết. Không đồng bộ hai chiều tự động, không merge/deploy hoặc thay quyền chia sẻ.

## Revision và phạm vi

Revision yêu cầu `40af3c85b01b4efdd6bfe7babbb6a4b4ab3a4222`; HEAD lúc bắt đầu `3a883614c17443e1dd3bb94219139eb299f0e7ab` hợp nhất giáo trình và là hậu duệ revision yêu cầu. Trong lúc làm việc có hai commit preview độc lập; đã đọc10 file thay đổi/thêm và đối chiếu HEAD `b75b780eb64430355f0b51a4b58b9e5269e0db43`. Báo cáo kiểm thử runtime được ghim theo hai mốc này; commit tổ chức chỉ thêm tài liệu/evidence/công cụ xác minh snapshot, không đổi ứng dụng.

[Kho chính](https://github.com/charityfundplus/CFP.plus) • [Draft PR124](https://github.com/charityfundplus/CFP.plus/pull/124) • [Nguồn kiểm kê hiện hành](https://github.com/charityfundplus/CFP.plus/tree/b75b780eb64430355f0b51a4b58b9e5269e0db43) • [Danh mục chức năng](../../docs/SOURCE_ORGANIZATION.md) • [Khôi phục](../../operations/SOURCE_RESTORE.md).

## Số liệu

| Loại chính, phân loại loại trừ nhau | File tại b75b780 |
| --- | ---: |
| apps/website/giao diện và nội dung website | 295 |
| CoreEngine và điều phối | 13 |
| SI/AI/Registry | 97 |
| Software/công cụ thực thi | 16 |
| Adapter/integration chính | 1 |
| Training chính | 3 |
| Tests | 43 |
| Cấu hình/dependency/CI | 15 |
| Tài liệu | 109 |
| Evidence/manifest/kết quả | 63 |
| Operations | 1 |
| **Tổng nguồn kiểm kê** | **656** |

Các module có nhiều chức năng vẫn chỉ được đếm một loại chính; ví dụ giáo trình tài liệu được đếm docs, kiểm thử đào tạo được đếm tests. Tổng trên chưa cộng các artifact tổ chức mới của lượt này.

Đã lập chỉ mục656 file, xác minh byte bằng Git blob hash và SHA-256; di chuyển0, giữ nguyên đường dẫn656, xóa0. Kiểm kê ban đầu649 file giữ manifest riêng. 61 nhánh đọc đủ cây, không truncated:14.909 lượt file theo nhánh và1.312 tổ hợp path/blob khác nhau;663 biến thể không ở HEAD ban đầu. Chỉ checksum Git tree/blob được kiểm tra cho mọi nhánh; không tuyên bố đã tải/chạy tất cả biến thể. Các nhánh không bị hợp nhất hoặc xóa.

7 nhóm checksum giống nhau,88 file nằm trong nhóm,81 bản ngoài bản đầu;21 file rỗng gồm Registry stub và Python package marker. Đây là danh sách review, không phải81 file được phép xóa. Route số cùng skeleton vẫn có ý nghĩa tham chiếu riêng. `DUPLICATE_REVIEW.json`, `BRANCH_INDEX.json`, `BRANCH_VARIANTS.json` lưu chi tiết.

## Lưu trữ và đọc lại

[Thư mục Drive hiện hữu](https://drive.google.com/drive/folders/1JxTGabFVepUW22TwyyeUEV0ZBCpszr9Z) • [Gói P0/P1 hiện hữu giữ nguyên](https://drive.google.com/drive/folders/1b2ebHt2WIK6Ys5SuYsBGNZScZ6fi4IHO).

[Snapshot b75b780 •150 file](https://drive.google.com/file/d/1rhjwMu4OB9kxdtJ07gNiycFDCXFvpk81/view?usp=drivesdk) • [Manifest656 file](https://drive.google.com/file/d/14b6cm1CkKGxtnUqZz69mtroZS_yAooSF/view?usp=drivesdk).

ZIP SHA-256 `cf0b9a40d6f215c7d058a988e9f84c0fc5632bacd290a692e9f54f25e7eb5d45`.

Manifest SHA-256 `a22cebc88de1acdf36a6fca89b7786591c4b71608fec2644850f01ee65df3ff5`.

Snapshot trước [3a883614 •143 file](https://drive.google.com/file/d/1bT5fZNvm-TmHFqeaWB5U5dnYFrAOQAQ4/view?usp=drivesdk) giữ nguyên, ZIP SHA-256 `72cbd147cf8385a307591036aa96c6736cd20bb8f40356251abd8ff04006256f`. [Manifest649](https://drive.google.com/file/d/1ZEPm-raMWuAHuDE-VtapHhJ7p1B8KRZm/view?usp=drivesdk) SHA-256 `05bb159cdae1558efb2d1fee356fb437bf9f7b7a736701f17764d2790d28f7e2`.

Quyền tạo file đã được chứng minh bằng upload thực tế vào đúng parent và đọc lại. Cả hai ZIP được tải lại, đối chiếu digest toàn bộ và từng entry; manifest649 tải lại khớp từng byte. Manifest656 nằm trong ZIP đã đối chiếu và file riêng được đọc lại. **SYNC VERIFIED chỉ áp dụng các artifact đã ghi/đọc/so hash này**. Không thay quyền thư mục cha. Không lấy metadata size hoặc phản hồi create thay cho kiểm tra nội dung.

Snapshot chỉ gồm Core/training/P2/docs và HUB69, không sao chép toàn repository. Không chứa lịch sử Git đầy đủ hoặc dữ liệu DB riêng; không đưa dữ liệu người học thật lên GitHub. Không có retained DB thật trong workspace nên chưa chứng nhận bảo toàn/backup trạng thái riêng ngoài phạm vi truy cập.

## Kiểm thử mới, không kế thừa PASS lịch sử

| Lượt thực chạy | Revision/phạm vi | Kết quả |
| --- | --- | --- |
| Core regression | 3a883614 | 40/40 PASS |
| P2 state/auth/backup/restore/corruption | 3a883614 | 10/10 PASS |
| HTTP/authorization/release/rollback | 3a883614 | 5/5 PASS |
| Training/Office/HSTDN integration | 3a883614 | 5/5 PASS |
| Basic và advanced curriculum contracts | 3a883614; chạy lại b75b780 | 2/2 PASS mỗi lượt |
| Pair concurrency | 3a883614 | 3 DB/service đồng thời ×3 pair;9 task reviewed; token chéo bị từ chối, reopen/audit PASS |
| Browser UI và HUB69 VI/EN/mobile390 | 3a883614; chạy lại b75b780 | 8/8 PASS mỗi lượt; download evidence SHA-256, scope người học/workspace, href/10 chương, no page errors |
| CTTTC v0.6.6 | Nguồn không thay đổi từ3a883614; Node-independent Python3.12 | 204/204 PASS, kể cả pinned remote evidence |
| Preview launcher/provision | b75b780 | 2/2 PASS |
| Current evidence verifier | b75b780 | 77/77 hashes PASS; tamper training config bị từ chối |
| HEAD source byte integrity | b75b780 | 656/656 SHA-256 và Git blob PASS |
| Restore từ ZIP tải lại vào thư mục mới | b75b780 | 150/150 source hashes PASS; P2 10/10, preview2/2,3×3 pair rehearsal PASS |

Lần thử đầu browser/socket và3 CTTTC fetch bị chặn sandbox; khi quyền mạng sandbox bổ sung có hiệu lực, đã chạy thực tế PASS như trên. Không sửa network policy/production để né hạn chế. Server/browser của test đã dừng. Core regression chỉ chạy ở3a883614 vì hai commit sau không đổi Core; browser và launcher được kiểm tra theo scope mới.

Verifier mặc định tại3a883614 báo sai lệch configs/training-basic-v1.json do manifest cũ trước hợp nhất; bằng chứng lỗi được giữ. Commit preview đồng thời cập nhật verifier/manifest và b75b780 PASS77; không ghi lại manifest P1/P2 cũ để giả tạo PASS. Candidate verifier thử trong workspace đã được thay bởi nguồn mới; không commit thay đổi verifier cạnh tranh.

Kết quả P1/P2/browser của các phiên trước giữ nguyên tại manifest/commit lịch sử, không đổi thành kết quả mới. P1 16/16 lịch sử không chứng nhận mọi luồng ở HEAD hiện tại. Nội dung advanced đã chuẩn bị, nhưng assessment thật vẫn NOT ASSESSED; synthetic tests không chứng nhận năng lực/đồng ý thành viên.

## Notion và Task Board

[Danh mục/vận hành hiện hữu](https://app.notion.com/p/0526dbcb40664a1ebd80d06961f3eb12) • [Bàn giao và Task Board Team SI/AI/HSTDN hiện hữu](https://app.notion.com/p/3f8caac9a55781f794dcc175b857057c).

Cập nhật bổ sung các mục inventory/archive/readback/restore, liên kết đúng snapshot/revision. Không tạo trang trùng hoặc lưu Core vận hành trong Notion. Status hoàn thành chỉ cho phạm vi có evidence; training nâng cao, reviewer/roster, năm kho thật và Human Governance giữ trạng thái riêng. Biên nhận cuối xác nhận write/readback Notion và GitHub; báo cáo này không tự chứng nhận một write chưa xảy ra.

## Quyền/điểm chặn còn lại

GitHub connector và Drive đọc/ghi artifact sử dụng được. Git clone vẫn không kết nối được nên không có full Git history bundle; lịch sử còn trên GitHub. Không kiểm tra/xác lập quyền của tất cả reviewer, quyền production hoặc quyền năm operational vaults. Các URL trong file nhánh được định vị theo tree, không đồng nghĩa đã chạy mọi module/API ngoài PR124.

Production vẫn NO-GO: năm vault thiếu owner/URL/scopes/readback; independent audit custodian/WORM chưa có; registry/D500 conflict/authority và thành viên/lineage/acceptance thật cần nguồn xác thực; advanced assessment chưa chạy; access/hosting và review chính danh/Human Governance còn chờ; shared-DB multi-process/process-kill/migration tổng quát chưa được chứng nhận; website EN cũ còn partial. Preview HTTPS ở báo cáo độc lập là lịch sử/ephemeral, không cung cấp một URL đã hết hạn làm URL hoạt động.

Giữ Draft PR124. Không đổi ID/Parent/DID/Canonical, không cấp DID/0, không đổi production/quyền/thanh toán/real adapters, không gửi ACK thay ai. Khôi phục chi tiết tại `operations/SOURCE_RESTORE.md` và công cụ `operations/verify-source-snapshot.py` (từ chối extract đè, path không an toàn hoặc sai hash).
