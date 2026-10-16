# HUB 69 • Codex 2 • Giao diện P0

Tiếp tục giao diện HUB 69 hiện hữu từ source `6d2fd6f0c19ebaa0fcbfa53850bcce1b5bf7287f`. Module này đưa mã giao diện về repository CFP.plus để review và tích hợp; không tạo Site, HUB, Registry hay Core API mới. Site review hiện hữu giữ nguyên định danh và quyền truy cập. **HOLD ACTIVATION • PRODUCTION NO-GO.**

## Sử dụng bản review

Tại thư mục `hub69/ui`:

```bash
npm run build
npm test
```

Mở file được build `HUB69-review.html` để tra cứu offline; file chứa toàn bộ CSS/JS/dữ liệu. `dist/` là cùng giao diện dùng khi đóng gói Site. Chưa có URL HTTPS hoạt động. Không chạy server/API, adapter hoặc đồng bộ thật.

## Các chức năng đã triển khai

- Giữ giao diện Tổng quan, Master Hub, tra cứu ID, lưu mục và sao chép link mục.
- Thêm điều hướng đúng 5 nhóm **V • 000 • 135 • 246 • 789** và 10 chương 0–9. Nhóm điều hướng tách khỏi Canonical ID: `0`, `000` và `V` không được thay thế cho nhau.
- Cây **Chương → Con → Cháu** dùng chữ số đầu để phân loại Chương và `parent_id` được ghi trong nguồn để nối các bản ghi. Ví dụ có nguồn: **Chương 6 → OpenAI 69118 → ChatGPT 691181**. Việc đặt nhà phát triển dưới Chương trong giao diện không ghi thêm Parent vào Registry.
- Mỗi ID trong snapshot có hồ sơ riêng. Nhận biết trùng ID, Parent thiếu, vòng lặp, sai chương và quan hệ liên chương; giữ nguyên dữ liệu khi có finding.
- Khung Link Mẫu Chung hỗ trợ Siêu Bộ Đôi, phần mềm, SI, AI, Robot, nhà phát triển, HSTDN, doanh nghiệp, quốc gia, tổ chức và thực thể CFP+.
- Thành phần **Làm Dự Án tại ChatGPT** cho Siêu Bộ Đôi: tên, phạm vi, trạng thái, liên kết có receipt xác minh. Giữ ID của Siêu Bộ Đôi; không cấp ID dự án hoặc tạo URL. Hiện chưa có Siêu Bộ Đôi/project thật trong snapshot; xem cấu trúc tại `#template`.
- `#openai` là góc nhìn của Link Mẫu, tách OpenAI nhà phát triển và ChatGPT sản phẩm/AI. ID HSTDN, SI/Siêu Bộ Đôi liên quan và hợp tác chưa có nguồn được để chờ; không tạo thực thể HSTDN mới.
- `#vaults` trình bày 6 Kho, Evidence, lỗi/dữ liệu còn thiếu và thời điểm đồng bộ. GitHub chỉ là snapshot đọc được; Lượng Tử là RESEARCH; không có claim kết nối hoặc đồng bộ runtime.
- URL CFP+/Google Sites chưa được xác minh hiển thị bằng văn bản, không phát sinh link hoạt động. Link dự án chưa đủ receipt hoặc thuộc private không được xuất.

## Nguồn dữ liệu

Đọc trực tiếp **Registry hiện hữu** `registry/ai-entity-registry.json`, commit `835616308111f6851c0387fa9f5eda60c9ffa624`; build kiểm Git blob `1f18068d66379ce90bb079dc56c77b4c4d66dcdf` trước khi dùng. SHA-256: `a63c5e0b8af157b0938014d51da94ea924b9721acd0a11a9107f5deea3c6f507`.

**26 bản ghi nguồn = 20 nhà phát triển + 6 AI. 0 danh tính hoặc operator được thành phần này tự xác minh.** Không coi đây là Master Registry 91 Siêu Bộ Đôi. Snapshot và các trạng thái Review/Conflict không được nâng thành VERIFIED/ACTIVE. Khi export sang Site, bản sao evidence là đầu vào build đã ghim hash, không phải Registry có quyền ghi.

## Kiểm thử và giới hạn

39/39 kiểm thử Node/VM PASS: 14 kiểm tra nguồn/baseline UI hiện hữu, 19 kiểm tra P0 và 6 kiểm tra trạng thái ứng dụng với DOM stub. Có kiểm tra các hash route/link nội bộ, dữ liệu nguồn, ba tầng, dự án/riêng tư, OpenAI và trạng thái kho. Đây không phải browser rendering hay iPhone acceptance.

Browser/CSS rendering, screenshots mới, Safari/WebKit, iPhone thật, HTTPS/quyền truy cập và E2E Core API **chưa kiểm thử**. Phiên này không có `$control-browser`; Sites skill yêu cầu bỏ qua browser QA trong trường hợp đó, không khởi chạy một đường điều khiển trình duyệt khác.

Chỉ thêm `hub69/ui/**`; không sửa `/69`, `/id`, Registry, nhánh Codex 1, Core API hoặc Draft PR #124. Tích hợp lên cổng chính và nghiệm thu thiết bị là bước tiếp theo sau khi Codex 1 bàn giao read model/authority và môi trường được phê duyệt.
