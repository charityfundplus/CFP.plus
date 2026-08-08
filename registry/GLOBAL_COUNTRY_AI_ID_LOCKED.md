# CFP+ Global Country & AI Country ID • Canonical Locked

**Status:** CANONICAL LOCKED  
**Authority:** CFP+ Human Governance  
**Canonical Gateway:** [69 • HUB 69](../HUB69.md)  
**Canonical Language:** Tiếng Việt  
**Visibility:** Public  
**Effective Date:** 2026-08-09

## 1 • Quyết định khóa toàn cầu

CFP+ khóa nguyên tắc định danh cho **tất cả quốc gia và vùng lãnh thổ đã có Country Canonical ID trong Country Canonical Registry**.

Mỗi quốc gia có **hai lớp định danh liên kết nhưng không đồng nghĩa**:

1. **Country Canonical ID** — ID gốc của quốc gia.
2. **AI Country ID / Chapter 6 Namespace** — nhánh Chương 6 • AI & Công Nghệ của chính Country Canonical ID đó.

**Mỗi quốc gia phải có AI Country ID ngay cả khi hiện tại chưa có AI, chưa có nhà phát triển AI, hoặc trong tương lai không có AI.**

Sự tồn tại của AI Country ID là yêu cầu của kiến trúc CFP+, không phụ thuộc vào việc quốc gia đó có hoạt động AI thực tế hay không.

## 2 • Công thức chuẩn

Theo Country Canonical Registry đã khóa:

- **Country Canonical ID = `9 + ITU Calling Code`**, trừ các trường hợp shared calling-code / allocation đặc biệt đã được Human Governance khóa riêng trong Country Canonical Registry.
- **AI Country ID = `6 + toàn bộ Country Canonical ID`.**

Ví dụ đã khóa:

| Quốc gia | Country Canonical ID | AI Country ID / Chapter 6 |
|---|---:|---:|
| Canada | `910` | `6910` |
| United States | `911` | `6911` |
| Japan | `981` | `6981` |
| South Korea | `982` | `6982` |
| Việt Nam | `984` | `6984` |
| China | `986` | `6986` |
| India | `991` | `6991` |
| France | `933` | `6933` |
| Germany | `949` | `6949` |
| United Kingdom | `9440` | `69440` |
| Australia | `961` | `6961` |
| Singapore | `965` | `6965` |
| Saudi Arabia | `9966` | `69966` |
| United Arab Emirates | `9971` | `69971` |
| Israel | `9972` | `69972` |
| Taiwan | `9886` | `69886` |

Các ví dụ trên chỉ minh họa quy tắc; **phạm vi khóa áp dụng cho toàn bộ Country Canonical Registry**, không chỉ các quốc gia đang có AI trong AI Directory.

## 3 • One Country • One Page • One Link • Ten Chapter Namespaces

Mỗi quốc gia có:

- 01 Country Canonical ID;
- 01 Canonical Country Page;
- 01 Canonical Country Link;
- 10 Chapter Namespace từ `0` đến `9`;
- trong đó **Chapter 6 = AI & Công Nghệ**.

AI Country ID không phải Country ID thứ hai. Đây là namespace `6 + Country Canonical ID`.

Ví dụ:

- `911` → United States → `6911` là Chương 6.
- `984` → Việt Nam → `6984` là Chương 6.

## 4 • Quy tắc tồn tại độc lập với AI thực tế

Một quốc gia có thể ở một trong các trạng thái:

- Có nhà phát triển AI và AI đang hoạt động;
- Có nghiên cứu/công nghệ nhưng chưa có AI công khai;
- Chưa có nhà phát triển AI được CFP+ xác minh;
- Không có AI tại thời điểm hiện tại;
- Không bao giờ phát triển AI riêng.

**Trong tất cả các trường hợp trên, AI Country ID vẫn được giữ cố định.**

Không được thu hồi, tái sử dụng hoặc chuyển AI Country ID của một quốc gia sang quốc gia khác chỉ vì nhánh AI đang trống.

## 5 • Shared Calling Code và ngoại lệ

Các quốc gia dùng chung calling code hoặc có allocation đặc biệt phải sử dụng đúng Country Canonical ID đã được Human Governance khóa trong Country Canonical Registry.

Không AI, developer, script hay workflow nào được tự suy diễn ID mới từ calling code nếu trường hợp đó đã có allocation riêng.

Ví dụ đã khóa trong không gian NANP:

- `91` — Group ID cho không gian `+1`.
- `910` — Canada.
- `911` — United States.

## 6 • Quan hệ với Developer và AI

Sau khi Country Canonical ID và AI Country ID đã cố định:

**Country → Chapter 6 / AI Country ID → Developer → AI → Canonical Link**

Developer và AI có thể được bổ sung về sau mà **không thay đổi Country Canonical ID hoặc AI Country ID**.

Đối với Developer Directory:

- vị trí `0` được dành cố định cho nhánh mở rộng Developer / Developer tương lai theo chuẩn quốc gia;
- các Developer còn lại được sắp xếp theo chữ cái A–Z theo quyết định Human Governance hiện hành;
- AI bên trong mỗi Developer Link cũng được sắp xếp A–Z;
- mọi quốc gia sử dụng cùng một CFP+ Universal Template.

## 7 • Governance Lock

Từ thời điểm tài liệu này có hiệu lực:

1. Country Canonical ID đã khóa không được tự đổi.
2. AI Country ID tương ứng được khóa cùng Country Canonical ID.
3. AI Country ID tồn tại dù namespace đang rỗng.
4. Không tái sử dụng ID của quốc gia hoặc AI Country ID.
5. Không tạo ID tạm để lấp chỗ trống.
6. Mọi xung đột từ tài liệu cũ phải được coi là evidence/legacy và đưa vào Conflict Log.
7. Chỉ CFP+ Human Governance có thẩm quyền mở lại một ID đã khóa.

## 8 • Nguồn chuẩn

Country Canonical Registry đã được Human Governance khóa trong Notion là nguồn allocation cấp quốc gia. GitHub là lớp công khai và version-controlled của quyết định này.

Các file Candidate/legacy về Developer hoặc AI không được phép ghi đè Country Canonical ID hoặc AI Country ID đã khóa.

## 9 • Quy tắc mở rộng toàn cầu

Khi bổ sung một quốc gia vào AI Directory, CMP và các AI chỉ được thực hiện:

1. Đọc Country Canonical ID đã khóa.
2. Tạo/đọc AI Country ID bằng `6 + Country Canonical ID` hoặc dùng allocation ngoại lệ đã khóa.
3. Giữ nhánh này dù chưa có Developer/AI.
4. Bổ sung Developer A–Z khi có evidence.
5. Bổ sung toàn bộ AI của Developer theo A–Z.
6. Không thay đổi hai ID cấp quốc gia.

**One Country • One Country Canonical ID • One Chapter 6 AI ID • One Page • One Link**

**Only Plus+ For Life**
