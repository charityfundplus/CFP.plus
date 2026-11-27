import hashlib
import json
import multiprocessing
import os
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator, FormatChecker

from super_quantum_z import api
from super_quantum_z.api import app
from super_quantum_z.core import Experiment, run

from super_quantum_z.isolation import ExperimentFailed, ExperimentTimedOut, _await_result

SCHEMA = json.loads(Path(__file__).with_name("schema.json").read_text(encoding="utf-8"))
client = TestClient(app)


@pytest.mark.parametrize("backend", ["cirq", "qiskit", "pennylane"])
def test_bell_state(backend):
    report = run(Experiment(backend=backend))
    result = report["result"]
    evidence = report["evidence"]
    assert result["probabilities"] == [0.5, 0.0, 0.0, 0.5]
    assert result["expectation"] == {"XX": 1.0, "ZZ": 1.0}
    Draft202012Validator(SCHEMA, format_checker=FormatChecker()).validate(evidence)
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
    assert evidence["evidence_sha256"] == hashlib.sha256(encoded).hexdigest()
    assert evidence["backend_type"] == "simulator"


def test_classical_optimization():
    report = run(Experiment(backend="ortools"))
    assert report == {
        "result": {
            "backend": "ortools",
            "experiment": "bounded-integer-optimization",
            "execution_type": "classical_optimization",
            "solution": [7, 0],
            "objective": 14,
        }
    }


def test_sandbox_endpoint(monkeypatch):
    path = "/sandbox/experiment"
    payload = {"backend": "cirq"}
    monkeypatch.delenv("SUPER_QUANTUM_Z_SANDBOX_TOKEN", raising=False)
    assert client.post(path, json=payload).status_code == 503
    monkeypatch.setenv("SUPER_QUANTUM_Z_SANDBOX_TOKEN", "test-token")
    assert client.post(path, json=payload).status_code == 401

    headers = {"Authorization": "Bearer test-token"}
    assert client.post(path, headers=headers, json={"backend": "physical_qpu"}).status_code == 422
    response = client.post(path, headers=headers, json=payload)
    assert response.status_code == 200
    assert response.json()["result"]["probabilities"] == [0.5, 0.0, 0.0, 0.5]


def test_cudaq_endpoint(monkeypatch):
    import importlib.util

    monkeypatch.setenv("SUPER_QUANTUM_Z_SANDBOX_TOKEN", "test-token")
    response = client.post(
        "/sandbox/experiment",
        headers={"Authorization": "Bearer test-token"},
        json={"backend": "cudaq"},
    )
    if importlib.util.find_spec("cudaq") is None:
        assert response.status_code == 503
        return
    assert response.status_code == 200
    report = response.json()
    assert report["result"]["target"] == "qpp-cpu"
    assert report["result"]["probabilities"] == [0.5, 0.0, 0.0, 0.5]
    assert report["result"]["expectation"] == {"XX": 1.0, "ZZ": 1.0}
    Draft202012Validator(SCHEMA, format_checker=FormatChecker()).validate(report["evidence"])


def _blocked_child(request, reply):
    time.sleep(60)


def _crashed_child(request, reply):
    os._exit(1)


def test_timeout_reaps_child():
    before = {child.pid for child in multiprocessing.active_children()}
    started = time.monotonic()
    with pytest.raises(ExperimentTimedOut):
        _await_result(_blocked_child, Experiment(backend="cirq"), 0.5)
    assert time.monotonic() - started < 5
    assert {child.pid for child in multiprocessing.active_children()} <= before


def test_child_exit_without_result():
    with pytest.raises(ExperimentFailed):
        _await_result(_crashed_child, Experiment(backend="cirq"), 10)


def test_timeout_http_response_and_worker_slot_recovery(monkeypatch):
    def timeout(request):
        raise ExperimentTimedOut()

    monkeypatch.setenv("SUPER_QUANTUM_Z_SANDBOX_TOKEN", "test-token")
    headers = {"Authorization": "Bearer test-token"}
    with monkeypatch.context() as patch:
        patch.setattr(api, "execute_isolated", timeout)
        for _ in range(3):
            response = client.post("/sandbox/experiment", headers=headers, json={"backend": "ortools"})
            assert response.status_code == 504
    response = client.post("/sandbox/experiment", headers=headers, json={"backend": "ortools"})
    assert response.status_code == 200
    assert response.json()["result"]["objective"] == 14
