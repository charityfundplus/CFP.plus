"""FastAPI • CMP Work Order • quản trị Emergency Stop. Fail-closed khi thiếu token."""

from __future__ import annotations

import hmac
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from . import __version__, backends
from .circuit import Circuit, CircuitError, check_shots
from .ids import InvalidID, classify
from .store import Store
from .ops6776 import EVIDENCE_SCHEMA, backup, validate_evidence, watchdog
from .si6788 import EvalCase, evaluate_response, verify_job
from .worker import Scheduler, Worker

from .executor import KINDS
from .validate import validate_payload

MAX_BODY_BYTES = int(os.getenv("SQZ_MAX_BODY_BYTES", "1000000"))


def _identity_map() -> dict[str, str]:
    """SQZ_IDENTITY_TOKENS="6788:tokA,87728:tokB" → {token: id}. Trống = chế độ token chung (chưa xác thực danh tính)."""
    out: dict[str, str] = {}
    for part in filter(None, (p.strip() for p in os.getenv("SQZ_IDENTITY_TOKENS", "").split(","))):
        cfp_id, _, tok = part.partition(":")
        if cfp_id and tok:
            out[tok] = cfp_id
    return out


def _caller(authorization: str = Header(default="")) -> str | None:
    """ID Số gắn với token (nếu bật SQZ_IDENTITY_TOKENS), dùng cho owner/reviewer."""
    supplied = authorization.removeprefix("Bearer ").strip()
    for tok, cfp_id in _identity_map().items():
        if supplied and hmac.compare_digest(supplied, tok):
            return cfp_id
    return None


def _bind_identity(claimed: str, caller: str | None) -> bool:
    """Trả True nếu danh tính đã xác thực. Khi bật chế độ danh tính, ID khai báo phải khớp token."""
    if not _identity_map():
        return False
    if caller != claimed:
        raise HTTPException(status_code=403, detail="ID khai báo không khớp token (chống mạo danh reviewer/owner)")
    return True


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


class EvalIn(BaseModel):
    response: str = Field(max_length=20000)
    expected_id: str
    allowed_sources: list[str] = Field(min_length=1, max_length=20)
    require_bilingual: bool = True


