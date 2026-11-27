"""v0.4: danh tính thực, đa worker + fencing + idempotency, Gateway, 1.110 ID, Team, PostgreSQL."""

import json
import os
import sys
import threading
import time
from collections import Counter
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from sqz import executor
from sqz.api import create_app
from sqz.auth import AuthError, authenticate, load_clients, require_act_as
from sqz.gateway import GATEWAY_WORK_ORDER_FIELDS, resolve_id, to_gateway_work_order
from sqz.store import Store
from sqz.teams import capacity_check, form_teams, rotate_reviewer, route_tasks
from sqz.worker import Worker

CLIENTS = {"clients": [
    {"ai_id": "CLAUDE_CODE", "token": "tok-claude", "scopes": ["read", "submit"], "act_as": ["6789", "87788"]},
    {"ai_id": "SI_6788", "token": "tok-6788", "scopes": ["read", "review"], "act_as": ["6788"]},
    {"ai_id": "REVIEW_87783", "token": "tok-87783", "scopes": ["read", "review", "submit"], "act_as": ["87783"]},
    {"ai_id": "OPS_6776", "token": "tok-6776", "scopes": ["read", "operate"], "act_as": ["6776"]},
]}
H = {k: {"Authorization": f"Bearer tok-{k}"} for k in ("claude", "6788", "87783", "6776")}


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("SQZ_CLIENTS_JSON", json.dumps(CLIENTS))
    monkeypatch.delenv("SQZ_API_TOKEN", raising=False)
    monkeypatch.setenv("SQZ_ADMIN_TOKEN", "admin-test")
    app = create_app(Store())
    with TestClient(app) as c:
        yield c, app.state.store


def drain(store, name="w"):
    w = Worker(store, name=name)
    while w.step():
        pass


# ------------------------------------------------------------ 3. danh tính thực
def test_tokens_are_hashed_unique_and_gateway_format_compatible():
    env = {"SQZ_CLIENTS_JSON": json.dumps(CLIENTS["clients"])}  # dạng list như CFP_MCP_CLIENTS_JSON
    assert len(load_clients(env)) == 4
    dup = {"SQZ_CLIENTS_JSON": json.dumps([{"ai_id": "A", "token": "x"}, {"ai_id": "B", "token": "x"}])}
    with pytest.raises(ValueError):
        load_clients(dup)
    with pytest.raises(ValueError):
        load_clients({"SQZ_CLIENTS_JSON": json.dumps([{"ai_id": "A", "token": "t", "act_as": ["6a"]}])})
    import hashlib

    hashed = {"SQZ_CLIENTS_JSON": json.dumps([{"ai_id": "H", "token_sha256": hashlib.sha256(b"s3").hexdigest(),
                                                "scopes": ["read"]}])}
    assert authenticate("Bearer s3", hashed).ai_id == "H"
    with pytest.raises(AuthError):
        authenticate("Bearer wrong", hashed)


def test_act_as_rules():
    env = {"SQZ_CLIENTS_JSON": json.dumps(CLIENTS)}
    claude = authenticate("Bearer tok-claude", env)
    require_act_as(claude, "6789", "submit")
    with pytest.raises(AuthError):
        require_act_as(claude, "6788", "submit")  # không đại diện 6788
    with pytest.raises(AuthError):
        require_act_as(claude, "6789", "review")  # thiếu scope review
    legacy = authenticate("Bearer L", {"SQZ_API_TOKEN": "L"})
    require_act_as(legacy, "123", "submit")
    with pytest.raises(AuthError):
        require_act_as(legacy, "6788", "review")  # LEGACY không bao giờ review


