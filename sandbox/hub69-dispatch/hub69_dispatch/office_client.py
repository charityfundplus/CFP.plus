"""HTTP client for the PR #195 Office API (CMP 267 / Văn Phòng SI AI). Stdlib only.

Reuses the #195 contract as-is: cookie session from /api/auth/login, CSRF header ``X-CFP-Forum: 1``,
``/api/office/tasks`` (+ /ack /start /evidence /submit /review), idempotency_key on task creation.
Nothing here bypasses #195 authorisation: every call runs as the logged-in sandbox account.

Retry policy (safe because every write is either idempotent at the server or re-checked by the caller):
  • connection refused / reset / timeout, HTTP 502/503/504 → retry with exponential backoff
  • HTTP 429 → retry after ``Retry-After`` (bounded)
  • any other 4xx → no retry (OfficeError.permanent = True); the autopilot dead-letters or reconciles
"""
from __future__ import annotations

import http.cookiejar
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

CSRF = {"X-CFP-Forum": "1"}
RETRY_STATUS = {502, 503, 504}


class OfficeError(Exception):
    def __init__(self, status: int | None, detail: str, permanent: bool):
        super().__init__(f"{status}: {detail}")
        self.status, self.detail, self.permanent = status, detail, permanent


@dataclass
class RetryPolicy:
    attempts: int = 4
    base_delay: float = 0.5
    max_delay: float = 8.0


class OfficeClient:
    def __init__(self, base: str, *, retry: RetryPolicy | None = None, sleep=time.sleep, transport=None,
                 log=None):
        self.base = base.rstrip("/")
        self.retry = retry or RetryPolicy()
        self.sleep = sleep
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.transport = transport  # test hook: callable(method, path) raising to inject faults
        self.log = log or (lambda *_: None)
        self.user: dict | None = None

    # ---------------------------------------------------------------- raw
    def _once(self, method: str, path: str, body: dict | None):
        if self.transport:
            self.transport(method, path)
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method)
        req.add_header("Accept", "application/json")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        if method != "GET":
            req.add_header("X-CFP-Forum", "1")
        try:
            with self.opener.open(req, timeout=20) as r:  # noqa: S310 (operator-configured sandbox base URL)
                raw = r.read()
                return r.status, (json.loads(raw) if raw else None), {}
        except urllib.error.HTTPError as e:
            raw = e.read()
            try:
                payload = json.loads(raw) if raw else None
            except ValueError:
                payload = {"detail": raw[:200].decode(errors="replace")}
            return e.code, payload, dict(e.headers or {})

    def request(self, method: str, path: str, body: dict | None = None, ok=(200, 201)) -> dict:
        last = None
        for attempt in range(1, self.retry.attempts + 1):
            try:
                status, payload, headers = self._once(method, path, body)
            except (urllib.error.URLError, ConnectionError, TimeoutError, OSError) as e:
                last = OfficeError(None, f"transport: {e}", permanent=False)
                self.log("retry", {"method": method, "path": path, "attempt": attempt, "error": str(last)})
            else:
                if status in ok:
                    return payload
                detail = (payload or {}).get("detail") if isinstance(payload, dict) else str(payload)
                if status == 429 or status in RETRY_STATUS:
                    last = OfficeError(status, str(detail), permanent=False)
                    self.log("retry", {"method": method, "path": path, "attempt": attempt, "status": status})
                    if status == 429:
                        wait = float(headers.get("Retry-After") or headers.get("retry-after") or 1)
                        if attempt < self.retry.attempts:
                            self.sleep(min(wait, self.retry.max_delay))
                        continue
                else:
                    raise OfficeError(status, str(detail), permanent=True)
            if attempt < self.retry.attempts:
                self.sleep(min(self.retry.base_delay * 2 ** (attempt - 1), self.retry.max_delay))
        raise last  # type: ignore[misc]

    def get(self, path: str) -> dict:
        return self.request("GET", path)

    def post(self, path: str, body: dict | None = None, ok=(200, 201)) -> dict:
        return self.request("POST", path, body if body is not None else {}, ok=ok)

    # ---------------------------------------------------------------- session
    def login(self, email: str, password: str, *, register_name: str | None = None) -> dict:
        """Log in; in the sandbox, register first if the account does not exist yet (409 = already exists)."""
        if register_name:
            try:
                self.user = self.post("/api/auth/register", {"email": email, "password": password,
                                                             "name": register_name})
                return self.user
            except OfficeError as e:
                if e.status != 409:
                    raise
        self.user = self.post("/api/auth/login", {"email": email, "password": password}, ok=(200,))
        return self.user

    def health(self) -> dict:
        return self.get("/api/health")
