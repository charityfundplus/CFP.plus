# CFP+ AI Work Framework v1

**Mục tiêu:** Tạo một khung duy nhất để tất cả AI 🤖 nhận việc, tạo kết quả, review và đưa nội dung vào CFP.plus nhanh nhất.

## 1 • Khung Website

Mỗi Chương Gốc dùng cấu trúc:

- Ông 👴 = 1 Chương Gốc
- 10 Con 👶 = 10 ID con trực tiếp
- 100 Cháu 👧 = 10 ID cháu dưới mỗi Con

Ví dụ:

- `3` → Chương Gốc
- `31` → Con
- `312` → Cháu

Đọc ngược để soi chiếu:

`312 → 31 → 3`

## 2 • Thứ tự triển khai

1. Định vị ID.
2. Tạo link số trực tiếp `https://cfp.plus/<ID>`.
3. Áp mẫu trang chuẩn.
4. Đưa nội dung hiện có vào đúng Parent.
5. AI khác review.
6. Bổ sung Evidence.
7. Sửa và tiếp tục review nhiều vòng.

Link và ID phải có trước để việc giao việc không bị mơ hồ.

## 3 • Khung AI Directory

AI Directory không giới hạn ở 0–100.

Cấu trúc:

`Quốc Gia → AI Country ID → Nhà Phát Triển → AI`

Quy tắc:

- `69` là HUB duy nhất cho AI 🤖.
- Link công khai dùng trực tiếp `cfp.plus/<CanonicalID>`.
- Không dùng `/hub/69/` làm lớp URL trung gian.
- `0` giữ lại cho phát triển và mở rộng.
- `1–9` dành cho các vị trí ưu tiên trong từng nhánh theo review.
- Không tự renumber hoặc reuse ID đã cấp.
- Khi chưa đủ dữ liệu để phân tầng: `Pending Classification`.

## 4 • Work Order chuẩn cho mỗi AI

Mỗi AI nhận việc phải có đúng các trường sau:

**AI / Vai trò chính:**
Tên AI và phạm vi chính.

**Scope:**
Chương, ID, quốc gia, Developer hoặc AI được giao.

**Source:**
Tài liệu, repo, link hoặc dữ liệu đầu vào.

**Target ID:**
ID cần tạo hoặc cập nhật.

**Target Link:**
`https://cfp.plus/<ID>`

**Việc phải làm:**
Nêu rõ đầu ra cụ thể.

**Deliverable:**
Trang, route, bảng, danh sách, nội dung hoặc Finding có thể kiểm tra.

**Evidence:**
Nguồn hỗ trợ khi có.

**Review Status:**
`PASS` / `PASS WITH CHANGES` / `NEEDS REVIEW` / `BLOCKED`

**Blocker:**
Chỉ ghi khi có collision, sai Parent, ghi đè Canonical, thiếu quyền kỹ thuật hoặc hành động không thể đảo ngược.

## 5 • Phân công AI Core Team

### ChatGPT
Điều phối tổng thể, cấu trúc Website, ID, route, GitHub Canonical, hợp nhất kết quả.

### Gemini
Bao phủ dữ liệu lớn, Quốc Gia, Nhà Phát Triển, AI, Google/Drive/Notion khi có quyền.

### Claude
Hiến Chương, Hiến Pháp, Governance, tài liệu dài, logic review.

### Perplexity
Nguồn công khai, Evidence, kiểm chứng Nhà Phát Triển và AI.

### Grok
Phản biện độc lập, stress test, tìm thiếu sót và edge case.

### Meta AI
Bổ sung hệ sinh thái, nền tảng, mạng xã hội, AI/Developer context.

### GitHub Copilot
Code, route generation, link test, automation và deployment khi được kết nối.

### Notion AI
Phân loại, chuẩn hóa, duy trì Workspace và Source of Truth.

## 6 • Quy tắc tăng tốc

- Không chờ hoàn hảo mới tạo trang.
- Phủ link và khung trước.
- Nội dung có thể sửa thì đưa lên trước ở trạng thái phù hợp.
- AI làm song song nhưng không cùng ghi đè một trang tại cùng thời điểm.
- Một Work Order chỉ có một AI đầu ra chính.
- Review chạy song song với Build.
- Không đưa các lo ngại giả định thành blocker.

## 7 • Tiêu chuẩn kết quả

Một Work Order chỉ được coi là có kết quả khi tạo ra ít nhất một trong các đầu ra sau:

- Link sống.
- ID đã định vị.
- Trang đã phủ nội dung.
- Danh sách đã bổ sung.
- Evidence đã gắn.
- Finding cụ thể.
- Commit hoặc thay đổi có thể kiểm tra.

Chỉ thảo luận hoặc đề xuất chung không tính là hoàn thành.

## 8 • Mục tiêu hiện tại

Ưu tiên P0:

1. Phủ khung Website 0–9.
2. Đủ 100 Con.
3. Đủ 1.000 Cháu.
4. Đưa tài liệu hiện có vào đúng ID.
5. HUB 69 sống.
6. Bảng Quốc Gia sống.
7. AI Directory có link trực tiếp.
8. Mở rộng danh sách Nhà Phát Triển và AI toàn cầu.
9. Review nhiều vòng.

**CFP+ Nâng Tầm AI 🤖 Thành Bạn Đồng Hành.**

**Only Plus+ For Life.**
