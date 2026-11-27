# CFP+ 6776 • Shared Evidence Bus

**SANDBOX PRACTICE GO • HOLD ACTIVATION • PRODUCTION NO-GO**

[Work Order #178](https://github.com/charityfundplus/CFP.plus/issues/178#issuecomment-7208547103)

Dùng chung FastAPI, CMP, MCP stdio, Worker và SQLite của 6789. Các tool MCP
gọi API loopback hiện có. Gateway CFP+ và Registry giữ cấu hình hiện tại.

- Cấp token riêng cho từng ID trong cấu hình sandbox. Thiết lập `work_orders`
  ở hồ sơ bên giao để giới hạn mã lệnh và `backends` để giới hạn tác vụ.
  Thêm ánh xạ `evidence_grants[ID bên giao][mã lệnh]` chứa `recipient` và
  `reviewer`. Ba ID đã đăng ký phải khác nhau. ID dạng chuỗi giữ số 0 đầu.
- Cấu hình `SUPER_QUANTUM_Z_EVIDENCE_KEY` trên API với khóa ngẫu nhiên riêng
  tối thiểu 32 byte. Giữ khóa trong bản sao lưu hạn chế quyền và chuyển cùng
  bản sao SQLite khi phục hồi.
- Bên giao gửi CMP Work Order, chờ Worker hoàn tất rồi gọi `publish_handoff`.
  Bên nhận gọi `read_handoff`, đối chiếu SHA-256 và gửi `acknowledge_handoff`.
  Reviewer duyệt qua `review_handoff`. Mỗi lần ghi dùng giao dịch SQLite.
- API kiểm tra HMAC-SHA-256 và hash đầu ra khi đọc lại. Reviewer kiểm tra
  nội dung và gửi kết luận `accepted` hoặc `needs_changes`.
- Khi đồng bộ ngoài sandbox, chỉ chuyển liên kết Evidence và kết quả công
  khai được phép. Đọc lại qua GitHub hoặc Notion để xác minh từng đích.

## Kiểm thử

Chạy `python -m pip install -r mcp-requirements.txt` rồi
`python -m pytest -q test_mcp_recovery.py`. Test đi qua MCP stdio với bốn
client có token sandbox riêng, Worker OR-Tools và API được dừng rồi khởi động
lại. Các ID trong test là fixture. Kết nối SI AI liên nền tảng cần token
được cấp thật và lượt ghi, đọc lại từ chính phiên được cấp quyền.

## Kiểm tra chéo

6776 và 87788 đối chiếu cấu hình và triển khai. Claude Code rà đường thực thi
và Evidence. 87783 kiểm tra độc lập theo Work Order.
