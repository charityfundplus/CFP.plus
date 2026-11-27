"""FastAPI • CMP Work Order • quản trị Emergency Stop. Fail-closed khi thiếu token."""

from __future__ import annotations

import hmac
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from . import __version__, backends
from .circuit import Circuit, CircuitError, check_shots
from .ids import InvalidID, classify
from .store import Store
from .worker import Scheduler, Worker

from .executor import KINDS


class JobIn(BaseModel):
    owner_id: str = Field(description="ID Số CFP+ hiện hữu của bên gửi (không cấp mới)")
    kind: str
    payload: dict[str, Any] = Field(default_factory=dict)


class WorkOrderIn(BaseModel):
    """Định dạng CMP Work Order rút gọn, tương thích cfp-gateway."""

    work_order_id: str
    source: str = "CMP"
    target: str = "6789"
    task: str
    payload: dict[str, Any] = Field(default_factory=dict)
    requested_by: str


class ReviewIn(BaseModel):
    reviewer_id: str
    verdict: str = Field(pattern="^(APPROVED|REJECTED|NEEDS_CHANGES)$")
    note: str = Field(default="", max_length=2000)


TRIO = {
    "6789": {"pillar": "Siêu Lượng Tử ⚛️ Super Quantum", "role": "compute",
             "link": "https://app.notion.com/p/422caac9a55781c98cb5c45475451edd"},
    "6788": {"pillar": "Siêu Trí Tuệ SI 🤖 AI 🤖", "role": "review",
             "link": "https://app.notion.com/p/422caac9a55781ef8eb7cff6c4752c9e"},
    "6776": {"pillar": "Siêu Phần Mềm • Super Software", "role": "operate",
             "link": "https://app.notion.com/p/422caac9a55781d5894efeac6f83f6f1"},
}


