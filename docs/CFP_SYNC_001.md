# CFP SYNC 001 • Trung Tâm Đồng Bộ Đa Nền Tảng

**Trạng thái:** REVIEW CANDIDATE • RECOVERY CONTROL  
**Governance Approved:** Chưa  
**Canonical Locked:** Chưa  
**Quy tắc an toàn:** Không tự đổi ID, Link, Parent hoặc trạng thái quản trị.

> Bảo đảm Notion, GitHub, Google Drive và Website CFP+ dùng cùng một phiên bản nội dung, có bằng chứng đồng bộ và không phụ thuộc vào một AI duy nhất.

## 1 • Mô hình nguồn thống nhất

1. **Notion:** Source of Truth làm việc, điều phối, quyết định và Decision Queue.
2. **GitHub:** nguồn công khai, AI readable, lịch sử phiên bản, Pull Request và bằng chứng kỹ thuật.
3. **Google Drive:** không gian cộng tác, hồ sơ review, biên bản, tài liệu chuyển giao và evidence.
4. **Website CFP+:** sản phẩm công khai được tạo từ nguồn đã duyệt. Website không tự trở thành Source of Truth.

**Một Nội Dung Gốc • Ba Bản Gốc Đồng Bộ • Một Website Được Sinh Từ Bản Đã Duyệt**

## 2 • Quyền của AI chủ nhà

| Nền tảng | AI chủ nhà | Được phép | Không được phép |
|---|---|---|---|
| Notion | Notion AI | Đọc, soạn Working Draft, đối chiếu, tạo Finding, cập nhật Work Queue theo quyền được cấp | Tự Governance Approve, tự Canonical Lock, tự ghi đè xung đột |
| Google Drive | Gemini | Đọc tài liệu được chia sẻ, soạn bản cộng tác, review, tạo evidence và đề xuất thay đổi | Tự đổi Canonical ID hoặc xuất bản Website ngoài quy trình |
| GitHub | GitHub Copilot, Codex | Đọc kho, tạo nhánh, commit, Pull Request, review và kiểm tra kỹ thuật | Ghi thẳng vào main cho thay đổi Canonical hoặc tự merge khi chưa đủ gate |
| Điều phối | ChatGPT | Hợp nhất kết quả, phát hiện xung đột, chuẩn hóa tiếng Việt, chuẩn bị Decision Package | Trở thành Source of Truth duy nhất hoặc tự thay Human Governance |

## 3 • Sync Manifest bắt buộc

1. Document ID ổn định.
2. Tên chuẩn.
3. Version.
4. Lifecycle Status.
5. Notion Page ID và Revision.
6. GitHub Path và Commit SHA.
7. Google Drive File ID và Revision.
8. Website Route và Build SHA khi đã xuất bản.
9. Content Hash.
10. Sync Timestamp.
11. Sync State: SYNCED, DRIFT, CONFLICT hoặc BLOCKED.
12. Evidence Link và Closure Criteria.

## 4 • Quy trình Sync Event

1. AI hoặc Con Người chỉnh sửa tại một nền tảng được phép.
2. CMP ghi nhận Sync Event.
3. Nội dung được so sánh với hai bản còn lại.
4. Nếu khớp chuẩn, tạo bản cập nhật tại Notion, GitHub và Drive.
5. Thay đổi GitHub đi qua nhánh và Pull Request.
6. Website chỉ triển khai từ commit đã qua review.
7. Kiểm tra route, ID, Link và nội dung tiếng Việt.
8. Chỉ đánh dấu SYNCED khi ba bản gốc và Website khớp với manifest.
9. Nếu có xung đột, giữ nguyên bằng chứng và chuyển Decision Queue. Không tự ghi đè.

## 5 • Chế độ phục hồi hiện tại

1. Đóng băng mọi thay đổi Canonical ID và Canonical Link.
2. Website CFP.plus đã phát hành chính thức; các nội dung Working Draft vẫn giữ đúng trạng thái và không được suy diễn thành Canonical Lock.
3. Kết quả Notion AI lập danh sách AI theo từng nhà phát triển được tiếp nhận là **Working Draft • Pending Review**.
4. Không dùng tài liệu Global AI Developer & System Integration Registry làm chuẩn Canonical khi chưa đồng bộ.
5. Đối chiếu riêng nhánh Hoa Kỳ 6911 và Việt Nam 6984 trước khi sửa Website.
6. Duy trì `robots.txt`, `sitemap.xml`, `llms.txt`, AI manifest và CMP Automated Review Protocol cho Website.
7. Không để gián đoạn ChatGPT Work ngăn Notion, GitHub, Drive hoặc Website tiếp tục đọc chuẩn đã công bố.

## 6 • Điểm vào

1. [Notion • CFP SYNC 001](https://app.notion.com/p/3bdcaac9a55781bfbcf9e55124f33b2e)
2. [Google Drive • CFP SYNC 001](https://docs.google.com/document/d/1WKyzYq6qnz1r8gGZeHvfCfYeBUfzPjfMyyMf7zPV3Zk/edit)
3. [GitHub • CFP.plus](https://github.com/charityfundplus/CFP.plus)
4. [Website • CFP+](https://cfp.plus)
5. [CMP Automated Review](https://cfp.plus/cmp-review)
6. [AI Manifest](https://cfp.plus/ai/manifest.json)

## 7 • Review Rule

**Finding → Evidence → Recommendation → Closure Criteria**

Nội dung chưa đủ bằng chứng ghi **PENDING EVIDENCE**. Không tự đổi, tái sử dụng hoặc khóa Canonical ID hoặc Canonical Link.
