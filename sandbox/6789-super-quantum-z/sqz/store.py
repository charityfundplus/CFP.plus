"""Hàng đợi Job, Heartbeat, Audit nối chuỗi băm và Emergency Stop.

Chạy trên SQLite (sandbox, mặc định) hoặc PostgreSQL (Cloud) qua SQLAlchemy Core:
`Store("sqlite:///path.db")`, `Store("postgresql+psycopg://...")`, hoặc đường dẫn tệp.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
import uuid
from pathlib import Path

from sqlalchemy import (Column, Float, Integer, MetaData, String, Table, Text, UniqueConstraint,
                        create_engine, event, func, insert, select, text, update)
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

GENESIS = "0" * 64
metadata = MetaData()
jobs = Table(
    "sqz_jobs", metadata,
    Column("id", String(32), primary_key=True),
    Column("owner_id", String(12), nullable=False),
    Column("kind", String(32), nullable=False),
    Column("payload", Text, nullable=False),
    Column("status", String(16), nullable=False, index=True),
    Column("result", Text),
    Column("error", Text),
    Column("attempts", Integer, nullable=False, default=0),
    Column("worker", String(128)),
    Column("lease_until", Float),
    Column("created_at", Float, nullable=False, index=True),
    Column("updated_at", Float, nullable=False),
    Column("priority", Integer, nullable=False, default=0),
    Column("idempotency_key", String(128)),
    Column("submitted_by", String(64)),
    Column("fence", Integer, nullable=False, default=0),  # fencing token, tăng mỗi lần nhận
    UniqueConstraint("owner_id", "idempotency_key", name="uq_sqz_jobs_idem"),
)
heartbeats = Table(
    "sqz_heartbeats", metadata,
    Column("worker", String(128), primary_key=True),
    Column("seen_at", Float, nullable=False),
    Column("info", Text),
)
audit_log = Table(
    "sqz_audit", metadata,
    Column("seq", Integer, primary_key=True, autoincrement=True),
    Column("at", Float, nullable=False),
    Column("actor", String(128), nullable=False),
    Column("event", String(64), nullable=False),
    Column("data", Text, nullable=False),
    Column("prev", String(64), nullable=False),
    Column("digest", String(64), nullable=False),
)
reviews = Table(
    "sqz_reviews", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("job_id", String(32), nullable=False, index=True),
    Column("reviewer_id", String(12), nullable=False),
    Column("verdict", String(16), nullable=False),
    Column("note", Text),
    Column("at", Float, nullable=False),
)
control = Table(
    "sqz_control", metadata,
    Column("key", String(64), primary_key=True),
    Column("value", Text, nullable=False),
    Column("at", Float, nullable=False),
)


def _digest(prev: str, at: float, actor: str, event_: str, data: str) -> str:
    return hashlib.sha256(f"{prev}|{at:.6f}|{actor}|{event_}|{data}".encode()).hexdigest()


def _engine(target: str | Path | None) -> Engine:
    if target is None or str(target) == ":memory:":
        return create_engine("sqlite://", connect_args={"check_same_thread": False},
                             poolclass=StaticPool)
    url = str(target)
    if "://" not in url:
        url = f"sqlite:///{url}"
    if url.startswith("sqlite"):
        eng = create_engine(url, connect_args={"check_same_thread": False})

        @event.listens_for(eng, "connect")
        def _wal(conn, _):  # nhiều tiến trình đọc/ghi an toàn hơn
            conn.isolation_level = None  # để SQLAlchemy tự phát BEGIN
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=10000")

        @event.listens_for(eng, "begin")
        def _immediate(conn):  # khóa ghi ngay đầu giao dịch: tuần tự hóa giữa các tiến trình
            conn.exec_driver_sql("BEGIN IMMEDIATE")

        return eng
    return create_engine(url, pool_pre_ping=True)


class Store:
    def __init__(self, target: str | Path | None = None) -> None:
        self.engine = _engine(target)
        self.backend = self.engine.dialect.name
        self._lock = threading.RLock()
        metadata.create_all(self.engine)
        with self.engine.begin() as c:
            if c.execute(select(control.c.key).where(control.c.key == "audit_head")).first() is None:
                c.execute(insert(control).values(key="audit_head", value=GENESIS, at=time.time()))

    def ping(self) -> bool:
        with self.engine.connect() as c:
            return c.execute(text("SELECT 1")).scalar() == 1

    # ---------------------------------------------------------------- audit
    def audit(self, actor: str, event_: str, data: dict) -> str:
        payload = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        # Compare-and-swap trên audit_head: đúng cho nhiều tiến trình/instance trên cả SQLite
        # (FOR UPDATE không có tác dụng) lẫn PostgreSQL. Thua cuộc thì đọc lại head và thử lại.
        with self._lock:
            for attempt in range(200):
                try:
                    with self.engine.begin() as c:
                        prev = c.execute(select(control.c.value).where(control.c.key == "audit_head")
                                         .with_for_update()).scalar_one()
                        at = time.time()
                        d = _digest(prev, at, actor, event_, payload)
                        won = c.execute(update(control).where(control.c.key == "audit_head",
                                                              control.c.value == prev)
                                        .values(value=d, at=at)).rowcount
                        if won == 1:
                            c.execute(insert(audit_log).values(at=at, actor=actor, event=event_,
                                                               data=payload, prev=prev, digest=d))
                            return d
                except OperationalError:  # SQLite bận: thử lại
                    pass
                time.sleep(0.001 * (attempt % 10))
        raise RuntimeError("Không ghi được audit sau 200 lần thử (tranh chấp quá cao)")

    @staticmethod
    def _verify_audit(connection) -> dict:
        prev, n = GENESIS, 0
        for r in connection.execute(select(audit_log).order_by(audit_log.c.seq)):
            if r.prev != prev or _digest(prev, r.at, r.actor, r.event, r.data) != r.digest:
                return {"ok": False, "broken_at_seq": r.seq, "checked": n}
            prev, n = r.digest, n + 1
        head = connection.execute(
            select(control.c.value).where(control.c.key == "audit_head")
        ).scalar_one_or_none()
        if head != prev:
            return {"ok": False, "broken_at_seq": None, "checked": n, "reason": "audit_head mismatch (dòng cuối bị xóa?)"}
        return {"ok": True, "checked": n, "head": prev}

    def verify_audit(self) -> dict:
        with self.engine.connect() as connection:
            return self._verify_audit(connection)

    # ---------------------------------------------------------------- control
    def set_stop(self, stopped: bool, actor: str, reason: str = "") -> None:
        val = "1" if stopped else "0"
        with self._lock, self.engine.begin() as c:
            if c.execute(update(control).where(control.c.key == "emergency_stop")
                         .values(value=val, at=time.time())).rowcount == 0:
                c.execute(insert(control).values(key="emergency_stop", value=val, at=time.time()))
        self.audit(actor, "EMERGENCY_STOP" if stopped else "RESUME", {"reason": reason})

    def stopped(self) -> bool:
        with self.engine.connect() as c:
            return c.execute(select(control.c.value).where(control.c.key == "emergency_stop")).scalar() == "1"

    # ---------------------------------------------------------------- jobs
    def submit(self, owner_id: str, kind: str, payload: dict, actor: str, *, priority: int = 0,
               idempotency_key: str | None = None) -> str:
        """Gửi Job. Cùng (owner_id, idempotency_key) thì trả lại Job cũ, không tạo trùng."""
        if not -100 <= int(priority) <= 100:
            raise ValueError("priority phải trong -100..100")
        if idempotency_key is not None:
            existing = self.find_idempotent(owner_id, idempotency_key)
            if existing:
                return existing
        jid, now = uuid.uuid4().hex, time.time()
        try:
            with self.engine.begin() as c:
                c.execute(insert(jobs).values(id=jid, owner_id=owner_id, kind=kind, payload=json.dumps(payload),
                                              status="QUEUED", attempts=0, created_at=now, updated_at=now,
                                              priority=int(priority), idempotency_key=idempotency_key,
                                              submitted_by=actor, fence=0))
        except IntegrityError:  # hai yêu cầu cùng khóa đến đồng thời
            existing = self.find_idempotent(owner_id, idempotency_key)
            if existing:
                return existing
            raise
        self.audit(actor, "JOB_SUBMITTED", {"job": jid, "owner_id": owner_id, "kind": kind,
                                            "priority": int(priority)})
        return jid

    def find_idempotent(self, owner_id: str, key: str | None) -> str | None:
        if key is None:
            return None
        with self.engine.connect() as c:
            return c.execute(select(jobs.c.id).where(jobs.c.owner_id == owner_id,
                                                     jobs.c.idempotency_key == key)).scalar()

    def claim(self, worker: str, lease_s: float = 60.0, max_attempts: int = 3,
              max_running_per_owner: int | None = None) -> dict | None:
        """Nhận nguyên tử một Job: ưu tiên cao trước, cũ trước; chỉ một worker thắng.

        Trả Job kèm `fence` mới: chỉ lượt nhận mang fence này được phép finish.
        `max_running_per_owner` giới hạn số Job RUNNING của mỗi owner (chia sẻ công bằng).
        """
        if self.stopped():
            return None
        now = time.time()
        with self._lock, self.engine.begin() as c:
            # Tự phục hồi: Job quá hạn lease quay lại hàng đợi, quá số lần thử thì FAILED.
            c.execute(update(jobs).where(jobs.c.status == "RUNNING", jobs.c.lease_until < now,
                                         jobs.c.attempts >= max_attempts)
                      .values(status="FAILED", error="lease expired too many times", updated_at=now))
            c.execute(update(jobs).where(jobs.c.status == "RUNNING", jobs.c.lease_until < now)
                      .values(status="QUEUED", worker=None, updated_at=now))
            q = select(jobs.c.id).where(jobs.c.status == "QUEUED")
            if max_running_per_owner:
                busy = (select(jobs.c.owner_id).where(jobs.c.status == "RUNNING")
                        .group_by(jobs.c.owner_id).having(func.count() >= max_running_per_owner))
                q = q.where(jobs.c.owner_id.not_in(busy))
            q = q.order_by(jobs.c.priority.desc(), jobs.c.created_at).limit(1)
            for _ in range(5):
                jid = c.execute(q).scalar()
                if jid is None:
                    return None
                won = c.execute(update(jobs).where(jobs.c.id == jid, jobs.c.status == "QUEUED")
                                .values(status="RUNNING", worker=worker, lease_until=now + lease_s,
                                        attempts=jobs.c.attempts + 1, fence=jobs.c.fence + 1,
                                        updated_at=now)).rowcount
                if won == 1:
                    break
            else:
                return None
        return self.get(jid)

    def finish(self, jid: str, worker: str, result: dict | None = None, error: str | None = None,
               fence: int | None = None) -> bool:
        """Chốt kết quả. Sai worker, sai fence hoặc Job không còn RUNNING → từ chối (False)."""
        cond = [jobs.c.id == jid, jobs.c.worker == worker, jobs.c.status == "RUNNING"]
        if fence is not None:
            cond.append(jobs.c.fence == fence)
        with self.engine.begin() as c:
            n = c.execute(update(jobs).where(*cond)
                          .values(status="FAILED" if error else "DONE",
                                  result=json.dumps(result) if result is not None else None,
                                  error=error, updated_at=time.time(), lease_until=None)).rowcount
        if n:
            self.audit(worker, "JOB_FAILED" if error else "JOB_DONE", {"job": jid, "error": error,
                                                                      "fence": fence})
        else:
            self.audit(worker, "STALE_FINISH_REJECTED", {"job": jid, "fence": fence})
        return bool(n)

    def get(self, jid: str) -> dict | None:
        with self.engine.connect() as c:
            r = c.execute(select(jobs).where(jobs.c.id == jid)).mappings().first()
        if r is None:
            return None
        d = dict(r)
        d["payload"] = json.loads(d["payload"])
        d["result"] = json.loads(d["result"]) if d["result"] else None
        return d

    def recent(self, kind: str | None = None, limit: int = 50) -> list[dict]:
        q = select(jobs.c.id).order_by(jobs.c.created_at.desc()).limit(limit)
        if kind:
            q = q.where(jobs.c.kind == kind)
        with self.engine.connect() as c:
            ids = [r[0] for r in c.execute(q)]
        return [self.get(i) for i in ids]

    def counts(self) -> dict:
        with self.engine.connect() as c:
            return {r[0]: r[1] for r in c.execute(select(jobs.c.status, func.count()).group_by(jobs.c.status))}

    # ---------------------------------------------------------------- review độc lập
    def review(self, jid: str, reviewer_id: str, verdict: str, note: str = "",
               reviewer_principal: str | None = None) -> dict:
        job = self.get(jid)
        if job is None:
            raise KeyError(jid)
        if reviewer_id == job["owner_id"]:
            raise PermissionError("Reviewer phải khác chủ trì (kiểm chứng độc lập)")
        if reviewer_principal and reviewer_principal == job.get("submitted_by"):
            raise PermissionError("Cùng một danh tính đã gửi Job thì không được tự review")
        if job["status"] not in ("DONE", "FAILED"):
            raise ValueError("Chỉ review Job đã kết thúc")
        with self.engine.begin() as c:
            c.execute(insert(reviews).values(job_id=jid, reviewer_id=reviewer_id, verdict=verdict,
                                             note=note, at=time.time()))
        self.audit(reviewer_principal or f"review:{reviewer_id}", "JOB_REVIEWED",
                   {"job": jid, "reviewer_id": reviewer_id, "verdict": verdict})
        return {"job_id": jid, "reviewer_id": reviewer_id, "verdict": verdict}

    def reviews_of(self, jid: str) -> list[dict]:
        with self.engine.connect() as c:
            return [dict(r) for r in c.execute(select(reviews).where(reviews.c.job_id == jid)
                                               .order_by(reviews.c.id)).mappings()]

    # ---------------------------------------------------------------- heartbeat
    def beat(self, worker: str, info: dict) -> None:
        now, payload = time.time(), json.dumps(info)
        with self._lock, self.engine.begin() as c:
            if c.execute(update(heartbeats).where(heartbeats.c.worker == worker)
                         .values(seen_at=now, info=payload)).rowcount == 0:
                c.execute(insert(heartbeats).values(worker=worker, seen_at=now, info=payload))

    def workers(self, stale_after_s: float = 30.0) -> list[dict]:
        now = time.time()
        with self.engine.connect() as c:
            rows = list(c.execute(select(heartbeats)))
        return [{"worker": r.worker, "age_s": round(now - r.seen_at, 3),
                 "alive": now - r.seen_at <= stale_after_s, **json.loads(r.info or "{}")} for r in rows]
