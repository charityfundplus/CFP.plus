from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_same_key_same_payload_returns_same_execution():
    payload = {
        "work_order_id": "WO-MVT-001",
        "provider": "gemini",
        "model": "gemini-mvt",
        "task": "Verify AI Coordination Pipeline",
        "payload": {"prompt": "ping"},
    }
    headers = {"Idempotency-Key": "mvt-idem-001"}

    first = client.post("/api/v1/work-orders", json=payload, headers=headers)
    second = client.post("/api/v1/work-orders", json=payload, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["execution_id"] == second.json()["execution_id"]


def test_same_key_different_payload_returns_409():
    headers = {"Idempotency-Key": "mvt-idem-002"}
    base = {
        "work_order_id": "WO-MVT-002",
        "provider": "gemini",
        "model": "gemini-mvt",
        "task": "Verify AI Coordination Pipeline",
        "payload": {"prompt": "ping"},
    }
    changed = {**base, "payload": {"prompt": "different"}}

    first = client.post("/api/v1/work-orders", json=base, headers=headers)
    second = client.post("/api/v1/work-orders", json=changed, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 409


def test_idempotency_key_is_required():
    payload = {
        "work_order_id": "WO-MVT-003",
        "provider": "gemini",
        "model": "gemini-mvt",
        "task": "Verify AI Coordination Pipeline",
        "payload": {"prompt": "ping"},
    }

    response = client.post("/api/v1/work-orders", json=payload)

    assert response.status_code == 400
