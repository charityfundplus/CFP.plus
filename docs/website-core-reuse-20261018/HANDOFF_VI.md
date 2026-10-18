# Core/UI tái sử dụng • PR #110 tiếp tục độc lập

**HOLD ACTIVATION • PRODUCTION NO-GO.** Gói local chưa mount, không phải
Staging hoặc bản Production. Không đổi Registry, ID, Parent, DID, quyền thật,
`/69`, `/8682`, Docker/nginx, DNS hoặc Origin.

## Mã thực tế

`scripts/prepare_core_reuse.py` xuất gói từ các Git object đã ghim:

Source mới đã kiểm thử: `8f4a3e76aebdff3119ecd3fa0e948061cda0e811`.
`RESULTS.json` ghim SHA-256 script/tests/workflow. Toàn bộ 360 public output
files vẫn khớp manifest của source0ec8555; không mount UI hoặc sửa trang thật.

- UI PR #141: `8ca11c26fbe3ba76db75ae1aa62b204744233d85`.
- Core/client PR #124: `06f386b1ba52358779cec6bc26c2d88f6a33664a`.
- Registry input cho build UI nguyên bản:
  `835616308111f6851c0387fa9f5eda60c9ffa624`; không xuất snapshot vào gói Core.

```bash
python scripts/prepare_core_reuse.py --output /tmp/cfp-core-ui-review
python tests/website/test_core_reuse.py
```

Output phải là thư mục mới ngoài source tree. Thư mục bundle có mode 0700;
chứa 10 UI assets chế độ Core, nguyên `registry-client.js` và `MOUNT_PLAN.json`.
Không tạo server, proxy, API, tài khoản hoặc môi trường triển khai. Manifest có
Git blob/SHA-256 nguồn và SHA-256 từng artifact. Client được kiểm tra với pin
đã có trong UI141. Core mode bắt đầu với `records:[]`, không fallback snapshot.
Quyền filesystem local không được mô tả là ACL/HTTPS Staging đã thiết lập.

## Tương thích đã xác minh

| Mối nối | Kết quả / ranh giới |
|---|---|
| UI → client | Dynamic import `/registry-client.js`, giữ nguyên source PR124 |
| Client → Core | `/api/core/**`, cookie same-origin, no-store; không token input/storage |
| Runtime phù hợp | `sandbox/p2-http.mjs` + `P2Sandbox`; không dùng demo `server.mjs` Bearer |
| Session | Login hiện hữu `/p2`, logout `/api/logout`; giữ cơ chế kiểm tra Host/Origin |
| Dữ liệu | 224 reference rows từ Core pin; không xác nhận 224 identity hoặc roster91 |
| Lỗi | 401/404/503 xóa stale data; không fallback sang Registry snapshot |
| Nhóm 000 / ID 0 | Nhóm điều hướng không remap ID; `#id/000` vẫn có thể 404 |
| Mount | Chưa có UI141 trong asset allowlist Core; relative assets cần review trước mount `/69` |

2/2 tests mới xác minh exact client bytes, zero snapshot rows, hash manifest,
no activation/payment, private local output và source không bị thay đổi.
6/6 tests HTTP loopback của UI141 chạy lại với đúng Core pin: anonymous401,
login/retry, provenance, 404, OpenAI/vault references, logout/revoke và503.
Chỉ dùng account/SQLite synthetic trong thư mục tạm của test, không tài khoản
hoặc quyền môi trường thật. Logs: `reuse-tests.txt`, `core-http.tap`.

CI tại HEAD cũ `0ec8555f06b1dd546b778c2fdc8351f85b82b145` đã hoàn tất 4 jobs,
gồm Production read-only collector: run `39124685009`. Collector SUCCESS không
có nghĩa Production content PASS. Không lấy CI cũ để chứng nhận source mới.

## Website • App • 8682

Một Core và một client là nguồn read model cho các bề mặt được duyệt. Website
có thể dùng các assets141 sau review mount vào HUB69 hiện hữu. App dạng web
surface có thể dùng cùng client khi nằm trong đúng origin/session policy;
native App hoặc cross-origin phải có auth design riêng được review, không
mặc nhiên chuyển cookie hoặc thêm Bearer/token vào client này.

8682 giữ ID hiện hữu và trạng thái source/pending. Manifest khai báo
`bindingVerified:false`, `ordersEnabled:false`, `paymentEnabled:false`.
Core pin chưa có verified commerce identity/tenant/merchant authority.
Không suy quyền bán hàng, đại diện, payment hoặc tình trạng hoạt động từ trang
`8682` có thể mở được. Không nhập module commerce synthetic của Core thành
dịch vụ thương mại thật.

Kiến trúc chuẩn bị tiếp theo tái sử dụng identity/provenance/auth/audit của Core;
module hàng hóa, inquiry, báo giá, đơn hàng và settlement chỉ được nối khi có
contract/quyền/dữ liệu được duyệt. Phân biệt dữ liệu nghiệp vụ với Canonical
identity; không cấp DID/ID Canonical mới để làm đầy sản phẩm/đơn hàng. Cần chốt
tenant isolation, idempotency, consent và retention trước write/payment.
Lượt này không thêm write endpoint hoặc thực hiện giao dịch.

## Phụ thuộc và trạng thái

| Phụ thuộc | Trạng thái | Evidence cần để tiếp tục |
|---|---|---|
| Cloudflare/Origin | BLOCKED BY ENVIRONMENT ACCESS | Chủ môi trường, scope READ ONLY, zone/proxy/origin config và receipt |
| Production revision/rollback | BLOCKED BY ENVIRONMENT ACCESS | Deployed revision, image digest, source/build ID, traffic split, rollback target tương thích |
| HTTPS Staging riêng tư | BLOCKED BY ENVIRONMENT ACCESS | Môi trường hiện hữu được chỉ định, URL, owner, scope vận hành và account kiểm thử |
| Core mount/Registry read | BLOCKED BY ENVIRONMENT ACCESS | Scope mount vào runtime hiện hữu, read-only checkout pin, Host/Origin/session policy |
| Safari iPhone | BLOCKED BY ENVIRONMENT ACCESS | Staging hợp lệ, thiết bị Safari thật, flow và receipts; Chromium390px không thay thế |
| Country routes | PENDING REGISTRY RECONCILIATION | Danh sách13 của source cũ + record/Parent/source authority; không tự cấp ID |
| Claude/Gemini review | NO RECEIPT | Review thực tế trên source/manifest cụ thể; không tự gắn ACK |
| SHA8a7dee7d… | SOURCE UNAVAILABLE FROM THIS SESSION | Original workspace hoặc branch/bundle nguyên SHA và ancestry |

Workspace gốc8a chưa truy cập được không có nghĩa đã mất vĩnh viễn. 13 country
routes, 3 remote CTTTC và các test count của source đó chưa được xác minh lại.
Yêu cầu bàn giao vẫn ở comment PR110 `6249568006`; không dựng lại hoặc thay thế
commit rồi tuyên bố tương đương. Codex2 review trong phiên này chỉ là reviewer
độc lập, không phải phiên đã tạo8a.

Để nghiệm thu khi môi trường được cung cấp: xác minh owner/scope và executable
pin → read-only Registry pin → private same-origin mount → anonymous denial /
authorized login → group/chapter/profile navigation → stale-data errors/logout
→ Safari iPhone screenshots/readback → review độc lập → Human Governance.
Giữ đường rollback đã xác minh và admission hiện có; chưa có quyền thì dừng ở
chuẩn bị local. Không tạo môi trường trùng lặp hoặc đổi ACL để đạt test PASS.
