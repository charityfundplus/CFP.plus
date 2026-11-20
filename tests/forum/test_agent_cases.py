"""Bộ hỏi đáp App CFP+ (MÔ PHỎNG) qua Siêu Phần Mềm giám sát — đủ 6 nhóm rủi ro, UNKNOWN/UNVERIFIED ≠ HOLD,
Knowledge legacy, và Evidence không chứa nội dung bản nháp (cùng script dùng cho HTTPS)."""
import json
import threading
import time
from pathlib import Path

import pytest
import uvicorn

from services.forum.answer_guard import check_answer
from services.forum.catalog import Catalog
from services.forum.registry import Registry

CASES = Path(__file__).resolve().parents[2] / "services/forum/agents/cases/app-cfp-simulated.json"
DOC = json.loads(CASES.read_text("utf-8"))


@pytest.fixture(scope="module")
def ctx():
    r = Registry()
    return r, Catalog(r)


@pytest.mark.parametrize("case", DOC["cases"], ids=[c["id"] for c in DOC["cases"]])
def test_app_cases(ctx, case):
    reg, cat = ctx
    res = check_answer(case["draft"], cat, case["question"], registry=reg)
    codes = {f["code"] for f in res["findings"]}
    ids = {x["id"]: x["status"] for x in res["ids"]}
    assert res["auto_reply"] == "HOLD" and res["guard_version"].startswith("sha256:")
    assert res["verdict"] == case["expected_verdict"], (case["id"], res["findings"])
    assert set(case["required_codes"]) <= codes, (case["id"], codes)
    assert all(ids.get(k) == v for k, v in case["expected_id_status"].items()), (case["id"], ids)
    assert all(f["category"] in ("id", "link", "source", "deployment_claim", "authority", "sensitive") for f in res["findings"])


def test_six_risk_groups_covered_and_origin_labelled():
    assert {c["risk"] for c in DOC["cases"]} >= {"id", "link", "source", "deployment_claim", "authority", "sensitive"}
    assert DOC["origin"].startswith("MÔ PHỎNG")  # không trình bày như bản nháp thật / tích hợp Meta


def test_unknown_unverified_hold_are_distinct(ctx):
    reg, cat = ctx
    st = {x["id"]: x["status"] for x in check_answer(
        "https://cfp.plus/3366/ https://cfp.plus/8682/ https://cfp.plus/69115/ https://cfp.plus/691151/ https://cfp.plus/691121/",
        cat, registry=reg)["ids"]}
    assert st == {"3366": "UNKNOWN", "8682": "UNVERIFIED", "69115": "HOLD", "691151": "PARENT_HOLD", "691121": "PARENT_HOLD"}


def test_evidence_script_redacts_and_passes(tmp_path, monkeypatch):
    """Chạy đúng script Evidence (dùng cho HTTPS) trên server local; Evidence không chứa nội dung bản nháp."""
    monkeypatch.setenv("CFP_FORUM_COOKIE_SECURE", "0")
    monkeypatch.setenv("CFP_SANDBOX_EPHEMERAL", "1")
    monkeypatch.setenv("CFP_SANDBOX_DIR", str(tmp_path))
    monkeypatch.setenv("CFP_BOOTSTRAP_PASSWORD", "local-only-pw-xyz")
    for k in ("CFP_FORUM_AUTH_DB", "CFP_OFFICE_DB", "CFP_FORUM_DB_SIEU_BO_DOI", "CFP_FORUM_DB_SI_AI_HSTDN"):
        monkeypatch.delenv(k, raising=False)
    from services.forum.app import create_app, Stores
    app = create_app(Stores.ephemeral_sandbox())
    srv = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=0, log_level="warning"))
    th = threading.Thread(target=srv.run, daemon=True)
    th.start()
    while not srv.started:
        time.sleep(0.05)
    port = srv.servers[0].sockets[0].getsockname()[1]
    try:
        from tests.forum.agent_evidence import run
        ev = run(f"http://127.0.0.1:{port}", CASES, allow_http=True)
    finally:
        srv.should_exit = True
        th.join(5)
    assert ev["result"] == "PASS" and ev["total"] == len(DOC["cases"]), [r for r in ev["rows"] if not r["pass"]]
    blob = json.dumps(ev, ensure_ascii=False)
    assert all(c["draft"] not in blob and c["question"] not in blob for c in DOC["cases"])  # đã loại nội dung
    assert ev["guard_version"].startswith("sha256:") and ev["auto_reply"] == "HOLD"
