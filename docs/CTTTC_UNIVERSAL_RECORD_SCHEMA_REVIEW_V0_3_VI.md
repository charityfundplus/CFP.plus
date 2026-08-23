# CTTTC Universal Record Schema v0.3 • Review

**Status:** REVIEW CANDIDATE  
**Review Result:** PASS WITH CHANGES  
**Scope:** Schema semantics, validation, evidence, temporal model, countdown, deduplication, test cases  

## 1 • Kết luận

Schema v0.3 đã sửa đúng các điểm lớn của v0.2: tách `ingestion_id` khỏi `canonical_record_id`, dùng `if/then` cho FUTURE, chuẩn hóa relation object, tách `source_url` và `content_hash`, giữ `schedule_history`, và giữ countdown không tự xác nhận sự kiện đã xảy ra.

Chưa chuyển sang Canonical Locked hoặc API production. Cần v0.4 hoặc patch v0.3.1 để xử lý các chốt dưới đây.

## 2 • Temporal Position phải được bắt buộc

`temporal_position` hiện có schema nhưng không nằm trong `required` cấp root. Điều này cho phép record không có năm hoặc calendar metadata vẫn hợp lệ.

**Yêu cầu:** thêm `temporal_position` vào `required`, trừ khi có một loại record đặc biệt `DATE_UNKNOWN` được định nghĩa rõ.

## 3 • `temporal_class` không nên là sự thật bất biến

PAST / PRESENT / FUTURE thay đổi theo thời gian. Không được coi đây là thuộc tính Canonical bất biến của sự kiện.

Khuyến nghị một trong hai cách:

1. Đổi tên thành `temporal_class_at_ingestion` và lưu `temporal_class_evaluated_at`; hoặc
2. Không lưu Canonical, để API dẫn xuất từ timestamp tại query time.

Nếu vẫn lưu, phải có transition history hoặc timestamp đánh giá.

## 4 • `day_key` và múi giờ phải có quy tắc ánh xạ rõ

Một sự kiện có thể rơi vào hai ngày khác nhau giữa múi giờ gốc và UTC+7.

Phải khóa quy tắc:

- `day_key` theo ngày lịch sử tại địa phương nơi sự kiện xảy ra; hoặc
- `day_key` theo CFP+ UTC+7.

Không được để mỗi ingestion worker tự chọn.

Khuyến nghị: giữ cả `event_day_local` và `event_day_cfp_utc7`, sau đó xác định một trường duy nhất là `canonical_day_key` theo Governance Rule.

## 5 • BCE / Julian vẫn chưa hoàn chỉnh

`year_value: -44` hỗ trợ BCE ở mức dữ liệu, nhưng `historical_date` vẫn dùng `format: date`, vốn không phù hợp cho nhiều record BCE, Julian, ngày xấp xỉ hoặc ngày không đầy đủ.

Cần tách:

- `historical_date_iso` cho Gregorian/ISO có thể xác định chính xác;
- `historical_date_text` cho biểu diễn gốc;
- `date_precision`: EXACT / DAY / MONTH / YEAR / APPROXIMATE / UNKNOWN;
- `calendar_type`;
- tùy chọn `calendar_conversion_note`.

Không ép dữ liệu cổ vào ngày Gregorian giả tạo.

## 6 • `is_leap_slot_mapping` cần định nghĩa lại

02-29 luôn tồn tại như một **structural slot** của CTTTC, nhưng điều đó không có nghĩa sự kiện ngày 29/02 được “map sang năm không nhuận” như một ngày thực tế.

Khuyến nghị đổi thành:

- `is_structural_feb29_slot`; hoặc
- bỏ field này khỏi event record và để thuộc tính 366-day structure ở Day Page metadata.

Lịch sử thực tế và slot cấu trúc phải tách biệt.

## 7 • Geographic coordinates chưa được validate đúng giới hạn

Schema hiện chỉ kiểm tra hai phần tử số. Description nói latitude/longitude có giới hạn nhưng schema chưa enforce.

Cần dùng `prefixItems`:

- latitude: minimum -90, maximum 90;
- longitude: minimum -180, maximum 180;
- `minItems: 2`, `maxItems: 2`.

`[0,0]` không nên dùng cho “Worldwide” chỉ để lấp field. Global event có thể để coordinates vắng mặt/null và dùng `scope_type: GLOBAL`.

## 8 • Country / Global cần typed geographic model

`country: "Global"` trộn quốc gia với phạm vi toàn cầu.

Khuyến nghị:

- `country_code`: ISO code hoặc null;
- `scope_type`: GLOBAL / REGIONAL / NATIONAL / LOCAL / MULTI_COUNTRY;
- `related_countries[]` cho sự kiện nhiều quốc gia.

Không dùng chuỗi “Global” như country code.

## 9 • Evidence semantics cần chặt hơn

Schema cho phép `evidence_status = Verified` khi `evidence = []`.

Cần conditional validation:

- Nếu `Verified` → `evidence.minItems >= 1`;
- ít nhất một evidence item phải có nguồn hoặc artifact hash có thể kiểm tra;
- nếu `source_url = null` thì `content_hash` hoặc persistent evidence locator phải có;
- nếu `content_hash = null` thì phải có source URL hoặc evidence locator.

`verified_at` của một evidence item không đồng nghĩa toàn record đã Verified.

