# 87788 • Team Super Trio Upgrade • Sandbox

Bộ công cụ nâng cấp Siêu Bộ Đôi → Siêu Bộ Tam (1. Siêu Lượng Tử ⚛️ • 2. SI 🤖 AI 🤖 • 3. Siêu Phần Mềm) dưới dạng **lớp phủ**: giữ nguyên ID, tên, Link Mẫu, Chương, Nhóm; không sửa hồ sơ nguồn, Registry, Parent, DID, Canonical.

**SANDBOX • REVIEW CANDIDATE • HOLD ACTIVATION • PRODUCTION NO-GO**

| Thành phần yêu cầu | Ở đâu |
| --- | --- |
| Bộ rà soát Registry / kiểm kê | `trio.py check` (đọc bảng 91 vị trí + `data/additions.json`) |
| Kiểm tra trùng ID và Link Mẫu | `check_inventory`: ID_DUPLICATE (khớp chuỗi chính xác), LINK_SHARED |
| Hệ thống 0–9, 5 Nhóm 🔟 Chương | ID_OUTSIDE_0_9, CHAPTER_MISMATCH, GROUP_MISMATCH, `chapters_covered` |
| Kiểm tra quyền hạn và danh tính | `guard_overlay`, `_safe_out` (trường cấm, đổi danh tính, ID mới, năng lực chưa có Evidence, ghi ngoài sandbox, `CFP_PRODUCTION`) |
| Nâng cấp hàng loạt có kiểm soát | `plan` (dry-run, `plan_sha256`) → `apply --batch-size --batch` |
| Khôi phục khi lỗi | journal + backup, `recover`, `rollback RUN_ID`, ghi nguyên tử, idempotent |
| Đồng bộ đa nền tảng / API • MCP | `data/platforms.json` (ma trận năng lực, UNVERIFIED_CLAIM) + `packs` (gói nhập thủ công) |
| Tổng hợp Evidence | `evidence` → `evidence/REPORT.md`, `evidence/evidence.json` |
| Kiểm thử tự động | `tests/test_trio.py` (21 test) + `tests/mutation.sh` (12 đột biến) + CI |

```bash
python3 trio.py check && python3 trio.py apply --all && python3 trio.py verify && python3 trio.py evidence
python3 -m unittest discover -s tests -v && bash tests/mutation.sh
```

Chỉ dùng thư viện chuẩn Python 3.10+. `out/` không commit (tái tạo xác định từ nguồn).
