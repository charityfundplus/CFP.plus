# 04 • Danh Sách Nội Dung Cần Human Governance Phê Duyệt

**Trạng thái:** REVIEW CANDIDATE • Không có quyết định nào được suy diễn hoặc tự ghi

Mỗi mục có một phương án đề xuất để tiết kiệm thời gian. Phương án đề xuất **không có hiệu lực** cho đến khi Human Governance ghi quyết định.

| Mã | Câu hỏi cần quyết định | Phương án đề xuất | Ảnh hưởng nếu chưa quyết |
|---|---|---|---|
| **HG-1** (C1) | Bộ 5 Nhóm chính thức: `V • 0 • 135 • 246 • 789` (Master Map) hay `V • D(D/500) • 000 • 135 • 246 • 789` (yêu cầu 18/11/2026)? | Notion (2026-10-20, PROPOSED) chốt `[D • V] • 000 • 135 • 246 • 789`; GitHub Master Map còn `V • 0 • …`. Đề xuất: HG ký một Governance Decision, sau đó cập nhật Master Map. Website giữ nguyên cho đến lúc đó | Navigation và Registry tiếp tục dùng Master Map |
| **HG-2** (C2) | Đổi tên Chương 6 thành "SI AI Robot Siêu Phần Mềm & Công Nghệ"? | Lập Change Proposal riêng, vì tên Chương xuất hiện ở nhiều tài liệu đã khóa | Giữ "AI & Công Nghệ" |
| **HG-3** (C3) | ID Cổng Tri Thức là `28882` hay `8882`? | Notion ghi 3 tên khác nhau cho 8882 và một mục ghi "28882 → 8882". Live: 28882 có trang, 8882 chỉ trả trang dự phòng. HG chọn tên/ID và quyết định có chuyển hướng hay không | Trang `/8882/` hiện chỉ là trang dự phòng `/id/` |
| **HG-4** (C4) | Văn bản và ID của Luật Thép CFP+ | Notion đặt Luật Thép trong 4742 (Chương 4); repo `58` = "Tổ Chức trong Cộng Đồng"; không nơi nào ghi Luật Thép = 58. Cần văn bản nguyên văn + ID | Kiểm duyệt Diễn Đàn chưa có căn cứ văn bản |
| **HG-5** (C5) | Cây Siêu Bộ Đôi dùng quy tắc A (0–9, 1.110 vị trí) hay B (0 dành cho mở rộng, 910 vị trí)? | Notion (Kiến trúc đệ quy + Mẫu Chung X0) nghiêng về quy tắc B. Lưu ý 6 ID đã dùng 0 làm vị trí thường (00, 000, 003, 005, 330, 500) phải giữ nguyên. Đề xuất: B cho ID **mới**, không áp ngược | Validator chạy được cả hai chế độ |
| **HG-6** (C6) | Parent xác định bằng tham chiếu tường minh hay bằng cắt chữ số? | Cả hai: bắt buộc ghi tường minh **và** phải khớp tiền tố (validator đã áp dụng) | — |
| **HG-7** (C8) | ID Gemini: `691141` (registry JSON) hay `6911421` (thư mục trang)? | Registry custodian đối chiếu và sửa một nguồn | Danh bạ Diễn Đàn ghi Gemini là PENDING |
| **HG-8** | Định nghĩa chính thức: SI AI, Siêu Phần Mềm, Siêu Bộ Đôi, Phục Vụ Vô Vụ Lợi | Dùng [03_GLOSSARY_PENDING_VI.md](03_GLOSSARY_PENDING_VI.md) làm bản nháp | Mọi tài liệu ghi "định nghĩa đang chờ" |
| **HG-9** | Có công bố mẫu Diễn Đàn/Văn Phòng tại đường dẫn chữ `/docs/si-ai-platform/mockups/…`, trái với Numeric Link Rule (chỉ link số)? | Chỉ dùng để review qua GitHub/preview. Khi chính thức, gắn vào ID số đã được cấp | Trên trang chủ đã đặt nhãn "Mẫu" |
| **HG-10** | Phê duyệt merge PR này vào `main` | Merge **sau khi** có ít nhất 1 review độc lập (ReviewSI) và quyết định HG-9 | Website không thay đổi |
| **HG-11** | Thêm mục "Thông Báo • Bản Thử Nghiệm" trên trang chủ có vượt phạm vi Release 1 inventory contract không? | Coi là nội dung trong Homepage hiện hữu, không phải portal mới | — |
| **HG-12** (C9) | Nguồn có thẩm quyền: Notion hay GitHub Registry JSON, theo từng loại dữ liệu? | Ma trận đề xuất: định danh/ID/Parent → GitHub Registry; tài liệu/điều phối → Notion; Evidence kỹ thuật → GitHub | Hai nguồn cùng tự nhận là Source of Truth |
| **HG-13** (C6) | Cung cấp Parent tường minh cho 91 Siêu Bộ Đôi | Registry custodian điền Parent theo từng ID; adapter sẽ tự dựng cây khi có dữ liệu | Chưa dựng được cây Cha–Con–Cháu thật |
| **HG-14** (C10, C11, C13) | Hồ sơ 333 trùng; 2273, 2588 chưa có link; 2624 so với 2684 | Registry custodian đối chiếu | Danh Bạ ghi chú cảnh báo |
| **HG-15** | Chọn một PR Diễn Đàn chính và một PR Core; đóng hoặc gộp các PR sandbox trùng (xem 06 mục 5) | Core: #124. Diễn Đàn: #195 hoặc #219 | Công sức bị phân tán qua hơn 10 PR Draft |
| **HG-16** (C12) | Mã Nhóm (000, 135, 246, 789, 500) cũng là ID Siêu Bộ Đôi | Ghi rõ hai loại quan hệ (phả hệ và điều phối) trong Registry | — |
| **HG-17** | Cho phép PR #124 bổ sung lệnh ACK riêng và một adapter **đọc thật, chỉ đọc** (GitHub/Notion) thay cho mock? | Chỉ sau khi chọn Core (HG-15); adapter giữ `externalRequests` được kiểm soát, không ghi | Công việc thật vẫn chạy ngoài Core, gắn bằng SHA-256 |
| **HG-18** | Cấp quyền đọc Google Drive cho tài liệu CFP+ (tài khoản hiện tại thấy 0 file) và mở thêm host Web cần nghiên cứu | Chia sẻ thư mục Drive cho tài khoản connector; liệt kê host cụ thể | Kho Google và Web chỉ ở mức PENDING/PARTIAL |
| **HG-19** | Trang Notion gắn cho **5284** nay là "Tài Liệu Tham Chiếu Lịch Sử • Đối Chiếu Link Gốc", không còn "Kiểm Chứng Tổng Hợp". 5284 có còn là Siêu Bộ Đôi kiểm chứng không? | Xác nhận tên/vai trò của 5284 trước khi dùng tiếp trong thí điểm | Vai trò kiểm chứng của thí điểm cần được xác nhận lại |
| **HG-20** | Chủ PR #124 có áp `patches/pr124-ack-readonly.patch` (ACK + adapter READ ONLY tắt mặc định) không? | Áp sau review độc lập. Bật `requireAck` cho thí điểm; adapter chờ HG-17 | Không có ACK riêng trong Core chính thức |

