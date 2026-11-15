# Codex 1 • P0 sandbox • 16/10/2026

**Đã triển khai và kiểm thử tại runtime commit `62e0e5f3b4156eab44e02f065f0bb62061905518`.**
Nhánh `codex/si-office-p0-draft-20261013`, Draft PR #124. Baseline được giữ để đánh giá `b75b780eb64430355f0b51a4b58b9e5269e0db43` không thay đổi. HOLD ACTIVATION • PRODUCTION NO-GO.

| Phần bàn giao | Kết quả kiểm chứng | Giới hạn còn lại |
|---|---|---|
| Core Registry API | Đọc trực tiếp 5 nguồn gốc có Git revision/blob/hash; tra cứu tên/ID, lọc loại/Chương, Cha/Con/Cháu; kiểm tra trùng, thiếu Parent, vòng lặp, sai lineage | 224 mục đọc được = 99 Country + 99 AI Country + 20 Developer + 6 AI; **không phải 91 Bộ Đôi đã xác minh**. Chưa có SI/HSTDN/pair bindings có thẩm quyền |
| HSTDN OpenAI mẫu | Hồ sơ tham chiếu `911 → 6911 → 69118 → 691181`; giới thiệu, sản phẩm tham chiếu ChatGPT, hướng dẫn Dự án, giới hạn, đào tạo, Evidence và trạng thái 6 Kho | ID/Parent/DID/Canonical của HSTDN riêng đều null. Hold mapping Hoa Kỳ được giữ. Không xác nhận đối tác, danh tính, kênh liên hệ hoặc vận hành |
| Làm Dự Án tại ChatGPT | API tạo hướng dẫn dùng đúng ID số và Link Mẫu hiện hữu; UI module đã nối vào `/p2` | Chuyển giao thủ công vào Dự án do người dùng chọn; không tự tạo project/ID/URL. Cặp synthetic chưa có ID giữ nút bị chặn |
| HUB 69 dữ liệu | Checkpoint SQLite nhất quán → RSA-OAEP/AES-GCM → replica thư mục riêng → readback → restore sang DB mới; bảo toàn output/audit và thu hồi session | Chỉ filesystem sandbox. Chưa đồng bộ cloud/6 Kho, chưa off-host custody/WORM/RPO/RTO thật; adapter thật vẫn tắt |
| Quyền backup | Chặn full-DB export từ maintainer chỉ có quyền một số pair và từ editor | Không thay đổi tài khoản/quyền hiện hữu |

## Kiểm thử mới và phần bị ảnh hưởng

```sh
cd drafts/si-office
node --test --test-reporter=tap tests/registry-read-model.test.mjs tests/registry-http.test.mjs tests/registry-loopback.test.mjs tests/hub69-data.test.mjs tests/p2.test.mjs tests/p2-http.test.mjs
```

**29/29 PASS, 0 FAIL, 0 skipped**: 14 ca mới + 15 hồi quy P2/HTTP bị ảnh hưởng. Lượt cuối chạy trên commit runtime đã ghim; `tests.tap` là output thực. Bao gồm HTTP loopback thật, auth/session/Origin/Host, dữ liệu workspace, bảo toàn số 0 đầu, V/0/000, metadata giả, nguồn bị sửa và restore không ghi đè.

`api-examples.json`: 5/5 response HTTP thật đã đăng nhập, chỉ dữ liệu public từ Registry, không chứa cookie/mật khẩu. Server local đã dừng; đây không phải URL Preview đang hoạt động.

**Browser QA BLOCKED**: Playwright có sẵn nhưng thiếu Chromium executable; tải Chromium trả ZIP không hợp lệ. `browser-results.json` có `pass=false`, không có browser check PASS. Không khẳng định đã kiểm UI, mobile, Safari hay iPhone thật. Script chuẩn bị: `node tests/registry-browser.mjs docs/p0-20261016` sau khi môi trường có Playwright/Chromium hợp lệ.

## Nguồn và Evidence

- Runtime manifest: `runtime-provenance.json`, 73 tệp runtime so khớp Git; SHA-256 manifest `55f832d1c4e7e67b2d3ec586150f02824ed4cd9e7d9df94c55e5ba1b46c1babb`.
- 11 tệp code/test đã thay đổi: `source-file-manifest.json`. Không thay nội dung `registry/`.
- Snapshot đọc: `registry-validation.json`, `openai-profile.json`, `chatgpt-project.json`. Chỉ là Evidence đã xuất; runtime không đọc các snapshot này và không xem chúng là Master Registry khác.
- Hash nguồn chứng minh byte/revision; không tự xác nhận identity, grant, năng lực hoặc quyền Human Governance.
- Tham khảo Dự án đã đọc: https://learn.chatgpt.com/docs/projects . Không giả định deep link tạo Dự án hoặc API quản lý Dự án.

## Bàn giao Codex 2 / ReviewSI / GrokSI

Hợp đồng tích hợp ở `CORE_API_CONTRACT.md`. Codex 2 dùng chính Core API và module hiện có; không tạo API/Registry khác. Nhánh `codex2/p1-evidence-registry-links` trả 404 khi đọc qua GitHub ở lượt này, nên chưa nhập hoặc xác nhận bản bàn giao Codex 2. Chưa có phản hồi kiểm tra độc lập của ReviewSI/GrokSI cho delta này.

**Có thể làm ngay:** chạy API trên checkout sandbox đầy đủ, tích hợp UI Codex 2 theo contract, kiểm browser khi có binary, đối chiếu các finding với Registry custodian. Không đợi nguồn 91 để dùng phần tra cứu hiện có, đồng thời không bổ sung ID/Parent bằng suy đoán.

**Đang chặn:** nguồn 91 Bộ Đôi có authority; HSTDN ID và SI bindings; nguồn/quyền/URL 6 Kho; HTTPS Preview được duyệt; browser/Safari/iPhone; review độc lập. Registry source adapter yêu cầu checkout có Git và 5 đường dẫn nguồn gốc. Release chỉ đóng gói `drafts/si-office` sẽ trả 503 cho API Registry; cần giải quyết nguồn được duyệt trước phát hành, không dùng snapshot thay thế âm thầm.

Không merge, deploy, tạo tài nguyên trả phí, mở rộng truy cập hoặc bật production trong đợt này.
