"""Hàng đợi Job, Heartbeat, Audit nối chuỗi băm và Emergency Stop trên SQLite.

SQLite dùng cho sandbox; khi nâng cấp dùng cùng schema trên PostgreSQL.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path

GENESIS = "0" * 64
SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL,
  status TEXT NOT NULL, result TEXT, error TEXT, attempts INTEGER NOT NULL DEFAULT 0,
  worker TEXT, lease_until REAL, created_at REAL NOT NULL, updated_at REAL NOT NULL);
CREATE INDEX IF NOT EXISTS jobs_status ON jobs(status, created_at);
CREATE TABLE IF NOT EXISTS heartbeats (worker TEXT PRIMARY KEY, seen_at REAL NOT NULL, info TEXT);
CREATE TABLE IF NOT EXISTS audit (
  seq INTEGER PRIMARY KEY AUTOINCREMENT, at REAL NOT NULL, actor TEXT NOT NULL,
  event TEXT NOT NULL, data TEXT NOT NULL, prev TEXT NOT NULL, digest TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS control (key TEXT PRIMARY KEY, value TEXT NOT NULL, at REAL NOT NULL);
"""


def _digest(prev: str, at: float, actor: str, event: str, data: str) -> str:
    return hashlib.sha256(f"{prev}|{at:.6f}|{actor}|{event}|{data}".encode()).hexdigest()


class Store:
    def __init__(self, path: str | Path = ":memory:") -> None:
        self._lock = threading.RLock()
        self.db = sqlite3.connect(str(path), check_same_thread=False, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        if str(path) != ":memory:":
            self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript(SCHEMA)

    # ---------------------------------------------------------------- audit
    def audit(self, actor: str, event: str, data: dict) -> str:
        payload = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        with self._lock:
            row = self.db.execute("SELECT digest FROM audit ORDER BY seq DESC LIMIT 1").fetchone()
            prev = row["digest"] if row else GENESIS
            at = time.time()
            d = _digest(prev, at, actor, event, payload)
            self.db.execute("INSERT INTO audit(at,actor,event,data,prev,digest) VALUES(?,?,?,?,?,?)",
                            (at, actor, event, payload, prev, d))
            return d

    def verify_audit(self) -> dict:
        prev, n = GENESIS, 0
        for r in self.db.execute("SELECT * FROM audit ORDER BY seq"):
            if r["prev"] != prev or _digest(prev, r["at"], r["actor"], r["event"], r["data"]) != r["digest"]:
                return {"ok": False, "broken_at_seq": r["seq"], "checked": n}
            prev, n = r["digest"], n + 1
        return {"ok": True, "checked": n, "head": prev}

    # ---------------------------------------------------------------- control
    def set_stop(self, stopped: bool, actor: str, reason: str = "") -> None:
        with self._lock:
            self.db.execute("INSERT INTO control(key,value,at) VALUES('emergency_stop',?,?) "
                            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, at=excluded.at",
                            ("1" if stopped else "0", time.time()))
        self.audit(actor, "EMERGENCY_STOP" if stopped else "RESUME", {"reason": reason})

    def stopped(self) -> bool:
        r = self.db.execute("SELECT value FROM control WHERE key='emergency_stop'").fetchone()
        return bool(r and r["value"] == "1")

    # ---------------------------------------------------------------- jobs
    def submit(self, owner_id: str, kind: str, payload: dict, actor: str) -> str:
        jid = uuid.uuid4().hex
        now = time.time()
        with self._lock:
            self.db.execute("INSERT INTO jobs(id,owner_id,kind,payload,status,created_at,updated_at) "
                            "VALUES(?,?,?,?, 'QUEUED', ?, ?)",
                            (jid, owner_id, kind, json.dumps(payload), now, now))
        self.audit(actor, "JOB_SUBMITTED", {"job": jid, "owner_id": owner_id, "kind": kind})
        return jid

    def claim(self, worker: str, lease_s: float = 60.0) -> dict | None:
        """Nhận nguyên tử một Job: chỉ một worker thắng nhờ UPDATE có điều kiện."""
        if self.stopped():
            return None
        now = time.time()
        with self._lock:
            # Trả Job quá hạn lease về hàng đợi (tự phục hồi khi worker chết).
            self.db.execute("UPDATE jobs SET status='QUEUED', worker=NULL, updated_at=? "
                            "WHERE status='RUNNING' AND lease_until < ?", (now, now))
            r = self.db.execute("SELECT id FROM jobs WHERE status='QUEUED' ORDER BY created_at LIMIT 1").fetchone()
            if r is None:
                return None
            cur = self.db.execute("UPDATE jobs SET status='RUNNING', worker=?, lease_until=?, "
                                  "attempts=attempts+1, updated_at=? WHERE id=? AND status='QUEUED'",
                                  (worker, now + lease_s, now, r["id"]))
            if cur.rowcount != 1:
                return None
            return self.get(r["id"])

    def finish(self, jid: str, worker: str, result: dict | None = None, error: str | None = None) -> None:
        with self._lock:
            self.db.execute("UPDATE jobs SET status=?, result=?, error=?, updated_at=?, lease_until=NULL "
                            "WHERE id=? AND worker=?",
                            ("FAILED" if error else "DONE", json.dumps(result) if result else None,
                             error, time.time(), jid, worker))
        self.audit(worker, "JOB_FAILED" if error else "JOB_DONE", {"job": jid, "error": error})

    def get(self, jid: str) -> dict | None:
        r = self.db.execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone()
        if r is None:
            return None
        d = dict(r)
        d["payload"] = json.loads(d["payload"])
        d["result"] = json.loads(d["result"]) if d["result"] else None
        return d

    def counts(self) -> dict:
        return {r["status"]: r["n"] for r in
                self.db.execute("SELECT status, COUNT(*) n FROM jobs GROUP BY status")}

    # ---------------------------------------------------------------- heartbeat
    def beat(self, worker: str, info: dict) -> None:
        with self._lock:
            self.db.execute("INSERT INTO heartbeats(worker,seen_at,info) VALUES(?,?,?) "
                            "ON CONFLICT(worker) DO UPDATE SET seen_at=excluded.seen_at, info=excluded.info",
                            (worker, time.time(), json.dumps(info)))

    def workers(self, stale_after_s: float = 30.0) -> list[dict]:
        now = time.time()
        return [{"worker": r["worker"], "age_s": round(now - r["seen_at"], 3),
                 "alive": now - r["seen_at"] <= stale_after_s, **json.loads(r["info"] or "{}")}
                for r in self.db.execute("SELECT * FROM heartbeats")]
