from fastapi.testclient import TestClient

from app.api.work_orders import _IDEMPOTENCY_STORE
from app.main import app

client = TestClient(app)


def setup_function():
    _IDEMPOTENCY_STORE.clear()


def _payload(work_order_id: str, prompt: str = "ping") -> dict:
    return {
        "work_order_id": work_order_id,
        "provider": "gemini",
        "model": "gemini-mvt",
        "task": "Verify AI Coordination Pipeline",
        "payload": {"prompt": prompt},
    }


def test_same_key_same_payload_returns_same_execution():
    payload = _payload("WO-MVT-001")
    headers = {"Idempotency-Key": "mvt-idem-001"}

    first = client.post("/api/v1/work-orders", json=payload, headers=headers)
    second = client.post("/api/v1/work-orders", json=payload, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["execution_id"] == second.json()["execution_id"]


def test_same_key_different_payload_returns_409():
    headers = {"Idempotency-Key": "mvt-idem-002"}
    first = client.post(
        "/api/v1/work-orders",
        json=_payload("WO-MVT-002", "ping"),
        headers=headers,
    )
    second = client.post(
        "/api/v1/work-orders",
        json=_payload("WO-MVT-002", "different"),
        headers=headers,
    )

    assert first.status_code == 201
    assert second.status_code == 409


def test_idempotency_key_is_required():
    response = client.post("/api/v1/work-orders", json=_payload("WO-MVT-003"))
    assert response.status_code == 400


def test_client_cannot_disable_evidence_collection():
    payload = _payload("WO-MVT-004")
    payload["evidence_required"] = False

    response = client.post(
        "/api/v1/work-orders",
        json=payload,
        headers={"Idempotency-Key": "mvt-idem-004"},
    )

    assert response.status_code == 422
