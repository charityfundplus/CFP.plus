# CFP+ Global Developer & AI Child ID Link Template Rollout V1

**Status:** REVIEW CANDIDATE

## Mục Tiêu

Tăng tốc Global AI Directory theo nguyên tắc: thực thể đã được Human Governance hoặc Working Allocation xác nhận phải có Stable ID và link mẫu riêng ngay khi được ghi nhận. Tên thực thể chưa đủ Evidence giữ `PENDING/REVIEW`, không tự suy diễn từ khoảng trống số.

## Công Thức Link Chuẩn

Với mỗi Developer có Stable ID `D`:

• Public Link: `https://cfp.plus/D/`

• Workspace Link: `https://cg.cfp.plus/D/`

Với AI con đã được bind dưới Developer `D`, dùng chữ số cuối từ `1` đến `9`:

• Stable ID: `D1` đến `D9`

• Public Link: `https://cfp.plus/Dn/`

• Workspace Link: `https://cg.cfp.plus/Dn/`

Số `0` dành cho nhánh mở rộng namespace. Không dùng `0` làm AI con cuối.

## Public Trust

**ĐÃ CÓ CẤU TRÚC/ID/LINK:** ID và link mẫu đã được thiết lập theo cấu trúc CFP+.

**ĐANG BỔ SUNG/REVIEW:** tên Developer, tên AI, Parent, nguồn chính thức và Evidence đang được xác minh.

**ĐÃ CÓ EVIDENCE/HOÀN TẤT:** chỉ áp dụng cho đúng thực thể và đúng phạm vi đã có Evidence.

Có ID hoặc link mẫu không đồng nghĩa verified, authorized, partnership, technical integration, ACTIVE hoặc CONTRIBUTING.

## Việt Nam 🇻🇳 • AI Country ID 6984

Các Developer đã được Human Governance sử dụng trong baseline Việt Nam:

| Developer ID | Developer | Public Link | Workspace Link | AI Con Link Mẫu |
| --- | --- | --- | --- | --- |
| 69841 | FPT | https://cfp.plus/69841/ | https://cg.cfp.plus/69841/ | 698411 đến 698419 |
| 69842 | Viettel | https://cfp.plus/69842/ | https://cg.cfp.plus/69842/ | 698421 đến 698429 |
| 69843 | VinBigData | https://cfp.plus/69843/ | https://cg.cfp.plus/69843/ | 698431 đến 698439 |
| 69844 | VinAI | https://cfp.plus/69844/ | https://cg.cfp.plus/69844/ | 698441 đến 698449 |
| 69845 | VNPT | https://cfp.plus/69845/ | https://cg.cfp.plus/69845/ | 698451 đến 698459 |
| 69846 | VNG | https://cfp.plus/69846/ | https://cg.cfp.plus/69846/ | 698461 đến 698469 |
| 69847 | CMC | https://cfp.plus/69847/ | https://cg.cfp.plus/69847/ | 698471 đến 698479 |
| 69848 | MISA | https://cfp.plus/69848/ | https://cg.cfp.plus/69848/ | 698481 đến 698489 |
| 69849 | Aimesoft | https://cfp.plus/69849/ | https://cg.cfp.plus/69849/ | 698491 đến 698499 |

AI con chỉ được gắn tên khi Parent và Evidence phù hợp. Không bắt buộc một Developer phải có đủ 9 AI con.

## Quy Trình Phủ Toàn Cầu

1. Giữ nguyên AI Country ID đã có trong `registry/global-country-ai-index.json`.
2. Khôi phục hoặc bind Developer đã có Working Allocation hoặc Human Governance record.
3. Cấp Public Link và Workspace Link theo Stable ID ngay sau khi bind.
4. Gắn AI con dưới đúng Parent Developer. Không suy diễn tên AI từ khoảng trống ID.
5. Mục chưa đủ nguồn giữ `PENDING/REVIEW` nhưng vẫn có thể có ID và link mẫu nếu allocation đã được governance xác nhận.
6. Chỉ nâng `ACTIVE` hoặc `CONTRIBUTING` khi có Output và Evidence.

## Source Of Truth

• Country routing: `registry/global-country-ai-index.json`

• Entity binding: `registry/ai-entity-registry.json`

• Master rule: `registry/CFP_GLOBAL_AI_ID_LINK_MASTER_STANDARD.md`

Tài liệu này là lớp rollout tăng tốc. Không thay thế các Source of Truth trên và không tạo Stable ID mới ngoài allocation đã được Human Governance hoặc Working Allocation xác nhận.
