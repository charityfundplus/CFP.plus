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

from services.forum.registry import CHAPTERS, GROUPS

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


ALL_IN_ONE_STATUSES = {
    "active": "Đã hoạt động", "testing": "Đang thử nghiệm",
    "research": "Đang nghiên cứu", "incomplete": "Chưa hoàn thành",
}


def all_in_one(catalog, office_on: bool = True) -> dict:
    """Điều hướng P0 từ nguồn hiện hữu; không cấp ID hay nâng trạng thái nghiệp vụ.

    ``active`` chỉ xác nhận trang nội dung có trong snapshot phục vụ sandbox. Các
    chức năng cần đăng nhập vẫn giữ kiểm quyền ở API đích; API này chỉ chứa link.
    331/332/333 do Founder nêu trong lệnh P0: thiếu trang thì giữ nguyên ID và
    không suy ra URL hoặc thay bằng 31/32/33 trong dữ liệu cũ.
    """
    def pending(label, note, status="incomplete", cid=None):
        return {"label": label, "url": None, "sandbox_url": None, "canonical_id": cid,
                "source": "Founder P0 2026-11-08", "version": None,
                "parent_status": "pending_verification", "status": status, "note": note}

    def page(cid, note="", label=None):
        item = catalog.items.get(cid)
        if not item:
            return pending(label or cid, note or "Chưa có trang trong nguồn hiện hữu; chờ đối chiếu.", cid=cid)
        return {"label": label or item["title"], "url": item["canonical_url"],
                "sandbox_url": item["sandbox_url"], "canonical_id": item["canonical_id"],
                "source": item["source"], "version": item["version"],
                "parent_status": item["parent_status"], "status": "active",
                "note": note or "Trang nội dung hiện hữu; chức năng và Evidence theo phạm vi ghi trong trang."}

    def technical(label, path, note):
        if not office_on and path.startswith(("/_internal/office/", "/_internal/ops/", "/_internal/van-phong-sieu-bo-doi/")):
            return pending(label, "Văn Phòng chưa được cấu hình trong runtime này.")
        return {"label": label, "url": None, "sandbox_url": path, "canonical_id": None,
                "source": "repo:services/forum/app.py", "version": None,
                "parent_status": "not_applicable", "status": "testing", "note": note}

    def category(number, key, title, status, note, links):
        return {"number": number, "key": key, "title": title, "status": status,
                "label": ALL_IN_ONE_STATUSES[status], "note": note, "links": links}

    categories = [
        category(1, "products", "Website • App • Sàn TMTC • Diễn Đàn • Văn Phòng Siêu Bộ Đôi", "testing",
                 "Dùng chung HUB và backend hiện hữu. App và chức năng giao dịch TMTC chưa hoàn thành.", [
                     technical("Website CFP+ trong sandbox", "/", "Điều hướng các trang nguồn hiện hữu."),
                     pending("App CFP+", "Chưa có App hoạt động; giao diện web trên điện thoại đang thử nghiệm."),
                     page("8682", "Trang giới thiệu TMTC; chức năng giao dịch/kết nối cung cầu chưa hoàn thành."),
                     technical("Diễn Đàn Siêu Bộ Đôi", "/_internal/forum/sieu-bo-doi/", "Đọc công khai; đăng bài cần tài khoản sandbox."),
                     technical("Diễn Đàn SI AI • HSTDN", "/_internal/forum/si-ai-hstdn/", "Nội dung và quyền thành viên theo API diễn đàn."),
                     technical("Văn Phòng Siêu Bộ Đôi", "/_internal/van-phong-sieu-bo-doi/", "Danh sách và điều hướng sandbox; kết nối SI AI bên ngoài cần Evidence riêng."),
                 ]),
        category(2, "structure", "5 Nhóm • 10 Chương • Hệ thống ID số", "active",
                 "Điều hướng theo trang và Registry hiện hữu. Nhãn Nhóm DV/Nhóm 0 còn chờ Human Governance đối chiếu.",
                 [page("0123456789"), page("000")] + [page(cid) for cid in CHAPTERS] + [page("4376")]),
        category(3, "funds", "Ba Quỹ CFP+ • 331 • 332 • 333", "incomplete",
                 "331, 332, 333 giữ đúng lệnh Founder. Chưa có trang cho ba ID này trong snapshot; không thay bằng 31, 32, 33.",
                 [page(cid, "ID do Founder chỉ định; chưa có trang nguồn trong snapshot.", "Quỹ CFP+ " + cid)
                  for cid in ("331", "332", "333")] + [page("3", "Trang Chương 3 hiện hữu; chưa xác nhận mapping mới 331/332/333.")]),
        category(4, "ctttc", "CTTTC • 366 Ngày • 28882", "testing",
                 "Trang giới thiệu và API lịch 366 vị trí đã có; tri thức theo từng ngày chưa hoàn thành.", [
                     page("28882"),
                     technical("Lịch CTTTC 366 vị trí", "/api/ecosystem/ctttc/days", "API lịch sandbox; 29/02 chỉ hợp lệ trong năm nhuận."),
                 ]),
        category(5, "education", "Giáo dục • Đào tạo • Giáo trình • Khóa học miễn phí", "research",
                 "Nguồn hiện hữu nêu định hướng giáo dục; chưa có giáo trình hoặc khóa học miễn phí được nghiệm thu trong snapshot.", [
                     page("2", "Chương Con Người có định hướng Giáo Dục Và Phát Triển."),
                     page("28882", "Định hướng tri thức và học tập; chưa phải một khóa học hoàn chỉnh."),
                     pending("Giáo trình và khóa học miễn phí", "Chưa có trang/ID và nội dung khóa học đã xác minh."),
                 ]),
        category(6, "research", "Chương trình • Đã nghiên cứu • Đang nghiên cứu • Định hướng tương lai", "research",
                 "Tra cứu nguồn hiện hữu; chương trình chỉ được ghi hoàn tất khi có Output, Evidence và Review đúng phạm vi.", [
                     page("28882", "CTTTC kết nối Quá Khứ • Hiện Tại • Tương Lai."),
                     technical("Danh mục công trình và tri thức", "/_internal/catalog/", "Tra cứu trang nguồn; không suy rộng listing thành chương trình đã hoàn tất."),
                     pending("Hồ sơ chương trình đã nghiên cứu", "Chưa có danh mục nghiệm thu riêng trong snapshot."),
                     pending("Chương trình đang nghiên cứu và tương lai", "Chưa có hồ sơ chương trình được xác minh riêng.", "research"),
                 ]),
        category(7, "technology", "SI AI • Robot • Siêu Phần Mềm • Công nghệ • Hàng không • Vũ trụ", "testing",
                 "Danh bạ và Văn Phòng sandbox có sẵn. Robot, hàng không và vũ trụ chưa có trang chuyên biệt được xác minh trong snapshot.", [
                     page("6"),
                     technical("Danh bạ SI AI và Văn Phòng", "/_internal/office/", "CFP+ ID khác ID chính thức của nhà cung cấp; trạng thái HOLD giữ nguyên."),
                     technical("Siêu Bộ Đôi • Siêu Phần Mềm", "/_internal/van-phong-sieu-bo-doi/", "Chức năng sandbox; không tự xác nhận adapter của nền tảng bên ngoài đã kết nối."),
                     pending("Robot • Hàng không • Vũ trụ", "Chờ hồ sơ nguồn chuyên biệt; không tự tạo ID hay link.", "research"),
                 ]),
        category(8, "ecosystems", "HSTDN • Quỹ • Ngân hàng • Sàn tài sản số • Tổ chức • Quốc gia", "research",
                 "Có các Chương và diễn đàn HSTDN; từng tổ chức, quốc gia và nghiệp vụ cần nguồn/Evidence riêng.", [
                     page("7"), page("8"), page("9"),
                     technical("Diễn Đàn SI AI • HSTDN", "/_internal/forum/si-ai-hstdn/", "Nghiên cứu doanh nghiệp theo quyền thành viên sandbox."),
                     pending("Ngân hàng • Sàn giao dịch tài sản số", "Chưa có danh mục chuyên biệt được xác minh trong snapshot.", "research"),
                 ]),
        category(9, "communities", "Tôn giáo • Cộng đồng • Nhà khoa học • Nhà hiền triết", "research",
                 "Điều hướng các Chương hiện hữu. Hồ sơ cá nhân và hoạt động cụ thể cần được kiểm chứng riêng.", [
                     page("4"), page("5"), page("2"),
                     pending("Nhà khoa học • Nhà hiền triết", "Chưa có hồ sơ chuyên biệt được xác minh trong snapshot.", "research"),
                 ]),
        category(10, "participation", "Lời mời Con Người toàn cầu • Tìm hiểu • Tham gia • Đóng góp • Đồng hành", "testing",
                 "Tìm hiểu CFP+ và tham gia thảo luận qua các lối hiện hữu; luồng đề xuất đóng góp → review → giao việc chưa hoàn thành.", [
                     page("000", "Giới thiệu CFP+ và định hướng phục vụ Con Người toàn cầu."),
                     page("5", "Định hướng kết nối cộng đồng và đóng góp."),
                     technical("Tham gia Diễn Đàn Siêu Bộ Đôi", "/_internal/forum/sieu-bo-doi/", "Đăng ký/đăng nhập tài khoản sandbox để thảo luận; không tự cấp vai trò governance."),
                     pending("Đề xuất đóng góp → Review → Nhiệm vụ", "Chưa có luồng đề xuất và duyệt hoàn chỉnh."),
                 ]),
    ]
    return {
        "hub": {"id": "69", "canonical_url": catalog.items.get("69", {}).get("canonical_url"),
                "sandbox_url": catalog.items.get("69", {}).get("sandbox_url")},
        "categories": categories, "statuses": dict(ALL_IN_ONE_STATUSES),
        "groups": [dict(g, chapters=list(g["chapters"])) for g in GROUPS],
        "chapters": [{"id": cid, "name": name} for cid, name in CHAPTERS.items()],
        "scope": "Đã hoạt động chỉ áp dụng cho trang nội dung và điều hướng trong snapshot sandbox; không xác nhận nghiệp vụ, tích hợp bên ngoài hay production.",
        "governance": "SANDBOX PRACTICE GO • HOLD ACTIVATION • PRODUCTION NO GO",
    }


def ecosystem_map(catalog, office_on: bool = True) -> dict:
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
            "counts": {s: sum(1 for i in items if i["function"]["status"] == s) for s in ("sandbox", "partial", "planned")},
            "all_in_one": all_in_one(catalog, office_on=office_on)}


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
