# CFP+ • CTTTC • Review Schema v0.6.5

Status: REVIEW CANDIDATE • PASS WITH CHANGES • VALIDATION EVIDENCE PENDING • CHƯA SANG API

## Kết luận

v0.6.5 chưa đủ điều kiện nâng lên VALIDATION EVIDENCE VERIFIED.

## Finding 1 • Positive hash log không khớp artifact pinned

Artifact được tuyên bố:

`README.md` tại commit `99aab62ef356d015a682ae85328b3e80a9df2ffe`.

Đối chiếu độc lập từ GitHub cho thấy README tại commit này có nội dung thực tế và Git blob SHA `955873111d4e96a2f53e81d6011974520484a8b5`.

SHA256 được tính độc lập từ nội dung UTF 8 trả về là:

`0cca6b93c8b705abfeb2b58f2669bb10f244ab80e4b63a53561b0ffd14d5a254`

Trong khi log v0.6.5 báo:

`4b825dc642cb6eb9a060e54bf8d69288fbee490426d3fbcdab9d40e87d0c3a62`

Hai giá trị không khớp. Vì vậy Positive Integrity Test chưa được chấp nhận.

## Finding 2 • Content length không khớp

Nội dung UTF 8 được đối chiếu có 1182 bytes.

Log v0.6.5 báo 2450 bytes.

Cần ghi lại exact bytes fetched và cách tính content_length để tái lập.

## Finding 3 • Claim Support log không tái lập

Record mẫu:

Title: `Charity Fund Plus Ecosystem Architecture`

Summary: `Universal record schema and governance protocols for CFP ecosystem.`

Theo chính thuật toán keyword v0.6.5, các từ dài hơn 4 ký tự chỉ khớp `governance` trong README pinned. Tỷ lệ đối chiếu độc lập xấp xỉ 1/9 = 0.11, thấp hơn ngưỡng 0.20.

Log báo 0.75 nên không tái lập được.

## Finding 4 • Claim Support heuristic chưa đủ để quyết định Evidence Verified

Keyword overlap 20% không chứng minh claim. Đây chỉ nên là `CLAIM_SUPPORT_CANDIDATE` hoặc `SEMANTIC_REVIEW_REQUIRED`.

Không tự chuyển Evidence sang Verified từ heuristic keyword.

## Finding 5 • Positive test đang tự lấy hash rồi verify lại cùng response target

Runner tải pinned URL để tính `real_sha256`, sau đó gọi verifier tải lại cùng URL và so sánh. Cách này kiểm tra verifier mechanics nhưng không chứng minh declared hash đã được lưu trước và đối chiếu độc lập.

Cần fixture có declared SHA256 cố định, được tính trước từ artifact immutable và commit vào repo. Test runner chỉ được đọc expected hash và so sánh với bytes tải về.

## Finding 6 • Error fallback có thể che lỗi mạng

Khi lần tải đầu lỗi, code đặt `real_sha256` thành toàn số 0. Sau đó vẫn chạy positive test. Nên fail ngay nếu không fetch được artifact, không dùng fallback hash cho positive test.

## Finding 7 • 02-29 matrix còn thiếu đối xứng đầy đủ

Đã có 4 test nhưng cần thêm tối thiểu:

Gregorian non leap + is_slot_mapping false = FAIL.

Gregorian non leap + actual_calendar_date 2023-02-29 = FAIL.

Julian non leap + structural slot = PASS.

Julian non leap + actual date 02-29 = FAIL.

Julian leap + is_slot_mapping true = FAIL.

## Finding 8 • Evidence status gate

`evidence_status = Verified` cần yêu cầu đồng thời:

Artifact integrity PASS.

Claim support reviewed and accepted.

No unresolved contradiction.

Verification actor and timestamp present.

Không được coi keyword ratio là đủ.

## Yêu cầu v0.6.6

1. Commit schema, validators, fixtures và runner thật vào repository.
2. Tạo pinned evidence fixture với URL immutable và SHA256 expected cố định.
3. Không tính expected hash trong cùng test run.
4. Positive hash phải so với expected hash đã commit trước.
5. Claim Support phải đổi thành review signal, không phải quyết định Verified tự động.
6. Bổ sung đầy đủ ma trận 02-29 Gregorian và Julian.
7. In exact response byte length và computed hash.
8. Chạy CI thật trên GitHub Actions nếu có thể và cung cấp Run ID, Commit SHA, Job Result, log.
9. Chỉ khi các evidence có thể tái lập độc lập mới xem xét VALIDATION EVIDENCE VERIFIED.

## Gate

Giữ nguyên:

REVIEW CANDIDATE

PASS WITH CHANGES

VALIDATION EVIDENCE PENDING

CHƯA SANG API
