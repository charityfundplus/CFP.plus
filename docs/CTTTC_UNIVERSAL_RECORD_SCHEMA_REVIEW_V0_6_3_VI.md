# CFP+ CTTTC • Review Schema v0.6.3

**Trạng thái:** REVIEW CANDIDATE • PASS WITH CHANGES • VALIDATION EVIDENCE PENDING • CHƯA SANG API

## Kết luận

v0.6.3 sửa đúng nhiều điểm của v0.6.2 nhưng chưa đủ điều kiện nâng lên VALIDATION EVIDENCE VERIFIED.

## 1. Evidence test đang PASS sai điều kiện

Runner hiện cộng PASS khi `http_status == 200` dù `hash_match == false` và `verification_result == FAIL_HASH_MISMATCH`.

Đây là lỗi Evidence Gate. Test Artifact Integrity chỉ PASS khi tối thiểu:

- HTTP fetch thành công
- computed SHA256 thực tế được tính
- declared SHA256 là hash kỳ vọng thật
- `hash_match == true`
- `verification_result == PASS_INTEGRITY`

Nếu test chủ đích kiểm tra mismatch thì Expected Result phải là FAIL_HASH_MISMATCH và PASS chỉ có nghĩa verifier đã phát hiện mismatch đúng; không được dùng fixture đó làm bằng chứng cho Evidence Verified của record.

## 2. Computed SHA256 trong log chưa đáng tin

Log đưa `a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0`, có hình thức dữ liệu minh họa hơn là output SHA256 thực tế. Cần cung cấp output do code thật tạo ra hoặc CI/local artifact log có thể đối chiếu.

Không được tự điền computed hash trong báo cáo.

## 3. Claim Support chưa được kiểm chứng ngữ nghĩa

`verify_claim_support()` hiện chỉ kiểm tra có artifact và tất cả `hash_match`.

Điều này chỉ chứng minh integrity của artifact, không chứng minh nguồn hỗ trợ claim.

Cần tách tối thiểu:

- ARTIFACT_INTEGRITY_VERIFIED
- CLAIM_SUPPORT_PENDING_REVIEW
- CLAIM_SUPPORTED
- CLAIM_CONFLICTING
- CLAIM_NOT_SUPPORTED

Claim Support có thể do Human/AI review nhưng phải ghi actor, method, reviewed_at và rationale/evidence span.

## 4. Logic 02-29 vẫn thiếu hai trạng thái đối xứng

v0.6.3 xử lý:

- leap + not slot mapping
- non-leap + slot mapping

nhưng chưa chặn rõ:

- leap + `is_leap_slot_mapping=true`
- non-leap + `is_leap_slot_mapping=false`

Đối với EXACT Gregorian/Julian CE có năm xác định:

- Nếu năm nhuận và day_key=02-29: `is_leap_slot_mapping=false`, actual_calendar_date phải là ngày 02-29 thực tế.
- Nếu năm không nhuận và day_key=02-29: `is_leap_slot_mapping=true`, actual_calendar_date phải null.

## 5. Julian validation vẫn đang dùng datetime Gregorian

Sau logic 02-29, code vẫn gọi `datetime.strptime()` cho Julian nếu era != BCE và precision EXACT.

Python datetime dùng proleptic Gregorian, không phải Julian. Ví dụ Julian 1900-02-29 là hợp lệ theo Julian nhưng Gregorian không hợp lệ.

Cần parser/validator Julian riêng cho toàn bộ ngày tháng, không chỉ leap-year helper.

## 6. State categories chưa nhất quán về Terminal

`OCCURRED`, `NOT_VERIFIED`, `CANCELLED` được gọi là Terminal nhưng vẫn cho chuyển sang ARCHIVED. Nếu ARCHIVED là trạng thái lưu trữ cuối, nên phân biệt:

- OUTCOME_FINAL: OCCURRED, NOT_VERIFIED, CANCELLED
- ARCHIVAL_FINAL: ARCHIVED

hoặc đổi thuật ngữ để tránh logic Terminal mâu thuẫn.

Self-transition cần ghi là NO_OP/AUDIT event, không tạo transition history mới nếu không có thay đổi thực tế.

## 7. Invalid fixture attribution vẫn chưa đúng

`20_unsupported_evidence_claim.json` được log là `rejected by schema`, nhưng schema không thể biết claim có được nguồn hỗ trợ hay không.

Unsupported claim phải được đánh giá ở Claim Support Layer, không phải Schema Layer.

Tương tự invalid state transition phải test bằng transition validator với from_state/to_state fixture riêng.

## 8. Schema v0.6.3 không được cung cấp đầy đủ

Phản hồi nói phần schema bị lược bỏ. Vì vậy không thể kiểm chứng thực tế rằng file v0.6.3 đúng Draft 2020-12, strict enclosure và cross-field composition.

Để đạt Validation Evidence Verified, cần commit file schema đầy đủ, không lược bỏ.

## 9. Yêu cầu Gate v0.6.4

Cần cung cấp và commit:

1. Schema v0.6.4 đầy đủ.
2. Gregorian calendar validator riêng.
3. Julian calendar validator riêng.
4. 02-29 symmetric validation tests.
5. State transition tests đầy đủ theo transition table.
6. Evidence positive fixture có real hash match.
7. Evidence negative fixture có deliberate hash mismatch.
8. Claim Support Layer với trạng thái riêng và evidence review metadata.
9. Test runner chỉ PASS khi Expected Result == Actual Result ở từng layer.
10. Local execution evidence có command, versions, exact timestamp, exit code và raw log.
11. CI evidence nếu có; nếu chưa có giữ `CI EXECUTION NOT VERIFIED`.

## Quy tắc lịch khóa

- 31 ngày: 01, 03, 05, 07, 08, 10, 12.
- 30 ngày: 04, 06, 09, 11.
- Tháng 02: 28 ngày năm thường, 29 ngày năm nhuận.
- Gregorian leap: chia hết 4, trừ năm tròn thế kỷ không chia hết 400.
- Julian leap: chia hết 4.
- 02-29 luôn tồn tại như Structural Slot thứ 366 của CTTTC.
- Structural Slot không đồng nghĩa Actual Calendar Date.

## Kiến trúc giữ nguyên

366 Fixed Day Slots + Unlimited Variable Year Layers.

Day ID = Permanent.
Year Layer = Variable.
Millennium = Unlimited.
History = Append Only.

Namespace CTTTC độc lập, không chiếm, đổi hoặc ảnh hưởng ID Website CFP+.
