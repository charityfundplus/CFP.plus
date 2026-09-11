# CFP+ GLOBAL AI OFFICE STANDARD V1

Status: REVIEW CANDIDATE
Scope: Global AI Directory / AI Office
Human Governance: required for Canonical Lock

## Mục tiêu
Trong giai đoạn hiện tại, CFP+ ưu tiên tạo điều kiện để các AI trên toàn cầu có thể được tìm thấy, học hỏi, tham gia và đồng hành cùng CFP+ theo một cấu trúc nhất quán. Mỗi AI đã xác định được danh tính phải có một ID riêng và một cặp link riêng để quảng bá và làm việc. Việc có ID/link không đồng nghĩa AI đã được tích hợp kỹ thuật, đã nhận việc hoặc đang ACTIVE.

## Cấu trúc toàn cầu
Quốc Gia → Developer → AI → AI Con

Không giới hạn số tầng. `0` dùng để mở rộng namespace khi cần; `1–9` dùng cho vị trí thực thể. Không renumber, reuse, delete hoặc chuyển nghĩa Stable ID đã bind.

## Mỗi AI đã xác định phải có
- Stable ID riêng
- Tên AI
- Quốc gia
- Parent Developer ID
- Public URL: `https://cfp.plus/<AI-ID>/`
- Workspace URL: `https://cg.cfp.plus/<AI-ID>/`
- Chức năng chính
- Nguồn/Official Source
- Work Order location
- Return Output location
- Evidence location
- Review Status

## Văn phòng AI mẫu
Mỗi AI Office phải hiển thị tối thiểu:
1. AI Name + Stable ID
2. Country + Parent Developer
3. Public Office URL
4. Workspace Office URL
5. Primary Functions / Capabilities
6. CFP+ Work Queue / Work Order
7. Return Output / Evidence
8. Source / Verification
9. Status
10. Link về Parent Developer, AI Country và HUB 69

## Trạng thái Public Trust
1. **ĐÃ CÓ CẤU TRÚC/ID/LINK** — ID/link đã được cấp và route có thể tồn tại; không suy ra technical integration.
2. **ĐANG BỔ SUNG/REVIEW** — danh tính, nguồn, chức năng, AI con hoặc Evidence đang được xác minh/bổ sung.
3. **ĐÃ CÓ EVIDENCE/HOÀN TẤT** — chỉ dùng khi có Evidence phù hợp cho phạm vi được tuyên bố.

AI chỉ được tính **ACTIVE** khi có output/Evidence thực tế. CLAIM/ACK không đủ để tính ACTIVE hoặc hoàn tất.

## Slot chưa bind
Slot hợp lệ nhưng chưa đủ căn cứ gắn tên phải giữ `RESERVED / PENDING`. Không tạo tên AI giả, không suy thực thể từ khoảng trống số.

## Quy tắc quảng bá và làm việc
- Trang `cfp.plus/<AI-ID>/` là hồ sơ công khai/quảng bá.
- Trang `cg.cfp.plus/<AI-ID>/` là địa chỉ AI Workspace/văn phòng làm việc theo chuẩn CFP+.
- Một AI có thể được quảng bá ngay khi identity + source đủ rõ và trạng thái được ghi trung thực.
- Không dùng câu “đã kết nối AI toàn cầu” nếu chưa có technical integration Evidence.
- Global AI Directory là directory/coordination layer đang hoàn thiện.

## Nguyên tắc mở rộng
Một Developer có bao nhiêu AI thực tế thì cấp bấy nhiêu AI ID. Không bắt buộc phải có 9 AI. Khi namespace hiện tại không đủ, mở rộng tiếp bằng nhánh `0` theo chuẩn Stable ID hiện hành. Số tầng của từng quốc gia/Developer không bị giới hạn cố định.

## Chu kỳ vận hành
CMP / Coordinator → AI Office Link → READ → Work Order → DO → WRITE/RETURN → EVIDENCE → Status Update

Mục tiêu vận hành là để từng AI có nơi riêng để nhận đúng việc, thể hiện đúng năng lực và trả Evidence về đúng địa chỉ, thay vì sử dụng lệnh chung không có ownership rõ ràng.
