# CFP+ • Codex 1 • Bàn giao Registry/Core API • 16/10/2026

**Runtime đã lấy lại từ GitHub và kiểm chứng:** `51e8a39d12615fcfff11a418d78bb81ce44ec591`.
**PR hiện hữu:** [#124](https://github.com/charityfundplus/CFP.plus/pull/124), Draft; không merge/deploy. Baseline đánh giá b75b780 giữ nguyên.

## Kết quả cụ thể

| Hạng mục | Kết quả / giới hạn |
|---|---|
| Nguồn Master | GitHub `registry/AI_CANONICAL_ID_REGISTRY.md` chỉ đúng các JSON gốc; `registry/SYNC_CURRENT_SYSTEM.md` quy định thứ tự nguồn. Đây là Review / Working Registry dưới CFP+ Human Governance, chưa phải Canonical Lock hay roster 91 được duyệt. API so khớp 6 tệp nguồn với Git/revision/hash. |
| 26 và 91 | JSON: 20 developer + 6 AI. Hai nguồn Notion hiện hữu: Master 84 dòng/83 ID; danh sách 91 REVIEW ONLY = 83 ID Master + 8 vị trí bổ sung. Giao ID chính xác với JSON26 bằng 0; khác phạm vi, không tính 26/91 thành độ phủ. Công cụ đối chiếu: 8/8 kiểm tra đạt; không nhập review vào runtime. Hai dòng nguồn 333 giữ nguyên. |
| API binding | Sửa launcher đóng gói để đọc **checkout Registry hiện hữu** qua path + revision do server cấu hình. Không chép Registry mới; thiếu nguồn/sai hash/HEAD đổi trả 503. Client cùng origin dùng cookie hiện hữu, từ chối dữ liệu cũ khi lỗi hoặc đổi revision trong lúc phân trang. |
| Link Mẫu | Panel `/p2` hiện hữu dùng client mới; luồng package → HTTP loopback → Registry → OpenAI → ChatGPT packet đã kiểm bằng socket thật. UI riêng của Codex 2 tại PR140 vẫn là snapshot, chưa mount/nối runtime và chưa được nghiệm thu browser. |
| HSTDN OpenAI | Bổ sung nguồn công khai về OpenAI, ChatGPT, Projects và hỗ trợ. Giữ chuỗi `911 → 6911 → 69118 → 691181`. Hồ sơ HSTDN là tham chiếu; ID/Parent/DID/Canonical HSTDN riêng vẫn null, không gán ID developer thành HSTDN. Không xác nhận partnership, SI, năng lực hay quyền; hold nhánh Hoa Kỳ giữ nguyên. |

**Kiểm thử mã ở đúng SHA trên:** 28/28 PASS, 0 FAIL, 0 SKIP (8 mới + 20 kiểm tra bị ảnh hưởng). Phạm vi: source binding, package launcher, HTTP socket thật, client/projection, auth/Origin/Host, cô lập workspace, read-only, Parent/zero/duplicate/cycle, release rollback và Office/training bị ảnh hưởng. Không chạy lại toàn bộ suite không đổi. Lệnh và output đầy đủ trong `TEST_RESULTS.tap`.

`BUILD_MANIFEST.json` đối chiếu 76 tệp runtime với Git; `REGISTRY_READBACK.json` giữ output validation/OpenAI từ source ghim. Git tree nguồn thực thi: `0677ad17c7a595c22952cefe872d95eaebc0c52e`. Root `registry/` không có diff so với đầu vào `0900cf51c0b8842bbeede4f5261bea51b6016c8f`.

Nguồn Notion chi tiết không đăng công khai trong PR. `RECONCILIATION_SUMMARY.json` chỉ chứa số tổng hợp và SHA-256 của gói đối chiếu riêng tư. Native Notion verification của hai trang là unverified; timestamp sửa trang hoặc hash nội dung không cấp quyền identity. Công cụ chỉ đọc, không sửa Master, tên, Parent, DID hoặc lịch sử.

## Phụ thuộc cần xử lý

1. **Codex 2:** dùng `public/registry-client.js` và [INTEGRATION.md](INTEGRATION.md) trên nhánh UI riêng; nối trước bootstrap, hiển thị provenance thật, dữ liệu OpenAI trả về và trạng thái 401/404/503/logout. Không coi snapshot PR140 là runtime đã nối.
2. **Human Governance / chủ quản Registry:** cung cấp hoặc xác nhận binding pair/HSTDN trong nguồn hiện hữu, record identity, Parent/DID theo evidence, revision/checksum, visibility và grants. Danh sách REVIEW ONLY đã đọc được nhưng chưa đủ thẩm quyền để bind.
3. **Chủ môi trường + Human Governance:** URL HTTPS riêng tư hiện hữu được phép, executable/source pins, tài khoản kiểm thử và quyền service **chỉ đọc** checkout Registry ghim. Không cần quyền ghi Registry cho API này. Chưa có môi trường/URL được cấp cho phiên; HTTPS Preview NOT AVAILABLE.
4. **Codex 2 + ReviewSI:** kiểm browser và Safari iPhone thật trên môi trường được phép; review đúng delta/SHA. Chưa có ACK hoặc acceptance độc lập được xác minh.

GitHub/Notion đọc được; không thiếu quyền đọc các nguồn đã dùng. Vấn đề còn lại là authority của runtime bindings, tích hợp UI và môi trường kiểm thử. Không xin mật khẩu/token, không tự mở quyền. 6 Kho chưa được chứng minh runtime sync.

**HOLD ACTIVATION • HUMAN REVIEW • PRODUCTION NO-GO.**
