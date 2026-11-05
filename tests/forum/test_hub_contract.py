"""HUB 69 • AI Directory • hợp đồng OpenAPI • ranh giới xác thực của mọi endpoint."""
import re

import pytest
from fastapi.testclient import TestClient

from services.forum import inventory
from services.forum.registry import Registry


@pytest.fixture(scope="module")
def app():
    return inventory.build_app()


@pytest.fixture(scope="module")
def client(app):
    return TestClient(app)


def test_openapi_contract_matches_snapshot(app):
    assert inventory.OPENAPI_PATH.read_text(encoding="utf-8") == inventory.openapi_text(app), \
        "Hợp đồng API thay đổi: chạy python -m services.forum.inventory --write và review diff"


def test_inventory_matches_code(app):
    assert inventory.INVENTORY_PATH.read_text(encoding="utf-8") == inventory.render_markdown(app)


def test_openapi_served_and_tagged(client):
    spec = client.get("/api/openapi.json").json()
    assert spec["info"]["title"].startswith("CFP+ Backend API")
    for path, ops in spec["paths"].items():
        assert path.startswith("/api/"), path
        for op in ops.values():
            assert op.get("tags"), f"{path} thiếu tag module"


def test_every_write_endpoint_requires_csrf(app, client):
    """Ranh giới chung: mọi POST/PUT/PATCH/DELETE không có header chống CSRF → 403 trước khi vào handler."""
    n = 0
    for r in inventory.iter_api_routes(app.routes):
        if not r.path.startswith("/api/"):
            continue
        for m in r.methods & {"POST", "PUT", "PATCH", "DELETE"}:
            path = re.sub(r"\{[^}]+\}", "1", r.path)
            assert client.request(m, path, json={}).status_code == 403, f"{m} {r.path}"
            n += 1
    assert n >= 20


def test_login_required_endpoints_reject_anonymous(app, client):
    n = 0
    for row in inventory.inventory_rows(app):
        if row["auth"] != "đăng nhập" or row["method"] != "POST":
            continue
        path = re.sub(r"\{[^}]+\}", "1", row["path"])
        if path.startswith("/api/forums/1"):
            path = path.replace("/api/forums/1", "/api/forums/sieu-bo-doi")
        r = client.post(path, json={}, headers={"X-CFP-Forum": "1"})
        assert r.status_code in (401, 422), f"{path} → {r.status_code}"
        n += 1
    assert n >= 10


def test_hub69_summary(client):
    d = client.get("/api/hub/69").json()
    assert [g["code"] for g in d["groups"]] == ["DV", "000", "135", "246", "789"]
    assert [c["id"] for c in d["chapters"]] == [str(i) for i in range(10)]
    assert {f["key"] for f in d["forums"]} == {"sieu-bo-doi", "si-ai-hstdn"}
    assert d["registry"]["total"] == len(Registry().entities)
    assert d["status"] == "SANDBOX • NOT DEPLOYED"
    status = {m["key"]: m["status"] for m in d["modules"]}
    assert status["tmtc"] == "missing" and status["website"] == "missing" and status["office"] == "implemented"


def test_directory_read_only(client):
    countries = client.get("/api/directory/countries").json()["countries"]
    us = next(c for c in countries if c["country_id"] == "911")
    assert us["ai_country_id"] == "6911" and us["developers"] >= 9
    d = client.get("/api/directory/69112").json()
    assert [x["id"] for x in d["chain"]] == ["911", "6911", "69112"]
    assert "691121" in [x["id"] for x in d["children"]]
    assert client.get("/api/directory/99999999").status_code == 404
    # Không có phương thức ghi nào trên Directory/HUB.
    for m in ("post", "put", "patch", "delete"):
        assert getattr(client, m)("/api/directory/911", headers={"X-CFP-Forum": "1"}).status_code == 405


def test_health_reports_modules(client):
    h = client.get("/api/health").json()
    assert h["status"] == "ok" and h["registry"]["read_only"] is True
    assert set(h["forums"]) == {"sieu-bo-doi", "si-ai-hstdn"} and h["office"]["offices"] == 0


def test_catalog_only_verified_pages_and_registry_parents():
    """Danh mục Link Mẫu: chỉ trang ID số đã xuất bản trong repo; parent chỉ từ Registry; không cấp ID."""
    import hashlib
    import re
    from pathlib import Path
    from services.forum.catalog import PENDING, Catalog, fold
    from services.forum.registry import Registry
    root = Path(__file__).resolve().parents[2]
    reg = Registry()
    cat = Catalog(reg)
    on_disk = {p.name for p in root.iterdir() if p.is_dir() and re.fullmatch(r"[0-9]+", p.name) and (p / "index.html").is_file()}
    assert set(cat.items) == on_disk and len(on_disk) >= 150
    for cid in ("69", "267", "28882", "8682", "691121"):
        it = cat.items[cid]
        assert it["canonical_url"] == f"https://cfp.plus/{cid}/" and it["classification"] == "PUBLIC"
        assert it["version"] == "sha256:" + hashlib.sha256((root / cid / "index.html").read_bytes()).hexdigest()[:16]
    assert cat.items["691121"]["parent_id"] == "69112" and cat.items["691121"]["parent_status"] == "registry"
    for it in cat.items.values():  # parent chỉ từ Registry; không có → chờ xác minh, không suy từ tiền tố
        e = reg.get(it["canonical_id"])
        assert it["parent_id"] == (e.parent_id if e else None)
        assert (it["parent_status"] == "registry") == bool(it["parent_id"])
    assert "HUB 69" in cat.items["69"]["title"]
    ids = [r["canonical_id"] for r in cat.search("tmtc")]
    assert "8682" in ids and all("tmtc" in fold(r["title"] + r["description"] + r["canonical_id"]) for r in cat.search("tmtc"))
    assert "31" in [r["canonical_id"] for r in cat.search("quy 1")]  # tìm không dấu
    assert cat.search("8682")[0]["canonical_id"] == "8682"  # khớp ID đứng đầu
    assert all("canonical_id" not in p for p in PENDING)


def test_catalog_api(client):
    r = client.get("/api/catalog", params={"q": "HUB 69"})
    assert r.status_code == 200 and r.json()["total"] >= 150
    assert any(x["canonical_id"] == "69" for x in r.json()["items"])
    it = client.get("/api/catalog/8682").json()
    assert it["canonical_url"] == "https://cfp.plus/8682/" and {c["canonical_id"] for c in it["children"]} <= set(
        x["canonical_id"] for x in client.get("/api/catalog", params={"limit": 200, "q": "8682"}).json()["items"])
    assert client.get("/api/catalog/99999999").status_code == 404  # không tự cấp ID
    m = client.get("/api/catalog/meta").json()
    assert [x["n"] for x in m["modules"]] == list(range(10))
    assert all(p["canonical_id"] is None and p["status"] == "pending_verification" for p in m["pending"])
    assert all(x["classification"] == "INTERNAL" for x in m["sandbox"])
    page = client.get("/_internal/catalog/")
    assert page.status_code == 200 and "noindex" in page.headers["x-robots-tag"]
