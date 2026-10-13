# CFP+ • Global SI AI Office • Implementation Draft

Ngày 13/10/2026 • P0 • HUB 69 duy nhất • PRODUCTION NO-GO.

Bản mẫu Node.js không dependency runtime: 12 phân hệ responsive, đăng ký theo Registry snapshot, bản ghi giả lập, draft/review, role demo, export JSON, audit hash chain. Đây là prototype vận hành thử; CRM, hợp đồng, thương mại và các module khác dùng chung cấu trúc bản ghi nháp, chưa phải sản phẩm đầy đủ.

## Chạy và thử

1. Cài Node.js 22+.
2. Tại thư mục này chạy `npm test`.
3. Chạy `npm start`.
4. Mở **http://127.0.0.1:4173** trên máy chạy server. Không phải URL public. Không mở cổng ra Internet.
5. Chọn vai trò demo; đăng ký hồ sơ giả với Country Canada và developer có sẵn. Chưa cấp ID/DID/Canonical.
6. Tạo bản ghi có Evidence HTTPS → Gửi review → đổi vai trò Người review → Review demo. Kết quả chỉ là DEMO REVIEWED, không phải xác minh danh tính.
7. Chọn Người xem để kiểm tra quyền; thử thanh toán và kết nối để thấy server từ chối.
8. Xuất JSON để review; restart server xóa toàn bộ dữ liệu và phiên.

Không nhập dữ liệu khách hàng thật, API key hoặc tài liệu mật. Checkbox là khai báo, không thể tự phát hiện mọi dữ liệu cá nhân. Role selector là công cụ test, không phải authentication production. Các cửa sổ trình duyệt dùng chung state demo của server.

Browser test tùy chọn: cài Playwright ngoài runtime của app, chạy `node tests/browser.mjs`; biến `PLAYWRIGHT_MODULE` hỗ trợ đường dẫn module có sẵn, `CHROMIUM_PATH` chọn Chromium, `PREVIEW_URL` chọn loopback. Không thêm workflow deploy.

## Bàn giao

- [Thiết kế và tích hợp](docs/ARCHITECTURE.md)
- [Nguồn, finding và rủi ro](docs/EVIDENCE_REVIEW.md)
- [Bảng đối chiếu và quyết định](docs/STATUS.md)
- [Ảnh desktop](docs/desktop.png) / [Ảnh điện thoại](docs/mobile.png)
- [Test API](docs/api-test-results.txt) / [Test browser](docs/browser-test-results.txt)

Nhân bản bằng cách copy thư mục, thay dữ liệu giả lập và giữ ID/DID/Canonical null. Không dùng copy để cấp định danh. Snapshot Registry chỉ là nguồn kiểm tra có phiên bản; không thay thế authority hiện hành.

## Triển khai sau này — Human Governance

Bản này chỉ chạy local. Trước staging phải có review độc lập và quyết định phạm vi; trước production cần identity provider, RBAC server theo tenant, database có backup/retention, consent/privacy, secret manager, OAuth scopes, CMP authorization, audit store độc lập, rate limiting, validation nghiệp vụ từng module và kiểm thử tích hợp thực tế. Canonical route chỉ `https://cfp.plus/<ID>` sau phân bổ hợp lệ; không `/hub/69/...`. Không merge/publish/deploy trong phạm vi bàn giao này.
