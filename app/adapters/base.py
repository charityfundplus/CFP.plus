from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List
import hashlib
import json

from app.schemas import ExecutionEvent


class BaseProviderAdapter(ABC):
    def __init__(self, provider_name: str, model_name: str, config: Dict[str, Any]):
        self.provider_name = provider_name
        self.model_name = model_name
        self.config = config

    @abstractmethod
    def normalize_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def execute(self, normalized_request: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def normalize_response(self, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def verify_response(self, normalized_response: Dict[str, Any]) -> bool:
        raise NotImplementedError

    def dispatch(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        normalized_request = self.normalize_request(payload)
        raw_response = self.execute(normalized_request)
        normalized_response = self.normalize_response(raw_response)
        if not self.verify_response(normalized_response):
            raise ValueError("Provider response verification failed")
        return normalized_response

    def build_evidence(
        self,
        execution_id: str,
        work_order_id: str,
        request_data: Dict[str, Any],
        response_data: Dict[str, Any],
        events: List[ExecutionEvent],
        http_status: int,
        evidence_uri: str,
    ) -> Dict[str, Any]:
        def digest(value: Dict[str, Any]) -> str:
            canonical = json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                default=str,
            ).encode("utf-8")
            return hashlib.sha256(canonical).hexdigest()

        return {
            "execution_id": execution_id,
            "work_order_id": work_order_id,
            "provider": self.provider_name,
            "model": self.model_name,
            "request_hash": digest(request_data),
            "response_hash": digest(response_data),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "http_status": http_status,
            "execution_logs": [event.model_dump(mode="json") for event in events],
            "evidence_uri": evidence_uri,
            "status": "RECORDED",
        }
