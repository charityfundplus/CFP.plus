"""Bộ kiểm thử tình huống tư vấn khách hàng • Siêu Phần Mềm giám sát câu trả lời (AUTO REPLY HOLD).

Mỗi tình huống: bản nháp của Agent (vd. Meta Business Agent) → verdict mong đợi + mã lỗi bắt buộc.
Không gọi API bên ngoài; chỉ dùng Link Mẫu (trang ID đã xuất bản) và hồ sơ review-holding trong repo.
"""
import uuid

import pytest
from fastapi.testclient import TestClient

from services.forum.agents import knowledge, load_agents, run_tests
from services.forum.answer_guard import check_answer
from services.forum.app import Stores, create_app
from services.forum.catalog import Catalog
from services.forum.registry import Registry
from tests.forum.office_flow import H, ok, register


@pytest.fixture(scope="module")
def cat():
    return Catalog(Registry())


# Bộ tình huống nằm trong cấu hình đào tạo (dùng chung cho test, API test-run và Văn Phòng Agent).
AGENTS = load_agents()
SCENARIOS = [(x["name"], x["question"], x["draft"], x["verdict"], set(x["codes"]))
             for x in AGENTS["meta-business-agent"]["scenarios"]]


@pytest.mark.parametrize("name,q,draft,verdict,codes", SCENARIOS, ids=[s[0] for s in SCENARIOS])
def test_consult_scenarios(cat, name, q, draft, verdict, codes):
    res = check_answer(draft, cat, q)
    got = {f["code"] for f in res["findings"]}
    assert res["auto_reply"] == "HOLD"  # không bao giờ tự gửi
    assert res["verdict"] == verdict, (name, res["findings"])
    assert codes <= got, (name, got)
    for c in res["citations"]:  # nguồn luôn là bản gốc hiện hành của Link Mẫu
        assert c["url"] == f"https://cfp.plus/{c['id']}/" and c["version"].startswith("sha256:")


def test_holds_from_review_holding(cat):
    assert cat.items["69115"]["parent_status"] == "hold_conflict"
    assert cat.items["691151"]["parent_status"] == "parent_hold" and cat.items["691151"]["hold"]["parent"] == "69115"
    assert cat.items["69113"]["parent_status"] == "hold_conflict"
    assert all(it["hold"] is None for it in cat.items.values() if it["parent_status"] in ("registry", "pending_verification"))


def test_answer_check_api(tmp_path, monkeypatch):
    monkeypatch.setenv("CFP_FORUM_COOKIE_SECURE", "0")
    st = Stores(f"sqlite:///{tmp_path}/a.db", {"sieu-bo-doi": f"sqlite:///{tmp_path}/s.db",
                                                "si-ai-hstdn": f"sqlite:///{tmp_path}/h.db"}, f"sqlite:///{tmp_path}/o.db")
    c = TestClient(create_app(st))
    body = {"draft": "App CFP+ đã hoạt động. Mật khẩu của bạn là gì? https://cfp.plus/69115/", "agent": "Meta Business Agent"}
    assert c.post("/api/office/answer-check", json=body, headers=H).status_code == 401  # khách không dùng được
    register(c, f"meta{uuid.uuid4().hex[:6]}@example.org", "Agent Trainer")
    res = ok(c.post("/api/office/answer-check", json=body, headers=H), 200)
    assert res["verdict"] == "block" and res["auto_reply"] == "HOLD"
    assert {"claim_unverified", "sensitive_request", "hold_id"} <= {f["code"] for f in res["findings"]}
    m = c.get("/api/catalog/meta").json()
    assert m["parent_counts"]["hold_conflict"] >= 1 and "69115" in m["holds"]


def test_agent_config_locked_and_knowledge(cat, tmp_path):
    a = AGENTS["meta-business-agent"]
    assert a["canonical_id"] is None and a["stage"] == "TRAINING"  # không tự cấp ID, không tự chuyển stage
    assert a["flags"] == {"auto_reply": "HOLD", "production": "NO-GO", "published": False, "meta_api_connected": False}
    kb = knowledge(a, cat)
    by = {r["id"]: r for r in kb["sources"]}
    assert by["69115"]["status"] == "excluded_hold" and not by["69115"]["use"]
    assert by["691151"]["status"] == "verifying" and by["69"]["status"] == "approved_source"
    assert all(r["url"] == f"https://cfp.plus/{r['id']}/" for r in kb["sources"] if r.get("url"))
    run = run_tests(a, cat)
    assert run["failed"] == 0 and run["total"] == len(SCENARIOS) and run_tests(a, cat)["sha"] == run["sha"]  # xác định
    bad = dict(a, flags=dict(a["flags"], auto_reply="ON"))  # cấu hình bật tự trả lời trước HUMAN_APPROVAL → từ chối
    import json
    (tmp_path / "x.json").write_text(json.dumps({k: v for k, v in bad.items() if k not in ("config_version", "config_source")}))
    with pytest.raises(ValueError):
        load_agents(tmp_path)


def test_agent_api_and_page(tmp_path, monkeypatch):
    monkeypatch.setenv("CFP_FORUM_COOKIE_SECURE", "0")
    st = Stores(f"sqlite:///{tmp_path}/a.db", {"sieu-bo-doi": f"sqlite:///{tmp_path}/s.db",
                                                "si-ai-hstdn": f"sqlite:///{tmp_path}/h.db"}, f"sqlite:///{tmp_path}/o.db")
    c = TestClient(create_app(st))
    assert [x["slug"] for x in ok(c.get("/api/office/agents"), 200)["agents"]] == ["meta-business-agent"]
    d = ok(c.get("/api/office/agents/meta-business-agent"), 200)
    assert d["developer_ref_status"] == "hold_conflict" and d["tests"]["failed"] == 0
    assert c.get("/api/office/agents/khong-co").status_code == 404
    assert c.post("/api/office/agents/meta-business-agent/test-runs", headers=H).status_code == 401
    register(c, f"tr{uuid.uuid4().hex[:6]}@example.org", "Agent Trainer")
    run = ok(c.post("/api/office/agents/meta-business-agent/test-runs", headers=H), 201)
    assert run["passed"] == run["total"] and run["auto_reply"] == "HOLD"
    ev = ok(c.get(f"/api/office/agents/meta-business-agent/test-runs/{run['sha']}"), 200)  # Evidence tính lại được
    assert ev["sha"] == run["sha"]
    assert c.get("/api/office/agents/meta-business-agent/test-runs/0000000000000000").status_code == 409
    page = c.get("/_internal/agent/meta-business-agent/")
    assert page.status_code == 200 and "noindex" in page.headers["x-robots-tag"] and "AUTO REPLY HOLD" in page.text
    assert c.get("/_internal/agent/khong-co/").status_code == 404
