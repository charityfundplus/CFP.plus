# HUB 69 Universal Master Template • v1.0 • Draft

## Mục tiêu

Khuôn mẫu thống nhất để Notion, GitHub, Google Drive và Website CFP+ phản chiếu đúng một kiến trúc HUB 69, giữ nguyên Canonical ID và Canonical Link, đồng thời bảo đảm traceability, evidence và review.

**Trạng thái:** DRAFT  
**Governance Approved:** Chưa  
**Canonical Locked:** Chưa

## 0 • Universal Short Links

1. HUB 69: https://cfp.plus/69
2. Mọi đối tượng: https://cfp.plus/<CanonicalID>
3. Một domain • Một dấu slash • Một Canonical ID là chuỗi số liền nhau.
4. Không dùng /hub/ hoặc /69/ trung gian.
5. Không dùng chữ, ký hiệu, tham số hoặc dấu slash cuối.
6. ID bắt đầu bằng 0 thuộc Chương 0 hợp lệ.
7. Không tái sử dụng ID hoặc Link.

## 1 • Universal Architecture Tree

1. HUB 69
2. Homepage
3. Groups: V • 000 • 135 • 246 • 789
4. Chapters: 0 đến 9
5. Core Content: 00 đến 99
6. AI Directory
7. Countries
8. Developers
9. AI
10. News
11. Assets
12. Evidence
13. Reviews
14. Releases
15. Archive

## 2 • Invariants

1. Một kiến trúc • Một hệ ID • Một cấu trúc nội dung • Nhiều nền tảng thực thi.
2. Không nền tảng nào tự tạo kiến trúc, ID, tên hoặc trạng thái Canonical khác.
3. Không dùng /group/0/.
4. Không tạo bảng hoặc cây ID song song.
5. HUB 69 là HUB duy nhất của CFP+.

## 3 • Cả Ba Nơi Làm Một Website

1. Notion làm nội dung, cấu trúc, Canonical ID, Canonical Link, inventory, Work Queue, review, Decision Queue và Governance Record.
2. Google Drive làm hình ảnh, PDF, tài liệu cộng tác, evidence, review package, release package và bản chuyển giao cho Gemini.
3. GitHub làm mã nguồn, routing, dữ liệu có cấu trúc, Pull Request, kiểm thử, build, deployment manifest và lịch sử kỹ thuật.
4. Website CFP.plus là một sản phẩm công khai duy nhất được sinh từ bản đã đồng bộ.
5. Không tạo ba Website riêng. Không nền tảng nào tự triển khai một phiên bản nội dung xung đột.

## 4 • AI Chủ Nhà Và Quyền Làm Website

1. Notion AI lập Working Draft, danh sách Developer → AI, inventory, Finding và Work Queue. Không tự cấp ID, đổi Parent, Governance Approve hoặc Canonical Lock.
2. Gemini đọc tài liệu Drive được chia sẻ, chuẩn bị nội dung và tài sản Website, review giao diện, đề xuất thay đổi. Không tự sửa ID hoặc xuất bản ngoài Pull Request đã duyệt.
3. GitHub Copilot và Codex đọc kho, tạo nhánh, commit, Pull Request, kiểm thử và build. Không ghi thẳng vào main cho thay đổi Canonical.
4. ChatGPT điều phối, hợp nhất kết quả, phát hiện drift, chuẩn hóa tiếng Việt và chuẩn bị Decision Package. Không trở thành Source of Truth duy nhất.
5. Human Governance giữ quyền quyết định cuối cùng.

## 5 • Universal Lifecycle

1. Draft
2. Review Candidate
3. Review Complete
4. Governance Approved
5. Canonical Locked

AI không tự Governance Approve. AI không tự Canonical Lock. Artifact đã Locked chỉ mở lại bằng Governance Decision. Không sửa ngược lịch sử. Mọi thay đổi phải có traceability.

## 6 • Universal Data Fields

