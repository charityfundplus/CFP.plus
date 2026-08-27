# CFP+ • AI WORK DISPATCH • 2026-08-27

Status: ASSIGNED • REVIEW REQUIRED
Priority: P0 • Website Việt Nam + HUB 69 + AI Directory + Evidence

## Nguyên tắc vận hành

- Shared MCP endpoint: https://mcp.cfp.plus/mcp/
- Scope mặc định: read + propose
- Evidence First
- Proposal writes luôn REVIEW_REQUIRED
- Human Governance là quyền quyết định cuối
- Không tự Canonical Lock
- Connected ≠ Running ≠ Paying

## Phân công 8 AI

### 1. ChatGPT • Điều phối tổng thể
- Tổng hợp tiến độ các Work Lane.
- Chốt ưu tiên Website public: /000, /0123456789, /0–/9, /69, /267, /28882.
- Đồng bộ nội dung giữa GitHub, Drive, Notion và Website.
- Gom blocker và chỉ chuyển Human Governance các quyết định thật sự cần người dùng.
- Output: bảng PASS/FAIL, blocker, evidence, next action.

### 2. Claude • Governance & Deep Review
- Review logic, governance, Canonical conflict và wording có rủi ro hiểu sai.
- Ưu tiên Chương 3 Ba Quỹ, Chương 6 AI & Công Nghệ, CFP+ • Con Người & AI.
- Kiểm tra không có đề xuất nào vượt REVIEW_REQUIRED hoặc Human Governance.
- Output: Critical/Major issues, đề xuất wording, conflict list.

### 3. Gemini • Vietnamese Content & UX QA
- Review tiếng Việt, lỗi ký tự, câu dài, trùng lặp, tính dễ đọc.
- Kiểm tra menu, tên trang, thứ tự 10 Chương, HUB 69, CMP, CTTTC.
- Không thay đổi ý nghĩa nền tảng hoặc Canonical ID.
- Output: UX/content issues + sửa câu trực tiếp.

### 4. Perplexity • Research, Evidence & Global Coverage
- Kiểm chứng claim bằng nguồn phù hợp.
- Review Global AI Directory: Country → Developer → AI.
- Tìm thiếu sót, duplicate, dead link, unsupported claim.
- Không quyết định Canonical mapping.
- Output: evidence map, gap list, source-backed recommendations.

### 5. GitHub Copilot • Repository & Technical QA
- Kiểm tra numeric routes, broken links, duplicate/stale files, CI, scripts, deployment consistency.
- Ưu tiên CFP.plus repo và cfp-gateway.
- Đề xuất patch kỹ thuật nhỏ, có thể review.
- Output: technical issue list + patch/commit candidate + verification steps.

### 6. Grok • Adversarial / Credibility Review
- Tìm điểm người ngoài có thể hiểu sai, phản biện hoặc cho là thiếu nhất quán.
- Review claims, navigation, wording, architecture explanation.
- Không thay đổi giá trị CFP+; chỉ nêu rủi ro và phương án giảm rủi ro.
- Output: credibility risks, adversarial questions, mitigation wording.

### 7. Meta AI • Information Architecture & Simplification
- Review cấu trúc thông tin và hành trình đọc từ Homepage → 10 Chương → HUB 69 → ID pages.
- Tìm nơi dư tầng, khó điều hướng hoặc khó hiểu.
- Đề xuất cấu trúc gọn, giữ đúng link gốc và Canonical ID.
- Output: navigation map, simplification candidates, misplaced content list.

### 8. Notion AI • Source of Truth & Status Matrix
- Duy trì bảng Route / ID / Parent / Status / Source / Evidence / Review State.
- Đối chiếu nội dung nào là CURRENT, LOCKED, REVIEW CANDIDATE, DRAFT.
- Phát hiện thiếu link, sai parent, collision, duplicate record.
- Output: SoT matrix + missing/conflict queue.

## Thứ tự ưu tiên chung

P0-1: Website public mở được và đúng nội dung.
P0-2: HUB 69 Core Reading Pack và AI Directory.
P0-3: 10 Chương và liên kết Canonical.
P0-4: Evidence, broken links, duplicate/conflict cleanup.
P0-5: Chuẩn bị mở rộng global AI onboarding.

## Quy tắc hoàn tất

Không tính COMPLETE nếu chưa có evidence. Một hạng mục chỉ PASS khi:

URL/Artifact mở được → nội dung đúng → link đúng → không Canonical conflict → có evidence.

## CMP/Human Governance escalation

Chỉ escalate khi có:
- ID collision
- wrong parent
- ambiguity ảnh hưởng Canonical
- governance conflict
- quyết định vượt quyền read/propose

Các vấn đề wording, formatting, broken links và evidence gap phải được AI xử lý trước khi chuyển Human Governance.
