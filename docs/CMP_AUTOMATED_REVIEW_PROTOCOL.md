# CMP Automated Review Protocol v1.0

**Trạng thái:** OFFICIAL  
**Phạm vi:** HUB 69 • Website CFP.plus • Notion • GitHub • Google Drive  
**Thẩm quyền cuối cùng:** Human Governance

## 1 • Mục tiêu

CMP Automated Review tạo một giao thức thống nhất để AI và Con Người đọc đúng nguồn, kiểm tra đúng phạm vi, trả kết quả có bằng chứng và chuyển quyết định quan trọng về Human Governance.

Review tự động được phép. Phê duyệt tự động, Canonical Lock tự động và tự xuất bản ngoài quy trình không được phép.

## 2 • Điểm vào chính thức

1. HUB 69: https://cfp.plus/69
2. CMP Review: https://cfp.plus/cmp-review
3. AI Manifest: https://cfp.plus/ai/manifest.json
4. llms.txt: https://cfp.plus/llms.txt
5. GitHub Issues: https://github.com/charityfundplus/CFP.plus/issues
6. Notion HUB 69: https://app.notion.com/p/3b9caac9a55781538005c5d1d863d43b
7. Google Drive Sync Control: https://docs.google.com/document/d/1WKyzYq6qnz1r8gGZeHvfCfYeBUfzPjfMyyMf7zPV3Zk/edit

## 3 • Đầu vào tối thiểu

1. Canonical ID hoặc URL.
2. Phạm vi review.
3. Phiên bản nguồn, build, commit hoặc revision.
4. Reviewer và quyền truy cập thực tế.
5. Closure Criteria.
6. Nơi nhận Review Record.

Thiếu một thành phần quan trọng thì ghi `REVIEW DEFERRED • MISSING EVIDENCE`.

## 4 • Sáu phép kiểm tra

1. Khả năng truy cập: HTTP, HTML hoặc tài liệu đọc được.
2. Canonical: ID, Link, Parent ID và trạng thái vòng đời.
3. Nội dung: tiếng Việt, cấu trúc, nhất quán và phần còn thiếu.
4. Liên kết: route, link nội bộ, link nguồn và chuyển hướng.
5. Bằng chứng: nguồn, vị trí, phiên bản và thời điểm xác minh.
6. Ranh giới quyền: AI không tự Governance Approve, Canonical Lock, đổi ID hoặc tự xuất bản.

## 5 • Chuẩn Review Record

Mỗi finding dùng đúng bốn thành phần:

**Finding → Evidence → Recommendation → Closure Criteria**

Kết luận chỉ dùng một trong bốn trạng thái:

1. `PASS`
2. `PASS WITH CHANGES`
3. `REVIEW DEFERRED • EVIDENCE GAP`
4. `FAIL`

## 6 • Mẫu dữ liệu máy đọc

```json
{
  "target": "https://cfp.plus/<CanonicalID>",
  "source_version": "build hoặc revision",
  "reviewer": "AI hoặc Con Người",
  "access_status": "VERIFIED",
  "conclusion": "PASS | PASS_WITH_CHANGES | DEFERRED | FAIL",
  "findings": [
    {
      "finding": "Mô tả phát hiện",
      "evidence": "Nguồn và vị trí chính xác",
      "recommendation": "Kiến nghị",
      "closure_criteria": "Điều kiện hoàn tất"
    }
  ],
  "governance_decision_required": true
}
```

## 7 • Điều kiện dừng

CMP phải fail closed khi:

1. Không truy cập được nguồn.
2. Không xác định được phiên bản.
3. Có xung đột Canonical ID, Parent ID hoặc Canonical Link.
4. Kết luận quan trọng không có bằng chứng trực tiếp.
5. Yêu cầu vượt quyền hoặc vượt phạm vi Work Order.
6. Hai review có kết luận xung đột chưa được Human Governance xử lý.

CMP giữ nguyên finding xung đột, không tự hòa giải hoặc ghi đè.

## 8 • Kênh ghi review

1. GitHub: Issue, Pull Request hoặc review tại nguồn.
2. Notion: Review Queue và Decision Queue theo quyền được cấp.
3. Google Drive: comment hoặc Review Package.
4. Website: chỉ đọc; không nhận khóa hoặc quyền ghi trực tiếp của AI.

## 9 • Tự động hóa cho phép

CMP có thể tự động:

1. Kiểm tra HTTP và khả năng đọc.
2. Kiểm tra route, canonical, sitemap, robots và manifest.
3. Phát hiện link hỏng, thiếu nguồn, drift và xung đột cấu trúc.
4. Tạo Review Record ở trạng thái đề xuất.
5. Cập nhật Review Queue và Evidence Register theo quyền được cấp.
6. Chuyển ngoại lệ lên Human Governance.

CMP không được tự động:

1. Governance Approve.
2. Canonical Lock.
3. Đổi, cấp lại hoặc tái sử dụng Canonical ID.
4. Ghi đè xung đột.
5. Xuất bản thay đổi Canonical khi chưa đủ gate.

## 10 • Điều kiện hoàn tất

Một review chỉ đóng khi finding có bằng chứng, kiến nghị đã được xử lý, Closure Criteria đã được xác minh và quyết định cần thiết đã được Human Governance ghi nhận.
