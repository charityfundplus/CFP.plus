# 05 • Kết Quả Kiểm Thử & Evidence

**Trạng thái:** REVIEW CANDIDATE • Kiểm thử trong sandbox • Chưa có review độc lập
**Thời điểm chạy:** 2026-11-18T22:50Z (UTC)
**Môi trường:** container sandbox Linux, Node v22.23.5, Python 3, Chromium + Playwright có sẵn, máy chủ tĩnh `python3 -m http.server` tại `127.0.0.1:8080`, phục vụ thư mục gốc repository
**Nhánh:** `claude/gracious-cray-9d8av1` (commit SHA được ghi trong Pull Request)

## 1 • Tóm tắt

| # | Kiểm thử | Lệnh | Kết quả | Evidence |
|---|---|---|---|---|
| T1 | Validator cây Siêu Bộ Đôi (11 ca) | `node --test docs/si-ai-platform/tools/validate-super-pairs.test.mjs` | ✅ **11/11 PASS** | [evidence/validator-tests.tap](evidence/validator-tests.tap) |
| T2 | Dữ liệu quy hoạch 10 slot gốc | `node docs/si-ai-platform/tools/validate-super-pairs.mjs` | ✅ 0 lỗi • 10 node Tầng 1 • 0 ID được cấp | [evidence/validator-report.json](evidence/validator-report.json) |
| T3 | JSON Schema hợp lệ (Draft 2020-12) + 10 node đạt schema | `jsonschema` (Python) | ✅ 0 lỗi | Chạy tay, ghi tại đây |
| T4 | Liên kết, bảo mật, viewport trên 3 file thay đổi | `node docs/si-ai-platform/tools/site-check.mjs` (xem mục 2) | ✅ **0 lỗi** | [evidence/site-check.json](evidence/site-check.json) |
| T5 | Song ngữ VI/EN cân bằng | như trên | ✅ forum 59/59 • office 31/31 | như trên |
| T6 | Giao diện điện thoại 360 px và 390 px (3 trang × 2 độ rộng) | `node docs/si-ai-platform/tools/mobile-check.mjs http://127.0.0.1:8080 …` | ✅ **6/6 PASS**: không cuộn ngang, 0 lỗi console, nút VI/EN hoạt động, vùng chạm ≥ 44 px | [evidence/mobile/mobile-check.json](evidence/mobile/mobile-check.json) + ảnh chụp |
| T7 | Hồi quy CTTTC hiện hữu | `python3 run_ctttc_v066_tests.py` | ✅ **204/204 PASS** | Không thay đổi file CTTTC |
| T8 | Truy cập thực tế các trang Canonical | `curl` tới `https://cfp.plus/...` | ⚠️ Xem mục 3 | Ghi tại đây |
| T9 | Toàn site (baseline, chỉ báo cáo) | `site-check.mjs` | ⚠️ 2 liên kết hỏng có từ trước • 52 liên kết số dùng trang dự phòng `/id/` | [evidence/site-check.json](evidence/site-check.json) |

Không chạy được: **Safari trên iPhone thật** (môi trường không có thiết bị Apple). T6 dùng Chromium giả lập di động, không thay thế cho kiểm thử trên iPhone thật.

## 2 • Nội dung kiểm tra bảo mật (T4)

- `target="_blank"` luôn đi kèm `rel="noopener"`.
- Không có liên kết `http://` không mã hóa, không có `javascript:` URL.
- Không có chuỗi giống khóa bí mật (AWS, GitHub, Slack, private key, `sk-…`).
- Mẫu giao diện: có **Content-Security-Policy** (`default-src 'self'`, `form-action 'none'`, `base-uri 'none'`), không có script inline, có `noindex,nofollow`, không có form, không thu thập dữ liệu.
- `lang.js` chỉ đọc/ghi `localStorage` cho tùy chọn ngôn ngữ, có `try/catch`.

## 3 • Truy cập thực tế `cfp.plus` (T8) • 2026-11-18T22:50:11Z

