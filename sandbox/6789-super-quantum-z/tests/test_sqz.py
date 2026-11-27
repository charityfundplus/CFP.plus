import random
import time

import numpy as np
import pytest
from fastapi.testclient import TestClient

from sqz import backends
from sqz.api import create_app
from sqz.circuit import Circuit, CircuitError, bell, ghz
from sqz.executor import bell_selftest, execute
from sqz.ids import InvalidID, classify
from sqz.optimize import maxcut_brute, maxcut_ortools
from sqz.store import Store
from sqz.worker import Scheduler, Worker

AVAILABLE = [b["name"] for b in backends.list_backends() if b["available"]]


def random_circuit(n: int, depth: int, seed: int) -> Circuit:
    rnd = random.Random(seed)
    c = Circuit(n)
    for _ in range(depth):
        g = rnd.choice(["h", "x", "y", "z", "s", "t", "rx", "ry", "rz", "cx", "cz"])
        if g in ("cx", "cz"):
            a, b = rnd.sample(range(n), 2)
            c.add(g, a, b)
        elif g.startswith("r"):
            c.add(g, rnd.randrange(n), param=rnd.uniform(0, 6.3))
        else:
            c.add(g, rnd.randrange(n))
    return c


# ------------------------------------------------------------ ID Số
def test_ids_keep_leading_zeros_and_levels():
    assert classify("0")["level"] == "CHUONG"
    assert classify("00")["level"] == "CON" and classify("000")["level"] == "CHAU"
    assert classify("6789") == {"id": "6789", "chapter": "6", "group": "246", "level": "SIEU_BO_TAM_4_SO"}
    assert classify("87788")["group"] == "789"
    for bad in ["", "12a", "-1", "1" * 13, 6789]:
        with pytest.raises(InvalidID):
            classify(bad)


# ------------------------------------------------------------ mạch và giới hạn
def test_circuit_limits():
    with pytest.raises(CircuitError):
        Circuit(21)
    with pytest.raises(CircuitError):
        Circuit(2).add("cx", 0, 0)
    with pytest.raises(CircuitError):
        Circuit(2).add("rx", 0)
    with pytest.raises(CircuitError):
        Circuit(2).add("toffoli", 0, 1)
    with pytest.raises(CircuitError):
        backends.get("numpy").run(bell(), shots=0)


def test_numpy_reference_bell_and_ghz_exact():
    sv = backends.get("numpy").statevector(bell())
    assert np.allclose(sv, [2 ** -0.5, 0, 0, 2 ** -0.5])
    sv3 = backends.get("numpy").statevector(ghz(3))
    assert np.isclose(abs(sv3[0]) ** 2, 0.5) and np.isclose(abs(sv3[7]) ** 2, 0.5)


def test_bit_order_q0_leftmost():
    c = Circuit(3).add("x", 0)
    for name in AVAILABLE:
        assert backends.get(name).run(c, 50, seed=1) == {"100": 50}, name


@pytest.mark.parametrize("name", AVAILABLE)
def test_backends_agree_with_reference_statevector(name):
    ref = backends.get("numpy")
    for seed in range(3):
        c = random_circuit(4, 30, seed)
        fid = abs(np.vdot(ref.statevector(c), backends.get(name).statevector(c))) ** 2
        assert fid > 1 - 1e-6, (name, seed, fid)


@pytest.mark.parametrize("name", AVAILABLE)
def test_bell_selftest_every_backend(name):
    r = bell_selftest(name)
    assert r["pass"], r
    assert set(r["counts"]) <= {"00", "11"}
    assert r["nature"] == "SIMULATION"


def test_unavailable_backend_reports_clearly():
    with pytest.raises(KeyError):
        backends.get("ibm-qpu")


# ------------------------------------------------------------ OR-Tools
def test_maxcut_ortools_matches_brute_force():
    rnd = random.Random(7)
    for _ in range(5):
        n = 8
        edges = [(u, v, rnd.randint(1, 9)) for u in range(n) for v in range(u + 1, n) if rnd.random() < 0.5]
        r = maxcut_ortools(n, edges)
        assert r["optimal"]
        assert r["cut"] == maxcut_brute(n, edges)[0]


# ------------------------------------------------------------ store, audit, queue
def test_audit_chain_detects_tampering():
    s = Store()
    for i in range(5):
        s.audit("t", "E", {"i": i})
    assert s.verify_audit() == {"ok": True, "checked": 5, "head": s.verify_audit()["head"]}
    s.db.execute("UPDATE audit SET data='{\"i\":99}' WHERE seq=3")
    v = s.verify_audit()
    assert not v["ok"] and v["broken_at_seq"] == 3


