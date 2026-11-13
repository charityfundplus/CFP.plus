"""Website tĩnh (cfp.plus): ô tìm ID dùng chỉ mục sinh từ trang đã xuất bản; CSS dùng chung tồn tại; link audit chạy được."""
import json
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from services.forum.app import Stores, create_app

ROOT = Path(__file__).resolve().parents[2]


def test_search_index_matches_published_pages():
    r = subprocess.run([sys.executable, "scripts/build_search_index.py", "--check"], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    items = json.loads((ROOT / "search-index.json").read_text("utf-8"))["items"]
    ids = {x["id"] for x in items}
    on_disk = {p.parent.name for p in ROOT.glob("*/index.html") if p.parent.name.isdigit()}
    assert ids == on_disk  # không thêm/bớt ID
    by = {x["id"]: x for x in items}
    assert by["69115"]["s"] == "HOLD" and by["691121"]["s"] == "Parent đang HOLD" and "8682" in ids


def test_pages_have_search_and_shared_css():
    for page in ("69", "0123456789"):
        s = (ROOT / page / "index.html").read_text("utf-8")
        assert s.count("data-cfp-search") == 1 and '<script src="/search.js" defer></script>' in s
    for page in ("267", "2676"):  # /assets/style.css không tồn tại (404 trên cfp.plus) → dùng /styles.css
        s = (ROOT / page / "index.html").read_text("utf-8")
        assert "/assets/style.css" not in s and 'href="/styles.css"' in s
    sys.path.insert(0, str(ROOT / "scripts"))
    from site_link_audit import audit
    a = audit(ROOT)
    assert a["pages"] >= 150 and "/assets/style.css" not in a["broken"]


@pytest.fixture()
def c(tmp_path):
    st = Stores(f"sqlite:///{tmp_path}/a.db", {"sieu-bo-doi": f"sqlite:///{tmp_path}/s.db",
                                                "si-ai-hstdn": f"sqlite:///{tmp_path}/h.db"}, f"sqlite:///{tmp_path}/o.db")
    return TestClient(create_app(st))


def test_sandbox_serves_search_assets(c):
    js = c.get("/search.js")
    assert js.status_code == 200 and "javascript" in js.headers["content-type"]
    idx = c.get("/search-index.json")
    assert idx.status_code == 200 and len(idx.json()["items"]) >= 150
    assert 'data-cfp-search' in c.get("/69/").text
