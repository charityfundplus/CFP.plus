# WO-META-WEB-CONTENT-001

Status: READY FOR EXECUTION • EVIDENCE REQUIRED
Primary AI: Meta Model API
Purpose: Viết nội dung Website CFP+ tiếng Việt theo từng Chương và trả kết quả về CMP.

## Scope

Meta xử lý từng Chương theo cơ chế cuốn chiếu:

1. Hoàn thành Chương đang được giao.
2. Trả toàn bộ output về CMP.
3. CMP review.
4. Nội dung đạt review được đưa vào đúng Chương trên Website.
5. Chỉ sau đó chuyển sang Chương kế tiếp.

Ưu tiên đầu tiên: Chương 0 • Nền Tảng CFP+.

## Required fields per ID

- Canonical ID
- Tên bài
- Câu hỏi chính
- Câu hỏi phụ
- Nội dung Website tiếng Việt
- Thông điệp Vì Sự Sống
- Evidence / nguồn cần kiểm chứng
- Parent mapping
- Review status

## Guardrails

- Không tự đổi ID.
- Không renumber.
- Không tự tạo Canonical ID mới.
- Không Governance Approve.
- Không Canonical Lock.
- Nếu thiếu bằng chứng: EVIDENCE REQUIRED.
- Output mặc định: DRAFT / REVIEW CANDIDATE.

## Automation target

CMP -> Meta Model API -> response artifact -> CMP review -> website chapter implementation.

Integration status remains EVIDENCE REQUIRED until a real API execution succeeds and the returned artifact is verified.
