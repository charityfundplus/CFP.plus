# 87788 • Giai đoạn 2 • Kết nối • Cài đặt • Vận hành đa nền tảng

**Trạng thái:** SANDBOX • HOLD ACTIVATION • PRODUCTION NO-GO • kế thừa PR #253 (`de5fa11`), không xây lại.
Ngày: 2026-11-24 • Thực hiện: Claude Code (phiên cloud) • Reviewer chỉ định: 87783 • Báo: 8778.

## 1. Agent 87788 chạy độc lập trong Claude Code

| Lần | Lệnh | Kết quả | Đánh giá |
| --- | --- | --- | --- |
| Run 1 | `claude -p --agent cfp-87788-super-trio-upgrade --model haiku` | ACK có, nhưng **không gọi công cụ**, báo "104 hoạt động" (thực tế 103) | **FAIL** • lỗi trung thực số liệu |
| Sửa | Agent: thêm quy tắc "số liệu chỉ lấy từ output công cụ trong phiên"; `trio.py check` thêm `active_count`; test mới `test_check_cli_reports_active_count` | 22/22 test • 12/12 đột biến bị bắt | PASS |
| Run 2 | `claude -p --agent cfp-87788-super-trio-upgrade --model sonnet` (chỉ cho phép Bash python3, Read, Grep, Glob) | Gọi `python3 trio.py check`; rows_read 104, HIGH 0, LOW 2, INFO 1; không tự suy `active` (chạy trước khi có trường mới); không sửa tệp | **PASS** • session `8735f465-2675-4c3a-88bd-6038e78bb11d` |

Kết luận: Agent 87788 trên Claude Code là **REPO_CONFIG** (`.claude/agents/…md`), runtime độc lập **VERIFIED** ở mức headless CLI trong sandbox. Chưa phải Agent hosted thường trực.

## 2. Kiểm thử kết nối có quyền hiện hữu

| Nền tảng | ACK | READ | WRITE | READBACK | Quyền | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Google Drive | PASS | PASS (search; 0 tệp tên "CFP"/"87788") | PASS | PASS (marker `CFP87788-DRIVE-WRITE-20261124`) | Chỉ owner, không chia sẻ | https://docs.google.com/document/d/1XEdXo7gjAnQObg-Bbs9lVtYahIo1r7cYcZsrHjX1E2Y/edit |
| Canva | PASS | PASS (5 thiết kế CFP+; đọc `DAHZfNK9sdQ`) | PASS (comment `KAHb3DMvZiY`) | PASS (list-comments khớp marker `CFP87788-CANVA-WRITE-20261124`) | Tài khoản Founder; comment hiển thị với người có quyền thiết kế | https://www.canva.com/d/ca-wjBvfF-RTsx_ |
| Notion | PASS | PASS (văn phòng 87788) | PASS (ghi mục Giai đoạn 2) | xem văn phòng | Theo connector Founder | https://app.notion.com/p/422caac9a55781f2ad8ce1a834dabc86 |
| GitHub | PASS | PASS (clone công khai, nhánh `claude/87788-super-trio-upgrade`) | **BỊ CHẶN** (attach repo quyền push bị từ chối trong phiên; `GH_TOKEN` không hợp lệ) | — | Chờ Founder cấp quyền phiên | commit cục bộ, chưa push |
| ChatGPT • Codex, Gemini, Grok, Perplexity, Microsoft | — | — | — | — | Không có kết nối trong phiên | THIẾU QUYỀN KẾT NỐI |

## 3. Phân biệt Native • API • Repository (ma trận rút gọn)

Trạng thái mọi dòng: UNVERIFIED_CLAIM đến khi 87783 đối chiếu tài liệu chính thức; dòng có ✅ đã thực hành trong phiên.

