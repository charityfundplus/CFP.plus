# CTTTC • Universal Record Schema v0.2 • Review Candidate

**Status:** PASS WITH CHANGES  
**Scope:** Review kỹ thuật trước API / UI  
**Canonical:** Chưa khóa

## 1 • Kết luận

Schema v0.2 đã xử lý tốt các điểm chặn của v0.1: 366 ngày hợp lệ, hỗ trợ lịch sử cổ, schedule history, tách exact hash khỏi similarity review, giữ NOT_VERIFIED như audit record, và countdown theo target datetime.

Tuy nhiên chưa nên khóa Canonical trước khi xử lý các điểm dưới đây.

## 2 • Record ID cần tách hai lớp

`record_id` hiện mô tả vừa Canonical ID vừa temporary ingestion ID. Hai vai trò này không nên dùng chung một trường.

Đề xuất:

- `ingestion_id`: bắt buộc, duy nhất trong pipeline ingest.
- `canonical_record_id`: nullable cho tới khi được allocation theo quy tắc CTTTC đã khóa.

Không gọi temporary ID là Canonical.

## 3 • FUTURE phải bắt buộc có future_metadata bằng điều kiện schema

Hiện `future_metadata` có schema riêng nhưng chưa có điều kiện bắt buộc khi `temporal_class = FUTURE`.

Cần dùng JSON Schema `allOf` + `if/then`:

- Nếu `temporal_class = FUTURE` → bắt buộc `future_metadata`.
- Nếu không phải FUTURE → không bắt buộc countdown metadata.

## 4 • 02-29 là structural slot, không đồng nghĩa mọi năm có ngày 29/02 thực tế

CTTTC luôn có ô `02-29` trong 366 ngày.

Nhưng một `target_datetime` hoặc `historical_date` thực tế chỉ được mang ngày 29/02 khi năm và calendar tương ứng thực sự có ngày đó.

Cần tách:

- `day_key = 02-29` như vị trí CTTTC cố định.
- actual event date validation theo `year + calendar_type`.

## 5 • Year không nên là integer|string|null tùy ý

Kiểu `string` mở quá rộng và có thể chứa dữ liệu không chuẩn.

Đề xuất tách:

- `year_value`: integer|null
- `era`: `CE | BCE | UNKNOWN`
- `date_precision`: `EXACT | APPROXIMATE | RANGE | UNKNOWN`
- `year_label`: string|null chỉ để giữ văn bản lịch sử gốc

Nếu dùng astronomical year numbering cần ghi rõ quy ước.

## 6 • PRESENT là trạng thái tương đối và sẽ hết hạn

`temporal_class = PRESENT` thay đổi theo thời gian. Nếu lưu cứng, cùng một record sẽ từ PRESENT thành PAST mà không đổi bản chất sự kiện.

Đề xuất:

- lưu `event_temporal_position` hoặc actual timestamps;
- `PAST / PRESENT / FUTURE` nên có thể là **derived state** tại thời điểm query;
- nếu vẫn lưu, phải có quy tắc transition rõ ràng và audit history.

## 7 • Evidence cần cấu trúc chặt hơn

`url_or_hash` đang gộp hai loại dữ liệu khác nhau.

Đề xuất:

- `source_url`
- `content_hash`
- `hash_algorithm`
- `source_title`
- `publisher`
- `published_at`
- `retrieved_at`
- `evidence_type`
- `verification_status`
- `verified_at`

Nếu `evidence_status = Verified`, ít nhất phải có một evidence item đủ điều kiện xác minh. Mảng `evidence` nên có `minItems: 1` trong trường hợp Verified.

## 8 • actual_outcome_evidence không nên chỉ là string[]

Nên dùng cùng Evidence Object hoặc reference tới `evidence_id` để giữ provenance thống nhất.

## 9 • Geographic coordinates cần validation

`coordinates` hiện chỉ có `maxItems: 2`.

Cần:

- `minItems: 2`
- `maxItems: 2`
- latitude trong `[-90, 90]`
- longitude trong `[-180, 180]`

