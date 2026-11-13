"""Kiểm tra liên kết nội bộ của website tĩnh (các trang ID số đã xuất bản + trang chủ) — chỉ đọc repo.

In ra JSON: số trang, số link nội bộ, và danh sách đích KHÔNG có trang trong repo (kèm trang nguồn).
Dùng trong CI (--fail-on-broken) và trong workflow HTTPS để đối chiếu với cfp.plus thật.
Không cấp ID: một đích "broken" phải được sửa thành văn bản không-link (chờ Registry), không tạo trang mới.
"""
import argparse
import collections
import html
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
HREF = re.compile(r'''(?:href|src)\s*=\s*["']([^"'#?]+)''', re.I)


def audit(root: pathlib.Path = ROOT) -> dict:
    pages = sorted([p for p in root.glob("*/index.html") if re.fullmatch(r"[0-9]+", p.parent.name)]) + [root / "index.html"]
    broken, total = collections.defaultdict(set), 0
    for p in pages:
        for raw in HREF.findall(p.read_text("utf-8", "replace")):
            u = html.unescape(raw.strip())
            if not u or u.startswith(("mailto:", "tel:", "javascript:", "data:")):
                continue
            if re.match(r"https?://", u):
                m = re.match(r"https?://(?:www\.)?cfp\.plus(/\S*)?$", u)
                if not m:
                    continue
                u = m.group(1) or "/"
            total += 1
            t = (root / u.lstrip("/")) if u.startswith("/") else (p.parent / u)
            if not (t.is_file() or (t / "index.html").is_file()):
                broken[u].add("/" if p.parent == root else f"/{p.parent.name}/")
    return {"pages": len(pages), "internal_links": total, "broken": {k: sorted(v) for k, v in sorted(broken.items())}}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fail-on-broken", action="store_true")
    a = ap.parse_args()
    r = audit()
    print(json.dumps(r, ensure_ascii=False, indent=1))
    sys.exit(1 if a.fail_on_broken and r["broken"] else 0)
