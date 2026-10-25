> Current P1 evidence supersedes historical browser BLOCKED statements below: 16/16 actual browser checks PASS for commit 50d17cc; see P1_DECISION_PACK.md.

# Chạy, nhân rộng, giám sát và nâng cấp • Step by Step

## Local quick start

1. Cài Node.js 22+; vào drafts/si-office. Không cần API key/runtime dependencies.
2. Chạy `npm test`: regression office + standard-core tests, no sockets required.
3. Chạy `npm run demo:core`: sample creates a website draft, independent demo acknowledgement, denied-tool training, recovery, synchronized metadata upgrade and rollback.
4. Chạy `npm start` trên máy được phép mở socket loopback. Mở http://127.0.0.1:4173/core; office cũ vẫn ở `/`. Không expose public.
5. Chọn Editor demo, giữ pair hub69-content-demo. Nhập synthetic draft, chọn normal, Create queued task → Run supervised. Xem 16 axis checks, staged draft artifact và audit.
6. Chọn Reviewer demo (phiên riêng), Acknowledge draft hoặc Reject draft. Đây không phải Governance approval.
7. Nhấn Revise as new draft để đưa text cũ vào form; sửa và tạo task mới. Output cũ và audit được giữ nguyên trong process.
8. Instantiate training-demo từ cấu hình. Tạo training-drill với scenario overreach/false-claim/bad-evidence/error/timeout; kiểm tra stop, null output, alert và training evaluation.
9. Reviewer → Recover khi pair STOPPED và quiescent. FAILED/INTERRUPTED task có Explicit retry, vẫn giữ lịch sử cũ. BLOCKED không được retry để vượt policy.
10. Instantiate us-hstdn-demo; chạy hst-us-draft. Profile/products/services hoàn toàn giả lập, source/capability/legal NOT VERIFIED.
11. Xuất/audit qua GET /api/core/state trong phiên demo hoặc chạy CLI. Kiểm tra manifest: `node scripts/verify-evidence.mjs`.

## Tạo thêm cặp bằng cấu hình, không copy source

1. Tạo thêm entry trong configs/pairs.json trên nhánh draft, dùng key local duy nhất. Có thể copy dữ liệu mẫu; không copy/rewrite engine.
2. Giữ mode=sandbox, protocol=1, mock provider, synthetic identity/null Canonical fields. Không gán ID/DID/Parent từ khoảng trống.
3. Chọn group/chapter/field/country/HSTDN, owner và missions đã hỗ trợ. Source.read là quyền tối thiểu; thêm draft.write chỉ khi mission cần ghi bản nháp. Resource phải thuộc KnowledgeEvidence allowlist.
4. Không nhập credential hoặc source private thật. Nguồn fixture mới là dữ liệu giả lập có provenance và hash; reviewed specialty module có thể mở rộng renderer/adapters sau kiểm thử, không tạo provider authority mới.
5. Chạy tests và config review; restart local draft để load danh sách mới. Giao diện tự liệt kê template, instantiate cùng một CoreEngine.
6. Real verified identity, model API, vault scope hoặc production mode vẫn BLOCKED dù tests đạt. Cần quyết định/evidence riêng.

## Nâng cấp và rollback demo

1. Kết thúc hoặc dừng các task đang chờ/chạy; review/reject các output AWAITING HUMAN REVIEW. Không xóa history để ép quiescence.
2. Reviewer chọn 0.1.1-sandbox → Upgrade cohort (metadata). Tất cả pair module-version maps đổi đồng bộ.
3. Thử 0.2.0-incompatible / 0.1.2-fault-sandbox để xác nhận previous cohort được giữ khi preflight fail.
4. Rollback cohort để restore version checkpoint; audit/version history tiếp tục tăng, không reset.
5. Đây là metadata-only rehearsal. Nâng cấp mã thực: chuẩn bị source/release manifest, review compatibility, backup durable data/audit, chạy regression và staging/browser checks, rồi chờ Human Governance. Draft này không tải/chạy binary từ release URL.

## Environment limits

Current execution sandbox blocks socket/browser launch (EPERM). In-process handler tests and CLI passed. Browser tests/core-browser.mjs is prepared for a permitted local environment; no current browser pass claimed. Memory resets on process restart; no production persistence, auth, durable audit or self-learning model training exists. Passing exercises cannot grant rights.
