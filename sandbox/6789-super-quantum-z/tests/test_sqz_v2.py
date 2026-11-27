import os

import pytest
from fastapi.testclient import TestClient

from sqz import backends
from sqz.api import create_app
from sqz.backends import Backend, NumpyBackend, register
from sqz.executor import execute
from sqz.optimize import assign_brute, assign_tasks, maxcut_ortools, qaoa_maxcut
from sqz.store import Store
from sqz.worker import Worker

API = {"Authorization": "Bearer api-test"}


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("SQZ_API_TOKEN", "api-test")
    monkeypatch.setenv("SQZ_ADMIN_TOKEN", "admin-test")
    app = create_app(Store())
    with TestClient(app) as c:
        yield c, app.state.store


# ------------------------------------------------------------ phân loại tính toán
def test_nature_classification_is_explicit():
    assert execute("maxcut", {"n": 3, "edges": [[0, 1, 1]]})["nature"] == "CLASSICAL"
    assert execute("bell_selftest", {})["nature"] == "QUANTUM_SIMULATION"
    r = execute("qaoa_maxcut", {"n": 4, "edges": [[0, 1, 1], [1, 2, 1], [2, 3, 1], [3, 0, 1]], "grid": 8})
    assert r["nature"] == "HYBRID_SIMULATION"
    for b in backends.list_backends():
        assert b["nature"] == ("QPU" if b["kind"] == "QPU" else "QUANTUM_SIMULATION")


def test_cirq_is_default_when_installed():
    expected = "cirq" if backends.REGISTRY["cirq"].available() else "numpy"
    assert backends.default_backend() == expected
    assert execute("bell_selftest", {})["backend"] == expected


# ------------------------------------------------------------ QPU tắt mặc định
def test_qpu_lane_off_by_default_and_refuses_to_run(monkeypatch):
    monkeypatch.delenv("SQZ_QPU_ENABLED", raising=False)
    for name in ("ibm-quantum-qpu", "google-quantum-qpu"):
        assert backends.REGISTRY[name].info()["available"] is False
        with pytest.raises(PermissionError):
            backends.get(name)
    monkeypatch.setenv("SQZ_QPU_ENABLED", "1")
    with pytest.raises(PermissionError):
        backends.REGISTRY["ibm-quantum-qpu"].run(None)


def test_api_rejects_qpu_backend(client):
    c, _ = client
    r = c.post("/jobs", json={"owner_id": "6789", "kind": "bell_selftest",
                              "payload": {"backend": "ibm-quantum-qpu"}}, headers=API)
    assert r.status_code == 403


# ------------------------------------------------------------ adapter mở
def test_open_adapter_registration():
    class EchoNumpy(NumpyBackend):
        name = "plugin-numpy-test"

    if "plugin-numpy-test" not in backends.REGISTRY:
        register(EchoNumpy())
    assert execute("bell_selftest", {"backend": "plugin-numpy-test"})["pass"]
    with pytest.raises(ValueError):
        register(EchoNumpy())  # không cho trùng tên


# ------------------------------------------------------------ tối ưu thực tế + lai
def test_assign_tasks_optimal_matches_brute_force():
    costs = [[4, 2, None], [3, None, 1], [2, 5, 3], [None, 2, 2], [1, 3, 4]]
    capacity = [2, 2, 1]
    r = assign_tasks(costs, capacity)
    assert r["optimal"] and r["cost"] == assign_brute(costs, capacity)
    assert all(costs[t][k] is not None for t, k in enumerate(r["assignment"]))
    for k, cap in enumerate(capacity):
        assert r["assignment"].count(k) <= cap


def test_assign_tasks_infeasible_reported():
    r = assign_tasks([[1, None], [1, None]], [1, 1])
    assert r["cost"] is None and not r["optimal"]


def test_qaoa_hybrid_reaches_good_ratio_and_reports_optimum():
    edges = [[0, 1, 1], [1, 2, 1], [2, 3, 1], [3, 0, 1], [0, 2, 1]]
    r = qaoa_maxcut(4, edges, grid=16)
    assert r["classical_optimum"] == maxcut_ortools(4, edges)["cut"] == 4
    assert 0.6 < r["approximation_ratio"] <= 1.0
    assert r["best_sampled_cut"] == 4


# ------------------------------------------------------------ tích hợp Siêu Bộ Tam
def test_trio_shared_profile_for_any_id(client):
    c, _ = client
    for cid in ("6789", "6788", "6776", "87788", "0"):
        d = c.get(f"/trio/{cid}").json()
        assert d["shared_api"] and set(d["pillars"]) == {"6789", "6788", "6776"}
    assert c.get("/trio/67x").status_code == 422


def test_independent_review_by_6788(client):
    c, store = client
    jid = c.post("/jobs", json={"owner_id": "6789", "kind": "bell_selftest"}, headers=API).json()["job_id"]
    body = {"reviewer_id": "6788", "verdict": "APPROVED", "note": "Bell 00/11"}
    assert c.post(f"/jobs/{jid}/review", json=body, headers=API).status_code == 409  # chưa chạy
    Worker(store, name="w").step()
    assert c.post(f"/jobs/{jid}/review", json={**body, "reviewer_id": "6789"}, headers=API).status_code == 403
    assert c.post(f"/jobs/{jid}/review", json=body, headers=API).status_code == 200
    assert c.get(f"/jobs/{jid}/reviews", headers=API).json()[0]["reviewer_id"] == "6788"


def test_evidence_report_for_6776(client):
    c, store = client
    from sqz.worker import Scheduler

    Scheduler(store).tick()
    w = Worker(store, name="w")
    while w.step():
        pass
    ev = c.get("/evidence", headers=API).json()
    assert ev["audit"]["ok"] and ev["emergency_stop"] is False
    assert all(v["pass"] == v["runs"] for v in ev["bell_selftests"].values())
    assert "QPU TẮT" in ev["nature_note"]


# ------------------------------------------------------------ PostgreSQL (CI)
@pytest.mark.skipif(not os.getenv("SQZ_TEST_DATABASE_URL"), reason="cần SQZ_TEST_DATABASE_URL")
def test_postgres_store_queue_and_audit():
    s = Store(os.environ["SQZ_TEST_DATABASE_URL"])
    assert s.backend == "postgresql"
    jid = s.submit("6789", "bell_selftest", {}, "pg-test")
    w = Worker(s, name="pg-w")
    while w.step():
        pass
    assert s.get(jid)["status"] == "DONE"
    assert s.claim("other") is None
    assert s.verify_audit()["ok"]
