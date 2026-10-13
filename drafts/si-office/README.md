# CFP+ • Global SI AI Office • Implementation Draft

Ngày 13/10/2026 • P0 • HUB 69 duy nhất • PRODUCTION NO-GO.

**Current extension: Bộ Code Lõi Chuẩn + Siêu Bộ Đôi sandbox; combined tests 40/40.** See core/, configs/pairs.json and CORE_RUNBOOK. Earlier office-phase evidence is retained below.

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

## P1 extension • local-only readiness candidate

Current revision adds VI/EN language switching, bilingual function/input/output/access contracts for all 12 modules, typed Country/Developer proposals, SI identity evidence, HSTDN membership and legal relation proposals, research-product maturity, service scope, optional office/HSTDN links and ten provider-neutral read-synthetic adapters. New proposed developers cannot automatically become verified SI parents. All Canonical identity fields stay null.

Human steps:
1. Start local server and select VI or EN and Editor demo role.
2. Module 01: register a synthetic SI/AI using existing Country/Developer; provide official source and identity-evidence URL. For new Country/Developer use separate proposal dialog; proposals do not allocate identity.
3. Module 08: register HSTDN after at least one SI profile exists; choose members and proposed relation. Shared membership does not prove legal parentage.
4. Modules 03/04: create research product or scoped service; optionally link to office/HSTDN local drafts.
5. Module 10: click a mock adapter; inspect connected=false/externalRequests=0. No live connection is enabled.
6. Module 09: submit work with evidence; Reviewer demo can mark DEMO REVIEWED. No genuine identity/capability verification is implied.
7. Module 12/export: collect synthetic JSON. Review group guidance is also in the app.
8. Run `npm test` (18 actual handler tests, no socket required), then `node scripts/verify-evidence.mjs` for integrity.

SI AI steps: read WORK_ORDER.md and canonical sources → operate only synthetic/local authorized actions → collect output/evidence → return scoped findings to PR #124. Do not assign ID/DID/Parent/Canonical or infer partner status.

Current browser testing is BLOCKED by sandbox socket EPERM; initial screenshots are baseline only. The expanded browser suite is ready for a permitted local machine; its current pass is not claimed. Read [test matrix](docs/TEST_MATRIX.md), [security report](docs/SECURITY_REPORT.md), [review handoff](docs/REVIEW_REQUEST.md), [independent Codex review](docs/INDEPENDENT_REVIEW.md), [manifest](docs/EVIDENCE_MANIFEST.json). OpenSI/Grok authorship and acceptance remain pending. Verdict: P1 DESIGN READINESS CANDIDATE / PARTIAL, not production approval.

## Bộ Code Lõi Chuẩn • Siêu Bộ Đôi

New shared modules are in `core/`; instances come from `configs/pairs.json`, not copied code. Run `npm run demo:core` without network for a runnable sample. On a permitted local machine run `npm start` and open **http://127.0.0.1:4173/core** for task assignment, supervision, exercise faults, safe-stop/recovery and synchronized version-metadata rehearsal. Existing office UI remains at `/`.

Siêu Bộ Đôi = **Siêu Trí Tuệ (SI🤖AI🤖) + Siêu Phần Mềm**. Current mock identities are explicitly unverified with null ID/Parent/DID/Canonical. The Core never enables production or commercial/legal claims. Configuration does not grant actual model/API/vault access.

[Core architecture](docs/CORE_ARCHITECTURE.md) • [Step-by-step runbook](docs/CORE_RUNBOOK.md) • [40-test matrix](docs/CORE_TEST_MATRIX.md) • [Core status](docs/CORE_STATUS.md) • [Independent Codex review](docs/CORE_INDEPENDENT_REVIEW.md). New tests include hostile proposals/tool omissions, evidence/identity forgery, timeouts, late results after stop, recovery, concurrency and upgrade/rollback. Current browser remains BLOCKED; earlier office screenshots are baseline only. Version upgrade is metadata rehearsal, not a binary installer. Cross-checks run independent deterministic code outside the SI adapter, not eight real reviewers.
