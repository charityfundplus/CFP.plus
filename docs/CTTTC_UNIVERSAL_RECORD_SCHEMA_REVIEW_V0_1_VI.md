# CTTTC • Universal Record Schema Review v0.1

**Status:** REVIEW CANDIDATE  
**Scope:** Review of proposed `ctttc-universal-record.schema.json`  
**Review Result:** PASS WITH CHANGES

## 1 • Những Phần Có Thể Giữ

- Một Universal Record cho Quá Khứ • Hiện Tại • Tương Lai.
- `day_key` làm vị trí cố định trong chu kỳ 366 ngày.
- Tách `discovered_at`, `integrated_at` khỏi ngày lịch sử của sự kiện.
- `future_metadata` riêng cho dữ liệu tương lai.
- Countdown không tự xác nhận sự kiện đã xảy ra khi chạm mốc.
- State Machine có bước `REACHED_TARGET` → `VERIFY_ACTUAL_OUTCOME`.
- Giữ `review_history`, `corrections`, `append_history` để phục vụ traceability.

## 2 • Finding P0 • `day_key` Validation Chưa Đúng

Regex hiện tại chỉ kiểm tra hình thức `MM-DD` nhưng vẫn chấp nhận ngày không tồn tại như `02-31`, `04-31`.

CTTTC có đúng 366 vị trí ngày cố định. Vì vậy validation phải dùng một trong hai cách:

1. `enum` đầy đủ 366 giá trị hợp lệ từ `01-01` đến `12-31`, bao gồm `02-29`; hoặc
2. custom validator kiểm tra ngày hợp lệ trong lịch chuẩn 366 vị trí.

**Quan trọng:** `02-29` luôn tồn tại như một vị trí của CTTTC, kể cả năm không nhuận. Tuy nhiên một sự kiện thực tế có `historical_date = YYYY-02-29` chỉ hợp lệ khi năm đó thực sự có ngày 29/02 theo calendar tương ứng.

## 3 • Finding P0 • Không Được Gọi `record_id` Là Canonical ID Khi Chưa Khóa Quy Tắc

Mô tả hiện tại ghi `Canonical unique identifier for the record`.

CTTTC chưa khóa định dạng Canonical Record ID cuối cùng. Vì vậy ở v0.1 nên đổi thành:

`record_id` = internal stable record identifier / provisional record identifier.

Không tự suy diễn Canonical ID từ ví dụ `REC-PAST-...`.

## 4 • Finding P0 • Dữ Liệu Lịch Sử Cổ Và Lịch Khác Gregorian

`year.minimum = 1` và `format: date` không đủ cho mục tiêu thu thập lịch sử toàn cầu lâu dài.

Cần bổ sung tối thiểu:

- `calendar_type`: `GREGORIAN / JULIAN / LUNAR / LOCAL / UNKNOWN`
- `date_precision`: `EXACT / DAY / MONTH / YEAR / APPROXIMATE / UNKNOWN`
- `era`: `CE / BCE / OTHER / UNKNOWN`
- `historical_date_text`: chuỗi nguyên bản khi không thể biểu diễn chắc chắn bằng ISO date.

Không ép sự kiện cổ đại hoặc ngày không chắc chắn vào một ISO date giả.

## 5 • Finding P0 • Múi Giờ

`timezone_original` không nên chỉ chứa `UTC+2`.

Ưu tiên IANA timezone khi xác định được, ví dụ `Europe/Paris`, `Asia/Ho_Chi_Minh`.

Cần có:

- `timezone_original`
- `timezone_precision`: `EXACT / OFFSET_ONLY / INFERRED / UNKNOWN`
- `event_time_original_text` cho nguồn lịch sử không có timestamp chuẩn.

`event_time_utc7` được phép `null` khi thời gian gốc không đủ chính xác.

## 6 • Finding P0 • Duplicate Detection Không Thể Dùng SHA256 Với Ngưỡng 95%

SHA256 là hash chính xác, không phải thước đo semantic similarity. Hai tiêu đề chỉ khác một ký tự có thể cho hash hoàn toàn khác.

Cần tách:

### Exact Fingerprint
Dùng hash cho nội dung đã canonicalize để phát hiện trùng chính xác.

### Similarity Candidate
Dùng normalized title + date + location + actor + source + semantic/text similarity để tạo `duplicate_candidate`.

Không tự merge chỉ vì similarity > một ngưỡng.

Quy trình:

`Candidate Duplicate → Compare Evidence → AI/Human Review → Merge / Link / Keep Separate`

## 7 • Finding P0 • DELAYED Và CHANGED Không Được Ghi Đè Lịch Sử

State Machine hiện mô tả `DELAYED → dời lịch sang day_key mới` và `CHANGED → cập nhật lại thông số & mốc ngày`.

CTTTC cần append-only.

Khi sự kiện bị hoãn hoặc thay đổi:

- giữ `original_target_datetime`;
- thêm `current_target_datetime`;
- ghi một entry trong `schedule_history[]`;
- giữ day_key lịch cũ như historical scheduling evidence;
- liên kết sang day_key mới nếu có lịch mới.

Không xóa hoặc ghi đè mốc ban đầu.

## 8 • Finding P0 • `NOT_VERIFIED` Không Đồng Nghĩa Với Rác

