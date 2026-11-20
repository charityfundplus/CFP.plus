# Văn Phòng Chung • Siêu Bộ Đôi • Bản đồ kế thừa (không xây trùng)

Trạng thái: **REVIEW CANDIDATE • PENDING HUMAN GOVERNANCE**. Tài liệu này không kích hoạt agent nào và không cấp ID.
Liên quan: #235, #178, #201, PR #124, #195, #232

## Kết luận

Các thành phần Văn Phòng Chung **đã có** trong hai nhánh đang HOLD. **Không cần thiết kế hệ thống mới.** Việc còn lại là ghép, review và quyết định phát hành theo từng lớp.

| Yêu cầu (#235 / đề nghị 20/11) | Thành phần hiện có | Nơi | Khoảng trống |
|---|---|---|---|
| Danh tính mỗi Siêu Bộ Đôi | Bảng `super_pairs`, `offices`; schema `super-pair-node` (`canonical_id` = null cho đến khi Governance cấp) | #195 `services/forum/sql/002_office.sql`; #232 `docs/si-ai-platform/schemas/` | Chưa thống nhất hai mô hình: bảng DB (#195) và node quy hoạch (#232). Cần quyết định nguồn chuẩn |
| Nhiệm vụ | `tasks`, `task_events`, `worker.py` (004) | #195 | #234 đang sửa chống ghi trùng `task_events` (HOLD) |
| Quyền hạn | `office_roles`, `office_maintainers`, RLS 003 / 003c / 03d; `grants` + `inherits_permissions: false` | #195, #234, #232 | Điều kiện C1/C2/G3/G4/G5 của #195 chưa đóng |
| Link Mẫu | `links`; `web/linkmau.html` | #195 | Chưa đối chiếu với Notion Link Mẫu (cần quyền đọc) |
| Evidence | `evidence`; thư mục evidence + SHA256SUMS | #195, #232 | — |
| Lịch sử hoạt động | `audit_log`, `task_events` | #195 | — |
| Phản biện độc lập | `reviews`; ACK lifecycle `09_ACK_LIFECYCLE_VERIFICATION_VI.md` | #195, #232 | — |
| Không tự nhận ACTIVE | `status` PLANNED → RESERVED → PROPOSED → BOUND → ACTIVE, chỉ ACTIVE khi có Evidence | #232 | — |
| Giao diện điện thoại | `office.html`, `vpsbd.html`, `sieu-bo-doi.html`; ảnh mobile 390px | #195, #232 | Chưa kiểm thử Safari thật |
| Nội dung giới thiệu công khai | Pipeline `content/pages/*.md` | PR của nhánh này | Không phụ thuộc backend, nên có thể phát hành trước |

## Thứ tự phát hành đề xuất (mỗi bước cần Human Governance duyệt riêng)

1. **Website (nhánh này):** `.dockerignore` (bảo mật), sau đó pipeline nội dung. Không cần database. Giới thiệu được CFP+, 3 Quỹ, HSTDN và SI AI ngay bằng Markdown.
2. **Văn Phòng read-only:** trang tĩnh danh sách Siêu Bộ Đôi, sinh từ `super-pair-plan.json` (#232) qua cùng pipeline. Chưa cần đăng nhập.
3. **Backend #195:** sau khi C1/C2/G3/G4/G5 và #234 đóng, triển khai lên môi trường **staging riêng** trước.
4. Kết nối từng SI AI: chỉ khi có danh tính xác minh và ACK receipt, theo vòng đời #232.

## Quyết định cần Human Governance

- D1: Nguồn chuẩn danh tính Siêu Bộ Đôi là bảng `super_pairs` (#195) hay `super-pair-node` (#232)? Đề xuất: DB là nguồn vận hành, schema #232 là định dạng trao đổi và validator.
- D2: Thứ tự phát hành như trên.
- D3: Hạ tầng backend: Render (`render.yaml` trong #195) hay Cloud Run CFP-CLOUD? Đề xuất: Cloud Run staging để dùng chung IAM và log.
