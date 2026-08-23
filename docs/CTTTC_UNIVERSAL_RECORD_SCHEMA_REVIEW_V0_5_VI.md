# CFP+ CTTTC • Universal Record Schema v0.5 • Review

**Trạng Thái:** REVIEW CANDIDATE • PASS WITH CHANGES • CHƯA SANG API

## 1 • Kết Luận

Schema v0.5 đã xử lý đúng nhiều điểm của v0.4: Draft 2020-12, prefixItems cho tọa độ, temporal_class bắt buộc, actual_calendar_date tách khỏi structural 02-29 slot, actual_outcome_evidence tái sử dụng Evidence Object.

Tuy nhiên chưa đủ cơ sở để tuyên bố State Machine và Evidence Governance đã được enforce toàn diện.

## 2 • State Machine Chưa Được Enforce Chỉ Bằng Enum

`event_status` enum chỉ giới hạn **các giá trị hợp lệ**, không giới hạn **chuyển đổi hợp lệ giữa hai trạng thái**.

Ví dụ Schema hiện tại vẫn có thể nhận một record có `event_status = OCCURRED` ngay sau khi trước đó là `RUNNING`, nếu chỉ validate một snapshot độc lập.

Các chuyển đổi cần được enforce tại validation layer/API/backend bằng transition table hoặc state transition function:

`RUNNING → REACHED_TARGET → VERIFY_ACTUAL_OUTCOME → OCCURRED | CHANGED | DELAYED | CANCELLED | NOT_VERIFIED`

Không cho phép `RUNNING → OCCURRED` hoặc các bước nhảy cóc tương tự.

## 3 • Báo Cáo Validator Chưa Có Evidence Thực Thi Đầy Đủ

Báo cáo nói `jsonschema 4.23` đã chạy thực tế, nhưng chưa kèm:

- fixture files thực tế
- command hoặc test script
- validator output/log
- exit code
- commit chứa schema + fixtures + tests

Do đó trạng thái phù hợp hiện tại là `VALIDATION REPORTED` chứ chưa phải `VALIDATION EVIDENCE VERIFIED`.

## 4 • Evidence URL Và Hash

`format: uri` chỉ kiểm tra hình thức URI, không xác minh URL có tồn tại hay nội dung có chứng minh claim.

Schema cũng chỉ kiểm tra `content_hash` có 64 ký tự hex, không chứng minh hash đó thuộc đúng artifact.

Quy tắc bắt buộc ngoài JSON Schema:

`Real URL ≠ Valid Evidence nếu nguồn không chứng minh claim.`

`Valid SHA256 Format ≠ Verified Artifact Hash.`

Cần Evidence Verification Layer thực hiện fetch artifact, tính SHA-256 và so sánh với `content_hash`.

## 5 • Không Dùng Evidence CFP+ Cho Claim Không Liên Quan

Fixture phải dùng nguồn thật và claim đúng với nguồn. Không được lấy một tài liệu CFP+ có thật rồi dùng nó để chứng minh một sự kiện lịch sử, roadmap hoặc sự kiện bên ngoài không được tài liệu đó xác nhận.

Fixture test schema có thể dùng record dữ liệu về chính schema/tài liệu CFP+ nếu cần nguồn thật.

## 6 • 02-29 Structural Slot

Cách tách `day_key`, `is_leap_slot_mapping` và `actual_calendar_date` là đúng hướng.

Cần thêm cross-field rule ở validation layer:

- Nếu `day_key != 02-29` thì `is_leap_slot_mapping` thông thường phải là `false`.
- Nếu `day_key = 02-29` và năm không nhuận thì `actual_calendar_date` không được là `YYYY-02-29`.
- Structural slot không được tạo ra một actual date giả.

## 7 • Cross Field Consistency Còn Thiếu

JSON Schema v0.5 chưa enforce các quan hệ sau:

- `event_status = RUNNING` phải phù hợp với `future_metadata.countdown_status = RUNNING`.
- `event_status = REACHED_TARGET` phải có `reached_target_at` phù hợp.
- `event_status = OCCURRED | CHANGED | DELAYED | CANCELLED | NOT_VERIFIED` phải phù hợp với `actual_outcome_status`.
- `countdown_enabled = false` không nên đồng thời có `countdown_status = RUNNING`.
- `original_target_datetime` phải bất biến qua lịch sử record.
- `current_target_datetime` phải khớp với entry mới nhất trong `schedule_history` khi lịch bị thay đổi.

Các rule này nên được thực hiện bằng application validation hoặc một policy validator riêng.

## 8 • Temporal Class Là Derived Field

`temporal_class` hiện vẫn được lưu trong record. Cần xác định rõ đây là:

- cached derived field, có thể được tính lại theo query time; hoặc
- trạng thái snapshot có timestamp.

Không nên xem `PRESENT` là thuộc tính vĩnh viễn.

## 9 • year_representation Còn Quá Tự Do

`year_representation` vẫn là string bất kỳ.

Nên chuyển sang cấu trúc typed, ví dụ:

- `year_number`
- `era: CE | BCE | UNKNOWN`
- `precision: EXACT | APPROXIMATE | RANGE | UNKNOWN`
- `range_start`
- `range_end`

Điều này tránh dữ liệu tự do như `khoảng năm xưa` vẫn PASS schema.

## 10 • additionalProperties

Schema hiện không khóa các field lạ. Nếu mục tiêu là API contract chặt chẽ, nên cân nhắc `additionalProperties: false` ở các object đã ổn định hoặc dùng `unevaluatedProperties: false` phù hợp Draft 2020-12.

Không nhất thiết áp dụng ngay cho toàn bộ record khi còn Review Candidate, nhưng cần quyết định trước Canonical API.

## 11 • Similarity Control

TC-16 là Backend Policy, không phải JSON Schema test. Cần tách report thành:

- Schema Validation Tests
- State Machine Tests
- Evidence Integrity Tests
- Duplicate/Similarity Policy Tests

Không ghi một policy simulation như thể đó là validator result của JSON Schema.

## 12 • Điều Kiện Mở API Contract Candidate

Có thể mở **API Contract Candidate**, nhưng chưa production, sau khi có:

1. Schema v0.5 file trong repo.
2. Fixture files độc lập.
3. Test runner thực tế.
4. Log/CI evidence cho validator.
5. State transition validator.
6. Evidence hash verification test.
7. Cross-field consistency tests.
8. Duplicate/Similarity policy tests tách riêng.

## 13 • Quy Tắc Kiến Trúc Giữ Nguyên

366 Day ID là namespace thời gian riêng của CTTTC.

Nó không thay thế, không chiếm, không đổi và không làm ảnh hưởng ID Website CFP+ 0–9 / 00–99 / 000–999 hoặc các nhánh mở rộng.

**Review Status:** PASS WITH CHANGES

**Next Gate:** VALIDATION EVIDENCE VERIFIED → API CONTRACT CANDIDATE