`NOT_VERIFIED` chỉ có nghĩa là chưa xác minh được kết quả thực tế.

Không được tự gắn `rác`, `false`, hoặc xóa record.

Có thể dùng thêm:

- `UNCONFIRMED`
- `CONTRADICTED`
- `FALSE_CLAIM_CONFIRMED`
- `SOURCE_RETRACTED`

với evidence phù hợp.

## 9 • Finding P0 • Countdown Chạy Đến Chính `target_datetime`, Không Chỉ 00:00:00

Countdown phải chạy tới timestamp đích cụ thể.

Nếu nguồn chỉ cho ngày mà không có giờ, hệ thống có thể dùng `target_precision = DATE_ONLY` và UI hiển thị countdown theo ngày.

Không giả định tất cả sự kiện chạm mốc lúc 00:00:00 UTC+7.

Khi `now >= target_datetime`:

`RUNNING → REACHED_TARGET → VERIFY_ACTUAL_OUTCOME`

Không tự chuyển sang `OCCURRED`.

## 10 • Finding P1 • Evidence Model Cần Giàu Hơn

Mỗi evidence nên hỗ trợ:

- `evidence_id`
- `source_type`
- `publisher`
- `author`
- `title`
- `url`
- `archive_url`
- `content_hash`
- `published_at`
- `accessed_at`
- `language`
- `quote_or_excerpt_reference`
- `evidence_role`: `PRIMARY / SECONDARY / CORROBORATING / CONTRADICTING`
- `verification_status`

`Verified` không nên được suy ra chỉ từ một nguồn hoặc một AI review.

## 11 • Finding P1 • Quốc Gia Và Phạm Vi Địa Lý

`country` là một string đơn lẻ chưa đủ cho sự kiện toàn cầu hoặc đa quốc gia.

Đề xuất:

- `primary_country`
- `related_countries[]`
- `region`
- `location[]`
- `geographic_scope`: `GLOBAL / REGIONAL / NATIONAL / LOCAL / MULTI_COUNTRY / UNKNOWN`

Không dùng `Global` như một country code.

## 12 • Finding P1 • Quan Hệ Timeline

`past_relations[]` và `future_relations[]` nên là typed relations thay vì chỉ string ID.

Ví dụ:

```json
{
  "record_id": "...",
  "relation_type": "CAUSES | CAUSED_BY | CONTINUES | FOLLOWS | PRECEDES | CORRECTS | CONTRADICTS | ANNIVERSARY_OF | FORECAST_OF | OUTCOME_OF",
  "confidence": "VERIFIED | PROBABLE | POSSIBLE | UNKNOWN"
}
```

Điều này giúp CTTTC xâu chuỗi Quá Khứ → Hiện Tại → Tương Lai có logic.

## 13 • Finding P1 • Record Hiện Tại Không Nên Tự Ghi Verified Nếu Evidence Là Placeholder

Các ví dụ dùng URL giả hoặc hash minh họa không được coi là evidence thực tế.

Record mẫu phải ghi rõ:

`EXAMPLE_ONLY` hoặc `Pending Evidence`.

Không dùng ví dụ giả làm dữ liệu Canonical.

## 14 • Schema Direction v0.2

Đề xuất cấu trúc cấp cao:

```text
identity
calendar
when
where
what
who
classification
evidence
relations
review
history
future_metadata
```

Các field có thể giữ phẳng trong JSON nếu cần đơn giản hóa API, nhưng semantics phải theo các nhóm trên.

## 15 • State Machine Đề Xuất

```text
INGESTED
→ CLASSIFIED
→ EVIDENCE_REVIEW
→ ACTIVE

Nếu FUTURE:
ACTIVE
→ COUNTDOWN_RUNNING
→ REACHED_TARGET
→ VERIFY_ACTUAL_OUTCOME
→ OCCURRED | CHANGED | DELAYED | CANCELLED | NOT_VERIFIED
```

Mỗi transition phải tạo history entry, không overwrite im lặng.

## 16 • Nguyên Tắc 366 Ngày

- CTTTC có 366 vị trí ngày cố định.
- Dữ liệu quá khứ tìm thấy bất kỳ lúc nào phải được tổng hợp, đối chiếu, xác minh và đưa về đúng day_key lịch sử.
- Dữ liệu hiện tại vào đúng day_key hiện tại.
- Dữ liệu tương lai được đặt vào đúng day_key mục tiêu và có countdown khi đủ dữ liệu thời gian.
- Khi lịch tương lai thay đổi, giữ toàn bộ lịch sử mốc cũ.
- `02-29` là vị trí CTTTC cố định, không biến mất trong năm không nhuận.

## 17 • Review Status

**PASS WITH CHANGES**

Schema v0.1 đủ tốt làm nền để phát triển v0.2, nhưng chưa đủ điều kiện `Canonical Locked`.

Ưu tiên sửa theo thứ tự:

1. day_key validator 366 ngày
2. provisional ID semantics
3. ancient date/calendar model
4. append-only future schedule history
5. duplicate model
6. evidence model
7. typed timeline relations
8. country/geographic model
9. state validation
10. UI/UX sau khi schema v0.2 ổn định

**Only Plus+ For Life.**