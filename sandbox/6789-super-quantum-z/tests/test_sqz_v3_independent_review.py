"""Kiểm tra độc lập (Perplexity, Siêu Bộ Tam 3) cho 6789 v0.2 @ 1701a94.

Mỗi test tái hiện một lỗi đã tìm thấy ở 1701a94 và khóa hành vi đúng sau bản vá.
"""

import itertools
import json
import math
import random
import threading
import time

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update

from sqz import __version__, backends, worker as worker_mod
from sqz.api import create_app
from sqz.circuit import Circuit
from sqz.optimize import cut_value
from sqz.store import Store, jobs
from sqz.worker import Worker

API = {"Authorization": "Bearer api-test"}
TOK = {"6788": {"Authorization": "Bearer tok-6788"}, "87728": {"Authorization": "Bearer tok-87728"}}


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("SQZ_API_TOKEN", "api-test")
    monkeypatch.setenv("SQZ_ADMIN_TOKEN", "admin-test")
    monkeypatch.delenv("SQZ_IDENTITY_TOKENS", raising=False)
    with TestClient(create_app(Store())) as c:
        yield c, c.app.state.store


def _drain(store):
    w = Worker(store, "w-test")
    while w.step():
        pass


# ------------------------------------------------------------ đúng đắn toán học (độc lập với test của Claude Code)
def _qaoa_p1_closed_form(n, edges, gamma, beta):
    """Công thức giải tích QAOA p=1 MaxCut không trọng số (Wang, Hadfield, Jiang, Rieffel 2018)."""
    adj = {i: set() for i in range(n)}
    for u, v, _ in edges:
        adj[u].add(v)
        adj[v].add(u)
    tot = 0.0
    for u, v, _ in edges:
        du, dv, lam = len(adj[u]) - 1, len(adj[v]) - 1, len(adj[u] & adj[v])
        tot += (0.5 + 0.25 * math.sin(4 * beta) * math.sin(gamma) * (math.cos(gamma) ** du + math.cos(gamma) ** dv)
                - 0.25 * math.sin(2 * beta) ** 2 * math.cos(gamma) ** (du + dv - 2 * lam) * (1 - math.cos(2 * gamma) ** lam))
    return tot


def test_qaoa_circuit_matches_analytic_p1_formula():
    rng = random.Random(6789)
    for _ in range(10):
        n = rng.randint(3, 7)
        edges = [(u, v, 1.0) for u, v in itertools.combinations(range(n), 2) if rng.random() < 0.5] or [(0, 1, 1.0)]
        cuts = np.array([cut_value([int(c) for c in format(i, f"0{n}b")], edges) for i in range(2 ** n)])
        g, b = rng.uniform(0, math.pi), rng.uniform(0, math.pi / 2)
        c = Circuit(n)
        for q in range(n):
            c.add("h", q)
        for u, v, w in edges:
            c.add("cx", u, v).add("rz", v, param=g * w).add("cx", u, v)
        for q in range(n):
            c.add("rx", q, param=2 * b)
        sim = float(np.abs(backends.get("numpy").statevector(c)) ** 2 @ cuts)
        # Mạch cài exp(+iγC); công thức dùng exp(-iγC) → so với γ đổi dấu.
        assert abs(sim - _qaoa_p1_closed_form(n, edges, -g, b)) < 1e-9


def test_asymmetric_state_sampling_order_all_backends():
    c = Circuit(3).add("x", 0)
    for b in backends.list_backends():
        if b["available"] and b["kind"] != "QPU":
            assert backends.get(b["name"]).run(c, 20, 1) == {"100": 20}, b["name"]


def test_version_matches_release():
    assert __version__ == "0.3.1"


# ------------------------------------------------------------ F1 • mạo danh reviewer / owner
def test_identity_mode_blocks_reviewer_spoofing(monkeypatch, client):
    c, store = client
    monkeypatch.setenv("SQZ_IDENTITY_TOKENS", "6788:tok-6788,87728:tok-87728")
    r = c.post("/jobs", headers=TOK["87728"], json={"owner_id": "87728", "kind": "maxcut",
                                                    "payload": {"n": 3, "edges": [[0, 1, 1]]}})
    assert r.status_code == 202 and r.json()["identity_verified"] is True
    jid = r.json()["job_id"]
    _drain(store)
    # 87728 cố tự duyệt bằng cách khai reviewer_id=6788 → bị chặn
    spoof = c.post(f"/jobs/{jid}/review", headers=TOK["87728"], json={"reviewer_id": "6788", "verdict": "APPROVED"})
    assert spoof.status_code == 403
    ok = c.post(f"/jobs/{jid}/review", headers=TOK["6788"], json={"reviewer_id": "6788", "verdict": "APPROVED"})
    assert ok.status_code == 200 and ok.json()["identity_verified"] is True
    # token chung không được nộp Job thay ID khác khi chế độ danh tính bật
    assert c.post("/jobs", headers=API, json={"owner_id": "87728", "kind": "maxcut",
                                              "payload": {"n": 3, "edges": [[0, 1, 1]]}}).status_code == 403


