"""Sinh search-index.json cho ô tìm kiếm ID trên website tĩnh (chạy được trên cfp.plus không cần backend).

Nguồn: chỉ các trang ID số đã xuất bản trong repo (Catalog của Link Mẫu) + trạng thái Parent/HOLD từ Registry và
registry/review-holding. Không cấp ID, không thêm trang. --check: CI báo lỗi nếu chỉ mục lệch với nguồn.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from services.forum.catalog import Catalog  # noqa: E402
from services.forum.registry import Registry  # noqa: E402

LABEL = {"hold_conflict": "HOLD", "parent_hold": "Parent đang HOLD", "registry": "Parent theo Registry",
         "inferred_prefix": "Parent chưa xác minh", "pending_verification": "Parent chưa xác minh"}


def build() -> str:
    cat = Catalog(Registry(), ROOT)
    items = [{"id": i["canonical_id"], "t": i["title"], "d": i["description"][:160], "s": LABEL[i["parent_status"]]}
             for i in sorted(cat.items.values(), key=lambda x: (len(x["canonical_id"]), x["canonical_id"]))]
    return json.dumps({"note": "Chỉ trang ID đã xuất bản; sinh bởi scripts/build_search_index.py", "items": items},
                      ensure_ascii=False, separators=(",", ":")) + "\n"


if __name__ == "__main__":
    out, f = build(), ROOT / "search-index.json"
    if "--check" in sys.argv:
        if not f.is_file() or f.read_text("utf-8") != out:
            sys.exit("search-index.json lệch với các trang ID đã xuất bản — chạy: python3 scripts/build_search_index.py")
        print("search-index.json khớp nguồn")
    else:
        f.write_text(out, "utf-8")
        print(f"đã ghi {f.name}: {len(json.loads(out)['items'])} ID")
