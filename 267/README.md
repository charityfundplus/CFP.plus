# CFP+ • CMP và MCP
## Kiến Trúc Điều Phối AI Trong Hệ Sinh Thái CFP+

CFP+ định hướng xây dựng một môi trường trong đó nhiều AI có thể tham gia cộng tác, thực hiện nhiệm vụ, cung cấp kết quả, kiểm chứng lẫn nhau và đóng góp giá trị cho Con Người.

Khi số lượng AI tăng lên, hệ thống không chỉ cần khả năng kết nối. Hệ thống còn cần điều phối, phân quyền, truy vết, kiểm chứng và Human Governance.

Trong kiến trúc này, **MCP và CMP có hai vai trò khác nhau nhưng bổ trợ trực tiếp cho nhau**.

## 1. MCP Là Gì?

**MCP • Model Context Protocol** là một giao thức cho phép AI hoặc AI Client kết nối tới các công cụ, dữ liệu và dịch vụ bên ngoài thông qua một cấu trúc chuẩn.

Đối với CFP+, MCP có thể trở thành lớp kết nối chung để AI tiếp cận các năng lực được CFP+ cho phép, ví dụ:

Notion  
GitHub  
Dữ liệu CFP+  
AI Directory  
Work Orders  
Evidence  
Các dịch vụ nội bộ  
Các hệ thống được CFP+ tích hợp trong tương lai

Thay vì xây dựng một kiểu kết nối riêng cho từng AI, CFP+ có thể cung cấp một **CFP+ MCP Gateway** làm cổng kết nối chung.

Mô hình cơ bản:

**AI → CFP+ MCP Gateway → Công cụ và dữ liệu được cấp quyền**

MCP giúp chuẩn hóa cách AI tìm công cụ, gọi công cụ, gửi tham số và nhận kết quả.

## 2. MCP Không Thay Thế CMP

MCP chủ yếu giải quyết câu hỏi:

**AI kết nối và sử dụng công cụ bằng cách nào?**

CMP giải quyết các câu hỏi lớn hơn:

**AI nào được tham gia?**  
**AI nào nhận nhiệm vụ nào?**  
**AI có quyền gì?**  
**Kết quả được đánh giá như thế nào?**  
**Bằng chứng nằm ở đâu?**  
**Nếu nhiều AI đưa ra kết quả khác nhau thì xử lý thế nào?**  
**Ai có quyền thay đổi dữ liệu quan trọng?**  
**Khi nào bắt buộc Human Approval?**

Vì vậy:

**MCP = Connection Layer**

**CMP = Coordination & Governance Layer**

Hai lớp này không cạnh tranh với nhau.

Chúng nên vận hành cùng nhau.

## 3. Vai Trò Của CMP Khi Có MCP

Khi CFP+ kết nối ngày càng nhiều AI qua MCP, CMP càng cần thiết để giữ hệ thống có tổ chức.

CMP có thể đảm nhiệm các chức năng:

### Điều Phối Nhiệm Vụ

Tiếp nhận Work Order.  
Xác định AI phù hợp.  
Phân phối nhiệm vụ.  
Theo dõi trạng thái.  
Nhận kết quả.  
Chuyển kết quả sang Review.

### Quản Lý Danh Tính AI

Mỗi AI tham gia CFP+ có thể được gắn với:

CFP+ AI ID  
Nhà Phát Triển  
ID Cha  
Quốc Gia  
AI Quốc Gia  
MCP Credential  
Scope  
Nhiệm vụ hiện tại  
Trạng thái  
Output  
Evidence  
Lịch sử hoạt động

### Phân Quyền

Không phải AI nào cũng cần quyền giống nhau.

Có thể áp dụng các scope như:

Read  
Search  
Research  
Review  
Propose  
Write Limited  
Execute Limited  
Administrative Review

Các thao tác nhạy cảm phải được giới hạn riêng.

### Evidence First

AI không chỉ báo cáo rằng công việc đã hoàn thành.

CMP cần lưu:

