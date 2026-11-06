"""Bản đồ hệ sinh thái (issue #198 • P0.1) + lịch CTTTC 28882 (366 vị trí; 29/02 chỉ năm nhuận)."""
import pytest
from fastapi.testclient import TestClient

from services.forum.app import Stores, create_app
from services.forum.ecosystem import COMPONENTS, ctttc_date, ctttc_days


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
