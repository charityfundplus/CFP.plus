# Registry mapping • nguồn ghim, không sửa Canonical

Nguồn đối chiếu: main `835616308111f6851c0387fa9f5eda60c9ffa624`;
Core `06f386b1ba52358779cec6bc26c2d88f6a33664a`.
`source-observations.json` giữ các dòng nguồn đã đọc, blob SHA và danh sách đường
dẫn Registry của complete tree. Đây là evidence snapshot, không phải Registry mới.
Mọi Owner/DID/SI/Robot/Capability không có evidence đều UNKNOWN; không cấp mới.

| Phạm vi / ID tham chiếu | Parent theo nguồn | Evidence tại main pin | Kết luận tích hợp |
|---|---|---|---|
| 6 → 69 | Không có explicit edge trong hai Registry JSON được dùng bởi Core | `HUB69.md` xác định 69 là gateway duy nhất, không xác nhận Parent=6; không có `registry/6.md` hoặc `registry/69.md` | BLOCKED / missing authority; điều hướng không chứng minh identity Parent |
| 69 → 696 | Không có dòng hoặc hồ sơ `registry/696.md` | Registry entity/country JSON và complete path inventory | BLOCKED; không suy từ prefix |
| 696 → 6969 | Không có dòng hoặc hồ sơ `registry/6969.md` | Registry entity/country JSON và complete path inventory | BLOCKED; không tạo hoặc bind ID |
| 911 → 6911 | Country → AI-country theo index và Core loader | `global-country-ai-index.json`, `core/registry-read-model.mjs` | Source mapping observed; operational authority vẫn chưa xác minh; US hold retained |
| 69118 → 691181 | OpenAI → ChatGPT; developer parent 6911, AI parent 69118 | `ai-entity-registry.json` | Source reference observed; HSTDN ID/Owner/DID không có; không đồng nhất Developer với HSTDN |
| OpenAI / 69110 vs 69118 | `HUB69.md`: 69110=OpenAI/691100=ChatGPT, 69118=CoreWeave; JSON: 69118=OpenAI/691181=ChatGPT | `HUB69.md` §7 vs `ai-entity-registry.json` | CONFLICT / BLOCKED; báo Human Governance, không tự sửa hoặc chọn làm public approval |
| 984 → 6984 (Việt Nam) | `HUB69.md`: country 984, chapter 6 6984; `registry/6984.md`: Parent Hub 698 | `HUB69.md` §8 vs `registry/6984.md`; loaded country JSON không chứa row 984/6984 | CONFLICT / BLOCKED; hồ sơ cũ gọi Hub quốc gia còn xung đột quy tắc gateway duy nhất; không tự đổi Parent |
| HSTDN Hoa Kỳ / Việt Nam | Chưa có binding HSTDN được xác minh trong JSON nguồn | `ai-entity-registry.json`: 20 developer + 6 AI; country index | pending_review, adapter disabled; các country/developer ID chỉ là tham chiếu |
| Chi Hội | Chưa được cung cấp ID/Parent/Owner/DID/capability/source binding | Issue #156 yêu cầu kết nối, không cấp identity | pending_review, adapter disabled |
| 8682 TMTC | Không được suy Parent từ chuỗi tích hợp công việc | Issue #156; không có binding trong hai JSON nguồn Core | pending_review, không giao dịch/checkout, không live connector |
| 8882 TTTC | Không được suy Parent từ 8682 hoặc flow nghiệp vụ | Issue #156; không có binding trong hai JSON nguồn Core | pending_review, không tài chính/tài khoản, không live connector |

Phân biệt: thiếu trong các nguồn đã đọc KHÔNG chứng minh một ID không tồn tại ở
mọi kho. Registry custodian cần cung cấp explicit original rows/edges và quyết
định xử lý xung đột. Không đổi JSON hoặc markdown gốc trong PR này.

Các URL evidence cố định:

- https://github.com/charityfundplus/CFP.plus/blob/835616308111f6851c0387fa9f5eda60c9ffa624/registry/ai-entity-registry.json
- https://github.com/charityfundplus/CFP.plus/blob/835616308111f6851c0387fa9f5eda60c9ffa624/registry/global-country-ai-index.json
- https://github.com/charityfundplus/CFP.plus/blob/835616308111f6851c0387fa9f5eda60c9ffa624/HUB69.md
- https://github.com/charityfundplus/CFP.plus/blob/835616308111f6851c0387fa9f5eda60c9ffa624/registry/6984.md
- https://github.com/charityfundplus/CFP.plus/blob/06f386b1ba52358779cec6bc26c2d88f6a33664a/drafts/si-office/core/registry-read-model.mjs
