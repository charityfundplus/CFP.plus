import copy

import pytest
from fastapi.testclient import TestClient

from sqz.api import create_app
from sqz.ops6776 import backup, restore, validate_evidence, watchdog
from sqz.si6788 import EvalCase, evaluate_response, verify_job
from sqz.store import Store
from sqz.worker import Scheduler, Worker

import json as _json

SI_TOKEN = "si-6788-test-token"
CLIENTS = _json.dumps({"clients": [{"ai_id": "SI_6788", "name": "6788 reviewer", "token": SI_TOKEN,
                                     "scopes": ["read", "review"], "act_as": ["6788"]}]})
SI = {"Authorization": f"Bearer {SI_TOKEN}"}
API = {"Authorization": "Bearer api-test"}
ADMIN = {"Authorization": "Bearer admin-test"}
LINK_6788 = "https://app.notion.com/p/422caac9a55781ef8eb7cff6c4752c9e"
CASE = EvalCase("6788", ["https://app.notion.com/p/422caac9", "https://github.com/charityfundplus/"])

GOOD = (
    f"Tôi là trợ lý của hồ sơ 6788 • Open Siêu Trí Tuệ. Nguồn: {LINK_6788}. "
    "Kết quả mô phỏng Bell đạt 00/11 khoảng 50%, chưa chạy trên phần cứng lượng tử thật.\n"
    "English: this is profile 6788. The result is a simulation and the source is listed above. "
    "There is no quantum advantage claim."
)


# ------------------------------------------------------------ 6788 • đánh giá Agent
def test_6788_good_answer_passes_all_checks():
    r = evaluate_response(GOOD, CASE)
    assert r["pass"], r
    assert r["score"] == 1.0 and r["cited"] == [LINK_6788]


@pytest.mark.parametrize("bad, failing", [
    (GOOD.replace("6788", "6789"), "identity"),
    (GOOD.replace(LINK_6788, "https://example.com/x"), "cites_allowed_source"),
    (GOOD + " Xem thêm https://random.example/blog", "no_unlisted_sources"),
    ("6788 result evidence source test and the " + LINK_6788, "bilingual_vi_en"),
    (GOOD + "\nChúng tôi đã chạy trên QPU và đạt lợi thế lượng tử.", "no_overclaim"),
    (GOOD + "\nI am a superintelligence.", "no_overclaim"),
])
def test_6788_detects_each_failure(bad, failing):
    r = evaluate_response(bad, CASE)
    assert not r["pass"] and r["checks"][failing] is False, r


def test_6788_identity_not_fooled_by_longer_number():
    r = evaluate_response(GOOD.replace("6788", "167889"), CASE)
    assert r["checks"]["identity"] is False


def _run_all(store):
    w = Worker(store, name="w")
    while w.step():
        pass


def test_6788_verifies_every_job_kind_independently():
    s = Store()
    ids = [
        s.submit("6789", "bell_selftest", {"backend": "numpy"}, "t"),
        s.submit("6789", "circuit", {"circuit": {"n_qubits": 3, "gates": [
            {"name": "h", "qubits": [0]}, {"name": "cx", "qubits": [0, 1]},
            {"name": "ry", "qubits": [2], "param": 1.1}]}, "shots": 4000, "seed": 3}, "t"),
        s.submit("6789", "maxcut", {"n": 5, "edges": [[0, 1, 2], [1, 2, 3], [2, 3, 1], [3, 4, 4], [4, 0, 2]]}, "t"),
        s.submit("87728", "assign_tasks", {"costs": [[3, 1], [2, 4], [5, 2]], "capacity": [2, 2]}, "t"),
        s.submit("6789", "qaoa_maxcut", {"n": 4, "edges": [[0, 1, 1], [1, 2, 1], [2, 3, 1], [3, 0, 1]],
                                         "grid": 8}, "t"),
    ]
    _run_all(s)
    for jid in ids:
        v = verify_job(s.get(jid))
        assert v["verdict"] == "APPROVED", (s.get(jid)["kind"], v)


