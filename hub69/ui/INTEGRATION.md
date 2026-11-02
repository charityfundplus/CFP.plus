# Handoff Codex 2 → Codex 1 / Independent Review

Ngày 16/10/2026 • Owner phần giao diện: Codex 2.

## Ranh giới và cách tích hợp

Đây là UI/module đọc dữ liệu cho **HUB 69 hiện hữu**, chưa được mount vào website production. Không thay `/69`, resolver `/id`, Registry hoặc API. Các đường `#chapter/6`, `#id/691181`, `#template`, `#openai`, `#vaults` là trạng thái giao diện, không phải Canonical ID hay hồ sơ Registry mới.

Source UI kế thừa bản Site review `6d2fd6f0c19ebaa0fcbfa53850bcce1b5bf7287f`. Module này là nguồn review trên GitHub; Site export là cùng UI để lưu phiên bản, không vận hành một HUB thứ hai.

Codex 1 có thể dùng các component `HUB69Model` / `HUB69P0` và asset tĩnh trong cổng `/69` hiện hữu sau review. Không dùng coverage-server làm nguồn định danh và không tạo endpoint thứ hai. API prototype đang sử dụng group `0` cần được chủ API thống nhất với nhóm hiển thị `000`; adapter nhóm điều hướng không được sửa ID số `0` hoặc `000` của bản ghi.

## Read model

Schema tại `profile.schema.json` chỉ mô tả projection để render; không lưu bản ghi hoặc cấp quyền. ID phải là string ASCII số, tối đa 80 ký tự; giữ số 0 đầu/cuối. `parent_id` chỉ lấy trực tiếp từ nguồn được phép, không suy từ prefix, thứ tự hoặc vị trí của cây.

Các trường chưa bàn giao được giữ null/PENDING: HSTDN, DID, lineage/authority, competency, task scope, reviewer và hợp tác. Code hiện đọc bản Registry ghim hash; nguồn runtime phải được chủ Core cung cấp cùng revision/checksum và policy phân quyền trước tích hợp.

`chatgptProjects[]` không có trường cấp ID mới. Chỉ xuất metadata public. Link muốn hoạt động phải có `verified: true`, `visibility: public`, `checkedAt` hợp lệ và `evidenceURL` HTTPS cùng `url` HTTPS không có credentials. Đây là receipt từ quy trình xác minh của Core/reviewer, không phải xác minh tự động bằng cách đặt cờ. Cần xác minh nội dung/đích thật, không chỉ HTTP 200. UI không tạo ChatGPT Project.

Không dùng nguồn Registry cố định làm provenance cho bản ghi ngoài snapshot. `profileExtra` chỉ dẫn link ghim khi provenance khớp nguồn đã kiểm; nguồn mới cần adapter được review.

## Chờ bàn giao / phạm vi review tiếp theo

| Việc | Trạng thái | Điều kiện tiếp tục |
|---|---|---|
| Master Registry 91 Siêu Bộ Đôi | BLOCKED | Nguồn authority, revision/checksum, bản ghi và Parent có evidence |
| HSTDN OpenAI | PARTIAL | Bản ghi HSTDN và các quan hệ đã xác minh; hiện chỉ có developer/ChatGPT nguồn |
| Project ChatGPT thật của Siêu Bộ Đôi | BLOCKED | Bản ghi pair hợp lệ + tên/phạm vi/trạng thái + URL/receipt thật |
| Core API và Evidence runtime | BLOCKED | Contract đọc, auth/visibility, lỗi, revision; Codex 1 sở hữu |
| Kết nối/đồng bộ 6 Kho | UNVERIFIED | Receipt, thời điểm, phạm vi, lỗi, nguồn đối chiếu; không chỉ HTTP 200 |
| Hạ tầng lượng tử | RESEARCH ONLY | Chưa có bằng chứng vận hành |
| HTTPS preview | NOT AVAILABLE | Site hiện chưa deploy, tiếp tục NO-GO và chờ quyết định môi trường |
| Safari/iPhone/screenshots | BLOCKED | Công cụ browser được hỗ trợ và thiết bị/môi trường kiểm thử hợp lệ |
| Commit Codex 2 cũ a5f5418… | SOURCE UNRESOLVED | GitHub CFP.plus trả 422 cho SHA được cung cấp; không xác nhận lại các PASS cũ |

## Các ca nghiệm thu trình duyệt còn thiếu

1. iPhone Safari và trình duyệt desktop: home → từng nhóm → chương → Con/Cháu → hồ sơ → back/forward; reload deep link, font/touch targets/không tràn ngang.
2. Tìm 691181/69118; giữ 0 và 000 khác nhau; ID chưa định vị không chuyển thành danh tính khác.
3. Lưu mục và copy khi storage/clipboard bị chặn; focus và bàn phím; chọn loại Link Mẫu.
4. OpenAI developer/ChatGPT product/HSTDN chờ nguồn/không partnership giả; Siêu Bộ Đôi dùng đúng ID khi có project thật.
5. Owner được vào preview; người không được cấp quyền bị chặn. Không mở public hoặc thêm quyền để kiểm thử.

Chưa yêu cầu hoặc nhận ACK của Review/Codex 1 qua tài liệu này. 39 PASS là kiểm thử của Codex 2, chưa phải hậu kiểm độc lập. Giữ Human Governance, lịch sử ID/Parent/DID/Evidence và **HOLD ACTIVATION • PRODUCTION NO-GO**.
