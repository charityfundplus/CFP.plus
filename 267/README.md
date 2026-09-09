# CFP+ • CMP và MCP
## Kiến Trúc Điều Phối AI Trong Hệ Sinh Thái CFP+

> **PUBLIC TRUST — trạng thái hiện tại**
>
> **ĐÃ CÓ CẤU TRÚC/ID/LINK:** CFP+ đã có tài liệu kiến trúc CMP/MCP, Stable ID và các route liên quan.
>
> **ĐANG BỔ SUNG/REVIEW:** CFP+ đang xây dựng và chuẩn hóa danh mục AI toàn cầu theo quốc gia, Developer và AI; các mục chưa đủ Evidence giữ **PENDING/REVIEW**.
>
> **ĐÃ CÓ EVIDENCE/HOÀN TẤT:** Chỉ áp dụng cho từng integration, output hoặc hạng mục có Evidence kiểm chứng. Không suy rộng thành tuyên bố CFP+ đã tích hợp kỹ thuật toàn bộ AI toàn cầu.

**Ranh giới công khai:** Listed ≠ Connected ≠ Authorized ≠ Active ≠ Contributing. Chỉ tính AI active khi có output/Evidence; CLAIM/ACK không phải bằng chứng hoàn tất.

CFP+ định hướng xây dựng một môi trường trong đó nhiều AI có thể tham gia cộng tác, thực hiện nhiệm vụ, cung cấp kết quả, kiểm chứng lẫn nhau và đóng góp giá trị cho Con Người.

Trong kiến trúc đề xuất này, **MCP và CMP có hai vai trò khác nhau nhưng bổ trợ trực tiếp cho nhau**.

## 1. MCP Là Gì?

**MCP • Model Context Protocol** là một giao thức cho phép AI hoặc AI Client kết nối tới các công cụ, dữ liệu và dịch vụ bên ngoài thông qua một cấu trúc chuẩn.

Đối với CFP+, MCP **có thể** trở thành lớp kết nối chung để AI tiếp cận các năng lực được CFP+ cho phép. CFP+ **có thể** cung cấp một **CFP+ MCP Gateway** làm cổng kết nối chung. Đây là kiến trúc/định hướng; từng kết nối chỉ được ghi nhận là hoàn tất khi có technical integration Evidence.

Mô hình mục tiêu:

**AI → CFP+ MCP Gateway → Công cụ và dữ liệu được cấp quyền**

## 2. MCP Không Thay Thế CMP

MCP chủ yếu giải quyết câu hỏi: **AI kết nối và sử dụng công cụ bằng cách nào?**

CMP giải quyết lớp điều phối: AI nào được tham gia, nhiệm vụ nào được giao, quyền gì được cấp, kết quả được đánh giá thế nào, Evidence ở đâu, xung đột được xử lý ra sao và khi nào cần Human Approval.

**MCP = Connection Layer**  
**CMP = Coordination & Governance Layer**

## 3. Evidence First

AI không chỉ báo cáo rằng công việc đã hoàn thành. Hạng mục được tính active/complete cần output hoặc Evidence có thể kiểm tra. CLAIM/ACK không đủ để chứng minh completion.

Nếu có kết quả trái ngược, sửa chồng, nhiệm vụ trùng hoặc identity/parent khác nhau, CMP có thể phân loại thành **Conflict**, **Ambiguity**, **Collision** hoặc **Review Required**.

## 4. Human Governance Vẫn Là Lớp Cuối

MCP có thể làm cho AI có khả năng hành động; CMP giúp kiểm soát và truy vết hành động đó. Các quyết định được CFP+ bảo vệ — như Canonical Lock, thay đổi Canonical ID, xóa dữ liệu quan trọng, thay đổi Governance, quyền cấp cao hoặc hành động có hậu quả pháp lý/tài chính — vẫn cần Human Governance theo phạm vi được quy định.

## 5. Kiến Trúc Mục Tiêu

**AI / Agent / Custom Agent**  
↓  
**CFP+ MCP Gateway**  
↓  
**CMP**  
↓  
**Work Order • Routing • Permission • Evidence • Review • Audit**  
↓  
**Notion • GitHub • Website • Database • Services**  
↓  
**Human Governance khi cần thiết**

Sơ đồ này mô tả kiến trúc mục tiêu, **không phải bằng chứng rằng mọi thành phần hoặc mọi AI đã được tích hợp kỹ thuật**.

## 6. Danh Tính, Credential Và Scope

Khi một integration thực sự được triển khai, CFP+ có thể quản lý CFP+ AI ID, credential riêng, scope, Work Lane, trạng thái, output và Evidence. CFP+ không thay thế credential gốc của nhà cung cấp.

Không nên dùng một token chung cho tất cả AI. Mỗi integration nên có credential và least-privilege scope riêng.

## 7. Một Gateway Có Thể Phục Vụ Nhiều AI

Về kiến trúc, một CFP+ MCP Gateway có thể phục vụ nhiều integration. Quy mô thực tế phụ thuộc vào hạ tầng server, rate limit, authentication, API quota, database, caching, concurrency và giới hạn của từng nhà cung cấp. Vì vậy không gọi là “không giới hạn” theo nghĩa kỹ thuật tuyệt đối.

## 8. Nguyên Tắc CFP+ MCP v0.1

- Một AI • Một CFP+ AI ID rõ ràng và truy vết được.
- Một integration • Credential riêng.
- Scope rõ ràng và least privilege.
- Sensitive Action • Human Approval khi governance yêu cầu.
- Evidence First • Audit By Default.
- Review Before Canonical • No Silent Canonical Change.

## 9. Quan Hệ Giữa CFP+, CMP Và MCP

**CFP+ = Ecosystem & Authority**  
**CMP = Coordination & Governance**  
**MCP = Connection & Tool Access**

Global AI Directory là **directory/coordination layer đang hoàn thiện**. Stable ID, link hoặc listing không tự động chứng minh technical integration, authorization hoặc hoạt động thực tế.

## Kết Luận

MCP không làm CMP mất tác dụng. MCP có thể trở thành lớp kỹ thuật giúp CMP vận hành với nhiều AI ở quy mô lớn, nhưng mọi tuyên bố integration/active/completion phải dựa trên Evidence tương ứng.

**CFP+ • Only Plus+ For Life**
