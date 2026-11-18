# 07 • Hồ Sơ Nghiệm Thu • PR #232 • Trình Human Governance

**Trạng thái:** DRAFT • HOLD ACTIVATION • PRODUCTION NO-GO • Chưa đủ điều kiện merge
**Phạm vi nghiệm thu:** tài liệu + công cụ + Danh Bạ sandbox. **Không** gồm production, DNS, Registry, ID.

## 1 • Sản phẩm bàn giao

| # | Sản phẩm | Chạy được? | Evidence |
|---|---|---|---|
| D1 | Bảng nguồn + đối chiếu 18 trang Notion | Tài liệu | `00`, `06` |
| D2 | Sơ đồ 5 Nhóm, 10 Chương, 3 tầng (vị trí quy hoạch ≠ ID) | Tài liệu | `01` |
| D3 | Dữ liệu 91 Siêu Bộ Đôi từ Notion | ✅ JSON, có test | T12 |
| D4 | Adapter vào Registry của PR #124 | ✅ chạy trong sandbox | T10–T12 |
| D5 | Validator cây Siêu Bộ Đôi (kế thừa tiêu chuẩn, không kế thừa quyền) | ✅ | T1, T16 |
| D6 | Kiểm tra link thật 91 ID | ✅ | T13 |
| D7 | Danh Bạ 91 Siêu Bộ Đôi (tìm, lọc, link Notion, trạng thái live, VI/EN) | ✅ sandbox | T14 |
| D8 | Mẫu Diễn Đàn, Văn Phòng; mục trang chủ | Mẫu tĩnh | T6, T15 |
| D9 | Kiểm kê thật 6 Kho | ✅ thăm dò chỉ đọc | `08` §2 |
| D10 | Mô-đun làm việc (GitHub audit, Notion cross-check, phân loại) | ✅ | T17 |
| D12 | ACK riêng + adapter READ ONLY (bản vá PR #124, adapter tắt) | ✅ 9/9 test mới; hồi quy 79/79 | `09` §2–3 |
| D13 | Tiến trình REGISTERED → REVIEWED + cổng ACTIVE | ✅ 5/5 test; ACTIVE = 0 | `09` §4 |
| D14 | Kiểm chứng độc lập: CI, CodeQL, Copilot, security-check | Xem PR #232 | `09` §6 |
| D11 | **Thí điểm 3 nhiệm vụ qua Core PR #124** (tạo → ACK/chạy → review độc lập → audit) | ✅ 3/3 REVIEWED DRAFT | T18, `evidence/pilot/` |

## 2 • Danh sách kiểm tra trước khi merge

- [x] Không cấp ID, không đổi Registry, Parent, DID, Canonical (`registryWrites=0` trong T12; diff không đụng `registry/`)
- [x] Không sửa Luật Thép hay quy tắc Canonical
- [x] Kiểm thử tự động có kết quả lưu trong repo
- [ ] Review độc lập (ReviewSI / SI AI khác) trên đúng commit head
- [ ] Safari trên iPhone thật cho trang chủ và Danh Bạ
- [ ] HG-1, HG-3, HG-4, HG-5, HG-9, HG-12 được quyết định hoặc ghi nhận hoãn
- [ ] HG-10: quyết định merge

## 3 • Đề xuất bước tiếp theo để vận hành thử nghiệm

1. **HG-15:** chọn một PR Diễn Đàn và một Core (#124), dừng phát triển song song.
2. **Codex 1 / PR #124:** thêm route `GET /api/core/super-pairs` dùng adapter của PR #232. Ước tính là thay đổi nhỏ, vì read-model đã hỗ trợ.
3. **Registry custodian:** cung cấp Parent cho 91 ID (HG-13) và xử lý 333, 2273, 2588, 2624, 8882.
4. **Website:** tạo trang riêng cho các ID ưu tiên trong 72 ID đang dùng trang dự phòng, mỗi trang cần ghi rõ trạng thái REVIEW.
5. **Một luồng sandbox thật** theo Notion: Forum 00 → Office → Task Intake → kiểm tra quyền → ACK → kết quả → review → Evidence, chạy trên PR Diễn Đàn được chọn, kiểm thử trên iPhone thật.
