# CFP-CLOUD • Phương án quyền tối thiểu (least privilege) cho kiểm chứng tự động

Trạng thái: **ĐỀ XUẤT • PENDING HUMAN GOVERNANCE**. Tài liệu này không tự cấp quyền.
Liên quan: #235, #176

| Mục | Giá trị |
|---|---|
| Project | `CFP-CLOUD` / `abiding-robot-507708-i3` |
| Cloud Run service | `cfp-plus` • `asia-southeast1` |
| Nguồn | `charityfundplus/CFP.plus`, nhánh `main` |

## Nguyên tắc

1. **Không khóa dài hạn.** Không tạo service-account key JSON và không dán credentials vào chat, issue hay Notion.
2. Dùng **Workload Identity Federation (WIF)**: GitHub Actions nhận token ngắn hạn (khoảng 1 giờ), giới hạn đúng repository này.
3. Claude Code và các SI AI **không giữ credentials Google**. Họ đọc kết quả qua GitHub Actions artifact đã lọc.
4. Mỗi lần chạy cần người duyệt qua GitHub Environment `gcp-readonly` (bật *Required reviewers*).
5. Mọi quyền ghi (deploy, đổi traffic, IAM) **không thuộc phạm vi này**. Nếu cần, trình riêng từng giai đoạn.

## Giai đoạn 1 • READ ONLY (đề nghị phê duyệt)

Danh tính: service account mới `cfp-readonly-verifier@abiding-robot-507708-i3.iam.gserviceaccount.com`, **không có key**.

| Role | Phạm vi | Dùng để |
|---|---|---|
| `roles/run.viewer` | project (hoặc chỉ service `cfp-plus`) | Xem service, revision đang phục vụ, image digest, traffic, domain mapping |
| `roles/cloudbuild.builds.viewer` | project | Xem lịch sử build, trigger và lỗi deploy (ví dụ build 28/09) |
| `roles/logging.viewer` | project | Đọc log lỗi Cloud Build và Cloud Run |

**Không cấp:** Owner, Editor, `run.admin`, `run.developer`, `iam.serviceAccountUser`, `iam.serviceAccountKeyAdmin`, Billing, DNS hoặc Secret Manager accessor.

### Lệnh để người có quyền IAM chạy (Human Governance thực hiện, không phải AI)

```bash
PROJECT=abiding-robot-507708-i3
PROJECT_NUMBER=$(gcloud projects describe $PROJECT --format='value(projectNumber)')
SA=cfp-readonly-verifier@$PROJECT.iam.gserviceaccount.com

gcloud iam service-accounts create cfp-readonly-verifier --project $PROJECT \
  --display-name "CFP+ read-only verifier (no keys)"
for R in roles/run.viewer roles/cloudbuild.builds.viewer roles/logging.viewer; do
  gcloud projects add-iam-policy-binding $PROJECT --member "serviceAccount:$SA" --role $R --condition=None
done

gcloud iam workload-identity-pools create github --project $PROJECT --location global \
  --display-name "GitHub Actions"
gcloud iam workload-identity-pools providers create-oidc cfp-plus-repo --project $PROJECT \
  --location global --workload-identity-pool github \
  --issuer-uri https://token.actions.githubusercontent.com \
  --attribute-mapping "google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.environment=assertion.environment" \
  --attribute-condition "assertion.repository=='charityfundplus/CFP.plus' && assertion.environment=='gcp-readonly'"

gcloud iam service-accounts add-iam-policy-binding $SA --project $PROJECT \
  --role roles/iam.workloadIdentityUser \
  --member "principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github/attribute.repository/charityfundplus/CFP.plus"
```

Sau đó, trong GitHub, mở *Settings → Environments*, tạo `gcp-readonly` và bật *Required reviewers*. Thêm hai **Variables** (không phải Secrets, vì đây không phải bí mật):
- `GCP_WIF_PROVIDER` = `projects/<PROJECT_NUMBER>/locations/global/workloadIdentityPools/github/providers/cfp-plus-repo`
- `GCP_READONLY_SA` = `cfp-readonly-verifier@abiding-robot-507708-i3.iam.gserviceaccount.com`

Workflow sử dụng: `.github/workflows/gcp_readonly_evidence.yml` (chỉ chạy thủ công).

### Thu hồi (rollback IAM)

```bash
for R in roles/run.viewer roles/cloudbuild.builds.viewer roles/logging.viewer; do
  gcloud projects remove-iam-policy-binding $PROJECT --member "serviceAccount:$SA" --role $R
done
gcloud iam service-accounts disable $SA --project $PROJECT
```

## Giai đoạn 2 • Staging (CHƯA đề nghị, chỉ để tham khảo)

Chỉ khi Giai đoạn 1 đã chạy ổn: một Cloud Run service **riêng** `cfp-plus-staging`. Cấp `roles/run.developer` **chỉ trên service đó**, cộng `iam.serviceAccountUser` trên runtime SA của staging. Production `cfp-plus` vẫn chỉ deploy qua `main` sau khi Human Governance merge.

## Lưu ý về dữ liệu công khai

Repository là **public**, nên artifact của Actions có thể bị người khác tải. Workflow chỉ xuất metadata (revision, image digest, trạng thái build) và log mức `WARNING` trở lên, đã bỏ trường `httpRequest` (IP và user-agent người truy cập).
