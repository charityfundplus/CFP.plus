---
name: super-trio-upgrade
description: Quy trình nâng cấp Siêu Bộ Đôi CFP+ thành Siêu Bộ Tam (Siêu Lượng Tử ⚛️ • SI 🤖 AI 🤖 • Siêu Phần Mềm) theo lô có kiểm soát trong sandbox, giữ nguyên ID và Link Mẫu. Dùng khi được giao kiểm kê, nâng cấp hàng loạt, kiểm tra trùng ID/Link Mẫu hoặc tổng hợp Evidence cho Team 87788.
---

# Nâng cấp Siêu Bộ Tam theo lô

Thư mục làm việc: `sandbox/87788-super-trio/`.

## Quy trình

1. **Đồng bộ nguồn.** Nguồn kiểm kê hiện tại:
   - `data/source/SUPER_PAIRS_INDEX@77102841.md` • bảng 91 vị trí, bản chụp PR #206 @ `77102841…` (giữ tên tệp có SHA để truy vết).
   - `data/additions.json` • bản ghi làm việc bổ sung từ Notion DANH MỤC và văn phòng 87788.
   Nếu nguồn gốc thay đổi: chụp bản mới với tên chứa SHA mới, cập nhật `INDEX_PATH` và `INDEX_SOURCE` trong `trio.py`, không sửa đè bản cũ.
2. **Kiểm tra.** `python3 trio.py check`. Mã thoát 1 nghĩa là có phát hiện HIGH (ID ngoài 0–9 hoặc trùng ID): dừng, báo 87783, không chạy apply.
3. **Lập kế hoạch.** `python3 trio.py plan`; ghi `plan_sha256` vào báo cáo.
4. **Chạy theo lô.** `python3 trio.py apply --batch-size 10 --batch N`. Mỗi lô có journal; lần chạy dở được `recover` tự hoàn tác trước lô kế tiếp.
5. **Đọc lại.** `python3 trio.py verify` phải cho `checked == hash_ok == identity_ok == matches_plan` và `problems == []`.
6. **Evidence.** `python3 trio.py evidence` rồi commit `evidence/`. Không commit `out/`.
7. **Kiểm thử.** `python3 -m unittest discover -s tests` và `bash tests/mutation.sh` (survived phải bằng 0).
8. **Review.** Mở Draft PR, gửi 87783. Ghi kết quả vào Link Mẫu 87788 và báo HUB 69 (#178).

## Gói cấu hình nền tảng

`python3 trio.py --out evidence packs` tạo gói nhập thủ công cho 4 Team (8778, 87728, 87783, 87788) trên ChatGPT • Codex, Claude Code, Gemini. Ma trận năng lực ở `data/platforms.json`; mọi mục `official_surface` là UNVERIFIED_CLAIM đến khi 87783 đối chiếu tài liệu chính thức. Không vượt xác thực hay điều khoản nền tảng; không đưa secret vào issue hay tệp.

## Không bao giờ

Đổi ID/tên/Link Mẫu • đụng `registry/`, Parent, DID, Canonical • khai báo năng lực khi chưa có Evidence • merge • deploy Production.