| URL | HTTP | TTFB | Tiêu đề trả về | Nhận xét |
|---|---|---|---|---|
| https://cfp.plus/ | 200 | 0,75 s | CFP+ • Only Plus+ For Life | 7.101 byte, trùng kích thước `index.html` trên `main` (chưa có thay đổi của PR này) |
| https://cfp.plus/69 | 200 | 0,68 s | 69 • HUB 69 • Cổng Duy Nhất CFP+ | Đạt |
| https://cfp.plus/28882/ | 200 | 0,40 s | 28882 • CTTTC • Cổng Tri Thức Toàn Cầu | Đạt |
| https://cfp.plus/8882/ | 200 | 0,58 s | **CFP+ • AI Office** | ⚠️ Không có trang riêng. Đây là trang dự phòng `/id/` (11.377 byte, giống hệt `/58/`). Xác nhận xung đột **C3** |
| https://cfp.plus/8682/ | 200 | 0,43 s | 8682 • CFP+ Global Trade | Đạt |
| https://cfp.plus/267/ | 200 | 0,43 s | CFP+ • 267 • CMP & MCP | Đạt |
| https://cfp.plus/6/ | 200 | 0,44 s | 6 • AI • CFP+ | Đạt |
| https://cfp.plus/0123456789/ | 200 | 0,40 s | 0123456789 • 5 Nhóm • 10 Chương CFP+ | Đạt |
| https://cfp.plus/691121/ | 200 | 0,39 s | 691121 • Claude • CFP+ | Đạt |
| https://cfp.plus/58/ | 200 | 0,39 s | **CFP+ • AI Office** | ⚠️ Trang dự phòng `/id/`, không phải Luật Thép. Xác nhận xung đột **C4** |
| https://cfp.plus/docs/si-ai-platform/mockups/forum.html | 404 | 0,42 s | 404 Not Found | Đúng như kỳ vọng: PR chưa merge, chưa deploy |

Đo một lần từ một vị trí sandbox. Chưa đo LCP/INP/CLS và chưa đo từ nhiều khu vực.

## 4 • Vấn đề còn tồn tại

| # | Vấn đề | Mức | Có từ trước? |
|---|---|---|---|
| R1 | `267/index.html` và `2676/index.html` trỏ tới `/assets/style.css`, file này không tồn tại | Trung bình | Có |
| R2 | 52 liên kết số không có thư mục riêng, được phục vụ bởi trang dự phòng `/id/`. Người đọc thấy HTTP 200 dù trang chưa có nội dung | Trung bình | Có |
| R3 | Xung đột ID Gemini: `registry/ai-entity-registry.json` ghi `691141 = Gemini`, nhưng thư mục `691141/` là "Google Cloud AI" và trang Gemini nằm ở `6911421/` (**C8**) | Cao | Có |
| R4 | Trang chủ ghi "Nhóm 000", trái với Master Map (**C7**) | Thấp | Có |
| R5 | Chưa có văn bản Luật Thép, chưa có định nghĩa chính thức các thuật ngữ | Cao | Có |
| R6 | Route API cho Siêu Bộ Đôi và Diễn Đàn mới ở mức thiết kế, chưa code vào Core vì PR #124 vẫn là Draft | — | Mới |
| R7 | Chưa kiểm thử Safari trên iPhone thật, chưa có review độc lập (ReviewSI) | — | Mới |
| R8 | Mẫu Diễn Đàn và Văn Phòng chỉ là giao diện tĩnh, dữ liệu mô phỏng | — | Mới, có chủ đích |

## 5 • Cách chạy lại

```bash
node --test docs/si-ai-platform/tools/validate-super-pairs.test.mjs
node docs/si-ai-platform/tools/validate-super-pairs.mjs
node docs/si-ai-platform/tools/site-check.mjs --json /tmp/site-check.json
python3 -m http.server 8080 --bind 127.0.0.1 &   # tại thư mục gốc repository
node docs/si-ai-platform/tools/mobile-check.mjs http://127.0.0.1:8080 /tmp/mobile
python3 run_ctttc_v066_tests.py
```