class StopIn(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


def _token_dep(env_name: str):
    def check(authorization: str = Header(default="")) -> str:
        expected = os.getenv(env_name, "")
        supplied = authorization.removeprefix("Bearer ").strip()
        if not expected or not supplied or not hmac.compare_digest(supplied, expected):
            raise HTTPException(status_code=401, detail="Unauthorized")
        return env_name

    return check


def _validate(kind: str, owner_id: str, payload: dict) -> None:
    try:
        classify(owner_id)
    except InvalidID as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if kind not in KINDS:
        raise HTTPException(status_code=422, detail=f"kind phải thuộc {sorted(KINDS)}")
    try:
        if kind == "circuit":
            Circuit.from_dict(payload["circuit"])
            check_shots(int(payload.get("shots", 1000)))
        if kind in ("circuit", "bell_selftest", "qaoa_maxcut"):
            backends.get(payload.get("backend") or backends.default_backend())
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except (CircuitError, KeyError, RuntimeError, ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def create_app(store: Store | None = None, *, run_worker: bool = False,
               scheduler_interval_s: float | None = None) -> FastAPI:
    store = store or Store(os.getenv("SQZ_DATABASE_URL") or os.getenv("SQZ_DB_PATH", ":memory:"))
    threads: list = []

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        store.audit("system", "STARTUP", {"version": __version__})
        if run_worker:
            threads.append(Worker(store))
        if scheduler_interval_s:
            threads.append(Scheduler(store, scheduler_interval_s))
        for t in threads:
            t.start()
        try:
            yield
        finally:
            for t in threads:
                t.stop()
            store.audit("system", "SHUTDOWN", {})

    app = FastAPI(title="CFP+ 6789 Super Quantum Z Core", version=__version__, lifespan=lifespan)
    app.state.store = store
    app.state.threads = threads
    api = Depends(_token_dep("SQZ_API_TOKEN"))
    admin = Depends(_token_dep("SQZ_ADMIN_TOKEN"))

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "service": "sqz-6789", "version": __version__}

    @app.get("/health/ready")
    def ready() -> dict:
        store.ping()
        alive = [w for w in store.workers() if w["alive"]]
        state = "STOPPED" if store.stopped() else ("READY" if alive or not run_worker else "DEGRADED")
        body = {"state": state, "db": store.backend, "workers_alive": len(alive), "jobs": store.counts()}
        if state != "READY":
            raise HTTPException(status_code=503, detail=body)
        return body

    @app.get("/backends")
    def list_backends() -> list[dict]:
        return backends.list_backends()

    @app.post("/jobs", status_code=202, dependencies=[api])
    def submit(job: JobIn) -> dict:
        if store.stopped():
            raise HTTPException(status_code=423, detail="EMERGENCY_STOP đang bật")
        _validate(job.kind, job.owner_id, job.payload)
        return {"job_id": store.submit(job.owner_id, job.kind, job.payload, f"api:{job.owner_id}"),
                "status": "QUEUED"}

    @app.get("/jobs/{job_id}", dependencies=[api])
    def get_job(job_id: str) -> dict:
        j = store.get(job_id)
        if j is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy Job")
        return j

    @app.post("/cmp/work-orders", status_code=202, dependencies=[api])
    def cmp_work_order(wo: WorkOrderIn) -> dict:
        if wo.target != "6789":
            raise HTTPException(status_code=422, detail="Work Order không dành cho 6789")
        job = submit(JobIn(owner_id=wo.requested_by, kind=wo.task, payload=wo.payload))
        store.audit(f"cmp:{wo.requested_by}", "CMP_WORK_ORDER_ACCEPTED",
                    {"work_order_id": wo.work_order_id, "job": job["job_id"]})
        return {"work_order_id": wo.work_order_id, **job, "review": "REVIEW_REQUIRED"}

    @app.post("/admin/emergency-stop", dependencies=[admin])
    def emergency_stop(body: StopIn) -> dict:
        store.set_stop(True, "admin", body.reason)
        return {"emergency_stop": True}

    @app.post("/admin/resume", dependencies=[admin])
    def resume(body: StopIn) -> dict:
        store.set_stop(False, "admin", body.reason)
        return {"emergency_stop": False}

    @app.get("/audit/verify", dependencies=[admin])
    def audit_verify() -> dict:
        return store.verify_audit()

    @app.post("/jobs/{job_id}/review", dependencies=[api])
    def review(job_id: str, body: ReviewIn) -> dict:
        """6788 • Siêu Trí Tuệ (hoặc reviewer khác chủ trì) ghi kết luận độc lập."""
        try:
            classify(body.reviewer_id)
            return store.review(job_id, body.reviewer_id, body.verdict, body.note)
        except InvalidID as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Không tìm thấy Job") from exc
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/jobs/{job_id}/reviews", dependencies=[api])
    def job_reviews(job_id: str) -> list[dict]:
        return store.reviews_of(job_id)

    @app.get("/trio/{cfp_id}")
    def trio(cfp_id: str) -> dict:
        """Hồ sơ dùng chung cho mọi ID Siêu Bộ Tam: một API, không cài riêng từng ID."""
        try:
            info = classify(cfp_id)
        except InvalidID as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {**info, "pillars": TRIO, "shared_api": True,
                "principle": "3 Trong 1 • Một ID • Một Link Mẫu • Chung Kho Tri Thức"}

    @app.get("/evidence", dependencies=[api])
    def evidence() -> dict:
        """6776 • Siêu Phần Mềm: báo cáo vận hành có thể đối chiếu (Evidence First)."""
        tests = [j for j in store.recent("bell_selftest", 200) if j["status"] == "DONE"]
        per: dict[str, dict] = {}
        for j in tests:
            r = j["result"]
            d = per.setdefault(r["backend"], {"runs": 0, "pass": 0, "last_at": 0})
            d["runs"] += 1
            d["pass"] += int(r["pass"])
            d["last_at"] = max(d["last_at"], j["updated_at"])
        return {"version": __version__, "storage": store.backend, "emergency_stop": store.stopped(),
                "jobs": store.counts(), "workers": store.workers(), "bell_selftests": per,
                "backends": backends.list_backends(), "audit": store.verify_audit(),
                "nature_note": "Kết quả lượng tử là MÔ PHỎNG; QPU TẮT"}

    @app.get("/workers", dependencies=[api])
    def workers() -> list[dict]:
        return store.workers()

    return app


def app_from_env() -> FastAPI:
    return create_app(run_worker=os.getenv("SQZ_WORKER", "1") == "1",
                      scheduler_interval_s=float(os.getenv("SQZ_SELFTEST_INTERVAL_S", "300")) or None)
