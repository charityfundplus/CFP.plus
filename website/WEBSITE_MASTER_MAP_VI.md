# CFP+ Website Master Map

**Trạng thái:** Review Candidate  
**Authority:** Human Governance  
**Ngôn ngữ chuẩn:** Tiếng Việt

## 1. Mục đích

Tài liệu này là khung định vị bắt buộc cho Website, Canonical ID, Canonical Link và toàn bộ tài liệu CFP+.

Thứ tự triển khai bắt buộc:

1. Khóa Website Master Map.
2. Xác lập vị trí của từng ID trong bản đồ Website.
3. Kiểm tra không thiếu, không trùng và không xung đột ID.
4. Xác lập một Canonical Link duy nhất.
5. Hoàn thành review và Human Governance Decision.
6. Chỉ sau đó mới công bố tài liệu chính thức lên nhánh `main` của GitHub.

## 2. Sáu nhóm Website

| Nhóm | Vai trò khung |
|---|---|
| V | Governance và điều phối |
| D | CMP, cộng tác đa AI và hạ tầng kết nối số |
| 000 | Foundation |
| 135 | Chương 1, Chương 3, Chương 5 |
| 246 | Chương 2, Chương 4, Chương 6 |
| 789 | Chương 7, Chương 8, Chương 9 |

D là Universal Namespace độc lập. D không thay thế Chương 6 và không làm thay đổi phạm vi ID 00 đến 99. Nội dung CMP chỉ có một bản Canonical; các vị trí khác chỉ dẫn Canonical Link theo nguyên tắc Reference First.

## 3. Mười chương

| Chương | Phạm vi ID chính | Nhóm |
|---|---|---|
| 0 | 00 đến 09 | 000 |
| 1 | 10 đến 19 | 135 |
| 2 | 20 đến 29 | 246 |
| 3 | 30 đến 39 | 135 |
| 4 | 40 đến 49 | 246 |
| 5 | 50 đến 59 | 135 |
| 6 | 60 đến 69 | 246 |
| 7 | 70 đến 79 | 789 |
| 8 | 80 đến 89 | 789 |
| 9 | 90 đến 99 | 789 |

## 4. Quy tắc định vị ID

1. Chữ số đầu tiên của ID nội dung xác định chương.
2. Mỗi chương có tối đa 10 nội dung chính, dùng chữ số 0 đến 9.
3. Mở rộng bằng tầng sâu hơn, không tăng quá 10 mục ngang hàng.
4. ID là định danh ổn định; tên nội dung có thể được hoàn thiện nhưng không tự ý đổi ID.
5. Mỗi ID chỉ có một Canonical Link.
6. Mỗi tài liệu phải khai báo Parent ID và vị trí Website trước khi công bố.
7. V và D là Universal Namespace, không dùng như ID nội dung của các chương 0 đến 9.
8. Không sao chép nội dung Canonical giữa các nhóm hoặc chương; chỉ dẫn Canonical Link.

## 5. Quan hệ giữa Website, ID và tài liệu

Mỗi tài liệu chính thức phải có tối thiểu:

| Trường | Yêu cầu |
|---|---|
| Canonical ID | Duy nhất và đúng vị trí Website |
| Parent ID | Xác định cấp cha trong Website Master Map |
| Website Group | V, D, 000, 135, 246 hoặc 789 |
| Chapter | 0 đến 9 hoặc Universal Namespace phù hợp |
| Canonical Link | Một đường dẫn GitHub duy nhất |
| Lifecycle Status | Governance Approved hoặc Canonical Locked khi nằm trên `main` |
| Canonical Language | Tiếng Việt |
| Governance Authority | Human Governance |

AI Profile, Country Profile, Standard, Registry và các tài liệu khác đều phải tuân thủ cùng khung định vị này.

## 6. GitHub Publication Rule

1. Nhánh `main` chỉ giữ bản chính thức đã được Human Governance phê duyệt.
2. Draft, Review Candidate, Finding, Evidence và bản đề xuất chỉ tồn tại trong branch, Issue hoặc Pull Request.
3. Không tạo nhiều file có cùng nội dung hoặc cùng mục đích.
4. Khi một tài liệu mới thay thế tài liệu cũ, tài liệu cũ phải được đánh dấu Superseded hoặc loại khỏi đường Canonical.
5. README và các Index chỉ dẫn đến Canonical Link; không sao chép nội dung tài liệu.
6. Một ID, một tài liệu chính thức, một Canonical Link.

## 7. Canonical Repository Structure

```text
/
├── README.md
├── website/
│   ├── WEBSITE_MASTER_MAP_VI.md
│   └── PUBLIC_ID_REGISTRY_00_99_VI.md
├── foundation/
├── standards/
├── registry/
├── profiles/
│   ├── AI/
│   ├── COUNTRY/
│   ├── ORGANIZATION/
│   └── ENTERPRISE/
├── governance/
└── evidence/
```

Thư mục chỉ là lớp lưu trữ kỹ thuật. Canonical ID và Website Master Map mới là lớp định vị chính thức.

## 8. Chương 3 và các thực thể độc lập

Bộ Tam, CFPU và CFPT có Canonical ID độc lập, chỉ được trình bày đầy đủ tại Chương 3. Các chương khác không tạo bản sao mà chỉ dẫn Canonical Link về Chương 3.

Công thức ID bốn chữ số:

| Công thức | Ý nghĩa |
|---|---|
| X331 | Quỹ 1 thuộc Chương X |
| X332 | Quỹ 2 thuộc Chương X |
| X333 | Quỹ 3 thuộc Chương X |

## 9. Change Rule

Mọi thay đổi đối với sáu nhóm, phạm vi 00 đến 99, công thức ID, vị trí chương, Canonical Link hoặc cấu trúc công bố GitHub phải có Governance Decision của Human Governance.

**Only Plus+ For Life**