class StopIn(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


def _token_dep(env_name: str):
    def check(authorization: str = Header(default="")) -> str:
        expected = os.getenv(env_name, "")
        supplied = authorization.removeprefix("Bearer ").strip()
        if env_name == "SQZ_API_TOKEN" and supplied and _caller(authorization):
            return env_name  # token danh tính riêng cũng là API token hợp lệ
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
        validate_payload(kind, payload)
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

    @app.middleware("http")
    async def body_limit(request: Request, call_next):
        size = request.headers.get("content-length")
        if size is not None and size.isdigit() and int(size) > MAX_BODY_BYTES:
            return JSONResponse({"detail": f"Body vượt {MAX_BODY_BYTES} byte"}, status_code=413)
        return await call_next(request)

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
    def submit(job: JobIn, caller: str | None = Depends(_caller)) -> dict:
        if store.stopped():
            raise HTTPException(status_code=423, detail="EMERGENCY_STOP đang bật")
        _validate(job.kind, job.owner_id, job.payload)
        verified = _bind_identity(job.owner_id, caller)
        return {"job_id": store.submit(job.owner_id, job.kind, job.payload, f"api:{job.owner_id}"),
                "status": "QUEUED", "identity_verified": verified}

    @app.get("/jobs/{job_id}", dependencies=[api])
    def get_job(job_id: str) -> dict:
        j = store.get(job_id)
        if j is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy Job")
        j["integrity"] = store.verify_job(job_id)
        return j

    @app.post("/cmp/work-orders", status_code=202, dependencies=[api])
    def cmp_work_order(wo: WorkOrderIn, caller: str | None = Depends(_caller)) -> dict:
        if wo.target != "6789":
            raise HTTPException(status_code=422, detail="Work Order không dành cho 6789")
        existing = store.work_order_job(wo.work_order_id)
        if existing:  # idempotent: gửi lại cùng Work Order không tạo Job trùng
            return {"work_order_id": wo.work_order_id, "job_id": existing, "duplicate": True,
                    "status": store.get(existing)["status"], "review": "REVIEW_REQUIRED"}
        job = submit(JobIn(owner_id=wo.requested_by, kind=wo.task, payload=wo.payload), caller)
        bound = store.bind_work_order(wo.work_order_id, job["job_id"])
        if bound != job["job_id"]:  # thua cuộc đua: Job vừa tạo bị hủy về FAILED, trả Job đã gắn
            store.cancel(job["job_id"], "duplicate work order")
            return {"work_order_id": wo.work_order_id, "job_id": bound, "duplicate": True,
                    "status": store.get(bound)["status"], "review": "REVIEW_REQUIRED"}
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
    def review(job_id: str, body: ReviewIn, caller: str | None = Depends(_caller)) -> dict:
        """6788 • Siêu Trí Tuệ (hoặc reviewer khác chủ trì) ghi kết luận độc lập."""
        try:
            classify(body.reviewer_id)
            verified = _bind_identity(body.reviewer_id, caller)
            return {**store.review(job_id, body.reviewer_id, body.verdict, body.note),
                    "identity_verified": verified}
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

    # ------------------------------------------------------------ 6788 • Siêu Trí Tuệ
    @app.post("/si/evaluate", dependencies=[api])
    def si_evaluate(body: EvalIn) -> dict:
        """Chấm câu trả lời của một Agent theo bài nghiệm thu 6788 (danh tính, nguồn, song ngữ, chống phóng đại)."""
        try:
            r = evaluate_response(body.response, EvalCase(body.expected_id, body.allowed_sources,
                                                          body.require_bilingual))
        except InvalidID as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        store.audit("si:6788", "AGENT_EVALUATED", {"expected_id": body.expected_id, "pass": r["pass"],
                                                   "score": r["score"]})
        return r

    @app.post("/si/verify/{job_id}", dependencies=[api])
    def si_verify(job_id: str) -> dict:
        """6788 chạy lại độc lập (khác backend/thuật toán) và ghi review nếu chủ trì khác 6788."""
        job = store.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy Job")
        v = verify_job(job)
        recorded = None
        if job["owner_id"] != "6788" and job["status"] in ("DONE", "FAILED"):
            try:
                recorded = store.review(job_id, "6788", v["verdict"],
                                        f"AUTOMATED • {v['method']} • {v['details']}")
            except ValueError:  # 6788 đã review Job này: mỗi reviewer một lần → không ghi trùng
                recorded = None
        return {**v, "job_id": job_id, "review_recorded": bool(recorded)}

    # ------------------------------------------------------------ 6776 • Siêu Phần Mềm
    @app.get("/evidence/schema")
    def evidence_schema() -> dict:
        return EVIDENCE_SCHEMA

    @app.post("/evidence/validate")
    def evidence_validate(report: dict) -> dict:
        return validate_evidence(report)

    @app.get("/ops/watchdog", dependencies=[api])
    def ops_watchdog() -> dict:
        r = watchdog(store, stale_s=30.0)
        if r["status"] != "OK":
            store.audit("ops:6776", "WATCHDOG_ALERT", {"status": r["status"],
                                                       "codes": [a["code"] for a in r["alerts"]]})
        return r

    @app.get("/ops/backup", dependencies=[admin])
    def ops_backup() -> dict:
        snap = backup(store)
        store.audit("ops:6776", "BACKUP_EXPORTED", {"sha256": snap["sha256"]})
        return snap

    @app.get("/workers", dependencies=[api])
    def workers() -> list[dict]:
        return store.workers()

    return app


def app_from_env() -> FastAPI:
    return create_app(run_worker=os.getenv("SQZ_WORKER", "1") == "1",
                      scheduler_interval_s=float(os.getenv("SQZ_SELFTEST_INTERVAL_S", "300")) or None)
