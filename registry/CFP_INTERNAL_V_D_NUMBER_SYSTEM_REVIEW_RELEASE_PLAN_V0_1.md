# CFP+ • V & D • BỘ SỐ NỘI BỘ • REVIEW & RELEASE PLAN

## Phạm vi
V và D là hai hệ riêng biệt, chỉ dùng nội bộ CFP+ trong giai đoạn hiện tại.

## V • Bộ Số Cổ La Mã
Mục tiêu: lưu trữ, chuẩn hóa, đối chiếu và bảo toàn bộ số cổ La Mã như một hệ tham chiếu độc lập.
Trạng thái: ARCHIVE / REFERENCE / INTERNAL.
Không dùng V làm nhóm Chương, không dùng V thay Canonical ID số hiện hành.

## D • Bộ Số Chữ Mới
Mục tiêu: đề xuất một bộ ký hiệu chữ mới để quy định và ánh xạ ra số theo quy tắc CFP+.
Trạng thái hiện tại: DRAFT • REVIEW REQUIRED • INTERNAL ONLY.
D là hệ riêng với V và riêng với 4 nhóm số 000 • 135 • 246 • 789.

## Nguyên tắc thiết kế D
1. Nhóm Chữ phải ánh xạ xác định ra số hoặc dãy số.
2. Một ký hiệu chỉ có một nghĩa trong cùng phiên bản.
3. Không làm thay đổi Canonical ID số đang dùng.
4. Không tự động thay thế 000 • 135 • 246 • 789.
5. Phải đọc được bằng Con Người và AI.
6. Phải có bảng tra hai chiều Chữ ⇄ Số.
7. Phải có version, provenance, reviewer, trạng thái và ngày phát hành.
8. Trước khi phát hành phải kiểm tra collision, ambiguity, leading zero và khả năng mở rộng.

## Kế hoạch phát hành D
Phase 0 • Thu thập yêu cầu và khóa phạm vi nội bộ.
Phase 1 • Đề xuất bảng chữ và công thức ánh xạ Chữ → Số.
Phase 2 • Review logic, collision, ambiguity, machine readability, human readability.
Phase 3 • Pilot nội bộ trên dữ liệu mẫu, không tác động Canonical ID.
Phase 4 • Review Complete và lập Release Candidate.
Phase 5 • Human Governance quyết định phát hành nội bộ.
Phase 6 • Phát hành D v1.0 INTERNAL và lưu bảng mapping bất biến theo version.

## Hồ sơ bắt buộc trước khi phát hành
Alphabet / Symbol Set
Mapping Rule
Reverse Mapping Rule
Reserved Symbols
Collision Matrix
Leading Zero Rule
Examples
Migration / Compatibility Note
Reviewer Notes
Release Notes
Version
Effective Date

## Guardrail
Không công khai ra ngoài CFP+ trong giai đoạn review.
Không Canonical Lock trước Human Governance.
Không dùng D để đổi ID số hiện hành.
Không gộp V và D thành một hệ.