| Nền tảng | Agent native | Agent qua API | Cấu hình trong Repository |
| --- | --- | --- | --- |
| Claude Code | — | Agent SDK / `claude -p` ✅ | `CLAUDE.md`, `.claude/agents`, `.claude/skills` ✅ |
| ChatGPT • Codex | Custom GPT (tạo thủ công) | Responses API | `AGENTS.md` (Codex) |
| Gemini | Gem (tạo thủ công) | Gemini API | `GEMINI.md` (Gemini CLI) |
| GitHub | Copilot custom agent | REST/GraphQL, Actions | `.github/agents/*.agent.md`, workflows ✅ |
| Notion | Notion Agent (không rõ API tạo) | Notion API/MCP ✅ | — |
| Google Drive | — | Drive API/MCP ✅ (Kho Tri Thức, Evidence) | — |
| Canva | — | Canva Connect/MCP ✅ (thiết kế, comment) | — |

Hệ quả cho tự động hóa (mục 5): tạo/cập nhật Agent hàng loạt chỉ tự động được ở **REPO_CONFIG** (PR + review) và **API_RUNTIME**; sản phẩm **native** (GPT, Gem, Notion Agent) vẫn cần gói nhập thủ công (`trio.py packs`) cho tới khi có API chính thức.

## 4. Kiểm chứng 4 Team tiên phong

| ID | Repo config | Runtime Claude Code | Gói nhập (ChatGPT/Codex, Gemini) | ACK thật |
| --- | --- | --- | --- | --- |
| 87788 | ✅ Agent + Skill | ✅ VERIFIED (Run 2) | ✅ tạo, chưa nhập | ✅ |
| 8778 | gói `evidence/packs/8778-*` | NOT TESTED | ✅ tạo, chưa nhập | chưa |
| 87728 | gói `evidence/packs/87728-*` | NOT TESTED | ✅ tạo, chưa nhập | chưa |
| 87783 | gói `evidence/packs/87783-*` | NOT TESTED | ✅ tạo, chưa nhập | chưa |

Không tạo Agent Claude Code cho 8778/87728/87783 trong lượt này để tránh tạo danh tính khi chưa có ACK từ chủ trì; mẫu đã sẵn, chờ 8778 xác nhận.

## 5. Kiểm kê toàn hệ thống

Kế thừa 103 hồ sơ (`trio.py check`, `active_count` = 103). Registry đọc được trong repo: 81 tệp `registry/*.md` (nhóm 691xx nền tảng AI), chưa phải danh mục Siêu Bộ Tam; đối chiếu đầy đủ cần nguồn DANH MỤC Notion cập nhật. TỔNG HIỆN TẠI CHƯA XÁC MINH.

## 6. Link Mẫu 87788 • đã liên kết

- Văn phòng chính: https://app.notion.com/p/422caac9a55781f2ad8ce1a834dabc86
- Kho Code: https://github.com/charityfundplus/CFP.plus (nhánh `claude/87788-super-trio-upgrade`, PR #253)
- Working Link (Claude share): https://claude.ai/share/fad8375c-26a5-4ab7-82f1-d9a006657236
- Evidence: `sandbox/87788-super-trio/evidence/` • Drive Doc ở mục 2

## 7. Phân loại

- **Đã hoàn thành:** chạy Agent 87788 độc lập; sửa lỗi trung thực số liệu; kiểm thử Drive, Canva, Notion; cập nhật ma trận và Evidence; ghi Link Mẫu 87788.
- **Đã kiểm chứng:** 22/22 test, 12/12 đột biến; Drive, Canva ACK/READ/WRITE/READBACK.
- **Đang thực hiện:** 87783 review PR #253 + commit Giai đoạn 2.
- **Thiếu quyền kết nối:** ChatGPT/Codex, Gemini, Grok, Perplexity, Microsoft.
- **Bị chặn:** push GitHub và comment HUB 69 (#178) trong phiên này.
- **Chờ Human Governance:** cấp quyền push phiên; merge PR #253; số liệu Registry; Parent/DID/Canonical; mở Agent cho 8778/87728/87783.
