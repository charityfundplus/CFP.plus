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
