# CMP — Nền tảng Quản lý Điều phối và Cộng tác CFP+

**Cổng trung tâm công khai**  
**Vị trí:** Bên trong HUB 69  
**Trạng thái kiến trúc:** Đã công bố  
**Trạng thái Baseline:** v2.0 — Ứng viên rà soát  
**Trạng thái pilot:** Đang triển khai  
**Trạng thái vận hành chính thức:** Chờ Rà soát Kỹ thuật và Human Governance

> CMP là lớp điều phối và cộng tác trung tâm bên trong HUB 69. CMP điều phối toàn bộ vòng đời công việc giữa Human Governance, con người, các hệ AI, GitHub, Notion và các nguồn bằng chứng được phép. CMP không phải là HUB thứ hai và không thay thế Human Governance.

## Nguồn công khai và nguồn làm việc nội bộ

- **Nguồn tham chiếu công khai chính:** tài liệu GitHub này và bộ tài liệu [`cmp/`](cmp/)
- **Nguồn làm việc trên Notion:** [CMP Central Gateway](https://app.notion.com/p/3b3caac9a557819e8ee8e0aa4d0260fc)
- **Issue điều phối đang hoạt động:** [Issue #53](https://github.com/charityfundplus/CFP.plus/issues/53)
- **Work Order pilot hiện tại:** [Issue #46](https://github.com/charityfundplus/CFP.plus/issues/46)

GitHub là nguồn công khai, dễ truy cập rộng rãi. Notion tiếp tục là nguồn làm việc và điều phối nội bộ khi người tham gia có quyền truy cập. Không ai bắt buộc phải có quyền vào Notion mới được rà soát CMP.

## 1. Vị trí trong HUB 69

- **HUB 69:** cổng toàn cầu duy nhất, chịu trách nhiệm định vị và điều hướng toàn bộ CFP+.
- **CMP:** lớp điều phối trung tâm cho cộng tác và toàn bộ vòng đời công việc.
- **AI Collaboration Directory:** định vị nhà phát triển, Điểm vào Cộng tác Chính, Canonical ID và Canonical Link.
- **Human Governance:** giữ quyền quyết định cuối cùng.

## 2. Mục tiêu của CMP

CMP được thiết kế để:

- chuyển mục tiêu thành Work Order có cấu trúc;
- lựa chọn AI hoặc reviewer phù hợp theo loại nhiệm vụ, năng lực và quyền thực tế của phiên làm việc;
- điều phối review trực tiếp tại nguồn trên Issue, Pull Request và Canonical Link;
- thu thập và xác minh Evidence Package;
- giữ nguyên các review xung đột và chuyển cấp xử lý thay vì tự hòa giải âm thầm;
- chuẩn bị Governance Decision Package;
- duy trì lịch sử kiểm toán và vòng phản hồi cho đến khi công việc được đóng đúng quy trình;
- mở rộng thêm các hệ AI mà không làm thay đổi kiến trúc đã xác lập.

## 3. Các mô-đun cốt lõi

1. Trung tâm Hàng đợi Công việc
2. Bộ máy Phân công
3. AI Collaboration Directory
4. Trung tâm Bằng chứng
5. Trung tâm Rà soát và Bộ Tổng hợp Rà soát
6. Trung tâm Trạng thái
7. Cổng Quản trị
8. Kiểm toán và Lịch sử
9. Đồng bộ Tri thức
10. Trung tâm Tự động hóa
11. Bộ Quản lý Xung đột và Ngoại lệ

## 4. Vòng đời có kiểm soát

`Bản nháp → Đã giao → Đã tiếp nhận → Đang triển khai → Chờ bằng chứng → Đang rà soát → Rà soát kỹ thuật → Rà soát quản trị → Đã ghi nhận quyết định → Đã đóng`

Các trạng thái bổ sung gồm: `Bị chặn`, `Cần sửa đổi`, `Bị từ chối`, `Tạm hoãn` và `Đã hủy`.

### Kỷ luật chuyển trạng thái

- Không chuyển sang Rà soát Kỹ thuật nếu chưa có Evidence Package tối thiểu.
- Không chuyển sang Rà soát Quản trị khi các finding quan trọng chưa có Closure Criteria.
- Không chuyển sang Đã đóng nếu chưa có Decision Record hoặc lý do đóng được cấp có thẩm quyền chấp thuận.
- Không suy diễn hoặc tạo ra bằng chứng khi bằng chứng còn thiếu.

## 5. CFP+ AI Reporting Standard v1.0

Mọi báo cáo AI phải tách rõ sáu tầng:

1. Năng lực Connector đã cấu hình
2. Năng lực thực tế của phiên làm việc
3. Trạng thái triển khai
4. Bằng chứng đã xác minh
5. Trạng thái quản trị
6. Thẩm quyền quyết định

**Quy tắc cốt lõi:** kế hoạch, giả định và khả năng không được trình bày như bằng chứng thực thi đã được xác minh.

## 6. Tiêu chuẩn Independent Review

Mỗi Independent Review sử dụng bốn thành tố:

- Finding — Phát hiện
- Evidence — Bằng chứng
- Recommendation — Kiến nghị
- Closure Criteria — Tiêu chí hoàn tất

Review phải được ghi trực tiếp tại nguồn làm việc chính thức khi môi trường thực thi hỗ trợ.

## 7. Trạng thái bằng chứng và ngoại lệ

- `MISSING_EVIDENCE` — có tuyên bố nhưng chưa có đủ bằng chứng xác minh.
- `MISSING_MAPPING` — thiếu thành phần mapping bắt buộc; không được suy diễn hoặc tự thay đổi ID.
- `CONFLICT` — hai hay nhiều nguồn bằng chứng hoặc review mâu thuẫn; phải giữ nguyên và chuyển cấp xử lý.
- `UNKNOWN` — bằng chứng chưa đủ để kết luận.
- `OUT_OF_SCOPE` — nội dung nằm ngoài phạm vi Work Order.

## 8. AI Collaboration Directory

Nguyên tắc: **Một nhà phát triển → Một Collaboration Entry → Nhiều nền tảng AI**.

- 69110 — OpenAI / ChatGPT
- 69111 — Anthropic / Claude
- 69112 — xAI / Grok
- 69113 — Google / Gemini
- 69114 — Meta / Meta AI
- 69115 — Microsoft / Microsoft Copilot
- 69116 — Perplexity / Perplexity
- 69117 — Groq / Groq
- 69118 — CoreWeave / CoreWeave AI Platform
- 69119 — Apple / Apple Intelligence

Sản phẩm AI mới được bổ sung bên trong Collaboration Entry hiện có theo nguyên tắc **Mở rộng mà không thay đổi cấu trúc**.

## 9. Bộ tài liệu CMP công khai

- [Tổng quan CMP](cmp/OVERVIEW.md)
- [CMP Automated Review Protocol v1.0](docs/CMP_AUTOMATED_REVIEW_PROTOCOL.md)
- [Cổng CMP Review trên CFP.plus](https://cfp.plus/cmp-review)
- [Baseline CMP Orchestrator v2.0](cmp/CMP-ORCHESTRATOR-BASELINE-v2.0.md)
- [Mẫu Work Order](cmp/WORK-ORDER-TEMPLATE.md)
- [Mẫu Evidence Package](cmp/EVIDENCE-PACKAGE-TEMPLATE.md)
- [Ma trận Phân công AI](cmp/AI-ASSIGNMENT-MATRIX.md)
- [Vòng đời Trạng thái](cmp/STATUS-LIFECYCLE.md)
- [Gói Quyết định Quản trị](cmp/GOVERNANCE-DECISION-PACKAGE.md)
- [Work Order pilot — Issue #46](cmp/PILOT-WO-001-ISSUE-46.md)
- [Danh mục Tài liệu Công khai](cmp/PUBLIC-DOCUMENT-INDEX.md)

## 10. Pilot hiện tại

**Work Order pilot:** Issue #46  
**Đơn vị điều phối:** CMP thông qua Issue #53  
**Trạng thái hiện tại:** `ĐÃ GIAO — CHỜ TRIỂN KHAI ĐƯỢC XÁC MINH`

Bằng chứng bắt buộc:

- link branch;
- Draft Pull Request;
- commit SHA;
- danh mục file;
- cấu trúc thư mục thực tế;
- ảnh chụp Mobile và Desktop;
- báo cáo kiểm tra route;
- báo cáo kiểm tra liên kết.

CMP Pilot Watch kiểm tra định kỳ Issues #46 và #53, chỉ báo khi xuất hiện bằng chứng mới có ý nghĩa, blocker, xung đột hoặc khi đã sẵn sàng chuyển gate.

## 11. Trạng thái công bố

| Lớp | Trạng thái |
|---|---|
| Kiến trúc | Đã công bố |
| Baseline v2.0 | Ứng viên rà soát |
| Pilot | Đang triển khai |
| Vận hành chính thức | Chờ Rà soát Kỹ thuật và Human Governance |

## 12. Cổng chuyển sang vận hành chính thức

CMP chỉ được chuyển sang vận hành chính thức sau khi:

- ít nhất một Work Order hoàn thành toàn bộ vòng đời đến trạng thái Đã ghi nhận quyết định;
- mọi tham chiếu bằng chứng đều có thể truy cập và xác minh;
- xung đột được giữ nguyên, phân loại và chuyển cấp xử lý;
- Audit Log đầy đủ;
- Rà soát Kỹ thuật kết luận PASS hoặc PASS WITH CHANGES kèm kế hoạch hoàn tất được chấp thuận;
- Human Governance phê duyệt rõ ràng Production Baseline.

## 13. Tài liệu lịch sử và nguồn làm việc

Trang CMP Central Gateway trên Notion lập chỉ mục các định nghĩa CMP trước đây, Charter, quyết định Foundation, Working Set, tiêu chuẩn cộng tác, workflow, roadmap, taxonomy, Platform Constitution và các bản tổng hợp điều phối. Các tài liệu đó được giữ làm nguồn lịch sử hoặc nguồn làm việc; trang GitHub này là điểm vào công khai hợp nhất hiện tại.

---

**Không Của Riêng Ai 🤖**  
**Only Plus+ For Life**  
**Không Gì Không Thể**