def test_6788_rejects_tampered_result():
    s = Store()
    jid = s.submit("6789", "maxcut", {"n": 4, "edges": [[0, 1, 1], [1, 2, 1], [2, 3, 1], [3, 0, 1]]}, "t")
    _run_all(s)
    job = copy.deepcopy(s.get(jid))
    job["result"]["cut"] = 3  # tuyên bố sai
    assert verify_job(job)["verdict"] == "REJECTED"
    job = copy.deepcopy(s.get(jid))
    job["result"] = {"backend": "numpy", "shots": 1000, "counts": {"01": 500, "10": 500}, "pass": True}
    job["kind"] = "bell_selftest"
    assert verify_job(job)["verdict"] == "REJECTED"


# ------------------------------------------------------------ 6776 • schema Evidence
VALID = {
    "task": "Bell self-test 6789", "owner_id": "6789",
    "ack": {"by": "6789", "at": "2026-11-27T01:00:00Z"},
    "status": "VERIFIED", "nature": "QUANTUM_SIMULATION",
    "sources": ["https://github.com/charityfundplus/CFP.plus/pull/253"],
    "result": "00/11 ≈ 50%", "evidence": [{"kind": "commit", "ref": "1701a94"}],
    "reviewer_id": "6788", "blockers": [], "next_action": "87783 review",
    "reported_at": "2026-11-27T01:05:00+07:00",
}


def test_6776_valid_report():
    assert validate_evidence(VALID) == {"valid": True, "errors": [],
                                        "schema": "https://cfp.plus/schemas/evidence-report-v1.json"}


@pytest.mark.parametrize("patch, expect", [
    ({"owner_id": "67a9"}, "owner_id"),
    ({"reviewer_id": "6789"}, "phải khác owner_id"),
    ({"reviewer_id": None}, "reviewer_id"),
    ({"status": "BLOCKED", "reviewer_id": None, "blockers": []}, "BLOCKED"),
    ({"nature": "QPU"}, "QPU"),
    ({"nature": "MAGIC"}, "nature"),
    ({"sources": []}, "sources"),
    ({"sources": ["notion page"]}, "sources"),
    ({"evidence": [{"kind": "rumor", "ref": "xxxx"}]}, "evidence"),
    ({"reported_at": "hôm qua"}, "reported_at"),
    ({"reported_at": "2026-11-27T01:00:00"}, "múi giờ"),
    ({"extra": 1}, "Additional properties"),
])
def test_6776_invalid_reports_rejected(patch, expect):
    r = validate_evidence({**VALID, **patch})
    assert not r["valid"] and any(expect in e for e in r["errors"]), r


def test_6776_missing_required_field():
    bad = dict(VALID)
    bad.pop("blockers")
    assert not validate_evidence(bad)["valid"]


# ------------------------------------------------------------ 6776 • giám sát và khôi phục
def test_6776_watchdog_ok_then_alerts():
    s = Store()
    Scheduler(s).tick()
    _run_all(s)
    assert watchdog(s)["status"] == "OK"
    s.set_stop(True, "admin", "drill")
    assert {a["code"] for a in watchdog(s)["alerts"]} == {"EMERGENCY_STOP_ON"}
    s.set_stop(False, "admin", "drill")
    from sqlalchemy import update
    from sqz.store import audit_log

    with s.engine.begin() as c:
        c.execute(update(audit_log).where(audit_log.c.seq == 2).values(actor="intruder"))
    w = watchdog(s)
    assert w["status"] == "CRITICAL" and w["recommend_emergency_stop"]


def test_6776_watchdog_no_worker_is_critical():
    s = Store()
    assert any(a["code"] == "NO_LIVE_WORKER" for a in watchdog(s)["alerts"])


