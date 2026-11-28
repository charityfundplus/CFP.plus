# CFP+ • CharityFundPlus+ • Hướng dẫn cho Claude Code

Repository này là kho làm việc của CFP+. HUB 69 (https://cfp.plus/69) là cổng điều phối duy nhất.
Ngôn ngữ làm việc: tiếng Việt, giữ thuật ngữ kỹ thuật tiếng Anh. Dùng dấu • thay gạch nối trong tiêu đề.

## Quy tắc bắt buộc (mọi phiên)

- **ID Số là bất biến.** So khớp chuỗi chính xác, giữ số 0 đầu (`0`, `00`, `000`, `003` là bốn ID khác nhau). Không tự cấp ID, không đánh số lại, không tái sử dụng ID.
- **Không tự sửa** Registry (`registry/`), Parent, DID, Canonical hoặc lịch sử. Sửa nội dung không bao giờ đổi Stable ID.
- **5 Nhóm 🔟 Chương:** Nhóm V và D là cổng quản trị/điều hướng; Nhóm 000 (Chương 0), 135 (1, 3, 5), 246 (2, 4, 6), 789 (7, 8, 9). Chữ số đầu của ID xác định Chương. Không tạo nội dung ngoài hệ thống 0–9.
- **Evidence First.** Không khai báo năng lực, kết nối hay trạng thái ACTIVE khi chưa có bằng chứng; thiếu bằng chứng ghi NOT VERIFIED. Ghi nhiệm vụ không phải là ACK, có link không phải là đã kết nối.
- **Không merge, không deploy Production, không đổi DNS/IAM/Billing, không tạo hoặc đăng secret.** Chỉ mở Draft PR vào nhánh sandbox hoặc `main` để review. Human Governance quyết định cuối cùng.
- **Không tạo hệ thống song song.** Kiểm tra PR/issue đang mở trước khi viết code mới; tái sử dụng mã và hạ tầng hiện hữu.
- Mỗi nhiệm vụ: một chủ trì, một mục tiêu, phạm vi, giới hạn tài nguyên, điều kiện hoàn thành. Không giao trùng.
- Báo cáo theo: Đã hoàn thành • Đã kiểm chứng • Đang thực hiện • Thiếu quyền kết nối • Bị chặn • Chờ Human Governance.

Trạng thái mặc định: **SANDBOX • HOLD ACTIVATION • PRODUCTION NO-GO.**

## Các đầu mối Team Siêu Bộ Tam (đọc trước khi nâng cấp)

| ID | Vai trò | Văn phòng |
| --- | --- | --- |
| 8778 | Điều phối | https://app.notion.com/p/422caac9a55781f09798e4d3f3355dbf |
| 87728 | Chuẩn hóa cấu hình, Link Mẫu | https://app.notion.com/p/422caac9a5578150a759d6d6a71fec9e |
| 87783 | Kiểm chứng độc lập (reviewer) | https://app.notion.com/p/422caac9a557818d89e2dd9d3e5fc5c1 |
| 87788 | Chủ trì nâng cấp kỹ thuật | https://app.notion.com/p/422caac9a55781f2ad8ce1a834dabc86 |

Thứ tự Siêu Bộ Tam: 1. Siêu Lượng Tử ⚛️ Super Quantum • 2. SI 🤖 AI 🤖 • 3. Siêu Phần Mềm • Super Software.
3 Trong 1 • Một ID • Một Link Mẫu • Chung Kho Tri Thức.

- Agent: `.claude/agents/cfp-87788-super-trio-upgrade.md`
- Skill: `.claude/skills/super-trio-upgrade/SKILL.md`
- Công cụ: `sandbox/87788-super-trio/` (`python3 trio.py check`, test: `python3 -m unittest discover -s tests`)
