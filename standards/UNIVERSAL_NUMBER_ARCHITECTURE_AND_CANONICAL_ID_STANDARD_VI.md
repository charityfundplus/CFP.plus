# CFP+ Universal Number Architecture and Canonical ID Standard

## 0 • Thông tin tài liệu

- **Tên tiếng Việt:** Kiến trúc Số Phổ quát và Tiêu chuẩn Canonical ID CFP+
- **Canonical Language:** Tiếng Việt
- **Document Type:** Foundation Standard
- **Lifecycle Status:** Working Draft
- **Governance Status:** Pending Human Governance Review
- **Canonical Status:** Chưa khóa
- **Repository:** CFP.plus

## 1 • Mục đích

Tài liệu này thống nhất trong một chủ đề duy nhất các nội dung liên quan đến:

1. Thiết kế kiến trúc số CFP+.
2. Công thức hình thành Canonical ID.
3. Cách đọc và diễn giải Canonical Path.
4. Nguyên tắc chọn và phân chia nội dung.
5. Quy tắc soạn thảo trang tương ứng với từng Canonical ID.
6. Điều kiện mở rộng thêm tầng.

Mọi tài liệu khác chỉ tham chiếu tiêu chuẩn này và không lặp lại định nghĩa.

## 2 • Mười Chương nền tảng

Toàn bộ kiến trúc sử dụng mười Chương cố định:

| Chữ số | Chương |
|---|---|
| 0 | Foundation |
| 1 | Sự Sống |
| 2 | Con Người |
| 3 | Ba Quỹ |
| 4 | Tôn Giáo |
| 5 | Cộng Đồng |
| 6 | AI và Công Nghệ |
| 7 | Doanh Nghiệp |
| 8 | Tổ Chức |
| 9 | Quốc Gia |

Mười Chương là khung phân loại chung nhằm tổ chức các lĩnh vực lớn của sự sống, con người và xã hội.

## 3 • Công thức Canonical ID

### 3.1 Chữ số đầu tiên

Chữ số nằm đầu tiên xác định **Chương gốc** của Canonical ID.

### 3.2 Mỗi chữ số là một Chương

Mọi chữ số xuất hiện trong Canonical ID đều đại diện cho đúng Chương mang số đó.

Không có chữ số đệm.

Không có chữ số chỉ dùng để định dạng.

### 3.3 Cách đọc

Canonical ID được đọc tuần tự từ trái sang phải.

Mỗi chữ số tiếp theo bổ sung thêm một Chương vào Canonical Path và kế thừa toàn bộ ngữ cảnh của các chữ số đứng trước.

Ví dụ:

- `0` = Chương 0.
- `00` = Chương 0 → Chương 0.
- `000` = Chương 0 → Chương 0 → Chương 0.
- `1234` = Chương 1 → Chương 2 → Chương 3 → Chương 4.
- `1203` = Chương 1 → Chương 2 → Chương 0 → Chương 3.

Vì vậy, `000` không phải một số 0 kèm hai số đệm. Đó là ba lần xuất hiện liên tiếp của Chương 0 trong cùng Canonical Path.

## 4 • Canonical Path

### 4.1 Tính bất biến

Canonical Path của một ID là bất biến sau khi được Human Governance phê duyệt và khóa.

### 4.2 Không đảo thứ tự

Các chữ số không được hoán đổi hoặc sắp xếp lại.

Thay đổi thứ tự chữ số tạo ra một Canonical Path khác và làm thay đổi ý nghĩa.

### 4.3 Kế thừa toàn bộ đường dẫn

Mỗi tầng mới không chỉ kế thừa tầng ngay trước nó mà kế thừa toàn bộ Canonical Path từ chữ số đầu tiên.

### 4.4 Định nghĩa Chương quyết định ý nghĩa

Canonical ID được tạo bằng chữ số nhưng được hiểu bằng định nghĩa của các Chương.

Thay đổi định nghĩa một Chương có thể làm thay đổi ý nghĩa của mọi Canonical Path chứa Chương đó. Vì vậy, định nghĩa của Mười Chương phải được quản trị và kiểm soát thay đổi.

## 5 • Nguyên tắc không chồng lấn

Khó nhất không phải tạo ra nhiều Canonical ID mà là xác định đúng mười nội dung nền tảng và các nội dung con sao cho:

- Không trùng nhau.
- Không chồng lấn nhau.
- Không quá sát nhau đến mức khó phân biệt.
- Không bỏ sót phạm vi thiết yếu.
- Có khả năng mở ra các thế hệ sau thuận lợi.

Mỗi nhóm mười nội dung ở một tầng phải có:

1. Phạm vi riêng.
2. Vai trò riêng.
3. Giá trị riêng.
4. Ranh giới rõ ràng.
5. Khả năng mở rộng độc lập.

Nếu một nội dung liên quan đến nhiều Canonical Path, nội dung đó chỉ có một Canonical ID chính. Các vị trí khác dẫn Canonical Link đến ID chính, không sao chép nội dung thành nhiều bản.