def test_api_reviewer_must_prove_identity(client):
    c, store = client
    assert c.get("/whoami", headers=H["6788"]).json()["act_as"] == ["6788"]
    r = c.post("/jobs", headers=H["claude"], json={"owner_id": "6788", "kind": "bell_selftest"})
    assert r.status_code == 403  # Claude Code không được gửi thay 6788
    jid = c.post("/jobs", headers=H["claude"], json={"owner_id": "6789", "kind": "bell_selftest"}).json()["job_id"]
    drain(store)
    body = {"reviewer_id": "6788", "verdict": "APPROVED"}
    assert c.post(f"/jobs/{jid}/review", headers=H["87783"], json=body).status_code == 403  # mạo danh 6788
    assert c.post(f"/jobs/{jid}/review", headers=H["claude"], json=body).status_code == 403  # thiếu scope
    assert c.post(f"/jobs/{jid}/review", headers=H["6788"], json=body).status_code == 200
    assert c.post(f"/jobs/{jid}/review", headers=H["87783"],
                  json={"reviewer_id": "87783", "verdict": "APPROVED"}).status_code == 200
    rv = c.get(f"/jobs/{jid}/reviews", headers=H["6776"]).json()
    assert [r["reviewer_id"] for r in rv] == ["6788", "87783"]


def test_same_principal_cannot_self_review(client):
    c, store = client
    jid = c.post("/jobs", headers=H["87783"], json={"owner_id": "87783", "kind": "bell_selftest"}).json()["job_id"]
    drain(store)
    # khác ID cũng không được, vì cùng một token đã gửi Job
    s = store.get(jid)
    with pytest.raises(PermissionError):
        store.review(jid, "6788", "APPROVED", reviewer_principal=s["submitted_by"])


def test_si_verify_requires_6788_identity(client):
    c, store = client
    jid = c.post("/jobs", headers=H["claude"], json={"owner_id": "6789", "kind": "maxcut",
                                                     "payload": {"n": 3, "edges": [[0, 1, 1], [1, 2, 1]]}}).json()["job_id"]
    drain(store)
    assert c.post(f"/si/verify/{jid}", headers=H["87783"]).status_code == 403
    assert c.post(f"/si/verify/{jid}", headers=H["6788"]).json()["verdict"] == "APPROVED"


# ------------------------------------------------------------ 4. đa worker, fencing, idempotency
def test_idempotency_same_key_returns_same_job(client):
    c, store = client
    body = {"owner_id": "6789", "kind": "bell_selftest", "idempotency_key": "order-0001-abc"}
    a = c.post("/jobs", headers=H["claude"], json=body).json()["job_id"]
    b = c.post("/jobs", headers=H["claude"], json=body).json()["job_id"]
    assert a == b and store.counts() == {"QUEUED": 1}
    wo = {"work_order_id": "WO-77", "task": "bell_selftest", "requested_by": "6789"}
    x = c.post("/cmp/work-orders", headers=H["claude"], json=wo).json()["job_id"]
    y = c.post("/cmp/work-orders", headers=H["claude"], json=wo).json()["job_id"]
    assert x == y


def test_concurrent_idempotent_submit_creates_one_job(tmp_path):
    s = Store(tmp_path / "idem.db")
    ids = []

    def go():
        ids.append(s.submit("6789", "bell_selftest", {}, "t", idempotency_key="same-key-123"))

    th = [threading.Thread(target=go) for _ in range(16)]
    [t.start() for t in th]
    [t.join() for t in th]
    assert len(set(ids)) == 1 and s.counts() == {"QUEUED": 1}


def test_stale_worker_cannot_finish_after_lease_reclaimed():
    s = Store()
    jid = s.submit("6789", "bell_selftest", {}, "t")
    a = s.claim("slow", lease_s=0.05)
    time.sleep(0.1)
    b = s.claim("fast", lease_s=30)
    assert b["id"] == jid and b["fence"] == a["fence"] + 1
    assert s.finish(jid, "slow", result={"x": 1}, fence=a["fence"]) is False  # bị chặn
    assert s.finish(jid, "fast", result={"x": 2}, fence=b["fence"]) is True
    assert s.finish(jid, "fast", result={"x": 3}, fence=b["fence"]) is False  # không chốt hai lần
    assert s.get(jid)["result"] == {"x": 2}


