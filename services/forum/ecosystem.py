"""Bản đồ hệ sinh thái CFP+ (issue #198 • P0.1) + lịch CTTTC 28882 (366 vị trí ngày).

Nguyên tắc trung thực — mỗi phân hệ có HAI lớp tách biệt:
  public_page : trang ID số đã xuất bản trên cfp.plus (tra trong Link Mẫu; không có → null). Trang giới thiệu
                ≠ chức năng đã chạy.
  function    : trạng thái chức năng THỰC TẾ trong sandbox — "sandbox" (chạy được, có test, CHƯA nghiệm thu),
                "partial" (một phần), "planned" (chưa có). Không có trạng thái "live/production" ở đây.
Không cấp ID; Date ID theo chuẩn YYYYMMDD đã công bố tại https://cfp.plus/28882/.
"""
from __future__ import annotations

import calendar
from datetime import date

# n, khóa, tên, ID trang công khai (đã có trong repo hay không do Link Mẫu xác định), chức năng sandbox, ghi chú
COMPONENTS = (
    (1, "hub69", "HUB 69 • điều hướng và điều phối", ["69"], "sandbox", "/_internal/office/",
     "Danh bạ Văn Phòng SI AI + bản đồ này; trang HUB 69 công khai là trang tĩnh."),
    (2, "website", "Website • 5 Nhóm • 10 Chương (0–9)", ["0123456789", "000", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
     "partial", "/", "Trang tĩnh trên cfp.plus; bản sandbox thêm lối vào chức năng. Thiết kế công khai: Canva DAHZcr4iJj4 (Muse)."),
    (3, "app", "App CFP+ (điện thoại)", [], "planned", None,
     "Chưa có app; giao diện sandbox một cột dùng được trên điện thoại (E2E iPhone 13)."),
    (4, "tmtc", "Sàn TMTC • nhu cầu • sản phẩm • dịch vụ", ["8682"], "planned", None,
     "Trang giới thiệu 8682 có sẵn; chức năng giao dịch/kết nối CHƯA xây dựng. Văn Phòng có hồ sơ doanh nghiệp (enterprises) trong sandbox."),
    (5, "ctttc", "CTTTC 28882 • 366 vị trí ngày", ["28882"], "sandbox", "/api/ecosystem/ctttc/days",
     "API lịch 366 vị trí; Date ID YYYYMMDD; 29/02 chỉ hợp lệ năm nhuận. Nội dung tri thức theo ngày: chưa có."),
    (6, "forums", "Các Diễn Đàn • Siêu Bộ Đôi • SI AI HSTDN", [], "sandbox", "/_internal/forum/sieu-bo-doi/",
     "Hai Diễn Đàn kho riêng, nối nhiệm vụ hai chiều. HSTDN: /_internal/forum/si-ai-hstdn/."),
    (7, "social", "Mạng xã hội tổng hợp", [], "planned", None, "Chưa xây dựng."),
    (8, "knowledge", "Cổng Tri Thức • bài viết • đề tài • dự án • giáo trình", [], "partial", "/_internal/catalog/",
     "Danh mục Link Mẫu (trang ID đã xuất bản) + chủ đề nghiên cứu/bài học trong Văn Phòng. Quy trình xuất bản bài viết: chưa có."),
    (9, "office", "Văn Phòng SI AI • nhiệm vụ • Evidence • Review", [], "sandbox", "/_internal/ops/",
     "Task → ACK → Evidence → Review độc lập → Closure → bài học → nhiệm vụ tiếp theo (CI + HTTPS user-only)."),
    (10, "linkmau", "Link Mẫu phổ thông", [], "sandbox", "/_internal/linkmau/69/",
     "Hồ sơ chung cho mọi ID đã xuất bản: ID • Parent • HOLD • vai trò • nhiệm vụ • Diễn Đàn • tri thức • Evidence • Review • lịch sử, theo quyền."),
)


def ecosystem_map(catalog) -> dict:
    items = []
    for n, key, name, ids, fn, path, note in COMPONENTS:
        pages = []
        for cid in ids:
            it = catalog.items.get(cid)
            pages.append({"id": cid, "url": it["canonical_url"], "title": it["title"], "parent_status": it["parent_status"]}
                         if it else {"id": cid, "url": None, "missing": True})
        items.append({"n": n, "key": key, "name": name, "public_pages": pages,
                      "function": {"status": fn, "sandbox_path": path}, "note": note,
                      "label": {"sandbox": "ĐANG THỬ NGHIỆM (sandbox)", "partial": "MỘT PHẦN",
                                "planned": "CHỜ HOÀN THIỆN"}[fn]})
    return {"components": items, "mode": "SANDBOX PRACTICE GO • PRODUCTION NO GO",
            "counts": {s: sum(1 for i in items if i["function"]["status"] == s) for s in ("sandbox", "partial", "planned")}}


def is_leap(y: int) -> bool:
    return calendar.isleap(y)


def ctttc_days(year: int | None = None) -> dict:
    """366 vị trí ngày (MMDD, năm nhuận tham chiếu 2024); valid_in_year cho năm hỏi."""
    days = []
    d = date(2024, 1, 1)
    for pos in range(1, 367):
        mmdd = d.strftime("%m%d")
        row = {"position": pos, "mmdd": mmdd, "label": d.strftime("%d/%m")}
        if year:
            row["valid_in_year"] = mmdd != "0229" or is_leap(year)
            row["date_id"] = f"{year:04d}{mmdd}" if row["valid_in_year"] else None
        days.append(row)
        d = date.fromordinal(d.toordinal() + 1)
    out = {"positions": 366, "days": days, "standard": "Date ID YYYYMMDD • https://cfp.plus/28882/"}
    if year:
        out |= {"year": year, "leap": is_leap(year), "valid_days": 366 if is_leap(year) else 365}
    return out


def ctttc_date(date_id: str) -> dict:
    """Kiểm tra Date ID YYYYMMDD (vd. 20260229 → không hợp lệ: 2026 không nhuận)."""
    if len(date_id) != 8 or not date_id.isdigit():
        raise ValueError("Date ID phải đúng 8 chữ số YYYYMMDD.")
    y, m, dd = int(date_id[:4]), int(date_id[4:6]), int(date_id[6:])
    try:
        d = date(y, m, dd)
    except ValueError:
        reason = (f"{y} không phải năm nhuận — 29/02 chỉ có trong năm nhuận." if (m, dd) == (2, 29)
                  else "Ngày không tồn tại trong lịch dương.")
        raise ValueError(reason) from None
    pos = (date(2024, m, dd) - date(2024, 1, 1)).days + 1
    return {"date_id": date_id, "valid": True, "position": pos, "mmdd": date_id[4:], "weekday": d.isoweekday(),
            "leap_year": is_leap(y), "page": "https://cfp.plus/28882/"}
