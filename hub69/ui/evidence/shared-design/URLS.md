# Bảng đường dẫn • Issue #156

GET chỉ đọc, không xác thực, giới hạn 128 KiB mỗi phản hồi. HTTP 200 chỉ là quan sát transport/content, không phải Preview/revision/Registry/ACL/hoạt động.

| URL thực tế | HTTP | Nội dung đọc được | Nghiệm thu |
| --- | --- | --- | --- |
| [https://sites.google.com/cfp.plus/hub69](https://sites.google.com/cfp.plus/hub69) | 200 | HUB 69 | Trang nguồn cũ; chưa là Preview revision mới |
| [https://sites.google.com/cfp.plus/hub69/hub-69-master-hub](https://sites.google.com/cfp.plus/hub69/hub-69-master-hub) | 200 | HUB 69 - HUB 69 – Master Hub | Trang nguồn cũ; chưa là Preview revision mới |
| [https://sites.google.com/cfp.plus/hub69/id](https://sites.google.com/cfp.plus/hub69/id) | 200 | HUB 69 - ID | Trang nguồn cũ; chưa là Preview revision mới |
| [https://cfp.plus/8682](https://cfp.plus/8682) | 200 | 8682 • CFP+ Global Trade • Thương Mại Toàn Cầu | Nội dung có TMTC; binding Registry vẫn PENDING |
| [https://cfp.plus/8882](https://cfp.plus/8882) | 200 | CFP+ • AI Office | BLOCKED: AI Office generic, chưa thấy TTTC |
| [https://app.notion.com/p/3fecaac9a557815ca9f6fbf60844d50b?pvs=204](https://app.notion.com/p/3fecaac9a557815ca9f6fbf60844d50b?pvs=204) | 200 | Notion | Shell Notion; chưa xác nhận nội dung/quyền qua HTTP |
| [https://app.notion.com/p/3fecaac9a5578132a41fec206bfb0552](https://app.notion.com/p/3fecaac9a5578132a41fec206bfb0552) | 200 | Notion | Shell Notion; chưa xác nhận nội dung/quyền qua HTTP |
| [https://github.com/charityfundplus/CFP.plus/issues/156](https://github.com/charityfundplus/CFP.plus/issues/156) | 200 | P0 • Codex 1 &amp; Codex 2 • Code + Đồng Bộ Siêu Bộ Đôi • HUB 69 • Gemini Google Sites · Issue #156 · charityfundplus/CFP.plus · GitHub | NOT VERIFIED |
| [https://www.amazon.com/](https://www.amazon.com/) | 200 | Amazon.com. Spend less. Smile more. | NOT VERIFIED |
| [https://www.ibm.com/quantum](https://www.ibm.com/quantum) | 200 | Site Unavailable | BLOCKED: trả trang Site Unavailable |
| [https://quantumai.google/](https://quantumai.google/) | 200 | Google Quantum AI | NOT VERIFIED |
| [https://www.nasa.gov/](https://www.nasa.gov/) | 200 | NASA | NOT VERIFIED |
| [https://www.esa.int/](https://www.esa.int/) | 200 | European Space Agency | NOT VERIFIED |
| [https://www.spacex.com/](https://www.spacex.com/) | 200 | SpaceX | NOT VERIFIED |
| [https://www.starlink.com/](https://www.starlink.com/) | 200 | Starlink | NOT VERIFIED |
| [https://support.google.com/sites/answer/6372865?hl=en](https://support.google.com/sites/answer/6372865?hl=en) | 429 | HTTP Error 429: Too Many Requests | BLOCKED_HTTP |

## Route Preview local

Build bằng `node build.mjs`; mở `HUB69-review.html` và phần fragment dưới đây. Chưa có HTTPS staging được duyệt.

| Màn hình | Fragment | Trạng thái |
| --- | --- | --- | --- |
| HUB 69 | `#home` | Offline UI review |
| Master Hub | `#master` | Nguồn + trạng thái |
| Danh mục ID | `#id` | 26 source bindings; không là roster 91 cặp |
| 5 Nhóm | `#chapters` | V / 000 / 135 / 246 / 789 |
| Chi Hội | `#chapter/5` | Khung nội dung; chờ roster thật |
| SI AI Robot Công Nghệ | `#chapter/6` | Nguồn + điều hướng |
| HSTDN | `#chapter/7` | Đi theo quốc gia |
| Quốc gia | `#chapter/9` | Bối cảnh; chưa gán binding |
| HSTDN Việt Nam | `#hstdn/vn` | Research có nguồn; chưa độc lập nghiệm thu |
| HSTDN Hoa Kỳ | `#hstdn/us` | Cùng presenter; giữ bối cảnh riêng |
| Nhà cung cấp Việt Nam | `#partners/vn/supplier` | MINH HỌA |
| Đối tác mua Hoa Kỳ | `#partners/us/buyer` | MINH HỌA |
| Đối tác bán | `#partners/all/seller` | MINH HỌA |
| TMTC | `#reference/8682` | PENDING REVIEW |
| TTTC | `#reference/8882` | PENDING REVIEW |
| App browser shell | `#app` | UI review; chưa native/PWA production |