Mã băm SHA-256 của các file đã kiểm thử: [evidence/SHA256SUMS.txt](evidence/SHA256SUMS.txt).

---

## 6 • Lượt 2 • 2026-11-18T23:04Z • Notion + PR #124 + Danh Bạ

| # | Kiểm thử | Lệnh | Kết quả | Evidence |
|---|---|---|---|---|
| T10 | **Core PR #124 chạy trong sandbox**, ghim SHA `e994ea8` | `npm test` trong `drafts/si-office` | ✅ **40/40 PASS** | [evidence/pr124-baseline-npm-test.tap](evidence/pr124-baseline-npm-test.tap) |
| T11 | Bộ test Registry của PR #124 (read-model, binding, http) | `node --test tests/registry-*.test.mjs` | ✅ **15/15 PASS** (6 + 6 + 3) | [evidence/pr124-baseline-registry.tap](evidence/pr124-baseline-registry.tap) |
| T12 | **91 Siêu Bộ Đôi Notion chạy trong `createRegistryReadModel` của PR #124** | `CFP_PR124_ROOT=… node --test tools/pr124-integration.test.mjs` | ✅ **8/8 PASS**: 91 bản ghi, 0 finding, `registryWrites=0`, `activationAllowed=false`, giữ số 0 đầu (`003`), không suy Parent | [evidence/pr124-integration.tap](evidence/pr124-integration.tap) |
| T13 | Kiểm tra thật 91 link `cfp.plus/<ID>/` | `node tools/link-audit.mjs` | 19 OWN_PAGE • 72 ID_FALLBACK • 0 lỗi HTTP | [evidence/link-audit.json](evidence/link-audit.json) |
| T14 | Danh Bạ trên điện thoại 360/390 px: hiển thị đủ 91 dòng, lọc Chương 6 = 9, tìm "luat thep" (không dấu) → 4742, VI/EN | `tools/mobile-check.mjs` | ✅ **8/8 PASS** (4 trang × 2 độ rộng) | [evidence/mobile/mobile-check.json](evidence/mobile/mobile-check.json) |
| T15 | Liên kết, bảo mật, song ngữ (4 file, có thêm `super-pairs.html`) | `tools/site-check.mjs` | ✅ 0 lỗi • VI/EN 65/65, 32/32, 19/19 | [evidence/site-check.json](evidence/site-check.json) |
| T16 | Validator cây + hồi quy CTTTC | như lượt 1 | ✅ 11/11 • 204/204 | [evidence/validator-tests.tap](evidence/validator-tests.tap) |

**CI trên PR #232:** không có check run nào. Workflow của repo (`ctttc_ci.yml`) chỉ chạy khi `schemas/` hoặc `tests/ctttc/` thay đổi. **Review:** 0 bình luận, 0 review tại 2026-11-18T23:04Z.

**Chưa kiểm thử:** Safari trên iPhone thật; route HTTP `/api/core/super-pairs` trên server P2 của PR #124 (chưa thêm, vì không sửa nhánh PR #124); kết nối SI AI thật.

---

## 7 • Lượt 3 • 2026-11-18T23:16Z • 6 Kho + thí điểm

| # | Kiểm thử | Kết quả | Evidence |
|---|---|---|---|
| T17 | Mô-đun làm việc: tất định, phát hiện đúng các xung đột đã biết | ✅ **4/4 PASS** | `tools/work-modules.test.mjs` |
| T18 | **Thí điểm qua PR #124 P2Sandbox**: 3 task, review độc lập, 4 lần từ chối, audit hợp lệ | ✅ **1/1 PASS** (cùng file test, cần `CFP_PR124_ROOT`) • receipt: 3/3 REVIEWED DRAFT, audit 23 sự kiện | [evidence/pilot/pilot-run.json](evidence/pilot/pilot-run.json) |
| T19 | Thăm dò 6 Kho (chỉ đọc) | 2 CONNECTED • 2 PARTIAL • 2 PENDING | [data/six-stores-inventory.json](data/six-stores-inventory.json) |
