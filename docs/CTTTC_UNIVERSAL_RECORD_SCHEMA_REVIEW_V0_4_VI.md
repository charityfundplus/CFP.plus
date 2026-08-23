# CFP+ CTTTC • Universal Record Schema v0.4 • Technical Review

**Trạng Thái:** PASS WITH CHANGES

**Mục Tiêu Review:** Kiểm tra JSON Schema Draft 2020-12, semantics của test cases, Evidence First, 366-day namespace, countdown state machine và khả năng chuyển sang API.

## 1 • Kết Luận Tổng Quan

Schema v0.4 tiến bộ rõ rệt nhưng chưa đủ điều kiện chuyển sang API Contract Candidate.

Các blocker chính hiện nay không nằm ở ý tưởng 366 ngày mà nằm ở JSON Schema semantics và tính trung thực của Evidence test data.

## 2 • JSON Schema Draft 2020-12 • Geographic Coordinates

Schema khai báo `$schema: https://json-schema.org/draft/2020-12/schema` nhưng phần `geographic_scope` dùng `dependencies` và tuple validation bằng `items: [schema1, schema2]`.

Trong Draft 2020-12 cần dùng `dependentSchemas` / `dependentRequired` khi phù hợp và tuple validation dùng `prefixItems`.

Đề xuất:

```json
"coordinates": {
  "type": ["array", "null"],
  "prefixItems": [
    {"type": "number", "minimum": -90, "maximum": 90},
    {"type": "number", "minimum": -180, "maximum": 180}
  ],
  "items": false,
  "minItems": 2,
  "maxItems": 2
}
```

Không dùng `[0,0]` để đại diện Global.

## 3 • temporal_class Và if/then

`temporal_class` hiện không nằm trong `required` toàn cục.

Trong JSON Schema, điều kiện `if` chỉ có `properties.temporal_class.const = FUTURE` có thể đánh giá thành công khi property không tồn tại, vì `properties` không bắt buộc property phải hiện diện.

Do đó record không có `temporal_class` có nguy cơ bị `then` yêu cầu `future_metadata` ngoài ý muốn.

Hai hướng hợp lệ:

1. Nếu lưu `temporal_class` trong record: thêm vào `required`.
2. Nếu `temporal_class` chỉ derive tại query time: trong `if` phải thêm `required: ["temporal_class"]` và API/query layer chịu trách nhiệm derive.

Không để trạng thái mơ hồ giữa stored field và derived field.

## 4 • 02-29 Structural Slot Không Đồng Nghĩa Với Ngày Thực Tế

Test `2023 + day_key 02-29 + is_leap_slot_mapping true` không được mô tả như một sự kiện đã xảy ra vào 29/02/2023 Gregorian, vì ngày đó không tồn tại.

Cần tách rõ:

- `day_key`: structural CTTTC slot.
- `actual_event_date`: ngày thực tế nếu xác định.
- `slot_assignment_reason`: lý do record được liên kết với structural slot.
- `is_structural_slot_only`: true khi 02-29 chỉ là vị trí hệ thống chứ không phải ngày lịch thực của năm đó.

CTTTC được phép giữ slot 02-29 vĩnh viễn nhưng không được tạo ngày lịch sử giả.

## 5 • Evidence Test Data Hiện Có Một Lỗi Nghiêm Trọng

Các test đang dùng link thật của CFP+ nhưng dùng link đó để chứng minh nhiều sự kiện không liên quan, ví dụ BCE, Julian, Roadmap 2030 hoặc các sự kiện lịch sử khác.

Một URL thật không đồng nghĩa với Evidence phù hợp.

Ngoài ra `content_hash = e3b0c442...b855` là SHA-256 nổi tiếng của nội dung rỗng. Không được gắn hash này cho tài liệu GitHub thực rồi đánh dấu `Verified` nếu chưa hash chính xác bytes/content artifact được xác định.

Quy tắc:

**Real URL + Wrong Claim = Invalid Evidence.**

**Real URL + Wrong Hash = Invalid Evidence.**

**Verified chỉ hợp lệ khi nguồn thực sự hỗ trợ claim đang được record ghi nhận.**

## 6 • Không Dùng Dữ Liệu Giả Chỉ Vì Test Schema

User requirement hiện tại là không dùng link minh họa.

Theo cùng nguyên tắc Evidence First, test fixture factual cũng không nên tạo sự kiện giả rồi gắn `Verified`.

Đề xuất chia test thành hai lớp:

### A. Schema Structural Fixtures

Chỉ kiểm tra validation mechanics và phải gắn rõ `fixture_type = SCHEMA_VALIDATION_ONLY`, không được nhập vào CTTTC data store và không được coi là factual record.

### B. Evidence Integration Fixtures

Phải dùng sự kiện, nguồn, hash và claim thực tế đã xác minh.

BCE/Julian tests cần nguồn lịch sử thực tế phù hợp, không dùng tài liệu CTTTC nội bộ làm chứng cứ cho Caesar hay một sự kiện ngoài phạm vi tài liệu.

## 7 • Evidence Object Cần Bổ Sung Claim Binding

Một evidence object nên nói rõ nó hỗ trợ claim nào.

Đề xuất thêm:

