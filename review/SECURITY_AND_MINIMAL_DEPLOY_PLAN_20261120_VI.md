# Bản vá lộ `.git` / tệp nội bộ • Evidence và phương án triển khai nhỏ nhất

Trạng thái: **SANDBOX VERIFIED • PENDING REVIEW • PENDING HUMAN GOVERNANCE**. Chưa merge, chưa deploy.
Liên quan: #235, PR #236. Evidence: `review/evidence/20261120-security/` (có `SHA256SUMS.txt`).

## 1. Hiện trạng production (đo read-only ngày 20/11/2026)

`tools/smoke_test_site.sh https://cfp.plus`: **FAIL**. Có 12 đường dẫn nội bộ trả về 200:

| Đường dẫn | Ảnh hưởng |
|---|---|
| `/.git/config`, `/.git/HEAD`, `/.git/FETCH_HEAD`, `/.git/logs/HEAD` | Lộ SHA, thời điểm build, tên host build |
| **`/.git/index`** | Lộ danh sách toàn bộ file. Kết hợp với `/.git/objects/...`, có thể tải lại toàn bộ repo |
| `/%2egit/config`, `/%2Egit/config`, `//.git/config` | Biến thể mã hóa, cùng lỗ hổng |
| `/.github/...`, `/Dockerfile`, `/tests/...`, `/run_ctttc_v066_tests.py` | Lộ cấu hình CI/build |

**Đánh giá mức độ:** repository `charityfundplus/CFP.plus` đang public, nên lượng thông tin lộ thêm hiện ở mức thấp. Rủi ro thật nằm ở tương lai: nếu một lần build có file bí mật trong thư mục làm việc (`.env`, token trong `.git/config`), file đó sẽ bị công khai ngay. Cần vá trước khi mở rộng nội dung và tích hợp.

## 2. Bản vá: hai lớp độc lập

| Lớp | Cơ chế | Kiểm chứng riêng lớp |
|---|---|---|
| L1 `.dockerignore` | `.git`, `.github`, `Dockerfile`, `tests`… không được đưa vào image | CI GitHub (checkout có `.git` thật): `/.git/config` → 404. Lệnh liệt kê file trong image: không còn file ẩn |
| L2 nginx `location ~ /\.` → 404 | Không phục vụ bất kỳ file hoặc thư mục bắt đầu bằng dấu chấm, kể cả `%2e` và `//` (nginx giải mã và chuẩn hóa URI trước khi so khớp) | Image cố ý **bỏ** `.dockerignore` (có `.git` bên trong): `/.git/config`, `/.git/index`, `/%2egit/config`, `//.git/config`, `/.github/...` đều trả 404 |

Bổ sung: `server_tokens off` (ẩn phiên bản nginx), `X-Content-Type-Options: nosniff`, `Referrer-Policy`, file `.md` trả `text/plain; charset=utf-8`.
**Cố ý không thêm** `X-Frame-Options` và CSP, vì có thể làm hỏng việc nhúng trang (mirror `cg.cfp.plus`, Notion, Canva). Nếu cần, trình riêng.

## 3. Kết quả kiểm thử (Docker, clone git thật như Cloud Build)

| Image | Smoke + exposure | Kiểm tra file trong image | 158 trang hiện có |
|---|---|---|---|
| `main` (công thức production hiện tại) | **FAIL**: tái hiện đúng lỗi live | có `.git`, `.github` | (chuẩn so sánh) |
| PR #236 (đầy đủ) | **ALL PASS** (42 mục) | sạch | 158/158 giống hệt |
| `security-min.patch` (chỉ bản vá) | **ALL PASS** | sạch | 158/158 giống hệt |
| Chỉ nginx, không `.dockerignore` | `.git` bị chặn | (`.git` vẫn có trong image) | — |

## 4. Phương án triển khai nhỏ nhất (đề xuất trình Human Governance)

**Bước 1: chỉ bản vá bảo mật.** `review/evidence/20261120-security/security-min.patch`: 2 file (`.dockerignore`, `Dockerfile`), +23 dòng. Không có pipeline nội dung, không có stage Python. Routing giữ nguyên.

1. Human Governance cho phép tạo một PR riêng từ patch này (cần quyền đẩy một nhánh mới; nhánh hiện tại của Claude Code chứa toàn bộ #236).
2. CI xanh, ReviewSI review, Human Governance merge.
3. Cloud Build tự build và deploy (theo cơ chế đã xác minh ở E8 trong báo cáo P0).
4. **Nghiệm thu thực tế:** `tools/smoke_test_site.sh https://cfp.plus` phải báo `RESULT: ALL PASS`. Đây là bằng chứng production đã cập nhật.
5. **Rollback:** revert PR trên GitHub (tự deploy lại), hoặc `gcloud run services update-traffic cfp-plus --region asia-southeast1 --to-revisions <REV_TRUOC>=100` (người có quyền Cloud Run thực hiện). Revision cũ vẫn còn trong Cloud Run.

**Bước 2: pipeline nội dung Markdown** (phần còn lại của #236). Làm sau Bước 1, khi có xác nhận trigger Cloud Build dùng Dockerfile ở gốc repo (D4).

## 5. Điểm cần ReviewSI phản biện

- R1: `location ~ /\.` cũng chặn `/.well-known/`. Hiện site không dùng đường dẫn này; chứng chỉ TLS do Google quản lý không cần nó. Nếu sau này cần (ví dụ xác minh domain), phải thêm ngoại lệ.
- R2: Sau Bước 1, `/.git/FETCH_HEAD` không còn đọc được. Việc xác minh SHA production chuyển sang workflow `gcp_readonly_evidence.yml`, nên cần IAM Giai đoạn 1.
- R3: Lỗi deploy lịch sử 28/09 chưa được giải thích bằng log (cần quyền Cloud Build). Nếu nguyên nhân là xung đột khi nhiều build chạy cùng lúc, một lần merge đơn lẻ sẽ không gặp lỗi này.
- R4: Lịch sử Git đã từng bị lộ. Đề nghị rà soát: repo có từng chứa bí mật không (secret scanning).