def test_claim_is_exclusive_and_expired_lease_requeues():
    s = Store()
    jid = s.submit("6789", "bell_selftest", {}, "t")
    a = s.claim("w1", lease_s=0.05)
    assert a and a["id"] == jid
    assert s.claim("w2") is None
    time.sleep(0.1)
    b = s.claim("w2")
    assert b and b["id"] == jid and b["attempts"] == 2


def test_emergency_stop_blocks_claims_and_worker():
    s = Store()
    s.submit("6789", "bell_selftest", {}, "t")
    s.set_stop(True, "admin", "test")
    w = Worker(s, name="w")
    assert w.step() is False and s.claim("x") is None
    assert s.workers()[0]["state"] == "STOPPED"
    s.set_stop(False, "admin", "test")
    assert w.step() is True
    assert s.counts() == {"DONE": 1}


def test_worker_records_failures_without_dying():
    s = Store()
    jid = s.submit("6789", "maxcut", {"n": 3, "edges": [[0, 0, 1]]}, "t")
    w = Worker(s, name="w")
    assert w.step()
    assert s.get(jid)["status"] == "FAILED"


def test_scheduler_submits_selftests_for_available_backends():
    s = Store()
    ids = Scheduler(s).tick()
    assert len(ids) == len(AVAILABLE)
    w = Worker(s, name="w")
    while w.step():
        pass
    results = [s.get(i)["result"] for i in ids]
    assert all(r["pass"] for r in results), results


# ------------------------------------------------------------ API
@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("SQZ_API_TOKEN", "api-test")
    monkeypatch.setenv("SQZ_ADMIN_TOKEN", "admin-test")
    app = create_app(Store(), run_worker=False)
    with TestClient(app) as c:
        yield c, app.state.store


API = {"Authorization": "Bearer api-test"}
ADMIN = {"Authorization": "Bearer admin-test"}


def test_api_fail_closed_without_tokens(monkeypatch):
    monkeypatch.delenv("SQZ_API_TOKEN", raising=False)
    with TestClient(create_app(Store())) as c:
        assert c.post("/jobs", json={"owner_id": "6789", "kind": "bell_selftest"},
                      headers={"Authorization": "Bearer x"}).status_code == 401


def test_api_job_lifecycle_and_validation(client):
    c, store = client
    assert c.post("/jobs", json={"owner_id": "6789", "kind": "bell_selftest"}).status_code == 401
    assert c.post("/jobs", json={"owner_id": "67a9", "kind": "bell_selftest"}, headers=API).status_code == 422
    bad = {"owner_id": "6789", "kind": "circuit", "payload": {"circuit": {"n_qubits": 30}}}
    assert c.post("/jobs", json=bad, headers=API).status_code == 422
    ok = {"owner_id": "6789", "kind": "circuit",
          "payload": {"circuit": bell().to_dict(), "backend": "numpy", "shots": 500, "seed": 1}}
    jid = c.post("/jobs", json=ok, headers=API).json()["job_id"]
    Worker(store, name="w").step()
    job = c.get(f"/jobs/{jid}", headers=API).json()
    assert job["status"] == "DONE" and sum(job["result"]["counts"].values()) == 500


def test_api_cmp_work_order(client):
    c, _ = client
    wo = {"work_order_id": "WO-6789-1", "task": "bell_selftest", "payload": {"backend": "numpy"},
          "requested_by": "87788"}
    r = c.post("/cmp/work-orders", json=wo, headers=API)
    assert r.status_code == 202 and r.json()["review"] == "REVIEW_REQUIRED"
    assert c.post("/cmp/work-orders", json={**wo, "target": "6776"}, headers=API).status_code == 422


def test_api_emergency_stop_requires_admin_and_blocks_submissions(client):
    c, _ = client
    assert c.post("/admin/emergency-stop", json={"reason": "drill"}, headers=API).status_code == 401
    assert c.post("/admin/emergency-stop", json={"reason": "drill"}, headers=ADMIN).status_code == 200
    assert c.post("/jobs", json={"owner_id": "6789", "kind": "bell_selftest"}, headers=API).status_code == 423
    assert c.get("/health/ready").status_code == 503
    assert c.post("/admin/resume", json={"reason": "drill done"}, headers=ADMIN).status_code == 200
    v = c.get("/audit/verify", headers=ADMIN).json()
    assert v["ok"] and v["checked"] >= 3


def test_mcp_tools_registered():
    from sqz import mcp_server

    r = mcp_server.sqz_bell_selftest("numpy")
    assert r["pass"]
    assert mcp_server.sqz_maxcut(3, [[0, 1, 1], [1, 2, 1]])["cut"] == 2
