"""Bản đồ hệ sinh thái (issue #198 • P0.1) + lịch CTTTC 28882 (366 vị trí; 29/02 chỉ năm nhuận)."""
import pytest
from fastapi.testclient import TestClient

from services.forum.app import Stores, create_app
from services.forum.ecosystem import COMPONENTS, all_in_one, ctttc_date, ctttc_days


@pytest.fixture(scope="module")
def c(tmp_path_factory):
    d = tmp_path_factory.mktemp("eco")
    st = Stores(f"sqlite:///{d}/a.db", {"sieu-bo-doi": f"sqlite:///{d}/s.db", "si-ai-hstdn": f"sqlite:///{d}/h.db"},
                f"sqlite:///{d}/o.db")
    return TestClient(create_app(st))


def test_map_ten_components_honest_and_openable(c):
    m = c.get("/api/ecosystem").json()
    assert [x["n"] for x in m["components"]] == list(range(1, 11)) and len(COMPONENTS) == 10
    by = {x["key"]: x for x in m["components"]}
    # Trang giới thiệu có sẵn ≠ chức năng: Sàn TMTC có trang 8682 nhưng chức năng CHƯA xây dựng
    assert by["tmtc"]["public_pages"][0]["url"] == "https://cfp.plus/8682/" and by["tmtc"]["function"]["status"] == "planned"
    assert by["app"]["function"]["status"] == "planned" and by["social"]["function"]["status"] == "planned"
    assert all(p.get("url") for p in by["website"]["public_pages"])  # đủ 0123456789 + 000 + Chương 0–9
    assert {p["id"] for p in by["website"]["public_pages"]} >= {str(i) for i in range(10)}
    assert "live" not in {x["function"]["status"] for x in m["components"]}  # không có gì tự nhận production
    for x in m["components"]:  # mọi lối vào sandbox mở được
        if x["function"]["sandbox_path"]:
            assert c.get(x["function"]["sandbox_path"]).status_code == 200, x["key"]
    page = c.get("/_internal/map/")
    assert page.status_code == 200 and "noindex" in page.headers["x-robots-tag"]


def test_ctttc_366_positions_and_leap_rule(c):
    a = ctttc_days()
    assert a["positions"] == 366 and a["days"][59]["mmdd"] == "0229" and a["days"][-1]["mmdd"] == "1231"
    y26 = c.get("/api/ecosystem/ctttc/days", params={"year": 2026}).json()
    assert y26["valid_days"] == 365 and not y26["leap"]
    feb29 = next(d for d in y26["days"] if d["mmdd"] == "0229")
    assert feb29["valid_in_year"] is False and feb29["date_id"] is None
    assert c.get("/api/ecosystem/ctttc/days", params={"year": 2028}).json()["valid_days"] == 366
    r = c.get("/api/ecosystem/ctttc/date/20260229")
    assert r.status_code == 422 and "năm nhuận" in r.json()["detail"]
    assert ctttc_date("20240229")["position"] == 60 and ctttc_date("20261231")["position"] == 366
    assert ctttc_date("21000301")["leap_year"] is False  # 2100 không nhuận
    for bad in ("2026023", "2026-02-2", "20261301", "20260431"):
        assert c.get(f"/api/ecosystem/ctttc/date/{bad}").status_code == 422


def test_all_in_one_covers_founder_scope_with_working_local_navigation(c):
    m = c.get("/api/ecosystem").json()["all_in_one"]
    assert m["hub"] == {"id": "69", "canonical_url": "https://cfp.plus/69/", "sandbox_url": "/69/"}
    assert [x["number"] for x in m["categories"]] == list(range(1, 11))
    assert {g["code"] for g in m["groups"]} == {"DV", "000", "135", "246", "789"}
    assert {ch["id"] for ch in m["chapters"]} == set("0123456789")
    assert "HOLD ACTIVATION" in m["governance"]
    paths = set()
    for category in m["categories"]:
        assert category["status"] in m["statuses"]
        assert category["label"] == m["statuses"][category["status"]]
        for link in category["links"]:
            assert link["status"] in m["statuses"] and link["note"] and link["source"]
            if link["sandbox_url"]:
                paths.add(link["sandbox_url"])
            if link["url"]:
                assert isinstance(link["canonical_id"], str)
                assert link["url"] == f"https://cfp.plus/{link['canonical_id']}/"
                assert link["source"] == f"repo:{link['canonical_id']}/index.html"
                assert link["version"].startswith("sha256:")
    for path in paths:
        assert c.get(path).status_code == 200, path