def test_many_workers_execute_each_job_exactly_once(tmp_path, monkeypatch):
    s = Store(tmp_path / "multi.db")
    n_jobs = 120
    for i in range(n_jobs):
        s.submit("6789", "maxcut", {"n": 3, "edges": [[0, 1, 1]]}, "t", priority=i % 5)
    calls = Counter()
    lock = threading.Lock()
    real = executor.execute

    def counting(kind, payload):
        out = real(kind, payload)
        with lock:
            calls["n"] += 1
        return out

    monkeypatch.setattr("sqz.worker.execute", counting)
    workers = [Worker(s, name=f"w{i}", poll_s=0.01) for i in range(8)]
    [w.start() for w in workers]
    deadline = time.time() + 60
    while s.counts().get("DONE", 0) < n_jobs and time.time() < deadline:
        time.sleep(0.05)
    [w.stop() for w in workers]
    [w.join(5) for w in workers]
    assert s.counts() == {"DONE": n_jobs}
    assert calls["n"] == n_jobs  # không thực thi trùng
    assert sum(w.processed for w in workers) == n_jobs
    assert s.verify_audit()["ok"]


def test_priority_order_and_fair_share():
    s = Store()
    low = s.submit("6789", "bell_selftest", {}, "t", priority=0)
    high = s.submit("6789", "bell_selftest", {}, "t", priority=50)
    assert s.claim("w", 30)["id"] == high
    s2 = Store()
    a1 = s2.submit("6789", "bell_selftest", {}, "t")
    s2.submit("6789", "bell_selftest", {}, "t")
    b1 = s2.submit("87788", "bell_selftest", {}, "t")
    assert s2.claim("w1", 30, max_running_per_owner=1)["id"] == a1
    assert s2.claim("w2", 30, max_running_per_owner=1)["id"] == b1  # 6789 đã chạm hạn mức
    assert s2.claim("w3", 30, max_running_per_owner=1) is None
    with pytest.raises(ValueError):
        s.submit("6789", "bell_selftest", {}, "t", priority=1000)
    assert low


# ------------------------------------------------------------ 2. Gateway • DID • CMP
def _mock(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_gateway_resolve_found_notfound_down():
    def handler(req):
        if req.url.path == "/api/id/6984":
            return httpx.Response(200, json={"id": "6984", "name": "Vietnam AI Directory", "status": "REFERENCE MODEL"})
        if req.url.path == "/api/id/69":
            return httpx.Response(200, json={"id": "69", "name": "HUB", "did": "did:example:69"})
        return httpx.Response(404, json={"detail": "Canonical ID not found"})

    g = "https://gw.test"
    r = resolve_id("6984", g, _mock(handler))
    assert r["verification"] == "GATEWAY_VERIFIED" and r["did_status"] == "NOT_ASSIGNED" and r["did"] is None
    assert resolve_id("69", g, _mock(handler))["did"] == "did:example:69"
    assert resolve_id("1234", g, _mock(handler))["verification"] == "GATEWAY_NOT_FOUND"

    def down(req):
        raise httpx.ConnectError("refused")

    assert resolve_id("6789", g, _mock(down))["verification"] == "LOCAL_FORMAT_ONLY"
    assert resolve_id("6789", None)["verification"] == "LOCAL_FORMAT_ONLY"


def test_gateway_resolver_preserves_exact_id_and_fails_closed_on_invalid_reply():
    origin = "https://gw.test"
    with _mock(lambda req: httpx.Response(200, json={"id": req.url.path.rsplit("/", 1)[-1]})) as client:
        assert resolve_id("0229", origin, client)["verification"] == "GATEWAY_VERIFIED"

    for response in (httpx.Response(200, text="not JSON"), httpx.Response(200, json=[]),
                     httpx.Response(200, json={"id": "229", "did": "did:example:229"}),
                     httpx.Response(200, json={"id": "0229", "did": 123})):
        with _mock(lambda req: response) as client:
            result = resolve_id("0229", origin, client)
        assert result["id"] == "0229" and result["verification"] == "LOCAL_FORMAT_ONLY"
        assert result["did"] is None and result["registry"] is None


def test_gateway_work_order_has_exact_gateway_fields():
    s = Store()
    jid = s.submit("6789", "bell_selftest", {}, "t")
    drain(s)
    wo = to_gateway_work_order(s.get(jid))
    assert set(wo) == GATEWAY_WORK_ORDER_FIELDS
    gw = Path("/home/user/cfp-gateway/main.py")
    if gw.exists():  # đối chiếu trực tiếp mô hình của cfp-gateway khi có mã nguồn
        src = gw.read_text()
        for f in GATEWAY_WORK_ORDER_FIELDS:
            assert f"    {f}:" in src, f


# ------------------------------------------------------------ 7. 1.110 ID nền tảng + kiểm kê mở rộng
def _foundation_ids():
    return [str(d) for d in range(10)] + [f"{d:02d}" for d in range(100)] + [f"{d:03d}" for d in range(1000)]


def _inventory_ids():
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "87788-super-trio"))
    import trio

    rows, excl, _ = trio.load_inventory()
    return [r["id"] for r in trio.check_inventory(rows, excl)["active"]]


