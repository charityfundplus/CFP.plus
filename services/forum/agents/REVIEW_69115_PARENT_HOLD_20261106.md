# Rà soát 69115 (Meta ↔ Microsoft AI) và ID con chịu PARENT HOLD • 06/11/2026

**Loại:** báo cáo đối chiếu, CHỈ ĐỌC. Không cấp, đổi, xoá hay gỡ HOLD bất kỳ ID nào. Quyết định thuộc Human Governance / Người sáng lập.
**Người lập:** Claude Code (trung tâm kỹ thuật) • nhánh `claude/gallant-carson-8uogxj` • PR #195.

## 1. Hai cách phân bổ 69110–69119 cùng tồn tại trong repo

| ID | Phương án A — `registry/ai-entity-registry.json` + trang cfp.plus đã xuất bản | Phương án B — `HUB69.md` • `CMP.md` • `registry/GLOBAL_AI_ID_BASELINE_CANDIDATE.md` |
|---|---|---|
| 69110 | (trang: CFP+ AI • Global AI Coordinator) | OpenAI → 691100 ChatGPT |
| 69111 | Amazon AI / AWS | Anthropic → 691110 Claude |
| 69112 | Anthropic → 691121 Claude | xAI → 691120 Grok |
| 69113 | Apple | Google DeepMind → 691130 Gemini, 691131 NotebookLM |
| 69114 | Google DeepMind (trang: Google AI Ecosystem) | Meta AI → 691140 |
| **69115** | **Meta AI** → 691151 Meta AI Assistant | **Microsoft AI** → 691150 Microsoft Copilot |
| 69116 | Microsoft AI → 691161 Copilot | Perplexity → 691160 |
| 69117 | NVIDIA AI | Groq → 691170 |
| 69118 | OpenAI → 691181 ChatGPT, 691182–691186 | CoreWeave |
| 69119 | xAI → 691191 Grok | Apple |

## 2. Bằng chứng theo từng nguồn

- `registry/AI_CANONICAL_ID_REGISTRY.md` (mục "Nguồn dữ liệu hiện hành"): binding Developer + AI = `registry/ai-entity-registry.json`; "Các bảng mapping cũ trong lịch sử GitHub chỉ giữ giá trị audit/review; không dùng để tự cấp, đổi…". → hướng về **Phương án A**.
- `registry/ai-entity-registry.json`: 69115 = "Meta AI", status **"REVIEW CANDIDATE • WORKING ALLOCATION"** (chưa phải phê duyệt).
- Blob trước khi làm rỗng `registry/69115.md` (`0dc15cd89ec9129f23bf61796b24d14d3ad5a877`): "69115 • Meta", ghi "Lifecycle Status: Canonical Locked • 2026-08-07" và quy tắc "x1–x9 = major developers ordered alphabetically by official English name". Thứ tự chữ cái (Amazon, Anthropic, Apple, Google, **Meta**, Microsoft, NVIDIA, OpenAI, xAI) khớp Phương án A. Lưu ý: tiêu chuẩn hiện hành cấm tự ghi "Canonical Locked" → nhãn này cần Human Governance xác nhận.
- Blob trước khi làm rỗng `registry/691150.md` (`8469bb97de868d7679223985180b696e68276b57`): Microsoft Copilot, Parent 69115 → thuộc Phương án B.
- `registry/review-holding/US_SYSTEMIC_CONFLICT_69110_69119_20260824.md` (24/08/2026): cả 69110–69119 và 9 ID con x0 ở trạng thái **HOLD • CHỜ QUYẾT ĐỊNH**. Chưa có hồ sơ nào trong repo ghi nhận việc gỡ HOLD.
- `registry/6911513.md` (GitHub Support) còn nội dung, ghi "Parent Entity: 69115 • Microsoft AI" → theo Phương án A thì Parent này trỏ nhầm sang Meta.
- Lịch sử git trên nhánh là shallow; thay đổi gần nhất của `HUB69.md`, `CMP.md`, `ai-entity-registry.json` và `69115/index.html` là commit `de4d9f0` (17/09/2026). Không tìm thấy commit/hồ sơ quyết định gỡ xung đột sau 24/08/2026.

