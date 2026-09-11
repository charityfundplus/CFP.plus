# CFP+ GLOBAL COUNTRY TERRITORY AUDIT • 2026 09 11

Status: P0 ACTIVE AUDIT

## Mục Tiêu

Rà soát toàn bộ Quốc Gia và Vùng Lãnh Thổ trong Global AI Directory để bảo đảm dữ liệu gốc, ID, Link, routing metadata, Developer coverage và Evidence không bị thiếu hoặc lệch giữa Notion và GitHub.

## Baseline Quốc Tế

Nguồn tham chiếu trung lập cho phạm vi rà soát là United Nations Statistics Division M49 • Countries or Areas.

Bản tiếng Anh hiện có 248 dòng Country or Area trong phần World.

Nguồn: https://unstats.un.org/unsd/methodology/m49/overview

Baseline này chỉ dùng để kiểm tra coverage tên Quốc Gia hoặc Vùng Lãnh Thổ. Baseline không tự cấp CFP+ Stable ID và không thay đổi mapping đã khóa.

## Evidence CFP+ Hiện Tại

Notion Master:

Bảng Quốc Gia • ID AI 🤖 Quốc Gia • ID Quốc Gia • Mã Gọi Quốc Tế

Trang Notion xác định đây là checklist gốc cho toàn bộ AI Country ID và Stable ID đã có phải được giữ nguyên.

GitHub Public Index:

registry/global-country-ai-index.json

Hiện có 99 record.

GitHub Route Metadata:

registry/country-route-map.json

Hiện có 32 record Quốc Gia hoặc Vùng Lãnh Thổ ngoài khối cấu hình Public Trust.

## Kết Quả Rà Soát P0 Đầu Tiên

1. Public Index hiện có 99 record trong khi baseline M49 có 248 Country or Area.

2. Route Map hiện có 32 record.

3. Chỉ 19 record hiện xuất hiện ở cả Public Index và Route Map.

4. Có 80 record trong Public Index chưa có Route Map metadata tương ứng.

5. Có 13 record trong Route Map chưa xuất hiện trong Public Index gồm Germany, United Kingdom, Australia, Singapore, Japan, South Korea, Việt Nam, China, Taiwan, India, Saudi Arabia, United Arab Emirates và Israel.

6. So với baseline M49, có ít nhất 136 Country or Area chưa xuất hiện trong cả hai file public hiện tại. Con số mapping thực tế cần rà thêm vì CFP+ đang có một số record cấp vùng hoặc nhóm không tương ứng một đối một với M49.

## Conflict Cần Cô Lập

### Réunion và Mayotte

Public Index hiện có một record tên Réunion và Mayotte review group.

M49 ghi Réunion và Mayotte là hai Country or Area riêng.

Không tự tách ID. Giữ record hiện tại và đưa mapping vào CHỜ QUYẾT ĐỊNH cho tới khi đối chiếu SoT.

### Diego Garcia

Public Index hiện có Diego Garcia ở cấp Country record.

M49 dùng British Indian Ocean Territory ở cấp Country or Area.

Diego Garcia có thể được giữ như sub area nếu CFP+ cần, nhưng không được dùng thay cho baseline Country or Area nếu chưa có quyết định mapping.

### Đảo Ascension

Public Index hiện có Đảo Ascension ở cấp Country record.

M49 ghi Saint Helena ở cấp Country or Area trong danh sách thống kê.

Giữ record lịch sử. Không renumber. Đưa quan hệ Parent và cấp phân loại vào review.

## Public Status Conflict

country-route-map.json vẫn dùng nhãn ĐANG BỔ SUNG/REVIEW trong Public Trust metadata và một số country status.

Chuẩn Website hiện hành phải thể hiện Global AI Directory là danh mục đã thiết lập và BỔ SUNG LIÊN TỤC.

Không mô tả toàn bộ danh mục như một danh sách chưa hoàn thành.

## Chu Trình Rà Soát Toàn Cầu

Country or Area Baseline → Notion Master Match → Country ID → AI Country ID → Canonical Link → Route Metadata → Developer or AI R&D → AI Children → Evidence → Review

## Quy Tắc An Toàn

Không renumber.

Không reuse.

Không remap Stable ID đã bind.

Không suy CFP+ ID mới chỉ từ M49 hoặc ISO.

Tên mới chỉ bind khi có source phù hợp.

Record thiếu mapping giữ MISSING MAPPING hoặc CHỜ QUYẾT ĐỊNH.

Không dùng ID hoặc Link làm bằng chứng hoạt động AI 🤖.

## Ưu Tiên Thực Thi

P0 A • Đồng bộ toàn bộ record từ Notion Master sang Public Index.

P0 B • Tạo Route Map metadata cho toàn bộ Public Index.

P0 C • So sánh Notion Master với 248 M49 Country or Area để tìm record thiếu hoặc record cấp sai.

P0 D • Kiểm tra Canonical Link thực tế cho từng AI Country ID.

P0 E • Gắn Developer coverage, AI R&D, AI Children và Evidence theo từng hồ sơ.

P0 F • Public Website chỉ hiển thị trạng thái DANH MỤC ĐÃ THIẾT LẬP • BỔ SUNG LIÊN TỤC • EVIDENCE THEO TỪNG HỒ SƠ.

## Acceptance Criteria

Public Index phản ánh đầy đủ Notion Master.

Route Map có metadata cho từng Public Index record.

Tất cả 248 baseline Country or Area có kết quả đối chiếu rõ ràng gồm MATCH, SUB AREA, GROUPING, MISSING MAPPING hoặc CHỜ QUYẾT ĐỊNH.

Không có duplicate Stable ID.

Không có duplicate Canonical Link sai Parent.

Không có Link được ghi LIVE nếu chưa mở đúng trang.

Không có Completion Claim nếu thiếu Evidence.

CFP+ • Only Plus+ For Life
