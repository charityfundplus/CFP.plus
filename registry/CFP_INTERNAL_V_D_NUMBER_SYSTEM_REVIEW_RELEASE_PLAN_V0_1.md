# CFP+ • V & D • ID INTERNAL STANDARD • REVIEW & RELEASE PLAN

## Trạng thái
P0 • PARALLEL SYNC • EVIDENCE REQUIRED • INTERNAL

## Quy tắc nền
Một đối tượng = một Canonical Identity = một ID dùng xuyên suốt Website, GitHub, Google và Notion.
Không tạo ID riêng cho từng nền tảng.

Website: `cfp.plus/<ID>`
GitHub: `gh.cfp.plus/<ID>`
Google: `gg.cfp.plus/<ID>`
Notion: `nt.cfp.plus/<ID>`

Các nền tảng chạy song song và phải đồng bộ nội dung, trạng thái, liên kết và bằng chứng. Nền tảng nào chưa đồng bộ thì giữ trạng thái `SYNC PENDING`.

## D • DID
`DID` là ID đang hoạt động.
`DID/0` là ID gốc.
`DID/1` là ID thay đổi lần 1.

`/0` và `/1` là lớp lịch sử của cùng một DID, không tạo Canonical Identity mới.
Không tự suy rộng quy tắc phiên bản tiếp theo nếu chưa có quyết định CFP+.

## V • FUTURE RESERVED
V là hệ dự phòng cho một hệ ID số mới trong tương lai nhằm giúp ID ngắn hơn khi CFP+ nhân rộng quy mô.
Hệ V vẫn dùng chữ số `0` đến `9` và được thiết kế để chạy song song với hệ ID hiện hành khi được kích hoạt.
V phải có mapping xác định về cùng Canonical Identity, không được tạo hai danh tính cho cùng một đối tượng.

Trạng thái hiện tại: `FUTURE RESERVED • NOT ACTIVE`.
Không triển khai V vào vận hành hiện tại và không để V làm chậm Website.

## Bộ Số Cổ La Mã
CFP+ sắp xếp, giải thích và lưu giữ Bộ Số Cổ La Mã như di sản tri thức để truyền lại cho các thế hệ sau.
Việc bảo tồn Bộ Số Cổ La Mã là hạng mục tham chiếu và lưu trữ, không đồng nghĩa với việc kích hoạt V.

## Tầm nhìn Bộ Số Mới
CFP+ nghiên cứu một bộ số hoặc lớp biểu diễn mới có khả năng phục vụ Con Người, AI, tính toán kỹ thuật số, cơ sở dữ liệu, API và hệ thống máy tính hiện đại.
Thiết kế phải ưu tiên tính xác định, mapping hai chiều, chống collision, khả năng đọc bằng máy và Con Người, tương thích lâu dài và không phá dữ liệu cũ.

## Kiểm tra bắt buộc trước phát hành
1. Mapping xác định và đảo ngược được.
2. Collision và ambiguity test.
3. Leading zero và sort order.
4. Human readability và machine readability.
5. Unicode/ASCII safety khi áp dụng.
6. Database/API compatibility.
7. Version, provenance, reviewer, status, evidence và effective date.
8. Human Governance quyết định trước khi phát hành nội bộ chính thức.

## P0 hiện tại
Website là ưu tiên vận hành số 1.
GitHub, Google và Notion chạy song song với Website, không chờ nền tảng này xong mới làm nền tảng khác.
Một thay đổi chỉ được coi là hoàn tất khi có bằng chứng kiểm chứng được trên các nơi cần đồng bộ.

## Ghi chú quản trị
Nội dung này cập nhật và làm rõ các mô tả V và D ở các revision trước. Khi có xung đột diễn giải, quy tắc mới nhất trong tài liệu này được ưu tiên ở lớp vận hành, nhưng không tự thay đổi Canonical ID đã khóa hoặc Architecture Baseline nếu chưa qua Human Governance.