def test_all_in_one_missing_funds_and_future_features_do_not_invent_links(c):
    m = c.get("/api/ecosystem").json()["all_in_one"]
    by = {x["key"]: x for x in m["categories"]}
    funds = by["funds"]
    assert funds["status"] == "incomplete"
    requested = [x for x in funds["links"] if x["canonical_id"] in {"331", "332", "333"}]
    assert {x["canonical_id"] for x in requested} == {"331", "332", "333"}
    assert all(x["url"] is None and x["sandbox_url"] is None and x["status"] == "incomplete" for x in requested)
    assert not {"31", "32", "33"} & {x["canonical_id"] for x in funds["links"]}
    app = next(x for x in by["products"]["links"] if x["label"] == "App CFP+")
    courses = next(x for x in by["education"]["links"] if "khóa học" in x["label"])
    for item in (app, courses):
        assert item["status"] == "incomplete"
        assert item["canonical_id"] is None and item["url"] is None and item["sandbox_url"] is None
    assert by["research"]["status"] == "research"
    tmtc = next(x for x in by["products"]["links"] if x["canonical_id"] == "8682")
    assert "chưa hoàn thành" in tmtc["note"]


def test_all_in_one_preserves_source_identity_hold_and_responds_to_missing_source():
    from types import SimpleNamespace
    item = {"canonical_id": "6", "canonical_url": "https://cfp.plus/6/", "sandbox_url": "/6/",
            "title": "Nguồn đang HOLD", "source": "repo:6/index.html", "version": "sha256:source-v2",
            "parent_status": "hold_conflict"}
    catalog = SimpleNamespace(items={"6": item})
    data = all_in_one(catalog)
    technology = next(x for x in data["categories"] if x["key"] == "technology")
    source_link = next(x for x in technology["links"] if x["canonical_id"] == "6")
    assert source_link["label"] == item["title"]
    assert source_link["version"] == item["version"] and source_link["parent_status"] == "hold_conflict"
    assert catalog.items == {"6": item}  # không ghi lại Registry hoặc bản ghi nguồn
    del catalog.items["6"]
    missing = next(x for x in all_in_one(catalog)["categories"] if x["key"] == "technology")["links"][0]
    assert missing["canonical_id"] == "6" and missing["url"] is None and missing["sandbox_url"] is None
    assert missing["status"] == "incomplete"


def test_all_in_one_hub_ui_is_sandbox_only_and_keeps_source_page(c):
    from pathlib import Path
    source = Path("69/index.html").read_bytes()
    page = c.get("/69/")
    assert page.status_code == 200 and "CFP+ ALL IN ONE" in page.text
    assert 'data-all-in-one' in page.text and page.text.count('<h1') == 1
    assert "noindex" in page.headers["x-robots-tag"]
    assert "script-src 'self'" in page.headers["content-security-policy"]
    assert '<script src="/_internal/site/all-in-one.js" defer>' in page.text
    assert c.get("/_internal/site/all-in-one.js").status_code == 200
    assert c.get("/_internal/site/all-in-one.css").status_code == 200
    assert c.get("/").status_code == 200 and 'data-all-in-one' not in c.get("/").text
    assert Path("69/index.html").read_bytes() == source
    assert b'CFP+ ALL IN ONE' not in source


def test_all_in_one_hides_office_links_when_office_is_not_configured(tmp_path):
    st = Stores(f"sqlite:///{tmp_path}/a.db", {
        "sieu-bo-doi": f"sqlite:///{tmp_path}/s.db", "si-ai-hstdn": f"sqlite:///{tmp_path}/h.db"})
    with TestClient(create_app(st)) as guest:
        items = guest.get("/api/ecosystem").json()["all_in_one"]["categories"]
        for category in items:
            for item in category["links"]:
                if item["sandbox_url"]:
                    assert guest.get(item["sandbox_url"]).status_code == 200, item
        assert 'aio-shortcuts' not in guest.get("/69/").text


def test_all_in_one_ui_respects_disabled_sandbox_website(tmp_path, monkeypatch):
    monkeypatch.setenv("CFP_SANDBOX_WEBSITE", "0")
    st = Stores(f"sqlite:///{tmp_path}/a.db", {
        "sieu-bo-doi": f"sqlite:///{tmp_path}/s.db", "si-ai-hstdn": f"sqlite:///{tmp_path}/h.db"})
    with TestClient(create_app(st)) as guest:
        assert guest.get("/69/").status_code == 404
        assert guest.get("/_internal/site/all-in-one.js").status_code == 404
        assert guest.get("/api/ecosystem").status_code == 200
