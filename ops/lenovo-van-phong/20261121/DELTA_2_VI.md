# CFP+ • HUB 69 • Delta 2 • 21/11/2026 (sau bàn giao tổng hợp)

Claude Code • phiên cloud sandbox • SANDBOX PRACTICE GO • PRODUCTION NO GO. Chỉ ghi phần **mới**; báo cáo trước: `REPORT_VI.md`.

| # | Việc | Trạng thái | Bằng chứng (thư mục này) |
|---|---|---|---|
| 1 | Lenovo: cổng 4173 + Chrome | **BLOCKED**: lúc 15:10 UTC vẫn chưa có thư mục Remote Control nào được chia sẻ cho phiên này | `list_computer_folders` = rỗng |
| 2 | Manifest mới cho PR #124 @ `e994ea8`, manifest cũ giữ nguyên | **VERIFIED** | `manifest/` |
| 3 | PR #236 D1: nhánh riêng + Draft PR chỉ chứa bản vá bảo mật | **VERIFIED (sandbox)**; merge/deploy: **HUMAN GOVERNANCE** | `evidence/secmin-smoke.txt`, `evidence/secmin-layer2.txt` |
| 4 | PR #236 D2: tách làn Website Content | **HUMAN GOVERNANCE** (quyết định quy trình) | PR #236 |
| 5 | PR #236 D3: danh sách quyền GCP READ ONLY | **PENDING phê duyệt** (danh sách đã sẵn; không tự cấp) | `ops/GCP_IAM_LEAST_PRIVILEGE_VI.md` trên PR #236 |
| 6 | PR #236 D4: Cloud Build dùng Dockerfile gốc | **REPORTED** (bằng chứng gián tiếp); xác nhận trực tiếp **BLOCKED** (chưa có quyền đọc GCP, chờ D3) | `evidence/d4-indirect.txt` |
| 7 | Canva DAHZcr4iJj4 | **VERIFIED (chỉ đọc)**: không sửa | mục 7 |
| 8 | Work Order có review độc lập thật | **PENDING**: chờ ReviewSI / SecuritySI | — |

## 2. Manifest mới (không ghi đè manifest cũ)

- Tệp: `manifest/PR124_HEAD_E994EA8_MANIFEST.json` + `.sha256` + `verify.mjs`.
- Cùng 88 đường dẫn với manifest lịch sử, băm lại tại `e994ea884fdf7a06ca5efe20674b96a0d51e24f8`. Ghi rõ thời điểm, commit nguồn, sha256 của manifest cũ, và danh sách 13 tệp đổi (hash cũ/mới + commit gây đổi).
- Kiểm chứng hai chiều:
  - `node verify.mjs <si-office @ e994ea8>` → **VERIFIED 88/88**.
  - `node verify.mjs <si-office @ d4d83ec>` → **MISMATCH 13/88**, đúng 13 tệp đã báo. Đối chiếu chéo khớp.
- `drafts/si-office/docs/ROUND1_CURRENT_MANIFEST.json` **không bị sửa**. Manifest mới nằm ngoài nhánh PR #124; Codex (chủ PR #124) có thể đưa vào nhánh đó nếu được đồng ý.

## 3. D1: Bản vá bảo mật tối thiểu

- Nhánh mới `claude/security-min-dotgit`, tạo từ `main` `8356163`, commit `c2f2b8e`. Chỉ 2 tệp (`.dockerignore`, `Dockerfile`, +23 dòng), đúng `security-min.patch` của PR #236.
- Build image thật (Docker trong sandbox) + `tools/smoke_test_site.sh` của PR #236: **43 PASS, 0 FAIL, RESULT: ALL PASS**. Image không chứa `.git`, `Dockerfile`, `tests`.
- Lớp 2 tự đứng được: build lại **bỏ `.dockerignore`** và cố ý đặt `.git/config` giả vào image. Nginx vẫn trả 404 cho `/.git/config`, `/%2egit/config`, `//.git/config`; `/` và `/69/` vẫn 200.
- Repo không có tệp dấu chấm nào được phục vụ công khai (ngoài `.github/`), nên luật `location ~ /\.` không chặn nội dung hợp lệ.
- Production lúc 15:26 UTC: `/.git/config` vẫn trả **200** (chỉ đọc mã trạng thái, không tải nội dung). Lỗ hổng vẫn mở cho tới khi Human Governance merge + deploy.

## 6. D4: bằng chứng gián tiếp

- `https://cfp.plus/Dockerfile` (đang bị lộ) **trùng byte** với `Dockerfile` gốc trên `main` (sha256 `b569826a…`). Không có `cloudbuild.yaml` trong `main`.
- Điều này cho thấy image được build với ngữ cảnh là thư mục gốc (`COPY .`). **Chưa chứng minh** cấu hình trigger (tên trigger, đường dẫn Dockerfile, nhánh). Cần quyền đọc từ D3 để chạy workflow `gcp_readonly_evidence.yml` của PR #236.

## 7. Canva: thiết kế chính duy nhất (chỉ đọc)

- `canva.link/3vziu16fkw4m4m6` → `DAHZcr4iJj4`, tên "Website CFP+ App, Sàn TMTC, CTTTC và Diễn Đàn SI AI", 1 trang, tạo 30/10/2026, **cập nhật lần cuối 21/11/2026 15:16 UTC** (không phải do phiên này; phiên này chỉ đọc).
- Trang là Canva Code: API trả nội dung rỗng và không sửa được (khớp comment ngày 06/11). Không tạo thiết kế mới, không sửa, không xóa.
- Kiểm kê các thiết kế cũ: **PENDING** (cần chủ tài khoản Canva xác nhận phạm vi thư mục).

## Bước kế tiếp

1. Human Governance: xem Draft PR D1 (merge + deploy là quyền của Human Governance). Sau deploy, chạy `tools/smoke_test_site.sh https://cfp.plus`.
2. Lenovo: bật Remote Control, hoặc chạy `lenovo-check.mjs` (xem `REPORT_VI.md` mục 4).
3. ReviewSI / SecuritySI: review độc lập Draft PR D1 và vòng Work Order PR #195, có danh tính và timestamp.
4. Sau khi D3 được phê duyệt: chạy workflow read-only để đóng D4.