def test_api_all_1110_foundation_ids_and_inventory(client):
    c, _ = client
    ids = _foundation_ids()
    assert len(ids) == 1110 and len(set(ids)) == 1110  # "0", "00", "000" là ba ID khác nhau
    levels = Counter()
    inventory = _inventory_ids()
    for batch, count in ((ids, True), (inventory, False)):
        for cid in batch:
            r = c.get(f"/trio/{cid}")
            assert r.status_code == 200, cid
            d = r.json()
            assert d["id"] == cid and d["chapter"] == cid[0]
            if count:
                levels[d["level"]] += 1
    assert levels == {"CHUONG": 10, "CON": 100, "CHAU": 1000}
    assert len(inventory) == 104
    assert c.get("/ids/000/resolve").json()["verification"] == "LOCAL_FORMAT_ONLY"


# ------------------------------------------------------------ 8–9. Team, phân bổ, thay phiên
def test_form_teams_small_exact():
    ids = [f"{g}{i:02d}" for g in (1, 2, 6, 7) for i in range(12)]  # 48 Siêu Bộ Tam, đủ 4 Nhóm
    r = form_teams(ids, n_teams=10, min_size=12, max_teams_per_trio=3, time_limit_s=20)
    assert r["status"] in ("OPTIMAL", "FEASIBLE")
    assert min(r["team_sizes"]) >= 12 and r["max_teams_per_trio_used"] <= 3
    assert r["groups_covered_all_teams"]
    assert set().union(*map(set, r["teams"])) == set(ids)  # không bỏ sót ai
    assert capacity_check(10, 115, 33, 40)["feasible"] is False
    assert form_teams(ids[:10], 5, 12, 3)["status"] == "INFEASIBLE"


def test_route_tasks_priority_first_when_capacity_short():
    tasks = [{"id": "T1", "priority": 1, "capability": "qc", "effort": 3},
             {"id": "T2", "priority": 9, "capability": "qc", "effort": 3},
             {"id": "T3", "priority": 5, "capability": "ops", "effort": 1}]
    teams = [{"id": "6789", "capabilities": ["qc"], "capacity": 3},
             {"id": "6776", "capabilities": ["ops"], "capacity": 2}]
    r = route_tasks(tasks, teams)
    assert r["assignment"] == {"T2": "6789", "T3": "6776"} and r["unassigned"] == ["T1"]