## Ghi nhận quyết định • 2026-11-18 (bình luận trên PR #232 từ tài khoản chủ repo)

Nguồn: [PR #232, bình luận 6994941355](https://github.com/charityfundplus/CFP.plus/pull/232#issuecomment-6994941355). Ghi lại nguyên ý; **không phải** phê duyệt production hay cấp quyền dữ liệu mới.

| Mã | Quyết định ghi nhận | Áp dụng trong PR #232 |
|---|---|---|
| HG-15 | PR #124 (Node + SQLite) là **Core tham chiếu cho thí điểm tiếp theo**. Giữ nguyên PR #195/#193; Core production cần nghiệm thu riêng | Thí điểm tiếp tục chỉ dùng PR #124. Không đụng tới #195/#193, Supabase hay Render |
| HG-17 | Cho phép **chuẩn bị và kiểm thử** adapter READ ONLY ở trạng thái **mặc định tắt**. Kích hoạt đọc thật cần hồ sơ quyền riêng (allowlist, chủ sở hữu, phạm vi tối thiểu, thời hạn, người kiểm chứng) và phê duyệt HG riêng | Adapter vẫn tắt; test chỉ dùng file tạm |
| HG-19 | **5284** giữ ở trạng thái cần xác minh vai trò; không dùng làm reviewer có thẩm quyền | Thí điểm đổi reviewer sang `review-independent` (không gắn ID Siêu Bộ Đôi); bỏ binding 5284 khỏi tiến trình |
| HG-20 | Đề nghị **chủ PR #124 và Codex review** bản vá trước khi áp; không phải quyền tự merge hay triển khai | **BLOCKED** cho PR #232: cần chủ PR #124/Codex review trên chính PR #124. PR #232 không push vào nhánh đó |
