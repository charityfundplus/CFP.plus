# CFP+ CTTTC • Review Schema v0.6.1

**Trạng Thái:** REVIEW CANDIDATE • PASS WITH CHANGES • VALIDATION EVIDENCE PENDING • CHƯA SANG API

## Kết Luận

Bản v0.6.1 đã tiến bộ rõ rệt ở cấu trúc 366 Fixed Day Slots, Structured Historical Time, State Transition Table, Evidence Verification Layer và kiểm tra lịch tháng. Tuy nhiên chưa đủ điều kiện nâng lên VALIDATION EVIDENCE VERIFIED do còn một số lỗi logic và bằng chứng thực thi chưa đầy đủ.

## 1. Lỗi logic 02-29 trong calendar_validator.py

Đoạn kiểm tra hiện tại cho phép trường hợp năm không nhuận, `day_key = 02-29`, `is_leap_slot_mapping = true` và `actual_calendar_date` vẫn được điền. Đây là sai.

Quy tắc đúng:

- Nếu `day_key = 02-29` và năm Gregorian không nhuận thì `actual_calendar_date` bắt buộc phải là `null`.
- `is_leap_slot_mapping = true` chỉ cho biết record đang dùng Structural Slot 02-29, không hợp pháp hóa một ngày thực tế không tồn tại.
- Nếu năm Gregorian là năm nhuận và `actual_calendar_date` được cung cấp, ngày phải đúng là `YYYY-02-29` và phải khớp `numeric_value`.

## 2. Gregorian và Julian không dùng chung leap-year validator

`is_leap_year()` hiện áp quy tắc Gregorian cho tất cả record. Với `calendar_type = Julian`, quy tắc năm nhuận khác: năm chia hết cho 4 là năm nhuận, không áp ngoại lệ 100/400 như Gregorian.

Validator phải dispatch theo `calendar_type`:

- Gregorian: divisible by 4, except 100 unless divisible by 400.
- Julian: divisible by 4.
- Approximate / Unknown: không được giả lập chính xác; cần giữ trạng thái bất định hoặc bỏ qua validation lịch chính xác.

## 3. `numeric_value` phải là integer cho năm chính xác

Schema hiện cho `numeric_value` kiểu `number`, cho phép số thập phân như `2026.5`. Với `precision = EXACT`, `DECADE`, `CENTURY` hoặc year anchor, nên dùng integer hoặc có cross-field rule bắt buộc giá trị nguyên.

Không nên dùng floating-point để biểu diễn năm lịch.

## 4. BCE không thể dùng trực tiếp Python datetime

`datetime.strptime` không hỗ trợ năm BCE/negative year. Vì vậy `actual_calendar_date` ISO chỉ nên áp dụng cho các trường hợp phù hợp với ISO/Gregorian CE mà runtime hỗ trợ.

BCE, Julian cổ hoặc Approximate phải dựa vào `temporal_position` và validator lịch riêng, không ép qua `datetime.strptime`.

## 5. Quy tắc tháng cần khóa rõ

Structural Day Slots CTTTC:

- 31 ngày: 01, 03, 05, 07, 08, 10, 12
- 30 ngày: 04, 06, 09, 11
- Tháng 02: 28 ngày năm thường, 29 ngày năm nhuận
- `02-29` vẫn luôn tồn tại như Structural Slot thứ 366 của CTTTC

Các ngày không hợp lệ phải bị từ chối cho actual calendar date: `02-30`, `02-31`, `04-31`, `06-31`, `09-31`, `11-31`.

## 6. State Machine chưa được test đầy đủ

Transition table là đúng hướng, nhưng 4 transition tests chưa đủ. Cần test toàn bộ cạnh hợp lệ và một tập cạnh cấm, đặc biệt:

- ARMED_COUNTDOWN → RUNNING
- RUNNING → REACHED_TARGET
- REACHED_TARGET → VERIFY_ACTUAL_OUTCOME
- VERIFY_ACTUAL_OUTCOME → từng outcome
- DELAYED → RUNNING
- OCCURRED → ARCHIVED
- các bước nhảy cấm như RUNNING → OCCURRED, REACHED_TARGET → OCCURRED, ARCHIVED → RUNNING