## 6 • Nguyên tắc tham chiếu trước khi soạn thảo

Trước khi tạo một Canonical ID hoặc soạn nội dung mới, người thực hiện phải rà soát:

- Các tầng tổ tiên của Canonical Path.
- Các ID cùng cấp và lân cận.
- Các nội dung đã tồn tại có phạm vi gần nhau.
- Các Canonical ID được tham chiếu.

Mục tiêu là:

- Kế thừa đúng nền tảng.
- Không sao chép.
- Không chồng lấn.
- Không tạo hai ID cho cùng một nội dung.
- Chỉ bổ sung giá trị mới cần thiết.

## 7 • Một Canonical ID tương ứng một trang độc lập

Mỗi Canonical ID tương ứng với một trang Website độc lập.

Canonical Path là cố định, nhưng cách trình bày trên trang có thể linh hoạt.

Trang có thể chứa:

- Văn bản.
- Hình ảnh.
- Video.
- Bảng.
- Dữ liệu.
- Canonical Link.
- Tài liệu tham chiếu.
- Nội dung mở rộng khác.

Mọi thành phần trên trang phải phục vụ đúng phạm vi và ý nghĩa của Canonical Path.

## 8 • Nguyên tắc mở rộng theo nhu cầu

### 8.1 Không bắt buộc mọi nhánh có cùng độ sâu

Độ sâu của Canonical ID phụ thuộc vào nhu cầu thực tế của nội dung.

Nếu nội dung đã đầy đủ, rõ ràng và trọn vẹn ở hai hoặc ba tầng thì dừng tại đó.

Không mở thêm tầng chỉ vì hệ thống còn khả năng mở rộng.

### 8.2 Chỉ mở tầng mới khi cần

Chỉ tạo tầng con khi có ít nhất một điều kiện sau:

- Nội dung hiện tại quá lớn để trình bày hiệu quả trên một trang.
- Có thể phân chia thành các chủ đề con độc lập.
- Mỗi chủ đề con có phạm vi rõ ràng và không chồng lấn.
- Việc tách tầng giúp người đọc, AI hoặc hệ thống quản lý hiểu rõ hơn.
- Nội dung mới thực sự cần một Canonical ID và Canonical Link riêng.

### 8.3 Quy tắc dừng

Một nhánh phải dừng mở rộng khi trang hiện tại đã:

- Đủ nội dung.
- Rõ nghĩa.
- Có ranh giới hoàn chỉnh.
- Không cần chia nhỏ để quản lý hoặc tham chiếu.

## 9 • Nguyên tắc sống và quan hệ

Canonical ID không được xem như một mã số cô lập.

Mỗi ID có:

- Nguồn gốc.
- Canonical Path.
- Quan hệ tổ tiên.
- Quan hệ cùng cấp.
- Quan hệ với các tầng con.
- Trách nhiệm kế thừa.
- Khả năng đóng góp trở lại hệ thống.

Một Canonical ID khỏe mạnh phải vừa nhận được giá trị từ hệ thống vừa đóng góp giá trị cho cộng đồng Canonical ID.

Đây là nguyên tắc thiết kế quan hệ, không thay thế các quy tắc kỹ thuật và quản trị.

## 10 • Quy tắc quản trị

1. Mười Chương nền tảng chỉ được thay đổi bằng Human Governance Decision.
2. Canonical Path chỉ được khóa sau khi hoàn thành review và có bằng chứng phù hợp.
3. Không tự ý đổi Canonical ID đã khóa.
4. Không tạo ID mới khi nội dung hiện tại đã đủ.
5. Không sao chép cùng một nội dung vào nhiều ID.
6. Nội dung liên quan ở vị trí khác phải dùng Canonical Link.
7. Mọi đề xuất thay đổi phải ghi rõ tác động đến các Canonical Path hiện có.

## 11 • Tuyên bố cốt lõi

> Khó nhất không phải là tạo ra vô số Canonical ID, mà là xác định đúng Mười Chương và mười nội dung của từng tầng: không trùng nhau, không chồng lấn, không quá sát nhau và đủ khả năng mở rộng thuận lợi cho các thế hệ sau.

> Canonical ID chỉ mở thêm tầng khi nội dung thực sự cần mở rộng. Nội dung đã đầy đủ, rõ ràng và trọn vẹn thì dừng tại tầng hiện có.

## 12 • Trạng thái review

Tài liệu này là **Working Draft** được tổng hợp từ chỉ đạo trực tiếp của Human Governance.

Tài liệu chưa phải Canonical Locked.

Các bước tiếp theo:

1. Kiểm tra sự thống nhất với Website Master Map.
2. Kiểm tra sự thống nhất với Public ID Registry.
3. Independent AI Review.
4. Human Governance Decision.
5. Cập nhật trạng thái nếu được phê duyệt.
