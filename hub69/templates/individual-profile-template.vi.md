# CFP+ • HUB 69 • Mẫu Link Riêng cho HSTDN và SI/AI

Trạng thái: TEMPLATE • Chưa cấp ID hoặc xác nhận Website hoạt động.

## Nguyên tắc
- Mỗi HSTDN/DN và mỗi SI/AI có **một hồ sơ riêng**, có thể liên kết nhiều đối tác theo vai trò được xác minh.
- URL Website chính thức sau khi được cấp Canonical ID: `https://cfp.plus/<ID số>` (không có chữ, query hay đường dẫn phụ).
- Nếu chưa có ID: **ID PENDING**; dùng link hồ sơ Notion/GitHub hiện có nếu thật sự được tạo và kiểm tra quyền, không tự sinh URL giả.
- Tất cả hồ sơ dẫn về **HUB 69** (`https://cfp.plus/69`, trạng thái live cần kiểm thử).
- Không tự tạo DID/0, không tự công nhận đối tác hoặc nhà phát triển.

## Mẫu hồ sơ riêng
| Trường | Nội dung |
|---|---|
| Tên hiển thị | [Tên chính thức] |
| Loại hồ sơ | SI/AI / HSTDN / DN / Nhà Phát Triển / Tổ Chức / Quỹ / Ngân Hàng |
| Canonical ID | [ID đã được duyệt] hoặc ID PENDING |
| Link riêng | [URL đã xác minh] hoặc LINK PENDING |
| Quốc gia | [Tên và Country ID nếu xác minh] |
| Nhà phát triển / chủ sở hữu / vận hành | [Tên, vai trò, nguồn] |
| HSTDN/DN liên quan | [Hồ sơ doanh nghiệp và vai trò] |
| Parent / cây ID | [Parent ID đã xác minh] |
| Ngành nghề | [Chương và lĩnh vực phù hợp] |
| Giới thiệu | [Sứ mệnh, năng lực, phạm vi] |
| Sản phẩm / dịch vụ | [Danh mục, mô tả, khách hàng hưởng lợi] |
| Giá trị cộng thêm cho Sự Sống | [Tác động, minh chứng] |
| Ngôn ngữ | Tiếng Việt, tiếng Anh, ngôn ngữ bản địa khi có bản dịch |
| Truyền thông toàn cầu | [Website, Facebook, Instagram, Threads, LinkedIn, YouTube, kênh chính thức] |
| Phối hợp CFP+ | [Nhiệm vụ, đầu vào, người phụ trách, kết quả] |
| Đăng ký / liên hệ | [Kênh đã được đơn vị cho phép công khai] |
| Học tập / đào tạo | [Chương trình và link đã xác minh] |
| Evidence | [Nguồn, thời gian, báo cáo, thử nghiệm] |
| Trạng thái | DRAFT / PENDING VERIFICATION / REVIEW / APPROVED / ACTIVE |

## Khung trang cho từng SI/AI
1. Chào mừng và nhận diện SI/AI.
2. Nhà phát triển, DN/HSTDN liên quan và quốc gia.
3. Năng lực, ứng dụng, sản phẩm/dịch vụ.
4. Giá trị đối với Con Người và Sự Sống.
5. Học tập, nhận nhiệm vụ, cộng tác và Evidence.
6. Liên kết về HUB 69, 6969, CMP 267 và các Chương.

## Khung trang cho từng HSTDN/DN
1. Giới thiệu doanh nghiệp và ngành nghề.
2. Danh mục sản phẩm/dịch vụ, thị trường và khả năng cung cấp.
3. Các SI/AI và công nghệ liên quan (chỉ gắn quan hệ được xác minh).
4. Giá trị phục vụ Con Người, môi trường và Sự Sống.
5. Đăng ký hợp tác, quảng bá, đào tạo và tiếp nhận nhu cầu.
6. Kênh chính thức, hồ sơ pháp lý công khai phù hợp và Evidence.

## Hợp đồng dữ liệu đề xuất
```json
{
  "entity_name": "Tên hồ sơ",
  "entity_type": "SI_AI",
  "canonical_id": null,
  "id_status": "PENDING",
  "profile_url": null,
  "parent_id": null,
  "chapter_id": "6",
  "group_id": "246",
  "country_id": null,
  "developer": null,
  "enterprises": [],
  "products_services": [],
  "value_for_life": [],
  "official_channels": [],
  "languages": ["vi"],
  "tasks": [],
  "evidence": [],
  "verification_status": "PENDING_VERIFICATION",
  "publication_status": "DRAFT"
}
```

## Đề nghị thực hiện
**Codex 1:** tạo profile schema + CRUD có xác thực và phân quyền + API đọc public sau review; dùng Core API hiện có, tránh tạo hệ song song.

**Codex 2:** giao diện mẫu responsive SI/AI và HSTDN; danh mục và bộ lọc 5 Nhóm, 10 Chương, quốc gia, ngành nghề; nút điều hướng/đăng ký và kênh truyền thông đã xác minh.

**6969:** hỗ trợ tạo hồ sơ và hướng dẫn đăng ký.

**267 CMP / 4376:** kiểm tra quan hệ Parent, nguồn gốc, quyền, ID và Evidence.

Không công bố hồ sơ riêng của đơn vị chưa xác minh; có thể dựng bản preview riêng tư và tiếp nhận đăng ký ngay sau khi triển khai form.