`from_state == to_state` hiện luôn trả True. Cần quyết định rõ self-transition có được phép cho tất cả trạng thái hay chỉ một số trạng thái idempotent. Không nên mặc định cho phép toàn bộ.

## 7. Cross-field outcome rules chưa đủ chặt

Hiện chỉ yêu cầu `actual_outcome_status` không null khi status thuộc nhóm outcome. Cần thêm:

- `event_status = OCCURRED` → `actual_outcome_status = OCCURRED`
- `CHANGED` → `CHANGED`
- `DELAYED` → `DELAYED`
- `CANCELLED` → `CANCELLED`
- `NOT_VERIFIED` → `NOT_VERIFIED`
- `VERIFY_ACTUAL_OUTCOME` → `actual_outcome_status` phải null cho đến khi xác minh xong
- outcome nào yêu cầu evidence thì phải enforce minItems phù hợp

## 8. schedule_history append-only chưa được chứng minh

Hàm hiện chỉ kiểm tra entry cuối khớp `current_target_datetime`. Chưa kiểm tra:

- continuity giữa `new_target` của entry trước và `previous_target` của entry sau
- thứ tự `changed_at`
- `original_target_datetime` không bị thay đổi
- lịch sử cũ không bị xóa hoặc sửa giữa hai phiên bản record

Phần append-only phải được enforce ở service/backend khi update record.

## 9. Evidence fixture vẫn có hash giả

Fixture mẫu dùng:

`c000000000000000000000000000000000000000000000000000000000000000`

Đây chỉ là chuỗi 64 hex hợp lệ về cú pháp, chưa phải SHA256 được chứng minh của README thật.

Do đó không được đánh dấu fixture này là `Verified` nếu Evidence Verification Layer chưa tải artifact và cho `hash_match = true`.

Quy tắc giữ nguyên:

- Real URL ≠ Valid Evidence
- 64 hex ≠ Verified Hash
- URL thật + hash sai = FAIL
- URL thật + claim không được nguồn hỗ trợ = FAIL

## 10. Báo cáo execution chưa đủ để VERIFIED

Actual Execution Output được cung cấp dưới dạng văn bản, nhưng chưa có repository artifacts tương ứng, CI log, commit chứa schema/test runner/fixtures, hoặc output file có thể đối chiếu.

Trạng thái phù hợp hiện tại:

**VALIDATION REPORTED** hoặc **VALIDATION EVIDENCE PENDING**

Chưa phải:

**VALIDATION EVIDENCE VERIFIED**

## Gate tiếp theo

Cần hoàn thiện bản v0.6.2 hoặc equivalent với:

1. Sửa validator 02-29.
2. Tách Gregorian / Julian leap validation.
3. Khóa numeric year semantics.
4. Xử lý BCE/Approximate không qua datetime thông thường.
5. Test toàn bộ transition table và self-transition policy.
6. Siết cross-field outcome consistency.
7. Test schedule history continuity và append-only ở business layer.
8. Dùng SHA256 thật được tính từ artifact thật.
9. Commit schema + fixtures + runner + validator vào GitHub.
10. Chạy test từ commit đó và lưu execution evidence / CI evidence.

Chỉ sau khi các điểm trên PASS bằng artifact thực tế mới nâng:

`VALIDATION EVIDENCE VERIFIED`

sau đó mới:

`API CONTRACT CANDIDATE`

## Kiến Trúc Khóa Giữ Nguyên

`366 Fixed Day Slots + Unlimited Variable Year Layers`

`Day ID = Permanent`

`Year Layer = Variable`

`Millennium = Unlimited`

`History = Append Only`

CTTTC 366 Day Namespace độc lập với Website CFP+ ID và không renumber, consume hay làm thay đổi hệ ID Website.