def test_shared_token_mode_marks_review_unverified_and_once_per_reviewer(client):
    c, store = client
    jid = c.post("/jobs", headers=API, json={"owner_id": "87728", "kind": "maxcut",
                                             "payload": {"n": 3, "edges": [[0, 1, 1]]}}).json()["job_id"]
    _drain(store)
    r = c.post(f"/jobs/{jid}/review", headers=API, json={"reviewer_id": "6788", "verdict": "APPROVED"})
    assert r.status_code == 200 and r.json()["identity_verified"] is False
    assert c.post(f"/jobs/{jid}/review", headers=API, json={"reviewer_id": "6788", "verdict": "APPROVED"}).status_code == 409


# ------------------------------------------------------------ F2 • lease/heartbeat khi Job dài
def test_long_job_keeps_lease_and_heartbeat(monkeypatch):
    store = Store()
    monkeypatch.setattr(worker_mod, "execute", lambda k, p: (time.sleep(1.2), {"ok": 1})[1])
    jid = store.submit("87728", "maxcut", {}, "t")
    w = Worker(store, "wA", lease_s=0.3)
    th = threading.Thread(target=w.step)
    th.start()
    time.sleep(0.8)
    assert store.claim("wB", lease_s=60) is None          # không bị worker khác nhận trùng
    assert all(x["alive"] for x in store.workers(stale_after_s=0.5))  # heartbeat vẫn chạy trong Job dài
    th.join()
    j = store.get(jid)
    assert j["status"] == "DONE" and j["attempts"] == 1


# ------------------------------------------------------------ F3 • kết quả Job được neo vào audit
def test_result_tampering_detected(client):
    c, store = client
    jid = c.post("/jobs", headers=API, json={"owner_id": "87728", "kind": "maxcut",
                                             "payload": {"n": 3, "edges": [[0, 1, 1], [1, 2, 1]]}}).json()["job_id"]
    _drain(store)
    assert c.get(f"/jobs/{jid}", headers=API).json()["integrity"]["ok"] is True
    with store.engine.begin() as conn:
        conn.execute(update(jobs).where(jobs.c.id == jid).values(result=json.dumps({"cut": 999})))
    assert c.get(f"/jobs/{jid}", headers=API).json()["integrity"]["ok"] is False


# ------------------------------------------------------------ F4 • kiểm tra payload ngay khi nhận
@pytest.mark.parametrize("kind,payload", [
    ("maxcut", {"n": 3, "edges": [[0, 9, 1]]}),
    ("maxcut", {"n": 3, "edges": [[0, 1, 1]], "time_limit_s": "nan"}),
    ("maxcut", {"n": 3, "edges": [[0, 1, 1]], "time_limit_s": -1}),
    ("assign_tasks", {}),
    ("assign_tasks", {"costs": [[1.0] * 200] * 500, "capacity": [1] * 200}),
    ("qaoa_maxcut", {"n": 3, "edges": [[0, 1, 1]], "grid": 0, "backend": "numpy"}),
    ("qaoa_maxcut", {"n": 3, "edges": [[0, 1, 1]], "grid": -5, "backend": "numpy"}),
])
def test_bad_payload_rejected_at_submit(client, kind, payload):
    c, _ = client
    assert c.post("/jobs", headers=API, json={"owner_id": "87728", "kind": kind, "payload": payload}).status_code == 422


def test_oversize_body_rejected(client):
    c, _ = client
    body = {"owner_id": "87728", "kind": "assign_tasks", "payload": {"costs": [[1.0] * 200] * 2000, "capacity": [1] * 200}}
    assert c.post("/jobs", headers=API, json=body).status_code == 413


# ------------------------------------------------------------ F5 • CMP Work Order idempotent
def test_work_order_is_idempotent(client):
    c, store = client
    wo = {"work_order_id": "WO-6789-1", "task": "maxcut", "payload": {"n": 3, "edges": [[0, 1, 1]]}, "requested_by": "87728"}
    a = c.post("/cmp/work-orders", headers=API, json=wo).json()
    b = c.post("/cmp/work-orders", headers=API, json=wo).json()
    assert a["job_id"] == b["job_id"] and b["duplicate"] is True
    assert store.counts().get("QUEUED", 0) == 1


def test_si_verify_twice_does_not_500(client):
    """v0.3: gọi /si/verify hai lần không được lỗi 500; review 6788 chỉ ghi một lần."""
    c, store = client
    jid = c.post("/jobs", headers=API, json={"owner_id": "87728", "kind": "maxcut",
                                             "payload": {"n": 3, "edges": [[0, 1, 1]]}}).json()["job_id"]
    _drain(store)
    r1 = c.post(f"/si/verify/{jid}", headers=API)
    r2 = c.post(f"/si/verify/{jid}", headers=API)
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["review_recorded"] is True and r2.json()["review_recorded"] is False
    assert [r["reviewer_id"] for r in store.reviews_of(jid)] == ["6788"]
