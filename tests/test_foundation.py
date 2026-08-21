from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.adapters.gemini import GeminiProviderAdapter
from app.api.work_orders import _IDEMPOTENCY_STORE
from app.main import app

client = TestClient(app)


def setup_function():
    _IDEMPOTENCY_STORE.clear()


def test_health_keeps_verification_labels_no():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["technical_integration_verified"] == "NO"
    assert response.json()["automation_verified"] == "NO"


def test_created_at_is_timezone_aware_utc():
    response = client.post(
        "/api/v1/work-orders",
        json={
            "work_order_id": "WO-MVT-TIME-001",
            "provider": "gemini",
            "model": "gemini-mvt",
            "task": "Verify timestamp policy",
            "payload": {"prompt": "ping"},
        },
        headers={"Idempotency-Key": "mvt-time-001"},
    )

    assert response.status_code == 201
    created_at = datetime.fromisoformat(response.json()["created_at"])
    assert created_at.tzinfo is not None
    assert created_at.utcoffset().total_seconds() == 0


def test_gemini_adapter_fails_closed_without_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    adapter = GeminiProviderAdapter(model_name="gemini-mvt", config={})
    normalized = adapter.normalize_request({"prompt": "ping"})

    with pytest.raises(RuntimeError, match="TECHNICAL INTEGRATION VERIFIED: NO"):
        adapter.execute(normalized)
