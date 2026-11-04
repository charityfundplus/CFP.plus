"""CFP+ Worker P0 • hàng đợi + lịch chạy có kiểm soát (SANDBOX).

Một tiến trình nền thật, chạy theo nhịp, với:
  • danh tính dịch vụ riêng: schema cfp_worker + role worker_app (004_worker.sql), không có quyền
    vào cfp_office / cfp_forum_* (quyền tối thiểu);
  • idempotency: mỗi việc định kỳ có khoá <kind>:<khung giờ>, chạy lại tick không tạo trùng;
  • giới hạn đồng thời (CFP_WORKER_MAX_RUNNING, mặc định 1), claim bằng FOR UPDATE SKIP LOCKED;
  • retry có backoff luỹ thừa, tối đa max_attempts lần → dead-letter (status=dead) + cảnh báo;
  • lease: việc "running" quá hạn (worker chết giữa chừng) được trả về hàng đợi;
  • heartbeat mỗi tick; nhật ký chỉ ghi thêm (worker_app không UPDATE/DELETE được log);
  • kill switch: control.paused — chỉ role worker_governance đổi được; hoặc CFP_WORKER_ENABLED=0.

Việc P0 duy nhất: registry_integrity — chỉ ĐỌC registry/, phát hiện Canonical ID / Parent bị đổi
so với lần chạy trước và kiểm tra chuỗi mẫu 911 → 6911 → 69112 → 691121. Không ghi dữ liệu nghiệp vụ,
không thay mặt SI AI nào (không ACK, không bình luận).

  python -m services.forum.worker run [--once]      # CFP_WORKER_DB
  python -m services.forum.worker status
  python -m services.forum.worker pause|resume       # CFP_WORKER_ADMIN_DB (SET ROLE worker_governance)

Cảnh báo P0: dòng log level=alert + stderr "ALERT"; /api/worker/status báo heartbeat trễ.
Chưa có kênh gửi email/push (không phát sinh chi phí).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import sys
import time
import traceback
from datetime import datetime, timedelta, timezone
from typing import Callable

from sqlalchemy import (Column, DateTime, Engine, Integer, MetaData, String, Table, Text, create_engine, func,
                        insert, select, update)
from sqlalchemy.exc import IntegrityError

VERSION = "0.1.0-p0"
md = MetaData()
jobs_t = Table("jobs", md,
               Column("id", Integer, primary_key=True),
               Column("kind", String(40), nullable=False),
               Column("idempotency_key", String(120), unique=True, nullable=False),
               Column("status", String(16), nullable=False, default="queued"),  # queued|running|done|dead
               Column("attempts", Integer, nullable=False, default=0),
               Column("max_attempts", Integer, nullable=False, default=3),
               Column("next_run_at", DateTime(timezone=True), nullable=False),
               Column("locked_by", String(120)),
               Column("started_at", DateTime(timezone=True)),
               Column("finished_at", DateTime(timezone=True)),
               Column("last_error", Text),
               Column("result", Text),
               Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()))
logs_t = Table("logs", md,
               Column("id", Integer, primary_key=True),
               Column("at", DateTime(timezone=True), nullable=False, server_default=func.now()),
               Column("worker_id", String(120), nullable=False),
               Column("job_id", Integer),
               Column("level", String(8), nullable=False),  # info|warn|error|alert
               Column("event", String(40), nullable=False),
               Column("message", Text, nullable=False),
               implicit_returning=False)
heartbeats_t = Table("heartbeats", md,
                     Column("worker_id", String(120), primary_key=True),
                     Column("last_seen", DateTime(timezone=True), nullable=False),
                     Column("state", String(16), nullable=False),  # running|paused
                     Column("version", String(24), nullable=False),
                     Column("ticks", Integer, nullable=False, default=0))
control_t = Table("control", md,
                  Column("key", String(40), primary_key=True),
                  Column("value", String(200), nullable=False),
                  Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()))

SCHEMA = "cfp_worker"


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _aware(v: datetime | None) -> datetime | None:
    return v.replace(tzinfo=timezone.utc) if v is not None and v.tzinfo is None else v


def engine_for(url: str) -> Engine:
    if url.startswith("sqlite"):
        eng = create_engine(url, connect_args={"check_same_thread": False})
        md.create_all(eng)
        return eng
    # Postgres: schema/role do 004_worker.sql tạo; worker_app có search_path = cfp_worker.
    return create_engine(url, pool_pre_ping=True, pool_size=2, max_overflow=1, pool_recycle=300,
                         connect_args={"options": f"-c search_path={SCHEMA}"})


# ---------------------------------------------------------------- việc P0
def registry_integrity(eng: Engine, job: dict) -> dict:
    """Chỉ đọc registry/: dấu vân tay (ID, Parent, type) + bất biến của chuỗi mẫu."""
    from services.forum.registry import Registry
    reg = Registry()
    rows = sorted((e.id, e.parent_id or "", e.type) for e in reg.entities.values())
    digest = hashlib.sha256(json.dumps(rows, ensure_ascii=False).encode()).hexdigest()
    chain = [x["id"] for x in reg.chain("691121")]
    problems = []
    if chain != ["911", "6911", "69112", "691121"]:
        problems.append(f"chuỗi 691121 sai: {chain}")
    bad = [e.id for e in reg.entities.values() if not e.id.isdigit()]
    if bad:
        problems.append(f"ID không phải số: {bad[:5]}")
    orphans = [e.id for e in reg.entities.values() if e.parent_id and e.parent_id not in reg.entities
               and e.type != "registry_record"]
    with eng.connect() as c:
        prev = c.execute(select(jobs_t.c.result).where(jobs_t.c.kind == "registry_integrity",
                                                       jobs_t.c.status == "done", jobs_t.c.id != job["id"])
                         .order_by(jobs_t.c.id.desc()).limit(1)).scalar()
    prev_digest = json.loads(prev)["digest"] if prev else None
    return {"entities": len(rows), "digest": digest, "previous_digest": prev_digest,
            "drift": bool(prev_digest and prev_digest != digest), "chain_691121": chain,
            "orphans": len(orphans), "problems": problems}


HANDLERS: dict[str, Callable[[Engine, dict], dict]] = {"registry_integrity": registry_integrity}
# kind → chu kỳ (giây). Khoá idempotency = kind:<số khung>.
SCHEDULE: dict[str, int] = {"registry_integrity": int(os.environ.get("CFP_WORKER_REGISTRY_EVERY", "3600"))}


# ---------------------------------------------------------------- lõi hàng đợi
class Worker:
    def __init__(self, eng: Engine, worker_id: str | None = None, *, max_running: int | None = None,
                 lease_seconds: int = 600, backoff_base: int = 60, backoff_cap: int = 3600,
                 handlers: dict | None = None, schedule: dict | None = None):
        self.eng = eng
        self.id = worker_id or f"{socket.gethostname()}:{os.getpid()}"
        self.max_running = max_running or int(os.environ.get("CFP_WORKER_MAX_RUNNING", "1"))
        self.lease = lease_seconds
        self.backoff_base, self.backoff_cap = backoff_base, backoff_cap
        self.handlers = HANDLERS if handlers is None else handlers
        self.schedule = SCHEDULE if schedule is None else schedule
        self.pg = eng.dialect.name == "postgresql"

    def log(self, level: str, event: str, message: str, job_id: int | None = None) -> None:
        with self.eng.begin() as c:
            c.execute(insert(logs_t).values(worker_id=self.id, job_id=job_id, level=level, event=event,
                                            message=message[:2000]))
        if level in ("alert", "error"):
            print(f"{'ALERT' if level == 'alert' else 'ERROR'} cfp-worker {event} job={job_id}: {message}",
                  file=sys.stderr, flush=True)

    def paused(self) -> bool:
        if os.environ.get("CFP_WORKER_ENABLED", "1") == "0":
            return True
        with self.eng.connect() as c:
            return c.execute(select(control_t.c.value).where(control_t.c.key == "paused")).scalar() == "true"

    def heartbeat(self, state: str, now: datetime) -> None:
        with self.eng.begin() as c:
            n = c.execute(update(heartbeats_t).where(heartbeats_t.c.worker_id == self.id)
                          .values(last_seen=now, state=state, version=VERSION, ticks=heartbeats_t.c.ticks + 1)).rowcount
            if not n:
                c.execute(insert(heartbeats_t).values(worker_id=self.id, last_seen=now, state=state,
                                                      version=VERSION, ticks=1))

    def enqueue(self, kind: str, key: str, now: datetime, max_attempts: int = 3) -> int | None:
        try:
            with self.eng.begin() as c:
                return c.execute(insert(jobs_t).values(kind=kind, idempotency_key=key, status="queued", attempts=0,
                                                       max_attempts=max_attempts, next_run_at=now)
                                 .returning(jobs_t.c.id)).scalar_one()
        except IntegrityError:
            return None  # đã có (idempotency)

    def enqueue_due(self, now: datetime) -> list[int]:
        out = []
        for kind, every in self.schedule.items():
            jid = self.enqueue(kind, f"{kind}:{int(now.timestamp()) // every}", now)
            if jid:
                out.append(jid)
                self.log("info", "enqueued", f"{kind} (chu kỳ {every}s)", jid)
        return out

    def recover_expired(self, now: datetime) -> None:
        cutoff = now - timedelta(seconds=self.lease)
        with self.eng.begin() as c:
            ids = c.execute(select(jobs_t.c.id).where(jobs_t.c.status == "running", jobs_t.c.started_at < cutoff)).scalars().all()
            for jid in ids:
                c.execute(update(jobs_t).where(jobs_t.c.id == jid, jobs_t.c.status == "running")
                          .values(status="queued", locked_by=None, next_run_at=now, last_error="lease hết hạn"))
        for jid in ids:
            self.log("warn", "lease_expired", "việc running quá hạn → trả về hàng đợi", jid)

    def claim(self, now: datetime) -> dict | None:
        with self.eng.begin() as c:
            if self.pg:  # tuần tự hoá claim giữa nhiều worker → giới hạn đồng thời là toàn cục
                c.exec_driver_sql("select pg_advisory_xact_lock(hashtext('cfp_worker.claim'))")
            running = c.execute(select(func.count()).select_from(jobs_t).where(jobs_t.c.status == "running")).scalar_one()
            if running >= self.max_running:
                return None
            q = (select(jobs_t).where(jobs_t.c.status == "queued", jobs_t.c.next_run_at <= now)
                 .order_by(jobs_t.c.next_run_at, jobs_t.c.id).limit(1))
            if self.pg:
                q = q.with_for_update(skip_locked=True)
            j = c.execute(q).mappings().first()
            if not j:
                return None
            n = c.execute(update(jobs_t).where(jobs_t.c.id == j["id"], jobs_t.c.status == "queued")
                          .values(status="running", attempts=jobs_t.c.attempts + 1, locked_by=self.id,
                                  started_at=now)).rowcount
            if n != 1:
                return None
            return {**dict(j), "attempts": j["attempts"] + 1}

    def execute(self, job: dict, now: datetime) -> str:
        fn = self.handlers.get(job["kind"])
        try:
            if fn is None:
                raise RuntimeError(f"không có handler cho {job['kind']}")
            result = fn(self.eng, job)
        except Exception as e:  # noqa: BLE001 — mọi lỗi việc đều qua retry/dead-letter
            err = f"{type(e).__name__}: {e}"
            if job["attempts"] >= job["max_attempts"]:
                with self.eng.begin() as c:
                    c.execute(update(jobs_t).where(jobs_t.c.id == job["id"])
                              .values(status="dead", finished_at=now, last_error=err, locked_by=None))
                self.log("alert", "dead_letter", f"{job['kind']} thất bại {job['attempts']}/{job['max_attempts']} lần: {err}", job["id"])
                return "dead"
            delay = min(self.backoff_cap, self.backoff_base * 2 ** (job["attempts"] - 1))
            with self.eng.begin() as c:
                c.execute(update(jobs_t).where(jobs_t.c.id == job["id"])
                          .values(status="queued", next_run_at=now + timedelta(seconds=delay), last_error=err,
                                  locked_by=None))
            self.log("error", "retry", f"{job['kind']} lần {job['attempts']}: {err} → thử lại sau {delay}s", job["id"])
            return "retry"
        with self.eng.begin() as c:
            c.execute(update(jobs_t).where(jobs_t.c.id == job["id"])
                      .values(status="done", finished_at=now, result=json.dumps(result, ensure_ascii=False),
                              last_error=None, locked_by=None))
        if result.get("drift") or result.get("problems"):
            self.log("alert", "registry_drift", json.dumps({k: result[k] for k in ("drift", "problems", "digest",
                                                                                  "previous_digest")}, ensure_ascii=False), job["id"])
        else:
            self.log("info", "done", f"{job['kind']} OK: {json.dumps(result, ensure_ascii=False)[:300]}", job["id"])
        return "done"

    def tick(self, now: datetime | None = None) -> dict:
        now = now or now_utc()
        if self.paused():
            self.heartbeat("paused", now)
            return {"state": "paused"}
        self.heartbeat("running", now)
        self.recover_expired(now)
        self.enqueue_due(now)
        ran = []
        while (job := self.claim(now)) is not None:
            ran.append((job["id"], self.execute(job, now)))
        return {"state": "running", "ran": ran}

    def run_forever(self, interval: float = 30.0) -> None:
        self.log("info", "start", f"worker {VERSION} bắt đầu, nhịp {interval}s, tối đa {self.max_running} việc song song")
        while True:
            try:
                self.tick()
            except Exception:  # noqa: BLE001 — giữ vòng lặp sống, ghi lỗi
                traceback.print_exc()
                try:
                    self.log("alert", "tick_error", traceback.format_exc(limit=3))
                except Exception:  # noqa: BLE001
                    pass
            time.sleep(interval)


# ---------------------------------------------------------------- trạng thái (đọc) + kill switch
def status(eng: Engine, now: datetime | None = None, stale_after: int = 180) -> dict:
    now = now or now_utc()
    with eng.connect() as c:
        hb = c.execute(select(heartbeats_t).order_by(heartbeats_t.c.last_seen.desc())).mappings().all()
        counts = dict(c.execute(select(jobs_t.c.status, func.count()).group_by(jobs_t.c.status)).all())
        paused = c.execute(select(control_t.c.value).where(control_t.c.key == "paused")).scalar() == "true"
        since = now - timedelta(hours=24)
        alerts = c.execute(select(func.count()).select_from(logs_t)
                           .where(logs_t.c.level == "alert", logs_t.c.at >= since)).scalar_one()
        recent = c.execute(select(logs_t.c.at, logs_t.c.level, logs_t.c.event, logs_t.c.job_id)
                           .order_by(logs_t.c.id.desc()).limit(20)).mappings().all()
        last_done = c.execute(select(jobs_t.c.id, jobs_t.c.kind, jobs_t.c.finished_at, jobs_t.c.result)
                              .where(jobs_t.c.status == "done").order_by(jobs_t.c.id.desc()).limit(1)).mappings().first()
    beats = []
    for h in hb:
        age = (now - _aware(h["last_seen"])).total_seconds()
        beats.append({"worker_id": h["worker_id"], "state": h["state"], "version": h["version"], "ticks": h["ticks"],
                      "last_seen": _aware(h["last_seen"]).isoformat(), "age_seconds": round(age), "stale": age > stale_after})
    alive = any(not b["stale"] for b in beats)
    res = json.loads(last_done["result"]) if last_done and last_done["result"] else None
    return {"mode": "SANDBOX", "alive": alive, "paused": paused, "heartbeats": beats, "jobs": counts,
            "alerts_24h": alerts,
            "last_done": {"id": last_done["id"], "kind": last_done["kind"],
                          "finished_at": _aware(last_done["finished_at"]).isoformat(),
                          "summary": {k: res.get(k) for k in ("entities", "drift", "chain_691121", "problems")} if res else None}
            if last_done else None,
            "recent": [{"at": _aware(r["at"]).isoformat() if r["at"] else None, "level": r["level"],
                        "event": r["event"], "job_id": r["job_id"]} for r in recent],
            "note": "Bằng chứng runtime = heartbeat + nhật ký. Không phải cam kết uptime 24/24."}


def set_paused(admin_url: str, paused: bool, who: str) -> None:
    eng = engine_for(admin_url)
    with eng.begin() as c:
        if eng.dialect.name == "postgresql":
            c.exec_driver_sql("SET LOCAL ROLE worker_governance")
        val = "true" if paused else "false"
        n = c.execute(update(control_t).where(control_t.c.key == "paused").values(value=val, updated_at=func.now())).rowcount
        if not n:
            c.execute(insert(control_t).values(key="paused", value=val))
        c.execute(insert(logs_t).values(worker_id=f"governance:{who}", level="alert" if paused else "info",
                                        event="kill_switch", message=f"paused={val} bởi {who}"))
    eng.dispose()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="cfp-worker")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--once", action="store_true")
    r.add_argument("--interval", type=float, default=float(os.environ.get("CFP_WORKER_INTERVAL", "30")))
    sub.add_parser("status")
    for name in ("pause", "resume"):
        p = sub.add_parser(name)
        p.add_argument("--by", required=True, help="người vận hành Human Governance")
    a = ap.parse_args(argv)
    if a.cmd in ("pause", "resume"):
        set_paused(os.environ["CFP_WORKER_ADMIN_DB"], a.cmd == "pause", a.by)
        print(f"OK: {a.cmd}")
        return 0
    eng = engine_for(os.environ["CFP_WORKER_DB"])
    if a.cmd == "status":
        print(json.dumps(status(eng), ensure_ascii=False, indent=1))
        return 0
    w = Worker(eng)
    if a.once:
        print(json.dumps(w.tick(), ensure_ascii=False))
        return 0
    w.run_forever(a.interval)
    return 0


if __name__ == "__main__":
    sys.exit(main())
