# CFP+ • Bộ cài Siêu Bộ Đôi (Sandbox)

**SANDBOX PRACTICE GO • HOLD ACTIVATION • PRODUCTION NO GO**

## Một lệnh

```
node scripts/superpair-install.mjs [--sample 69103] [--out <thư mục evidence>]
```

Hoặc `npm run superpair:install`. Yêu cầu Node.js ≥ 22 (có `node:sqlite`). Không cần cài thêm package.

| Bước | Script | Dừng nếu FAIL |
|---|---|---|
| 1. Kiểm tra môi trường (chỉ đọc) | `scripts/env-doctor.mjs` | Node ≥ 22, `node:sqlite`, thư mục tạm, cổng 4173 |
| 2. Toàn bộ bộ test | 6 bộ: core 40, P2 10, P2 HTTP 5, Review Round 1 5, Training 2, Siêu Bộ Đôi 6 | có |
| 3. Siêu Bộ Đôi mẫu | `superpair-init.mjs --sample <ID>` | có |
| 4. Khởi tạo hàng loạt | `superpair-init.mjs --batch` | có |
| 5. Evidence | `install-report.json` + `.sha256` cho từng file | — |

## Khởi tạo từ Registry — quy tắc

- Nguồn: snapshot Registry đã ghim trong package (`registry.sourceCommit`). **Không cấp ID mới, không gắn Canonical ID** — danh tính bộ đôi vẫn `SYNTHETIC ONLY` (lõi chặn bằng `CANONICAL_ALLOCATION_FORBIDDEN`).
- Liên kết Registry nằm trong sidecar `registryRef` (ID, lineage, HUB 69, Permanent Link *tham chiếu*, 12 mô đun Văn phòng, giáo trình). `permanentLinkVerified=false`, `identityBound=false`.
- Phân loại: `SANDBOX_PRACTICE` (lineage nhất quán, chưa có evidence) → được thực hành; `HELD` (xung đột / quốc gia đang bị chặn) → chờ Human Governance; `NOT_IN_SNAPSHOT` → không tạo hồ sơ.
- Mỗi bộ đôi thực hành 4 kịch bản: `registry-audit` và `training-drill` × (bình thường → chờ người review độc lập; vượt quyền → BLOCKED). Chuỗi audit phải hợp lệ.
- Adapter SI chỉ `mock-local`; quyền chỉ `source.read`, `draft.write`. Không mạng, không tài khoản, không thanh toán.

## Chưa tích hợp

Diễn Đàn (nằm ở nhánh riêng), xác minh Permanent Link thật, danh tính thật, kích hoạt SI AI bên ngoài — đều cần Human Governance.
