# 04 • Danh Sách Nội Dung Cần Human Governance Phê Duyệt

**Trạng thái:** REVIEW CANDIDATE • Không có quyết định nào được suy diễn hoặc tự ghi

Mỗi mục có một phương án đề xuất để tiết kiệm thời gian. Phương án đề xuất **không có hiệu lực** cho đến khi Human Governance ghi quyết định.

| Mã | Câu hỏi cần quyết định | Phương án đề xuất | Ảnh hưởng nếu chưa quyết |
|---|---|---|---|
| **HG-1** (C1) | Bộ 5 Nhóm chính thức: `V • 0 • 135 • 246 • 789` (Master Map) hay `V • D(D/500) • 000 • 135 • 246 • 789` (yêu cầu 18/11/2026)? | Giữ Master Map cho website Release 1. Ghi V và D là namespace nội bộ (theo `HUB69_5_GROUPS…`) cho đến khi có Change Proposal riêng | Navigation và Registry tiếp tục dùng Master Map |
| **HG-2** (C2) | Đổi tên Chương 6 thành "SI AI Robot Siêu Phần Mềm & Công Nghệ"? | Lập Change Proposal riêng, vì tên Chương xuất hiện ở nhiều tài liệu đã khóa | Giữ "AI & Công Nghệ" |
| **HG-3** (C3) | ID Cổng Tri Thức là `28882` hay `8882`? | Xác nhận `28882` là Canonical (đang có trang). Nếu `8882` là đúng, cần quyết định chuyển hướng | Trang `/8882/` hiện chỉ là trang dự phòng `/id/` |
| **HG-4** (C4) | Văn bản và ID của Luật Thép CFP+ | Nhập bản nguyên văn vào `governance/` theo Locked Documents Registry. Xác nhận ID (hiện `58` = "Tổ Chức trong Cộng Đồng") | Kiểm duyệt Diễn Đàn chưa có căn cứ văn bản |
| **HG-5** (C5) | Cây Siêu Bộ Đôi dùng quy tắc A (0–9, 1.110 vị trí) hay B (0 dành cho mở rộng, 910 vị trí)? | Quy tắc B, để nhất quán với `AI_INDEX.md` và genealogy schema. Khi đó con số "1.110" cần ghi lại thành "910 + slot mở rộng" | Validator chạy được cả hai chế độ |
| **HG-6** (C6) | Parent xác định bằng tham chiếu tường minh hay bằng cắt chữ số? | Cả hai: bắt buộc ghi tường minh **và** phải khớp tiền tố (validator đã áp dụng) | — |
| **HG-7** (C8) | ID Gemini: `691141` (registry JSON) hay `6911421` (thư mục trang)? | Registry custodian đối chiếu và sửa một nguồn | Danh bạ Diễn Đàn ghi Gemini là PENDING |
| **HG-8** | Định nghĩa chính thức: SI AI, Siêu Phần Mềm, Siêu Bộ Đôi, Phục Vụ Vô Vụ Lợi | Dùng [03_GLOSSARY_PENDING_VI.md](03_GLOSSARY_PENDING_VI.md) làm bản nháp | Mọi tài liệu ghi "định nghĩa đang chờ" |
| **HG-9** | Có công bố mẫu Diễn Đàn/Văn Phòng tại đường dẫn chữ `/docs/si-ai-platform/mockups/…`, trái với Numeric Link Rule (chỉ link số)? | Chỉ dùng để review qua GitHub/preview. Khi chính thức, gắn vào ID số đã được cấp | Trên trang chủ đã đặt nhãn "Mẫu" |
| **HG-10** | Phê duyệt merge PR này vào `main` | Merge **sau khi** có ít nhất 1 review độc lập (ReviewSI) và quyết định HG-9 | Website không thay đổi |
| **HG-11** | Thêm mục "Thông Báo • Bản Thử Nghiệm" trên trang chủ có vượt phạm vi Release 1 inventory contract không? | Coi là nội dung trong Homepage hiện hữu, không phải portal mới | — |