- `claim_id`
- `supports`: true/false/partial
- `source_published_at`
- `retrieved_at`
- `verification_method`
- `verification_actor_type`
- `evidence_role`: primary / corroborating / contradictory / contextual

Như vậy nhiều nguồn có thể hỗ trợ hoặc mâu thuẫn với các phần khác nhau của một record.

## 8 • Verified Không Chỉ Là minItems >= 1

`Verified` với một evidence item chưa chắc đúng.

Validation syntax chỉ có thể chặn evidence rỗng. Quyết định Verified cần policy layer.

Đề xuất:

- Schema layer: `Verified => evidence minItems 1`.
- Policy layer: claim coverage, source quality, contradiction check, reviewer rules.
- Audit layer: lưu ai/AI nào xác minh, lúc nào, bằng phương pháp nào.

Không để JSON Schema một mình quyết định chân lý của record.

## 9 • year_representation Không Nên Là Free-form String Lâu Dài

`"Approx 1200"`, `"-0044"`, `"Unknown"` trong cùng một string gây khó search, sort, timeline và query API.

Đề xuất cấu trúc typed:

```json
"temporal_position": {
  "year_type": "EXACT | BCE | APPROXIMATE | RANGE | UNKNOWN",
  "year_value": 2026,
  "year_start": null,
  "year_end": null,
  "display_text": "Approx 1200",
  "calendar_type": "Gregorian | Julian | Other | Unknown"
}
```

Không cần khóa đúng enum này ở v0.4, nhưng v0.5 nên chuyển sang typed time representation.

## 10 • day_key Basis Cần Chốt

`day_key` cần quy tắc rõ ràng:

- Ngày lịch sử gốc/local date quyết định vị trí lịch sử khi nguồn xác định được local date.
- UTC+7 là chuẩn vận hành CFP+ cho ingest, review, countdown và system timestamps.
- Không chuyển một sự kiện sang ngày khác chỉ vì UTC+7 khác local date, trừ khi taxonomy của CTTTC sau review cố ý chọn operational-day mapping.

Cần lưu cả `event_local_date` và `event_time_utc7` khi có đủ dữ liệu.

## 11 • Countdown State Machine Chưa Được Encode Đủ Trong Schema

State machine mô tả `VERIFY_ACTUAL_OUTCOME`, nhưng schema hiện không có field/state tương ứng rõ trong `countdown_status` hoặc outcome workflow status.

Đề xuất tách:

- `countdown_status`: RUNNING / REACHED_TARGET / PAUSED / STOPPED
- `outcome_verification_status`: NOT_STARTED / PENDING_REVIEW / VERIFYING / COMPLETE
- `actual_outcome_status`: OCCURRED / CHANGED / DELAYED / CANCELLED / NOT_VERIFIED / null

Không cho phép RUNNING → OCCURRED trực tiếp.

## 12 • DELAYED Và day_key

Khi một future event bị DELAYED sang ngày mới:

- `original_target_datetime` bất biến.
- `schedule_history[]` append-only.
- `current_target_datetime` cập nhật.
- `day_key` active view có thể cần chuyển theo current target.
- Phải giữ link/reference về day_key cũ để không mất lịch sử dự kiến ban đầu.

Cần định nghĩa `original_day_key` hoặc schedule-history day keys nếu event đổi ngày.

## 13 • Similarity Không Được Tự Merge

Giữ nguyên quy tắc:

`exact_fingerprint exact match` có thể tạo duplicate candidate mạnh.

`semantic similarity` chỉ tạo `SIMILARITY_REVIEW`.

Kết quả review:

- SAME_EVENT
- RELATED_EVENT
- DISTINCT_EVENT
- CORRECTION_OF

Không tự merge record chỉ vì similarity score cao.

## 14 • 366 Day Namespace Không Ảnh Hưởng Website

366-day ID/namespace là namespace thời gian riêng của CTTTC.

Nó không thay thế, chiếm, renumber hoặc làm thay đổi Website Chapter IDs 0-9 / 00-99 / 000-999 hay các Canonical Entity IDs khác.

Cross-reference chỉ là liên kết giữa hệ thời gian và hệ nội dung/entity.

## 15 • Điều Kiện Trước Khi Sang API Contract Candidate

Cần ít nhất:

1. Sửa Draft 2020-12 coordinate tuple syntax.
2. Sửa semantic của `if/then` với `temporal_class`.
3. Tách structural 02-29 khỏi actual calendar occurrence.
4. Loại bỏ Evidence sai claim và hash giả/sai.
5. Tách structural test fixtures khỏi factual Evidence fixtures.
6. Thêm outcome verification state.
7. Chốt day_key basis local date vs UTC+7.
8. Bắt đầu typed temporal representation cho BCE/Approximate/Range.
9. Chạy validator thực sự trên toàn bộ valid/invalid fixtures.
10. Báo cáo validator name/version và kết quả PASS/FAIL thực tế.

## 16 • Trạng Thái

**Schema v0.4:** PASS WITH CHANGES

**API Contract:** NOT READY

**Đề Xuất Tiếp Theo:** Schema v0.5 + machine-executed validation report + Evidence fixture correction.

**Nguyên Tắc:** Quá Khứ + Hiện Tại + Tương Lai + Evidence + Review + Bổ Sung → Cộng Thêm Mãi Mãi.