Tốt hơn nữa dùng object:

```json
{"latitude": 0, "longitude": 0}
```

để tránh đảo thứ tự.

## 10 • Relations cần required và taxonomy

Mỗi relation item nên bắt buộc:

- `target_record_id`
- `relation_type`

`relation_type` không nên là text tự do hoàn toàn. Cần Candidate taxonomy, ví dụ:

- `CAUSES`
- `CAUSED_BY`
- `PRECEDES`
- `FOLLOWS`
- `CONTEXT_FOR`
- `CORRECTS`
- `UPDATES`
- `RELATED_TO`
- `FORECASTS`
- `OUTCOME_OF`

Có thể giữ `relation_note` cho phần diễn giải tự do.

## 11 • Duplicate Detection cần hai tầng

**Exact Duplicate**

Dùng deterministic fingerprint của các trường chuẩn hóa, ví dụ:

`normalized_title + actual_date + country + source_identity`

SHA256 chỉ dùng so sánh exact fingerprint.

**Similarity Candidate**

Dùng semantic/text similarity riêng. Kết quả chỉ đưa vào `Similarity Review`; không tự merge khi chưa review.

Hai sự kiện khác nhau có tiêu đề giống nhau không được gộp chỉ vì hash tiêu đề giống.

## 12 • Countdown State Machine cần nhất quán

Nên thống nhất:

`CREATED → COUNTDOWN_RUNNING → REACHED_TARGET → VERIFY_ACTUAL_OUTCOME → outcome`

`PAUSED` và `STOPPED` là trạng thái vận hành countdown, không phải kết quả sự kiện.

Countdown chạy đến đúng `current_target_datetime` có timezone/offset cụ thể.

Khi chạm target:

- khóa countdown;
- ghi `reached_target_at`;
- chuyển `REACHED_TARGET`;
- kích hoạt `VERIFY_ACTUAL_OUTCOME`;
- tuyệt đối không tự ghi `OCCURRED`.

## 13 • DELAYED / CHANGED không xóa lịch sử

Giữ bất biến:

- `original_target_datetime`

Cập nhật:

- `current_target_datetime`

Mọi thay đổi phải append vào `schedule_history[]`.

Nếu ngày đích đổi sang ngày khác, trang mới có thể được liên kết nhưng hồ sơ lịch sử tại ngày cũ phải còn trace.

## 14 • additionalProperties

Để schema ổn định trước API, nên cân nhắc `additionalProperties: false` tại các object đã khóa cấu trúc, hoặc áp dụng có chọn lọc sau khi taxonomy đủ trưởng thành.

Trong giai đoạn Review Candidate có thể giữ mở ở những block cần nghiên cứu thêm.

## 15 • Điểm đạt của v0.2

- Strict 366-day `day_key`: PASS.
- 02-29 luôn có structural slot: PASS.
- Historical calendar support: PASS WITH CHANGES.
- Schedule history: PASS.
- Exact hash vs similarity review: PASS.
- NOT_VERIFIED retention: PASS.
- Countdown target logic: PASS WITH CHANGES.
- Evidence model: PASS WITH CHANGES.
- Canonical ID allocation: PENDING.

## 16 • Yêu cầu v0.3

Gemini / AI Review tiếp theo cần trả:

1. JSON Schema v0.3.
2. Conditional validation cho FUTURE.
3. Tách ingestion ID và Canonical ID.
4. Date model cho BCE / Julian / approximate / unknown.
5. Evidence Object v0.2.
6. Relation taxonomy.
7. Exact duplicate fingerprint specification.
8. Similarity Review specification.
9. Countdown transition rules.
10. Test vectors gồm valid và invalid records.

## 17 • Trạng thái

**REVIEW STATUS: PASS WITH CHANGES**

Chưa khóa Canonical. Chưa chuyển sang API production cho tới khi các conditional rules và ID model được review xong.

**CFP+ • CTTTC • 366 Ngày • Cộng Thêm Mãi Mãi**

**Only Plus+ For Life**