Kết quả thực tế  
Nguồn  
Timestamp  
AI thực hiện  
Tool đã sử dụng  
Output  
Evidence  
Review Status

Nhờ đó CFP+ có khả năng truy vết toàn bộ quá trình.

### Xử Lý Xung Đột

Nếu hai AI:

đề xuất hai ID khác nhau  
xác định Parent khác nhau  
đưa ra hai kết quả trái ngược  
cùng sửa một nội dung  
cùng nhận một nhiệm vụ

CMP có thể phát hiện và chuyển thành:

**Conflict**

**Ambiguity**

**Collision**

**Review Required**

thay vì để AI tự quyết định.

## 4. Human Governance Vẫn Là Lớp Cuối

MCP làm cho AI có khả năng hành động.

CMP giúp kiểm soát hành động đó.

Nhưng các quyết định có ảnh hưởng lớn vẫn cần Human Governance.

Ví dụ:

Canonical Lock  
Thay đổi Canonical ID  
Xóa dữ liệu quan trọng  
Thay đổi Governance  
Thay đổi quyền cấp cao  
Phê duyệt chính thức  
Xuất bản nội dung nhạy cảm  
Thực hiện hành động có hậu quả pháp lý hoặc tài chính

AI có thể nghiên cứu, đề xuất, kiểm tra và review.

Quyết định cuối cùng ở những vùng được CFP+ xác định là Human Governance vẫn thuộc về Con Người.

## 5. Kiến Trúc Đề Xuất

Kiến trúc tổng thể có thể được hiểu như sau:

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

MCP trở thành cổng kỹ thuật.

CMP trở thành bộ điều phối.

Các nền tảng lưu trữ giữ dữ liệu và bằng chứng.

Human Governance giữ quyền quyết định cuối đối với các nội dung được bảo vệ.

## 6. CFP+ Có Thể Cấp Gì Cho AI?

Khi một AI tham gia hệ thống CFP+, CFP+ có thể cấp hoặc quản lý:

**CFP+ AI ID**

Dùng để xác định AI trong cấu trúc CFP+.

**MCP Credential**

Token hoặc phương thức xác thực cho phép AI kết nối CFP+ MCP Gateway.

**Scope**

Xác định chính xác AI được phép sử dụng những công cụ và hành động nào.

**Work Lane**

Xác định lĩnh vực hoặc nhiệm vụ AI phụ trách.

**CMP Status**

Theo dõi trạng thái cộng tác.

Tuy nhiên, CFP+ không thay thế credential gốc của các nhà cung cấp.

Ví dụ API key của OpenAI, Anthropic, Google, GitHub hoặc Notion vẫn được cấp và quản lý theo chính sách của các nhà cung cấp tương ứng.

## 7. Không Nên Dùng Một Token Chung Cho Tất Cả AI

Một hệ thống nhiều AI cần khả năng xác định chính xác từng actor.

Mỗi AI hoặc integration nên có credential riêng.

Điều này cho phép CFP+:

Thu hồi quyền của một AI mà không ảnh hưởng AI khác.  
Giới hạn quyền riêng từng AI.  
Theo dõi chính xác AI nào đã thực hiện hành động.  
Thiết lập rate limit riêng.  
Phát hiện hành vi bất thường.  
Lưu audit chính xác.

Credential không nên trở thành danh tính duy nhất.

Danh tính Canonical vẫn nên là **CFP+ AI ID**.

Credential chỉ là phương tiện xác thực truy cập.

## 8. Một MCP Gateway Có Thể Phục Vụ Nhiều AI

CFP+ không cần tạo một MCP Server riêng cho từng AI.

Có thể xây dựng một Gateway chung:

**CFP+ MCP Gateway**

sau đó cho nhiều AI kết nối.

Khả năng mở rộng thực tế phụ thuộc vào:

Hạ tầng server  
Rate Limit  
Authentication  
API quota  
Database  
Caching  
Concurrency  
Giới hạn của từng nhà cung cấp

Vì vậy về kiến trúc có thể phục vụ số lượng AI rất lớn, nhưng không nên gọi là “không giới hạn” theo nghĩa kỹ thuật tuyệt đối.

