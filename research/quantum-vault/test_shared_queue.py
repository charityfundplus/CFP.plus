import hashlib
import json
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from super_quantum_z.api import app
from super_quantum_z.core import Experiment
from super_quantum_z.queue import Queue
from super_quantum_z.worker import work_once


class Clock:
    now = 1000

    def __call__(self):
        return self.now


def test_worker_disconnect_restart_and_fenced_result(tmp_path):
    clock = Clock()
    db = tmp_path / "queue.db"
    queue = Queue(db, clock)
    job = queue.submit("0229", "WO-1", Experiment(backend="cirq"))
    first = queue.claim()
    clock.now += 10
    recovered = Queue(db, clock)
    assert not recovered.heartbeat(job, first["session"])
    assert recovered.claim() is None
    clock.now += 2
    second = recovered.claim()
    assert second["job"] == job
    assert second["session"] != first["session"]
    assert not queue.finish(job, first["session"], {"stale": True})
    assert recovered.finish(job, second["session"], {"ok": True})
    assert not queue.finish(job, second["session"], {"duplicate": True})
    evidence = recovered.evidence("0229", job)
    assert evidence["digest"] == hashlib.sha256(b'{"ok":true}').hexdigest()
    assert [event["event"] for event in evidence["audit"]] == [
        "submitted", "claimed", "lease_lost", "claimed", "result_committed",
    ]


def test_heartbeat_cannot_extend_deadline(tmp_path):
    clock = Clock()
    queue = Queue(tmp_path / "queue.db", clock)
    experiment = Experiment(backend="cirq")
    job = queue.submit("6789", "WO-1", experiment)
    pending = queue.submit("6789", "WO-2", experiment)
    clock.now += 115
    claim = queue.claim()
    assert queue.heartbeat(job, claim["session"])
    clock.now += 5
    assert not queue.finish(job, claim["session"], {"late": True})
    assert queue.status()["jobs"] == {"expired": 2}
    assert queue.evidence("6789", pending)["state"] == "expired"


def test_emergency_stop_persists_across_restart(tmp_path):
    db = tmp_path / "queue.db"
    queue = Queue(db)
    work = Experiment(backend="cirq")
    first = queue.submit("6789", "WO-1", work)
    second = queue.submit("6789", "WO-2", work)
    claim = queue.claim()
    queue.set_stop(True)
    restarted = Queue(db)
    assert restarted.claim() is None
    assert not restarted.heartbeat(first, claim["session"])
    assert not restarted.finish(first, claim["session"], {"late": True})
    assert restarted.evidence("6789", second)["state"] == "cancelled"
    restarted.set_stop(False)
    assert restarted.claim() is None
    assert restarted.submit("6789", "WO-3", work) != first


def test_concurrent_replay_and_claim_limit(tmp_path):
    queue = Queue(tmp_path / "queue.db")
    work = Experiment(backend="cirq")
    with ThreadPoolExecutor(8) as pool:
        jobs = list(pool.map(lambda _: queue.submit("6789", "WO-1", work), range(8)))
        assert len(set(jobs)) == 1
        for index in range(2, 5):
            queue.submit("6789", f"WO-{index}", work)
        claims = list(pool.map(lambda _: queue.claim(), range(8)))
    assert len({claim["job"] for claim in claims if claim}) == 2
    assert claims.count(None) == 6


def test_retry_exhaustion(tmp_path):
    clock = Clock()
    queue = Queue(tmp_path / "queue.db", clock)
    job = queue.submit("6789", "WO", Experiment(backend="cirq"))
    for delay in (2, 4, 8):
        claim = queue.claim()
        assert queue.finish(job, claim["session"])
        clock.now += delay
    assert queue.claim() is None
    assert queue.evidence("6789", job)["state"] == "failed"


def test_cmp_access_and_real_worker(tmp_path, monkeypatch):
    db = tmp_path / "queue.db"
    setup = tmp_path / "sandbox.json"
    setup.write_text(json.dumps({"database": str(db), "principals": {
        "0229": {"token": "a" * 32, "backends": ["ortools"]},
        "6789": {"token": "b" * 32, "backends": ["cirq"]},
    }}))
    monkeypatch.setenv("SUPER_QUANTUM_Z_QUEUE_CONFIG", str(setup))
    request = {"work_order_id": "CMP-1", "experiment": {"backend": "ortools"}}
    headers = {"Authorization": "Bearer " + "a" * 32}
    client = TestClient(app)
    route = "/sandbox/cmp/0229/work-orders"
    assert client.post("/sandbox/experiment", json={"backend": "ortools"}).status_code == 503
    assert client.post(route, json=request).status_code == 403
    response = client.post(route, headers=headers, json=request)
    assert response.status_code == 202
    job = response.json()["job"]
    assert client.post(route, headers=headers, json=request).json()["job"] == job
    assert work_once(Queue(db))
    evidence = client.get(f"/sandbox/cmp/0229/evidence/{job}", headers=headers).json()
    assert evidence["owner"] == "0229"
    assert evidence["result"]["result"]["objective"] == 14
    assert client.get(f"/sandbox/cmp/6789/evidence/{job}", headers={
        "Authorization": "Bearer " + "b" * 32,
    }).status_code == 404
    assert client.post(route, headers=headers, json={
        "work_order_id": "CMP-2", "experiment": {"backend": "cirq"},
    }).status_code == 403


def test_coverage_preserves_leading_zero_and_overlaps(monkeypatch):
    from super_quantum_z import coverage

    def git_response(args, **kwargs):
        command = args[1:]
        if command[0] == "rev-parse":
            return command[-1]
        if command[0] == "ls-tree":
            return "0229/index.html\nregistry/691181.md\n"
        if command[-1].endswith(coverage.TRIO_INDEX):
            return "| `0229` | Day |\n| `0229` | Second record |\n"
        if command[-1].endswith(coverage.TRIO_ADDITIONS):
            return '{"records":[]}'
        return '{"691181":{"id":"691181"}}'

    monkeypatch.setattr(coverage.subprocess, "check_output", git_response)
    result = coverage.inventory("registry", "trio")
    assert len(result["groups"]) == 5
    rows = result["records"]
    assert sum("Ngày" in row["roles"] for row in rows.values()) == 366
    assert rows["0229"]["roles"] == ["Ngày", "Chuyên trách"]
    assert rows["0229"]["status"] == "review_overlap"
    assert rows["5"]["roles"] == ["Chương", "V"]
    assert rows["500"]["roles"] == ["Cháu", "D"]
    assert rows["691181"]["roles"] == ["Chuyên trách"]
