# CFP+ P0 • 25/10/2026

HOLD ACTIVATION • PRODUCTION NO-GO • PR124 Draft/unmerged.

## Đã hoàn thành

- CoreEngine hiện hữu: một vòng đăng ký → ghi nhận 5 bài học → training-drill → feedback → reviewer synthetic riêng → lưu Evidence → mở lại SQLite và đọc lại. Hai Siêu Bộ Đôi `hub69-content-demo` / `training-demo` chạy đồng thời ở hai database; 44 kiểm tra expected/observed PASS. Token/task/pair truy cập chéo bị từ chối. Có kiểm tra thêm cùng database khác workspace, cùng workspace khác pair. Không tuyên bố kiểm chứng shared-DB concurrency nhiều process.
- Chuẩn hóa 5 kho theo `SYNC_FIVE_STORES_PLAN.json`: Notion/GitHub/Google/MCP/CMP. `core/store-status.mjs` cung cấp cùng dữ liệu cho `P2Sandbox.adapters()` và generator HUB69. Website là projection, không thêm kho thứ sáu hoặc đổi cấu trúc Registry. Kế hoạch Office có tập kho khác được giữ nguyên như hồ sơ lịch sử; đây không phải quyết định Governance về source of truth.
- HUB69 có bảng HTML đọc được khi tắt JS: tên/link/owner/quyền và scope/thời điểm/Evidence/đồng bộ; dữ liệu JSON tải riêng. Trường thiếu giữ UNKNOWN/null; mọi kho giữ NOT VERIFIED, adapters disconnected, zero external calls. GitHub source evidence không được coi là vault-sync receipt. Link Notion/Drive nội bộ không được công khai thêm trong bảng.
- Chromium local: 25 kiểm tra PASS, màn hình 320/375/390/430/1280, không tràn ngang toàn trang, bảng cuộn ngang có keyboard focus, không page error; 5 dòng còn đọc được khi tắt JS. Đã xem ảnh và sửa tên kho bị ngắt từng ký tự. Screenshot đặt sticky header về static khi chụp riêng section; không đổi hành vi trang khi chạy.
- Live Firecrawl `maxAge=0`: HUB `/69` và 7 route `/69/`, `/000/`, `/0/`, `/6/`, `/6911/`, `/691181/`, `/28882/` trả HTTP200. Nội dung production đọc được chưa có training/status của draft. Không chứng nhận deployed SHA hoặc mọi route toàn website.

## Evidence

- Baseline từ PR124: `06f386b1ba52358779cec6bc26c2d88f6a33664a`. Git clone lỗi proxy; phục hồi 93 file qua GitHub connector, đối chiếu exact Git blob, dựng lại cây Git và commit gốc bằng hash. Không coi snapshot tự tạo là SHA gốc; original commit thực sự khớp SHA.
- Runtime được đọc lại từ GitHub và thực thi: `1958a3ff04c17dfa6c61d5dbde9dd51b46f98640`. 9 file delta khớp byte/Git blob. `RUNTIME_RECEIPT.json` có 44 checks; `p0-team-0.json` / `p0-team-1.json` giữ taskKey, output, executionReceipt, manifest, feedback, registration và audit checkpoint sau readback. Không lưu password/token/database thật.
- Browser source: `599852c304a321abb9f134fb244d69cda4bbef42` (chỉ thêm mobile CSS + browser test sau runtime1958). `BROWSER_RECEIPT.json`, 2 PNG preview, `LIVE_ROUTES.json`, `BASELINE_SOURCE_READBACK.json` và `MANIFEST.json` đi cùng hồ sơ này. Commit chứa Evidence không phải deployed SHA.
- 2/2 tests mới status và 21/21 tests hồi quy PASS tại runtime1958: P2 10, HTTP/release 5, Office intake 6. Số 44 là checks tích hợp, 25 là browser checks; không cộng thành số unit tests. Không chạy lại cohort12 bài tập hoặc historical assessments để thay bằng chứng thiếu.
- ID/Parent/DID/Canonical và root Registry không bị sửa. Lịch sử audit cũ không bị ghi lại; chỉ database synthetic riêng có event mới. Hai registration synthetic giữ identity fields null; competency NOT ASSESSED, authorityVerified=false, activationAllowed=false.

## Tái lập

Tại checkout runtime1958, chạy từ repository root, dùng thư mục output chưa tồn tại:

```sh
node drafts/si-office/tests/p0-20261025-flow.mjs /tmp/NEW-cfp-p0-round
node drafts/si-office/tests/store-status.test.mjs
node drafts/si-office/tests/p2.test.mjs
node drafts/si-office/tests/p2-http.test.mjs
node drafts/si-office/tests/office-intake.test.mjs
```

Browser tại source599852, cần Python Playwright và Chromium `/usr/bin/chromium`, quyền loopback:

```sh
python drafts/si-office/tests/p0-hub69-browser.py /tmp/NEW-cfp-p0-browser
```

Generator projection: `node drafts/si-office/scripts/render-hub69-stores.mjs`. Chỉ chỉnh config nguồn rồi generate lại; JSON và HTML được test khớp runtime. Generator không kết nối kho hoặc xác nhận receipt.

## Blocker

- iPhone Safari thật chưa kiểm thử. Chromium mobile viewport không phải Safari.
- Chưa có stable private HTTPS preview / deployed-SHA receipt được cấp cho đợt này. PNG và local loopback là preview đã kiểm thử; không có preview công khai mới. Không deploy để vượt HOLD.
- Các kho chưa có đủ public approved target/owner/actor grant, exact payload revision/hash và current content readback/review. `checkedAt=null` có nghĩa chưa kiểm chứng vận hành; thời điểm chạy test nằm trong receipt, không thay thời điểm kiểm tra từng kho.
- Chưa có phản hồi review độc lập GrokSI/Claude chính danh cho delta này. Chưa chứng minh báo cáo Grok gốc từ một URL/receipt riêng; triển khai theo chỉ đạo và điểm nghẽn CFP+ cung cấp, không ghi ACK/approval thay reviewer.
- Real pair/assessor binding và nghiệm thu năng lực thật vẫn thiếu; synthetic reviewer không thay Human Governance. MCP/CMP không được gọi vận hành hoặc tự cấp quyền.

## Việc tiếp theo

GrokSI đối chiếu runtime1958, task/output digest, 44 checks và source readback. Claude ReviewSI đọc-only source599852, scope/isolation, trạng thái kho và manifest; ghi finding cụ thể theo path/SHA/expected/observed trên PR124 hoặc Issue130. CMP điều phối theo quyền thực tế; owner cung cấp target/scope/receipt còn thiếu. Chạy actual iPhone Safari và HTTPS readback khi có môi trường/thiết bị. Mọi merge/production deploy/Governance change tiếp tục cần phê duyệt riêng.