**Kết luận kỹ thuật (không phải quyết định):** nguồn "hiện hành" theo tiêu chuẩn và các trang đã xuất bản thống nhất với Phương án A (69115 = Meta). `HUB69.md`/`CMP.md` còn bảng Phương án B nên gây nhầm cho người/AI đọc. Cho đến khi Human Governance quyết định, Link Mẫu (sandbox) hiển thị 69110–69119 là `hold_conflict` và ID con là `parent_hold`.

## 3. ID con chịu PARENT HOLD (từ Registry + hồ sơ registry/*.md)

| ID | Trạng thái | Parent | Tên trong Registry | Tiêu đề trang cfp.plus | Ghi chú |
|---|---|---|---|---|---|
| 691121 | PARENT HOLD | 69112 | Claude | 691121 • Claude • CFP+ |  |
| 691141 | PARENT HOLD | 69114 | Gemini | 691141 • Google Cloud AI • CFP+ | ⚠️ tên Registry ≠ trang |
| 691151 | PARENT HOLD | 69115 | Meta AI Assistant | 691151 • Meta AI • CFP+ |  |
| 691161 | PARENT HOLD | 69116 | Microsoft Copilot | 691161 • Microsoft Copilot • CFP+ |  |
| 691181 | PARENT HOLD | 69118 | ChatGPT | 691181 • ChatGPT • CFP+ |  |
| 691182 | PARENT HOLD | 69118 | 691182 • GPT 6 Family | — (chưa có trang) | nguồn registry/691182.md |
| 691183 | PARENT HOLD | 69118 | 691183 • Codex | — (chưa có trang) | nguồn registry/691183.md |
| 691184 | PARENT HOLD | 69118 | 691184 • GPT Live | — (chưa có trang) | nguồn registry/691184.md |
| 691185 | PARENT HOLD | 69118 | 691185 • GPT Image Family | — (chưa có trang) | nguồn registry/691185.md |
| 691186 | PARENT HOLD | 69118 | 691186 • Daybreak | — (chưa có trang) | nguồn registry/691186.md |
| 691191 | PARENT HOLD | 69119 | Grok | 691191 • Grok • CFP+ |  |
| 6911513 | PARENT HOLD | 69115 | GitHub Support (`registry/6911513.md`, ghi Parent "Microsoft AI") | — (chưa có trang) | ⚠️ không có trong ai-entity-registry.json; Parent ghi Microsoft nhưng 69115 = Meta theo Phương án A |

Tổng: 12 ID con chịu PARENT HOLD • 19 ID nằm trong hồ sơ HOLD (69110–69119, 691100, 691110, 691120, 691130, 691131, 691140, 691150, 691160, 691170).

Trang đã xuất bản dưới tiền tố bị HOLD nhưng KHÔNG có trong Registry (Link Mẫu ghi `pending_verification`): 691109 Perplexity AI, Inc. • 691142 Google DeepMind • 6911421 Gemini • 691143 Google Labs • 691144 Google Research.

## 4. Quyết định cần Người sáng lập / Human Governance

1. Chọn phương án chuẩn cho 69110–69119 (A hay B) và gỡ HOLD — hoặc giữ HOLD.
2. Cập nhật `HUB69.md` / `CMP.md` / `GLOBAL_AI_ID_BASELINE_CANDIDATE.md` theo phương án đã chọn (bảng cũ hiện mâu thuẫn).
3. Xác định Parent của 6911513 GitHub Support (Microsoft = 69116 theo A).
4. Đối chiếu tên 691141 (Registry "Gemini" ↔ trang "Google Cloud AI") và vị trí 6911421 Gemini.
5. Sau khi 69115 ổn định: có cấp ID riêng cho Meta Business Agent dưới 69115 hay không (Claude không tự cấp).