def test_rotate_reviewer_fair_and_independent(client):
    pool = ["6788", "87783", "6776"]
    hist: list[str] = []
    for _ in range(9):
        hist.append(rotate_reviewer(pool, "6789", hist))
    assert Counter(hist) == {"6788": 3, "87783": 3, "6776": 3}
    assert all(a != b for a, b in zip(hist, hist[1:]))
    assert "6788" not in [rotate_reviewer(pool, "6788", []) for _ in range(3)]
    c, _ = client
    assert c.get("/si/next-reviewer", params={"owner_id": "6789", "pool": "6788,87783",
                                              "history": "6788"}).json()["reviewer_id"] == "87783"


# ------------------------------------------------------------ 5. PostgreSQL mất kết nối / restart
@pytest.mark.skipif(not os.getenv("SQZ_TEST_DATABASE_URL"), reason="cần SQZ_TEST_DATABASE_URL")
def test_postgres_survives_killed_connections_and_restart():
    from sqlalchemy import create_engine, text

    url = os.environ["SQZ_TEST_DATABASE_URL"]
    s = Store(url)
    jid = s.submit("6789", "bell_selftest", {}, "pg-kill")
    admin = create_engine(url, isolation_level="AUTOCOMMIT")
    with admin.connect() as c:  # giết mọi kết nối khác (mô phỏng DB restart / mạng rớt)
        killed = c.execute(text("SELECT count(pg_terminate_backend(pid)) FROM pg_stat_activity "
                                "WHERE datname = current_database() AND pid <> pg_backend_pid()")).scalar()
    assert killed >= 0
    assert s.ping()  # pool_pre_ping tự kết nối lại
    drain(s, "pg-after-kill")
    assert s.get(jid)["status"] == "DONE"
    s.engine.dispose()  # "restart" tiến trình: bỏ pool, Store mới cùng DB
    s2 = Store(url)
    assert s2.get(jid)["status"] == "DONE" and s2.verify_audit()["ok"]


@pytest.mark.skipif(not os.getenv("SQZ_TEST_DATABASE_URL"), reason="cần SQZ_TEST_DATABASE_URL")
def test_postgres_many_workers_exactly_once():
    s = Store(os.environ["SQZ_TEST_DATABASE_URL"])
    before = s.counts().get("DONE", 0)
    n = 60
    for _ in range(n):
        s.submit("6789", "maxcut", {"n": 3, "edges": [[0, 1, 1]]}, "pg-multi")
    workers = [Worker(Store(os.environ["SQZ_TEST_DATABASE_URL"]), name=f"pg{i}", poll_s=0.01) for i in range(6)]
    [w.start() for w in workers]
    deadline = time.time() + 90
    while s.counts().get("DONE", 0) < before + n and time.time() < deadline:
        time.sleep(0.1)
    [w.stop() for w in workers]
    [w.join(5) for w in workers]
    assert s.counts().get("DONE", 0) == before + n and not s.counts().get("RUNNING")
    assert sum(w.processed for w in workers) == n
    assert s.verify_audit()["ok"]


def _proc_audit(path, tag, n):
    from sqz.store import Store as S

    st = S(path)
    for i in range(n):
        st.audit(tag, "E", {"i": i})
        if i % 5 == 0:
            st.submit("6789", "bell_selftest", {}, tag)


def test_audit_chain_intact_with_multiple_processes(tmp_path):
    """Lỗi thật phát hiện khi chạy 2 instance: chuỗi audit rẽ nhánh. Kiểm bằng 4 tiến trình."""
    import multiprocessing as mp

    path = str(tmp_path / "mp.db")
    Store(path)  # tạo schema trước
    ctx = mp.get_context("spawn")
    procs = [ctx.Process(target=_proc_audit, args=(path, f"p{i}", 40)) for i in range(4)]
    [p.start() for p in procs]
    [p.join(120) for p in procs]
    assert all(p.exitcode == 0 for p in procs)
    v = Store(path).verify_audit()
    assert v["ok"] and v["checked"] == 4 * 40 + 4 * 8, v