## 10 • Hash phải có format validation

`exact_fingerprint` và `content_hash` đang nhận string bất kỳ.

Nếu là SHA-256, dùng pattern hex 64 ký tự hoặc thêm `hash_algorithm`.

Khuyến nghị Evidence Artifact:

```text
hash_algorithm: SHA256
content_hash: <64 hex chars>
```

Không nên cho phép mô tả là SHA-256 nhưng schema không kiểm tra.

## 11 • Test Case 1 chưa thể coi là Evidence Valid hoàn toàn

Test sử dụng URL `https://cfp-plus.org/doc`. Đây chỉ được coi là **placeholder test URL**, không phải evidence thực của CFP+.

Ngoài ra record đặt:

- `evidence_status = Pending Evidence`;
- evidence item có `verified_at`.

Điều này có thể hợp lệ nếu nghĩa là artifact đã được kiểm tra nhưng claim/sự kiện chưa được xác minh. Tuy nhiên semantics phải ghi rõ để tránh reviewer hiểu `verified_at` là record Verified.

Nên đổi tên thành `artifact_checked_at` hoặc thêm `verification_scope`.

## 12 • Countdown State Machine cần một trạng thái xác minh rõ

`countdown_status` hiện có RUNNING / REACHED_TARGET / PAUSED / STOPPED nhưng workflow đã thống nhất có bước `VERIFY_ACTUAL_OUTCOME`.

Có hai lựa chọn:

- thêm `VERIFYING_OUTCOME` vào countdown/workflow status; hoặc
- tạo field riêng `outcome_verification_status` = NOT_STARTED / PENDING / IN_REVIEW / VERIFIED / INCONCLUSIVE.

Không dùng `actual_outcome_status = null` như trạng thái workflow lâu dài nếu API cần query hàng đợi review.

## 13 • Countdown phải bám đúng target timestamp

Worker chỉ được chuyển RUNNING → REACHED_TARGET khi `now >= current_target_datetime` theo timestamp tuyệt đối.

Không hard-code “00:00:00 UTC+7”.

`reached_target_at` phải ghi timestamp thực tế worker xử lý, không giả bằng target timestamp.

## 14 • Schedule History phải append-only

`original_target_datetime` bất biến.

Khi delay/change:

1. append một entry vào `schedule_history`;
2. update `current_target_datetime`;
3. không xóa hoặc sửa entry lịch sử cũ;
4. giữ evidence/source cho lý do đổi lịch nếu có.

Nên thêm `change_type`: DELAYED / ADVANCED / RESCHEDULED / CORRECTED / CANCELLED và `source_evidence_ids[]`.

## 15 • Exact duplicate và semantic similarity phải tách hoàn toàn

`exact_fingerprint` chỉ dùng exact normalized payload fingerprint.

Semantic similarity phải là subsystem riêng, ví dụ:

- `similarity_review_status`;
- `candidate_duplicate_ids[]`;
- `similarity_score`;
- `review_decision`: DISTINCT / DUPLICATE / RELATED / UNCERTAIN.

Không tự merge chỉ vì similarity score cao.

## 16 • Relation semantics cần kiểm tra chiều quan hệ

Enum đã tốt hơn nhưng `past_relations` có `SUBSEQUENT_PHASE`, tên này có thể ngược chiều semantic.

Nên chuyển về một relation collection thống nhất:

```text
relations[] = {target_record_id, relation_type, direction, confidence, evidence_ids[]}
```

Hoặc định nghĩa cực rõ mỗi relation type là quan hệ từ source record → target record.

## 17 • Additional Properties

Schema hiện không đặt `additionalProperties: false` ở các object quan trọng. Điều này cho phép typo field đi qua validation.

Khuyến nghị:

- root và object ổn định: `additionalProperties: false`;
- object còn đang mở rộng có thể cho phép extension namespace rõ ràng.

## 18 • Bộ test cần mở rộng trước API

Ngoài 3 test hiện tại, bắt buộc thêm ít nhất:

1. Valid 02-29 structural slot.
2. Invalid 04-31.
3. Invalid coordinates `[91,0]`.
4. Invalid coordinates `[0,181]`.
5. FUTURE thiếu future_metadata.
6. FUTURE có countdown nhưng thiếu current_target_datetime.
7. PAST có retained future_metadata để audit sau khi sự kiện đã qua.
8. BCE/Julian approximate record.
9. Verified record với evidence rỗng phải fail.
10. Evidence không URL và không hash phải fail.
11. Invalid SHA-256 length.
12. Duplicate exact fingerprint candidate.
13. Similar but not exact duplicate candidate.
14. DELAYED event giữ original target và schedule history.
15. CANCELLED event giữ record, không delete.
16. REACHED_TARGET chưa có outcome phải vào hàng Verify Actual Outcome.
17. Multi-country/global record không giả country code.
18. Event local date khác CFP+ UTC+7 date.

## 19 • Gate tiếp theo

**v0.3 = PASS WITH CHANGES.**

Không chuyển thẳng sang API production.

Tiếp theo:

**Schema v0.4 → Validator Test Suite → State Machine Tests → Evidence Tests → Duplicate Tests → API Contract Candidate → UI/UX.**

Có thể bắt đầu dựng API mock hoặc interface contract song song, nhưng không khóa storage model trước khi các test trên PASS.

**Only Plus+ For Life.**