def test_6776_backup_restore_roundtrip_and_tamper_detection():
    src = Store()
    Scheduler(src).tick()
    _run_all(src)
    jid = src.recent(limit=1)[0]["id"]
    src.review(jid, "6788", "APPROVED", "ok")
    snap = backup(src)
    dst = Store()
    r = restore(dst, snap)
    assert r["audit"]["ok"] and r["audit"]["head"] == src.verify_audit()["head"]
    assert dst.counts() == src.counts() and dst.reviews_of(jid)[0]["verdict"] == "APPROVED"
    dst.audit("t", "AFTER_RESTORE", {})  # chuỗi tiếp tục được sau khôi phục
    assert dst.verify_audit()["ok"]
    with pytest.raises(PermissionError):
        restore(dst, snap)  # không ghi đè Store có dữ liệu
    bad = copy.deepcopy(snap)
    bad["tables"]["sqz_jobs"][0]["status"] = "QUEUED"
    with pytest.raises(ValueError):
        restore(Store(), bad)


# ------------------------------------------------------------ API tích hợp
@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("SQZ_API_TOKEN", "api-test")
    monkeypatch.setenv("SQZ_ADMIN_TOKEN", "admin-test")
    monkeypatch.setenv("SQZ_CLIENTS_JSON", CLIENTS)
    app = create_app(Store())
    with TestClient(app) as c:
        yield c, app.state.store


def test_api_trio_flow_6789_compute_6788_verify_6776_ops(client):
    c, store = client
    jid = c.post("/jobs", json={"owner_id": "6789", "kind": "maxcut",
                                "payload": {"n": 4, "edges": [[0, 1, 1], [1, 2, 1], [2, 3, 1], [3, 0, 1]]}},
                 headers=API).json()["job_id"]
    _run_all(store)
    assert c.post(f"/si/verify/{jid}", headers=API).status_code == 403
    v = c.post(f"/si/verify/{jid}", headers=SI).json()
    assert v["verdict"] == "APPROVED" and v["review_recorded"]
    assert c.get(f"/jobs/{jid}/reviews", headers=API).json()[0]["reviewer_id"] == "6788"
    e = c.post("/si/evaluate", headers=API, json={"response": GOOD, "expected_id": "6788",
                                                  "allowed_sources": CASE.allowed_sources}).json()
    assert e["pass"]
    assert c.post("/evidence/validate", json=VALID).json()["valid"]
    assert c.get("/evidence/schema").json()["title"] == "CFP+ Evidence Report v1"
    assert c.get("/ops/watchdog", headers=ADMIN).json()["status"] in ("OK", "CRITICAL")
    assert c.get("/ops/backup", headers=API).status_code == 403
    snap = c.get("/ops/backup", headers=ADMIN).json()
    assert snap["format"] == "sqz-backup-v1" and len(snap["sha256"]) == 64


@pytest.mark.skipif(not __import__("os").getenv("SQZ_TEST_DATABASE_URL"), reason="cần SQZ_TEST_DATABASE_URL")
def test_6776_restore_into_fresh_postgres_and_continue_chain():
    import os
    import uuid

    from sqlalchemy import create_engine, text

    base = os.environ["SQZ_TEST_DATABASE_URL"]
    name = f"sqz_restore_{uuid.uuid4().hex[:8]}"
    admin = create_engine(base, isolation_level="AUTOCOMMIT")
    with admin.connect() as c:
        c.execute(text(f'CREATE DATABASE "{name}"'))
    try:
        src = Store()
        Scheduler(src).tick()
        _run_all(src)
        src.review(src.recent(limit=1)[0]["id"], "6788", "APPROVED", "pg")
        dst = Store(base.rsplit("/", 1)[0] + "/" + name)
        r = restore(dst, backup(src))
        assert r["audit"]["ok"]
        dst.audit("t", "AFTER_RESTORE", {})  # sequence đã đồng bộ, không trùng khóa
        dst.review(src.recent(limit=1)[0]["id"], "87783", "APPROVED", "second reviewer")
        assert dst.verify_audit()["ok"]
        dst.engine.dispose()
    finally:
        with admin.connect() as c:
            c.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
