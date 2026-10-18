# Website P0 • bàn giao mã nguồn và bằng chứng

**Draft PR #110 • Production NO-GO • không merge/publish.**

Repository: https://github.com/charityfundplus/CFP.plus

Nhánh hiện hữu: `review/numeric-link-restoration-20261008`.
Source đã kiểm thử: `779526404300e4f88a591d49da000674f50c9cc8`.
Commit render chính: `fa752ecbce380ff8d37ef53431d65458e316f00a`.
Các commit sau chỉ sửa validator/test và vị trí lưu browser evidence. Manifest
public output tại source cuối: `public-file-sha256.json`. Không tạo app/Registry/PR thứ hai.

## Mã nguồn và triển khai

- Trang chủ: `index.html`; Chương: `0/index.html` … `9/index.html`;
  bản đồ: `0123456789/index.html`; HUB: `69/index.html`.
- HTML/CSS tĩnh; nội dung chung: `content/site-standard.json`;
  generator: `scripts/build_foundation_pages.py`, `build_priority_pages.py`;
  public build: `scripts/build_public_site.py`.
- Candidate dùng Docker Python build → nginx port 8080, cấu hình `nginx.conf`.
  Main dùng Docker nginx copy root và fallback `/id/index.html`.
- GET production: 26/26 HTTP 200; 21 response khớp toàn bộ bytes của file main
  `835616308111f6851c0387fa9f5eda60c9ffa624`. Đây là bằng chứng đối chiếu
  nội dung, **không chứng minh deployed source SHA/branch/build provenance**.
- Revision/image digest/build ID/trigger/deployment principal/rollback target
  của Cloud chưa truy xuất được. Phiên không có GCP identity. Không khẳng định
  nhánh main là deployed branch chỉ dựa vào nội dung giống nhau.

## Thay đổi thực tế

- Bản đồ `/0123456789` dùng đúng V/000/135/246/789 và đủ 10 Chương từ cùng
  nguồn tên; bỏ việc group link mở Chương đầu tiên.
- Chương 6 bổ sung sứ mệnh, phạm vi Robot/Siêu Máy Tính, tham chiếu Việt Nam,
  link HUB/quốc gia/OpenAI/ChatGPT/khóa học. Nhãn theo mục
  `CẬP NHẬT TÊN CHƯƠNG 6 • HUMAN DIRECTIVE` trong Master, vẫn Review Candidate.
  Master còn nhãn lịch sử mâu thuẫn; native verification `unverified`.
- Link Mẫu Chuẩn được bổ sung vào template hiện hữu; HSTDN dùng tiếp mẫu
  Developer. Trường pháp nhân/đại diện/quyền chưa có Evidence giữ UNKNOWN.
  PR #142 tiếp tục là nơi review hồ sơ OpenAI; không ghi đè hồ sơ đó.
- Validator read-only kiểm tra ID chuỗi ASCII, số 0 đầu, key/id, DID khi có,
  Parent tồn tại/cycle, URL đúng domain/ID/protocol/query/fragment. Legacy slash
  ghi finding; không tự sửa source. Thiếu Parent/DID ghi finding.
- Diff `registry/` so với `c0c9d37` rỗng. Không đổi Canonical ID/Parent/DID,
  Canonical Lock, quyền, DNS hoặc production.

## Kiểm thử

- 24/24 unit/local HTTP tests PASS: 7 nội dung + 8 foundation + 6 identity +
  3 publication. `local-tests.txt`.
- Docker build và nginx syntax PASS; local image
  `sha256:a953918e0281a2ea233001c8467cd3305c351c3b71b02be60cfcfe6055f17734`.
  Đây là local image ID, không phải production registry digest.
- 1.399 nginx HTTP/content checks + 7 exposure checks PASS (`nginx-http.json`).
- Chromium desktop 1280px/mobile 390px: 2.852 checks/704 page-viewports PASS
  (`container-browser-evidence.json`). Chromium 390px không phải Safari/iPhone thật.
- `canonical-urls.json`: 351 URL numeric đã kiểm tra candidate HTTP và source
  readback; giữ riêng production observation và governance acceptance.
  V là informational view, không được cấp Canonical numeric ID.
- Codex 2 review độc lập: URL validation finding P2 đã sửa trong `a34888f`;
  6/6 tests PASS, không finding mới trong phạm vi fix. Đây là Codex review,
  không phải receipt Claude/Gemini (`codex2-review.md`).

## Registry đối chiếu và phần còn chặn

Đã đọc READ ONLY `CFP-REG-002 • CFP+ Master Registry v1.0`
(`57292852d4b04cd1876e38f09a72f5c6`): 13 dòng tài sản tài liệu, không phải
roster entity ID số. Nguồn yêu cầu một dòng/một Canonical Asset và quản lý
phiên bản qua Supersedes/Superseded By. Nguồn không cung cấp numeric
Parent/DID/HSTDN binding; không dùng trạng thái tài liệu để phê duyệt entity.
Receipt và giới hạn freshness: `master-registry-receipt.json` (native
verification unverified; last edited 2026-07-09). Không đổi dòng nào.

`master-source-rows.json` là trích xuất 84 dòng/83 ID từ Master Notion hiện hữu,
không phải Registry mới. Không xuất Agent refs/nội dung hồ sơ riêng. Native
verification của nguồn là unverified; không xác nhận 84 runtime.
`master-reconciliation.json` ghi kết quả so sánh ID chính xác:
0 ID giao với JSON entity26; 23 giao với snapshot25. Không dùng các tập khác
loại này để tính tỷ lệ coverage. 333 giữ hai dòng nguồn; 330 có hồ sơ riêng;
2624/2684 và 9624/9584 không remap. Parent/DID và identity binding cần custodian
đối chiếu/phê duyệt; không tạo hồ sơ để lấp khoảng trống.

Các blocker thực tế còn lại:

1. Cloud READ ONLY provenance, deployed revision/image/source/build/trigger và
   rollback target. Gemini có thể đối chiếu khi được cấp quyền phù hợp.
2. Production chưa có candidate: `/135`, `/246`, `/789`, `/6535`, `/8882` trả
   trang generic “CFP+ AI Office”; `/911` có client redirect. HTTP 200 không
   phải content PASS (`production-readback.json`, 26 GET).
3. Master identity/Parent/DID và HSTDN cần nguồn có thẩm quyền, đối chiếu các
   xung đột, review PR #124/#141/#142; không thay hồ sơ chưa duyệt.
4. Chưa có receipt Claude review độc lập hoặc Gemini Cloud review; chưa có
   nghiệm thu Safari/iPhone thật và Human Governance phê duyệt phát hành.

Chưa hoàn thành P0 production. Không yêu cầu merge/deploy để thay thế những
bằng chứng còn thiếu; giữ Draft và Production NO-GO.
