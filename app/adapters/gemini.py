import os
import random
import re
import time
from threading import Lock
from typing import Any, Dict

import httpx

from app.adapters.base import BaseProviderAdapter


class GeminiProviderAdapter(BaseProviderAdapter):
    """Gemini REST adapter for the P0 MVT.

    Secrets are runtime-only and must never be included in request/response
    evidence. Verification remains NO until a real end-to-end MVT is executed.
    """

    API_ROOT = "https://generativelanguage.googleapis.com/v1beta/models"
    RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}

    def __init__(self, model_name: str, config: Dict[str, Any]):
        super().__init__(provider_name="gemini", model_name=model_name, config=config)
        if not re.fullmatch(r"[A-Za-z0-9._-]+", model_name):
            raise ValueError("Invalid Gemini model name")

        self.api_key = config.get("api_key") or os.getenv("GEMINI_API_KEY")
        self.timeout_seconds = float(config.get("timeout_seconds", 20.0))
        self.max_retries = int(config.get("max_retries", 3))
        self.backoff_base_seconds = float(config.get("backoff_base_seconds", 1.0))
        self.min_interval_seconds = float(config.get("min_interval_seconds", 0.0))
        self._rate_lock = Lock()
        self._last_request_at = 0.0

        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if not 0 <= self.max_retries <= 8:
            raise ValueError("max_retries must be between 0 and 8")
        if self.min_interval_seconds < 0:
            raise ValueError("min_interval_seconds cannot be negative")

    def normalize_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        prompt = payload.get("prompt", "")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Gemini payload requires a non-empty prompt")

        return {
            "contents": [{"role": "user", "parts": [{"text": prompt.strip()}]}],
            "generationConfig": {
                "temperature": payload.get("temperature", 0.2),
            },
        }

    def _apply_local_rate_limit(self) -> None:
        if self.min_interval_seconds == 0:
            return
        with self._rate_lock:
            now = time.monotonic()
            remaining = self.min_interval_seconds - (now - self._last_request_at)
            if remaining > 0:
                time.sleep(remaining)
            self._last_request_at = time.monotonic()

    def _retry_delay(self, attempt: int, response: httpx.Response | None = None) -> float:
        if response is not None:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    return min(float(retry_after), 60.0)
                except ValueError:
                    pass
        exponential = self.backoff_base_seconds * (2**attempt)
        jitter = random.uniform(0, min(0.5, exponential * 0.25))
        return min(exponential + jitter, 60.0)

    def execute(self, normalized_request: Dict[str, Any]) -> Dict[str, Any]:
        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured. "
                "TECHNICAL INTEGRATION VERIFIED: NO; AUTOMATION VERIFIED: NO."
            )

        url = f"{self.API_ROOT}/{self.model_name}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }

        last_error: Exception | None = None
        with httpx.Client(timeout=self.timeout_seconds) as client:
            for attempt in range(self.max_retries + 1):
                self._apply_local_rate_limit()
                try:
                    response = client.post(url, headers=headers, json=normalized_request)
                except (httpx.TimeoutException, httpx.NetworkError) as exc:
                    last_error = exc
                    if attempt >= self.max_retries:
                        raise
                    time.sleep(self._retry_delay(attempt))
                    continue

                if response.status_code in self.RETRYABLE_STATUS and attempt < self.max_retries:
                    time.sleep(self._retry_delay(attempt, response))
                    continue

                response.raise_for_status()
                body = response.json()
                body["_cfp_http_status"] = response.status_code
                return body

        if last_error is not None:
            raise last_error
        raise RuntimeError("Gemini execution failed without a response")

    def normalize_response(self, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        candidates = raw_response.get("candidates", [])
        if not candidates:
            return {
                "output_text": "",
                "finish_reason": None,
                "http_status": raw_response.get("_cfp_http_status"),
            }

        candidate = candidates[0]
        parts = candidate.get("content", {}).get("parts", [])
        text_output = "".join(
            part.get("text", "") for part in parts if isinstance(part, dict)
        )
        return {
            "output_text": text_output,
            "finish_reason": candidate.get("finishReason"),
            "http_status": raw_response.get("_cfp_http_status"),
        }

    def verify_response(self, normalized_response: Dict[str, Any]) -> bool:
        return (
            normalized_response.get("http_status") == 200
            and bool(normalized_response.get("output_text"))
        )
