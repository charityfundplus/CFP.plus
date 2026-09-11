# CFP+ CMP MCP AI Routing And Evidence Protocol V1

Status: REVIEW CANDIDATE

Purpose: tạo một chuẩn điều phối AI có thể kiểm chứng bằng Output và Evidence, đủ rõ để Con Người, Cộng Đồng, Doanh Nghiệp và Tổ Chức đánh giá hoạt động thật của CFP+.

## 1. Nguyên tắc cốt lõi

1. Work Order là đơn vị công việc chuẩn.
2. CMP chịu trách nhiệm nhận việc, kiểm tra phạm vi, chọn AI, điều phối trạng thái, thu Evidence và chuyển Review.
3. MCP là lớp kết nối công cụ và hệ thống khi kết nối tương ứng đã được cấu hình và kiểm chứng.
4. Stable ID và Link dùng để nhận diện. Stable ID hoặc Link không chứng minh AI đã thực thi.
5. AI chỉ được ghi nhận Active hoặc Contributing khi có Output và Evidence phù hợp.
6. Không đổi Stable ID đã bind. Không tái sử dụng Stable ID. Không dịch chuyển Stable ID.
7. Human Governance giữ quyền quyết định tại các vùng được bảo vệ.

## 2. Vòng đời Work Order

Receive → Validate → Route → Acknowledge → Execute → Return Output → Evidence → Review → Decision → Publish hoặc Rework

Mỗi bước phải có timestamp, actor, trạng thái và artifact tham chiếu khi bước đó có phát sinh hành động.

## 3. Capability Based Routing

CMP chấm điểm ứng viên theo sáu nhóm tiêu chí:

1. Phù hợp chuyên môn.
2. Quyền truy cập cần thiết.
3. Khả năng đọc và ghi trên hệ thống đích.
4. Khả năng tạo Evidence truy vết.
5. Độ tin cậy từ các Work Order trước.
6. Khả năng hoàn tất trong phạm vi và thời gian yêu cầu.

AI có điểm phù hợp cao nhất được chọn làm Primary Actor. Một hoặc nhiều AI có thể được chọn làm Reviewer hoặc Backup Actor khi cần.

## 4. Xử lý AI mới và AI cũ

AI mới không bị loại chỉ vì chưa có lịch sử trong CFP+.

AI mới được phép nhận Work Order thử nghiệm có phạm vi nhỏ để kiểm chứng Capability.

AI cũ được ưu tiên khi có Evidence lịch sử phù hợp nhưng không được mặc định giữ vai trò nếu AI khác phù hợp hơn.

Kết quả Work Order được dùng để cập nhật Capability Profile và chất lượng Evidence của từng AI.

## 5. Timeout, Retry và Reassignment

1. Nếu AI không Acknowledge trong thời hạn của Work Order, CMP ghi Timeout và chuyển sang Backup Actor.
2. Nếu AI Acknowledge nhưng không có Output trong thời hạn, CMP ghi Execution Timeout và chuyển hoặc chia lại phạm vi.
3. Nếu Output không có Evidence tối thiểu, trạng thái giữ Awaiting Evidence.
4. Nếu Output xung đột với Output khác, CMP ghi CONFLICT và chuyển Independent Review.
5. Không xóa dấu vết thất bại, timeout hoặc reassignment khỏi Audit Log.

## 6. Evidence Gate tối thiểu

Một Work Order chỉ được tính là Executed khi có đủ các thành phần sau theo phạm vi áp dụng:

1. Work Order ID.
2. Primary Actor và Stable AI ID nếu đã bind.
3. Input hoặc source version.
4. Acknowledge timestamp hoặc session evidence.
5. Output artifact.
6. Evidence artifact hoặc log có thể truy vết.
7. Verification hoặc read back khi có thao tác ghi.
8. Review result.
9. Human Governance decision nếu Work Order đi qua governance gate.

Không Evidence nghĩa là không có Completion Claim.

## 7. Trạng thái chuẩn

Prepared → Dispatched → Accepted → Executing → Output Returned → Evidence Verified → Reviewed → Decision Recorded → Closed

Trạng thái bổ sung:

Timeout

Reassigned

Awaiting Evidence

Conflict

Blocked

Needs Revision

Rejected

## 8. Public Proof Model

Để chứng minh cho Con Người, Cộng Đồng, Doanh Nghiệp và Tổ Chức, CFP+ cần công khai được tối thiểu các dữ kiện sau cho từng Work Order đủ điều kiện công khai:

1. Work Order ID.
2. AI đã nhận việc.
3. Nhiệm vụ được giao.
4. Thời điểm nhận việc.
5. Output đã trả.
6. Evidence đã xác minh.
7. Reviewer.
8. Kết luận.
9. Trạng thái hiện tại.

Nội dung nhạy cảm, token, credential, secret và dữ liệu riêng tư không được công khai.

## 9. Demo P0 End To End

Mục tiêu Demo P0 là chứng minh một Work Order đi hết chuỗi:

Receive → Route → Acknowledge → Execute → Return Output → Evidence → Review

Demo phải đáp ứng:

1. Work Order thật.
2. AI Actor thật có session hoặc connector evidence.
3. Output thật.
4. Evidence thật.
5. Review độc lập hoặc verification rõ ràng.
6. Public summary đủ để người ngoài hiểu điều gì đã xảy ra.

Demo đầu tiên không cần chứng minh toàn bộ CFP+ đã tự động hóa. Demo chỉ chứng minh đúng Capability đã chạy thành công.

## 10. Tự động hóa CMP

CMP có thể tự động:

1. Chuẩn hóa Work Order.
2. Đọc Capability Profile.
3. Chọn ứng viên.
4. Dispatch.
5. Theo dõi timeout.
6. Retry và reassignment.
7. Thu Evidence reference.
8. Kiểm tra completeness.
9. Đồng bộ trạng thái.
10. Sinh Public Summary và Audit Log.

CMP không tự động:

1. Đổi Stable ID đã khóa.
2. Canonical Lock.
3. Governance Approval.
4. Xóa Evidence bất lợi.
5. Tạo Evidence giả.
6. Công bố secret hoặc dữ liệu riêng tư.

## 11. Kết quả cần đo

1. Tỷ lệ Work Order có Acknowledge.
2. Tỷ lệ Work Order có Output.
3. Tỷ lệ Output có Evidence đạt chuẩn.
4. Thời gian trung vị từ Dispatch tới Output.
5. Tỷ lệ timeout.
6. Tỷ lệ reassignment thành công.
7. Tỷ lệ Review PASS.
8. Số Work Order có Public Proof đủ chuẩn.

## 12. Nguyên tắc chứng minh

CFP+ không chứng minh sức mạnh AI bằng số lượng tên AI trong danh mục.

CFP+ chứng minh bằng Work Order có Output, Evidence, Review và lịch sử truy vết.

Only Plus+ For Life