1. Title
2. Canonical ID
3. Canonical Link
4. Parent ID
5. Node Type
6. Chapter
7. Group
8. Language
9. Status
10. Version
11. Owner
12. Source of Truth
13. Notion Page ID
14. GitHub Path
15. GitHub Commit SHA
16. Google Drive File ID
17. Google Drive Revision
18. Website Route
19. Build SHA
20. Content Hash
21. Evidence Link
22. Review Record
23. Governance Decision
24. Last Updated
25. Next Action
26. Sync State

## 7 • Universal Page Template

1. Identity: Title, Canonical ID, Canonical Link, Node Type, Parent ID.
2. Purpose: vai trò, phạm vi và đối tượng phục vụ.
3. Placement: Group, Chapter và vị trí trong kiến trúc.
4. Content: toàn văn tiếng Việt hiện hành.
5. Directory: Country → Developer → AI khi áp dụng.
6. Evidence: nguồn, trạng thái bằng chứng và thời điểm kiểm tra.
7. Review: Finding → Evidence → Recommendation → Closure Criteria.
8. Governance: lifecycle, Decision Record và quyền phê duyệt.
9. Sync: Notion, GitHub, Drive, Website, hash, revision và trạng thái.
10. Release: build, route audit, deployment evidence và rollback.

## 8 • Universal Sync Protocol

1. Một chỉnh sửa hợp lệ tại Notion, GitHub hoặc Drive tạo một Sync Event.
2. CMP xác định Document ID, version, source revision, destination và evidence.
3. So sánh nội dung với hai bản còn lại.
4. GitHub thay đổi qua nhánh và Pull Request.
5. Website chỉ build từ commit đã review.
6. Production validation trả bằng chứng về Notion và Drive.
7. Chỉ đánh dấu SYNCED khi nội dung, ID, Link, route và manifest khớp.
8. Nếu collision, ambiguity, wrong parent hoặc ID conflict thì dừng đối tượng lỗi, giữ bằng chứng và chuyển Human Governance.
9. Các đối tượng không phụ thuộc được tiếp tục.

## 9 • Registers Bắt Buộc

1. Website Inventory
2. Canonical Link Map
3. Conflict Log
4. Sync Log
5. Evidence Register
6. Review Register
7. Release Register
8. Decision Queue

## 10 • Output Manifests

1. Notion Manifest: page ID, content status, relations, review, governance và sync state.
2. GitHub Manifest: /docs/, /registry/, /directory/, /assets/, /evidence/, /releases/, /archive/.
3. Google Drive Manifest: Assets, Evidence, Reviews, Releases và Archive.
4. Website Manifest: route, Canonical ID, source commit, build SHA, validation và deployment evidence.
5. Tên file bắt đầu bằng Canonical ID khi áp dụng. Không rename ID.

## 11 • Chế Độ Phục Hồi

1. Danh sách AI theo từng nhà phát triển do Notion AI đang lập có trạng thái Working Draft • Pending Review.
2. Đóng băng thay đổi Canonical ID và Canonical Link cho đến khi hoàn tất đối chiếu.
3. Giữ Website ở trạng thái Public Preview.
4. Đối chiếu riêng Hoa Kỳ 6911 và Việt Nam 6984 trước khi sửa dữ liệu công khai.
5. Bổ sung robots.txt, sitemap.xml và manifest dữ liệu máy đọc.
6. Không để gián đoạn một AI ngăn ba nền tảng còn lại tiếp tục đọc và review.

## 12 • Điểm Vào Đồng Bộ

1. Notion: https://app.notion.com/p/19bc113a05654b19adb2a609506a8ace
2. CFP SYNC 001: https://app.notion.com/p/3bdcaac9a55781bfbcf9e55124f33b2e
3. GitHub Pull Request: https://github.com/charityfundplus/CFP.plus/pull/72
4. Google Drive: https://docs.google.com/document/d/1KiqNXQLvaHeookeArmLfhJ-UPCzkDeeXp37cYnzD5cM/edit
5. Website: https://cfp.plus/69

## 13 • Review Rule

**Finding → Evidence → Recommendation → Closure Criteria**

Nội dung chưa đủ bằng chứng ghi **PENDING EVIDENCE**. Không tự đổi, tái sử dụng hoặc khóa Canonical ID hoặc Canonical Link.
