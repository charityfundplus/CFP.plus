# CFP+ CTTTC • Review Schema v0.6.4

**Trạng Thái:** REVIEW CANDIDATE • PASS WITH CHANGES • VALIDATION EVIDENCE PENDING • CHƯA SANG API

## Kết Luận

v0.6.4 đã cải thiện rõ rệt về Gregorian/Julian validation, 02-29 symmetry, State Machine và Evidence positive/negative test structure. Tuy nhiên chưa đủ điều kiện nâng lên VALIDATION EVIDENCE VERIFIED.

## Blocker 1 • Positive Evidence Hash Sai

Execution log tuyên bố README thật có SHA256:

`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

Đây là SHA256 nổi tiếng của nội dung rỗng. README hiện tại trong repository có nội dung thực, nên hash này không thể là hash của README hiện tại.

Yêu cầu v0.6.5:

1. Fetch bytes thật của đúng raw URL.
2. In byte length.
3. Tính SHA256 từ chính bytes vừa fetch.
4. In computed hash.
5. Dùng chính computed hash đó cho positive test.
6. Positive test chỉ PASS khi HTTP 200 AND byte_length > 0 AND computed_sha256 == declared_sha256.

## Blocker 2 • Runner Thiếu Import

Đoạn runner sử dụng `urllib.request` và `hashlib` để lấy real_sha256 nhưng phần imports được trình bày không import hai module này. Nếu artifact thực tế giống đoạn đã gửi, runner sẽ NameError trước Evidence test.

Phải cung cấp file chạy đầy đủ và log đúng từ chính file đó.

## Blocker 3 • Claim Support Chưa Được Gọi

`verify_claim_support()` đã được định nghĩa nhưng runner v0.6.4 không gọi hàm này. Vì vậy chưa có execution evidence rằng Unsupported Claim được kiểm tra bằng content semantics.

Test `20_unsupported_evidence_claim.json` không được phép được báo là rejected by schema nếu lỗi cần chứng minh là unsupported claim. Phải chạy Claim Support Layer riêng và ghi rõ kết quả.

## Blocker 4 • 02-29 Structural Slot cần test đủ hai chiều

Cần ít nhất bốn fixture rõ ràng:

- Gregorian leap year + 02-29 real date = PASS
- Gregorian non-leap + 02-29 structural only = PASS
- Gregorian leap + is_leap_slot_mapping=true = FAIL
- Gregorian non-leap + is_leap_slot_mapping=false = FAIL

Tương tự cần fixture Julian để chứng minh 1900-02-29 hợp lệ theo Julian nhưng không hợp lệ theo Gregorian.

## Blocker 5 • Schema format=date và Julian

`actual_calendar_date` vẫn dùng JSON Schema `format: date`. Một validator có FormatChecker có thể áp ISO/Gregorian semantics và từ chối một Julian date hợp lệ như 1900-02-29 trước khi Julian validator riêng được chạy. Cần quyết định rõ:

- hoặc không dùng `format: date` cho trường có thể chứa Julian;
- hoặc tách `actual_calendar_date_gregorian` và `historical_calendar_expression`;
- hoặc chỉ bật FormatChecker có điều kiện theo calendar_type ở validation layer.

Không để schema và Julian validator mâu thuẫn nhau.

## Blocker 6 • State Machine cần audit transition evidence

State transition function hiện trả boolean, nhưng API sau này cần ít nhất from_state, to_state, occurred_at, actor, reason, transition_id và append-only history. Self-transition cần được gọi là NO_OP hoặc REASSERTED, không trộn với lifecycle transition có thay đổi trạng thái.

## Blocker 7 • Evidence Verification cần reproducibility

Để nâng lên VALIDATION EVIDENCE VERIFIED, cần lưu hoặc in:

- source_url
- resolved_url
- HTTP status
- content_type
- content_length
- retrieved_at
- computed_sha256
- declared_sha256
- hash_match
- claim_support_result
- validator/test runner version
- exit code

Tốt nhất pin nguồn theo commit SHA thay vì `main`, vì `main` có thể thay đổi làm hash test không reproducible.

## Gate Tiếp Theo

Yêu cầu v0.6.5:

1. Sửa positive hash test bằng bytes thật và hash thật.
2. Bổ sung imports và cung cấp runner đầy đủ.
3. Thực sự chạy Claim Support Verification.
4. Tách unsupported claim test khỏi schema test.
5. Giải quyết xung đột `format: date` với Julian.
6. Thêm 02-29 matrix tests đầy đủ Gregorian + Julian.
7. Pin Evidence URL theo commit SHA để tái lập được.
8. Cung cấp execution log mới.

Chỉ khi toàn bộ evidence trên PASS thực tế mới xét `VALIDATION EVIDENCE VERIFIED`, sau đó mới mở `API CONTRACT CANDIDATE`.

## Quy Tắc Kiến Trúc Giữ Nguyên

366 Fixed Day Slots là namespace riêng của CTTTC. Day ID cố định. Year Layer thay đổi không giới hạn qua năm, thế kỷ và thiên niên kỷ. Hệ này không chiếm, đổi hoặc ảnh hưởng ID Website CFP+.
