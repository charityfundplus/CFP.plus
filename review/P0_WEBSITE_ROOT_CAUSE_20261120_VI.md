# P0 • Nguyên nhân Website CFP+ khó cập nhật • Evidence 2026-11-20

Người thực hiện: Claude Code • Nhánh: `claude/cfp-website-hub69-update-j56w9f`
Trạng thái: **SANDBOX • REVIEW CANDIDATE • KHÔNG MERGE / KHÔNG DEPLOY khi chưa có Human Governance**

## 1. Kết luận chính

**Hệ thống triển khai KHÔNG hỏng.** Website chưa cập nhật vì **không có thay đổi nào vào `main` từ 2026-09-28** (53 ngày), và vì cách viết trang hiện tại buộc mỗi bài viết phải sửa HTML thủ công.

## 2. Evidence

| # | Kiểm tra | Kết quả |
|---|---|---|
| E1 | `curl -I https://cfp.plus` | `server: Google Frontend` (Cloud Run), `last-modified: Mon, 28 Sep 2026 13:01:59 GMT` |
| E2 | Commit cuối `main` | `8356163` lúc 13:01:51 UTC 28/09/2026, tức 8 giây trước E1, nên `main` → production tự triển khai đang hoạt động |
| E3 | So sánh byte live và `main`: `/`, `/69/`, `/000/`, `/6911/`, `/6984/`, `/28882/`, `/267/`, `/9/`, `/6/` | **Giống hệt 9/9**. Production đang chạy đúng `main` |
| E4 | PR đang mở | 31 PR, gần như tất cả Draft/HOLD/“KHÔNG MERGE”; nhiều PR xếp chồng lên nhánh sandbox khác (#195 → #234, #214, #215, #216; #203 → #206 → #207) |
| E5 | Cách tạo trang | 158 file `index.html` viết tay; 75/158 trang không dùng header chung; thanh điều hướng khác nhau giữa các trang; không có template hay bước build |
| E6 | `website/*.md` trên live | Trả về `application/octet-stream`, nên iPhone tải file xuống thay vì hiển thị; nội dung Markdown không trở thành trang web |
| E8 | **SHA production (đã xác minh 20/11/2026)**: `https://cfp.plus/.git/FETCH_HEAD`, `/.git/refs/heads/master`, `/.git/logs/HEAD` | Đều là `835616308111f6851c0387fa9f5eda60c9ffa624` = HEAD `main`. Clone lúc `1790600519` = **2026-09-28 13:01:59 UTC**, khớp `last-modified`. File chỉ có trong commit đó (`registry/691186.md`) live giống hệt `main` |
| E9 | Build lịch sử 28/09 “deploy FAILED” (ảnh Console do Human Governance cung cấp, #235) | **Không phải lỗi hiện tại.** Revision đang phục vụ chạy đúng HEAD `main` (E8). 9 commit được push trong 20 giây (13:01:31 đến 13:01:51), có thể kích hoạt 9 build chồng nhau. *Giả thuyết, chưa chứng minh*: một deploy cũ bị thay thế hoặc xung đột. Cần log Cloud Build để xác nhận (workflow `gcp_readonly_evidence.yml`) |
| E7 | **Bảo mật** `https://cfp.plus/.git/config` | **200**, lộ cấu hình git. Nguyên nhân: Dockerfile `COPY .` không có `.dockerignore`. Cùng lý do, `/Dockerfile`, `/.github/workflows/*` và `/tests/*` cũng công khai |

## 3. Nguyên nhân gốc (Root Cause)

1. **Quy trình:** Không có đường “nội dung nhỏ, rủi ro thấp” để vào `main`. Mọi thay đổi bị gộp chung với backend, forum và Supabase trong PR lớn đang HOLD, nên nội dung website cũng bị giữ theo.
2. **Kỹ thuật:** Mỗi bài viết là một file HTML sao chép tay. Người biên tập phải sửa mã nguồn, dễ lệch giao diện và khó review.
3. **Hiển thị:** File Markdown không được render.

## 4. Sửa lỗi tối thiểu trong nhánh này

| Thay đổi | Tác dụng |
|---|---|
| `content/pages/<ID>.md` + `tools/build_pages.py` | Thêm hoặc sửa trang bằng **một file Markdown**. Breadcrumb, Trang Con (Con • Cháu), SEO và canonical được tạo tự động. Chỉ dùng thư viện chuẩn Python |
| Kiểm tra an toàn khi build | ID chỉ gồm chữ số (giữ số 0), Parent phải tồn tại, cấm 66666, cấm khóa lạ, **không ghi đè 158 trang viết tay**, chặn HTML/script và link `javascript:`. Lỗi ở bất kỳ file nào thì không xuất bản gì |
| `Dockerfile` (multi-stage) | Build trang Markdown trước khi đóng gói nginx. Nếu build lỗi, image không được tạo và bản đang chạy giữ nguyên |
| `.dockerignore` | Đóng lỗ hổng `/.git`, `/Dockerfile`, `/.github`, `/tests` |
| nginx | `.md` trả về `text/plain; charset=utf-8`, đọc được trên iPhone |
| `.github/workflows/website_content.yml` | CI **chỉ kiểm tra**: validate, unit test, build image thật, smoke test. Không deploy, không ghi repo |

Không thay đổi Canonical ID, Parent, Registry, DNS hay production. Không cấp ID mới.

## 5. Kiểm chứng đã chạy (sandbox, Docker cục bộ)

- Unit test: **15/15 PASS** (`python3 -m unittest discover -s tests/website`)
- Hồi quy: build image `main` cũ và image mới; **158/158 trang hiện có giống hệt byte**. Route số dự phòng `/12345678/` → `/id/` giữ nguyên.
- Image mới: `/Dockerfile`, `/.github/...`, `/tests/...` từ 200 chuyển thành **404**; `.md` chuyển từ `octet-stream` sang `text/plain; charset=utf-8`.
- E2E: tạo tạm `content/pages/6900099.md` → `/6900099/` và `/6900099` trả 200; `<script>` bị vô hiệu; link `javascript:` bị bỏ. Ở khổ iPhone 13 (Chromium giả lập, **không phải Safari thật**): không cuộn ngang, 0 lỗi console. Trang tạm **đã xóa, không commit**.

## 6. Giới hạn và việc còn lại

- Chưa xác minh trực tiếp pipeline Cloud Run/Cloud Build (không có quyền GCP READ ONLY). Kết luận “tự deploy” dựa trên E1, E2 và E3. Cần người có quyền GCP xác nhận trigger build dùng Dockerfile ở gốc repo.
- Chưa kiểm thử trên iPhone Safari thật.
- `sitemap.xml` chưa tự thêm trang Markdown mới.
- Đa ngôn ngữ (3366): đã có trường `lang`; chưa có bộ chuyển ngôn ngữ.
- Lịch sử chỉnh sửa và khôi phục: dùng lịch sử Git và Cloud Run revision, không cần CMS riêng.

## 7. Đề nghị Human Governance quyết định

1. **Tách làn “Website Content”**: PR chỉ chạm `content/pages/**` và CI xanh thì được review và merge riêng, không chờ backend #195 hay forum.
2. **Ưu tiên merge riêng `.dockerignore`** (sửa bảo mật E7), độc lập với phần còn lại.
3. Chỉ định người có quyền GCP xác nhận pipeline build trước khi merge thay đổi Dockerfile.
