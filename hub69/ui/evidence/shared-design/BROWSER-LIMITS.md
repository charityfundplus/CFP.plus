# Browser / thiết bị • BLOCKED

Không có screenshot/video browser hay iPhone được tạo trong đợt này.

- Firefox 153.0 (Playwright firefox 1538) tải được; `firefox.launch()` thành công.
- Tạo browser page không hoàn tất trong 15 giây. Harness ghi `BLOCKED`, 0 browser assertions, 0 screenshot, 0 video. Không nhận responsive/axe PASS.
- Chromium và Chromium headless shell tải về archive không hợp lệ; không chạy được.
- WebKit 26.5 tải được nhưng thiếu shared libraries. `install-deps webkit` không thực hiện được setgroups/setegid/seteuid trong môi trường hiện tại; không thay cấu hình bảo vệ để vượt lỗi.
- Physical Safari iPhone, Android và HTTPS staging: chưa được bàn giao. Không có deploy hoặc thiết bị thật để nghiệm thu.

Bản `HUB69-review.html` là Preview offline thực tế có thể mở sau build; đây không là screenshot hoặc URL staging. Chạy lại `integration/browser-review.mjs` trong môi trường QA hỗ trợ, rồi kiểm thử thiết bị thật theo checklist.
