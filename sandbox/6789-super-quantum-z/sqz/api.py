"""FastAPI • CMP Work Order • quản trị Emergency Stop. Fail-closed khi thiếu token."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from . import __version__, backends
from .circuit import Circuit, CircuitError, check_shots
from .ids import InvalidID, classify
from .store import Store
from .ops6776 import EVIDENCE_SCHEMA, backup, validate_evidence, watchdog
from .si6788 import EvalCase, evaluate_response, verify_job
from .worker import Scheduler, Worker

from .auth import AuthError, Principal, authenticate, require_act_as
from .executor import KINDS
from .gateway import resolve_id, to_gateway_work_order


class JobIn(BaseModel):
    owner_id: str = Field(description="ID Số CFP+ hiện hữu của bên gửi (không cấp mới)")
    kind: str
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=0, ge=-100, le=100)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=128)


class WorkOrderIn(BaseModel):
    """Định dạng CMP Work Order rút gọn, tương thích cfp-gateway."""

    work_order_id: str
    source: str = "CMP"
    target: str = "6789"
    task: str
    payload: dict[str, Any] = Field(default_factory=dict)
    required_capability: str | None = None
    requested_by: str
    priority: int = Field(default=0, ge=-100, le=100)


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


def needs(scope: str):
    """Xác thực bearer token → Principal có scope yêu cầu (fail-closed)."""

    def check(authorization: str = Header(default="")) -> Principal:
        try:
            p = authenticate(authorization)
        except (AuthError, ValueError) as exc:
            raise HTTPException(status_code=401, detail="Unauthorized") from exc
        if not p.can(scope):
            raise HTTPException(status_code=403, detail=f"Thiếu scope {scope}")
        return p

    return check


def _act(p: Principal, cfp_id: str, scope: str) -> None:
    try:
        require_act_as(p, cfp_id, scope)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except AuthError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


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
    reader = Depends(needs("read"))
    admin = Depends(needs("admin"))

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

    @app.get("/whoami")
    def whoami(p: Principal = Depends(needs("read"))) -> dict:
        return p.public()

    def _submit(job: JobIn, p: Principal) -> dict:
        if store.stopped():
            raise HTTPException(status_code=423, detail="EMERGENCY_STOP đang bật")
        _act(p, job.owner_id, "submit")
        _validate(job.kind, job.owner_id, job.payload)
        try:
            jid = store.submit(job.owner_id, job.kind, job.payload, p.ai_id, priority=job.priority,
                               idempotency_key=job.idempotency_key)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {"job_id": jid, "status": store.get(jid)["status"]}

    @app.post("/jobs", status_code=202)
    def submit(job: JobIn, p: Principal = Depends(needs("submit"))) -> dict:
        return _submit(job, p)

    @app.get("/jobs/{job_id}", dependencies=[reader])
    def get_job(job_id: str) -> dict:
        j = store.get(job_id)
        if j is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy Job")
        return j

    @app.post("/cmp/work-orders", status_code=202)
    def cmp_work_order(wo: WorkOrderIn, p: Principal = Depends(needs("submit"))) -> dict:
        if wo.target != "6789":
            raise HTTPException(status_code=422, detail="Work Order không dành cho 6789")
        # work_order_id làm khóa idempotency: CMP gửi lại không tạo Job trùng.
        job = _submit(JobIn(owner_id=wo.requested_by, kind=wo.task, payload=wo.payload,
                            priority=wo.priority, idempotency_key=f"cmp:{wo.work_order_id}"[:128]), p)
        store.audit(p.ai_id, "CMP_WORK_ORDER_ACCEPTED",
                    {"work_order_id": wo.work_order_id, "job": job["job_id"]})
        return {"work_order_id": wo.work_order_id, **job, "review": "REVIEW_REQUIRED"}

    @app.get("/cmp/work-orders/{job_id}/gateway-format", dependencies=[reader])
    def cmp_gateway_format(job_id: str) -> dict:
        j = store.get(job_id)
        if j is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy Job")
        return to_gateway_work_order(j)

    @app.get("/si/next-reviewer")
    def next_reviewer(owner_id: str, pool: str, history: str = "") -> dict:
        """Thay phiên SI AI: reviewer ít lượt nhất, khác chủ trì, khác người vừa review."""
        from .teams import rotate_reviewer

        try:
            pick = rotate_reviewer([x for x in pool.split(",") if x], owner_id,
                                   [x for x in history.split(",") if x])
        except (InvalidID, ValueError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {"reviewer_id": pick, "owner_id": owner_id}

    @app.get("/ids/{cfp_id}/resolve")
    def ids_resolve(cfp_id: str) -> dict:
        """Tra ID Số Sống qua CFP+ Gateway; không cấp ID, không bịa DID."""
        try:
            return resolve_id(cfp_id)
        except InvalidID as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/admin/emergency-stop", dependencies=[admin])
    def emergency_stop(body: StopIn, p: Principal = Depends(needs("admin"))) -> dict:
        store.set_stop(True, p.ai_id, body.reason)
        return {"emergency_stop": True}

    @app.post("/admin/resume", dependencies=[admin])
    def resume(body: StopIn, p: Principal = Depends(needs("admin"))) -> dict:
        store.set_stop(False, p.ai_id, body.reason)
        return {"emergency_stop": False}

    @app.get("/audit/verify", dependencies=[admin])
    def audit_verify() -> dict:
        return store.verify_audit()

    @app.post("/jobs/{job_id}/review")
    def review(job_id: str, body: ReviewIn, p: Principal = Depends(needs("review"))) -> dict:
        """Reviewer phải chứng minh quyền thật: token có scope review và được đại diện reviewer_id."""
        _act(p, body.reviewer_id, "review")
        try:
            return store.review(job_id, body.reviewer_id, body.verdict, body.note, reviewer_principal=p.ai_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Không tìm thấy Job") from exc
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/jobs/{job_id}/reviews", dependencies=[reader])
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

    @app.get("/evidence", dependencies=[reader])
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
    @app.post("/si/evaluate", dependencies=[reader])
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

    @app.post("/si/verify/{job_id}")
    def si_verify(job_id: str, p: Principal = Depends(needs("review"))) -> dict:
        """6788 chạy lại độc lập; chỉ danh tính được đại diện 6788 mới ghi được review."""
        _act(p, "6788", "review")
        job = store.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy Job")
        v = verify_job(job)
        recorded = None
        if job["owner_id"] != "6788" and job["status"] in ("DONE", "FAILED"):
            try:
                recorded = store.review(job_id, "6788", v["verdict"],
                                        f"AUTOMATED • {v['method']} • {v['details']}",
                                        reviewer_principal=p.ai_id)
            except PermissionError as exc:
                raise HTTPException(status_code=403, detail=str(exc)) from exc
        return {**v, "job_id": job_id, "review_recorded": bool(recorded)}

    # ------------------------------------------------------------ 6776 • Siêu Phần Mềm
    @app.get("/evidence/schema")
    def evidence_schema() -> dict:
        return EVIDENCE_SCHEMA

    @app.post("/evidence/validate")
    def evidence_validate(report: dict) -> dict:
        return validate_evidence(report)

    @app.get("/ops/watchdog", dependencies=[Depends(needs("operate"))])
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

    @app.get("/workers", dependencies=[reader])
    def workers() -> list[dict]:
        return store.workers()

    return app


def app_from_env() -> FastAPI:
    return create_app(run_worker=os.getenv("SQZ_WORKER", "1") == "1",
                      scheduler_interval_s=float(os.getenv("SQZ_SELFTEST_INTERVAL_S", "300")) or None)