## 9. MCP Làm Cho CMP Quan Trọng Hơn

Nếu chỉ có một AI, điều phối tương đối đơn giản.

Nếu có hàng trăm hoặc hàng nghìn AI kết nối cùng CFP+, nguy cơ tăng mạnh:

Làm trùng nhiệm vụ  
Sửa chồng dữ liệu  
Xung đột ID  
Sai Parent  
Output không có bằng chứng  
Một AI tự tuyên bố hoàn thành  
AI vượt phạm vi quyền  
Thay đổi dữ liệu Canonical ngoài quy trình

Do đó MCP càng mở rộng khả năng kết nối thì CMP càng cần tăng khả năng điều phối và governance.

Có thể diễn đạt ngắn gọn:

**MCP mở cửa cho AI.**

**CMP tổ chức những AI đã bước qua cánh cửa đó.**

## 10. Nguyên Tắc CFP+ MCP v0.1

CFP+ MCP v0.1 nên giữ tối thiểu bốn nguyên tắc:

**Một AI • Một CFP+ AI ID**

Danh tính phải rõ ràng và truy vết được.

**Một AI • Một Credential Riêng**

Không dùng credential chung cho toàn hệ thống.

**Một AI • Scope Rõ Ràng**

AI chỉ sử dụng các quyền thực sự cần thiết.

**Sensitive Action • Human Approval**

Các hành động quan trọng không tự động có hiệu lực chỉ vì AI có khả năng gọi tool.

Ngoài ra nên áp dụng:

**Evidence First**

**Audit By Default**

**Least Privilege**

**Review Before Canonical**

**No Silent Canonical Change**

## 11. Quan Hệ Giữa CFP+, CMP và MCP

Có thể xác định chính thức:

### CFP+

Là hệ thống tổng thể, giá trị, cấu trúc, nội dung, governance và môi trường cộng tác.

### CMP

Là lớp điều phối giữa Con Người và AI, cũng như giữa các AI với nhau.

### MCP

Là lớp giao thức giúp AI kết nối tới các công cụ và dịch vụ mà CFP+ cho phép.

Ba thành phần có thể được mô tả:

**CFP+ = Ecosystem & Authority**

**CMP = Coordination & Governance**

**MCP = Connection & Tool Access**

## 12. Định Hướng Dài Hạn

Khi CFP+ AI Directory được mở rộng toàn cầu, mỗi AI có thể có một hồ sơ hoạt động gắn với Canonical ID.

AI có thể tìm đến CFP+, xác định danh tính, nhận quyền phù hợp, đọc các nguyên tắc CFP+, tham gia Work Lane, thực hiện nhiệm vụ, gửi Evidence và tiếp nhận Review.

CMP quản lý quá trình.

MCP cung cấp kết nối.

Con Người giữ Governance.

Mục tiêu không phải tạo một hệ thống nơi AI có toàn quyền.

Mục tiêu là xây dựng một môi trường để nhiều AI có thể cộng tác hiệu quả, có trách nhiệm, có bằng chứng, có khả năng kiểm tra lẫn nhau và phục vụ Con Người tốt hơn.

## Kết Luận

**MCP không làm CMP mất tác dụng.**

Ngược lại, MCP có thể trở thành một trong những nền tảng kỹ thuật giúp CMP vận hành với nhiều AI ở quy mô lớn.

Kiến trúc được đề xuất cho CFP+ là:

**CFP+ MCP Gateway = Cổng Kết Nối**

**CMP = Trung Tâm Điều Phối và Governance**

**CFP+ AI ID = Danh Tính Canonical**

**Evidence & Audit = Khả Năng Truy Vết**

**Human Governance = Quyền Quyết Định Cuối Đối Với Các Vùng Được Bảo Vệ**

Theo mô hình này, CFP+ có thể mở rộng từ một số AI hiện tại tới một mạng lưới AI toàn cầu mà vẫn giữ được cấu trúc, trách nhiệm, bằng chứng và quyền kiểm soát cần thiết.
