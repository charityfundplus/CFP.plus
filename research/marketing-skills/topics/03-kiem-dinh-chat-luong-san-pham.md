# CFP+ • Kiểm định chất lượng sản phẩm trước khi phục vụ
Trạng thái: POLICY PROPOSAL / backend gate chưa hoạt động.

## Quy tắc
Kho nghiên cứu có thể chứa tài liệu chưa kiểm chứng nhưng phải gắn nhãn. Kho ứng dụng chính thức chỉ phân phối sản phẩm đã nghiên cứu, thử nghiệm, kiểm chứng độc lập, phê duyệt và phát hành.

## Các trạng thái
RESEARCH → SANDBOX → REVIEWED → APPROVED → RELEASED; HOLD hoặc REVOKED khi có vấn đề.

## Hồ sơ bắt buộc
Nguồn, tác giả, license, commit, checksum, version, SBOM, phạm vi sử dụng, kết quả chức năng/an toàn/hiệu năng, reviewer, approval, giới hạn, giám sát và phương án thu hồi.

## Backend gate
Không phân phối RESEARCH/SANDBOX/REVIEWED/APPROVED chưa RELEASED. Kiểm tra quyền, hiệu lực phê duyệt, hash, quốc gia và ngôn ngữ. Mọi thay đổi phải audit; bản nâng cấp kiểm thử lại.

## Kiểm thử
Chặn sản phẩm thiếu evidence, sai hash, hết hạn, bị thu hồi hoặc không phù hợp locale. Xem Issue #229.
