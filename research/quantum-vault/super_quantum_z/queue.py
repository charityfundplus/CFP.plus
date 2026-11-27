"""Durable single-host sandbox queue with fenced leases."""

import hashlib
import json
import sqlite3
import time
from contextlib import contextmanager
from uuid import uuid4

from .core import Experiment


class QueueConflict(Exception):
    pass


class Queue:
    def __init__(self, path, clock=time.time):
        self.path = path
        self.clock = clock
        with self.transaction() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS control (
                singleton INTEGER PRIMARY KEY CHECK (singleton = 1), stopped INTEGER NOT NULL)""")
            db.execute("INSERT OR IGNORE INTO control VALUES (1, 0)")
            db.execute("""CREATE TABLE IF NOT EXISTS jobs (
                job TEXT PRIMARY KEY, owner TEXT NOT NULL, request_key TEXT NOT NULL,
                backend TEXT NOT NULL, deadline REAL NOT NULL, ready REAL NOT NULL,
                state TEXT NOT NULL, attempt INTEGER NOT NULL DEFAULT 0,
                session TEXT, lease REAL, result TEXT, digest TEXT,
                UNIQUE(owner, request_key))""")
            db.execute("""CREATE TABLE IF NOT EXISTS audit (
                seq INTEGER PRIMARY KEY, at REAL NOT NULL, owner TEXT NOT NULL,
                job TEXT NOT NULL, event TEXT NOT NULL, attempt INTEGER NOT NULL)""")

    @contextmanager
    def transaction(self):
        db = sqlite3.connect(self.path, timeout=2)
        db.row_factory = sqlite3.Row
        try:
            with db:
                db.execute("BEGIN IMMEDIATE")
                yield db
        finally:
            db.close()

    def _event(self, db, row, event):
        db.execute("INSERT INTO audit(at,owner,job,event,attempt) VALUES (?,?,?,?,?)",
                   (self.clock(), row["owner"], row["job"], event, row["attempt"]))

    def _schedule(self, db, now):
        rows = db.execute("""SELECT * FROM jobs WHERE state IN ('queued','running')
            AND (deadline <= ? OR (state = 'running' AND lease <= ?))""", (now, now))
        for row in rows.fetchall():
            if row["deadline"] <= now:
                state, event = "expired", "deadline_elapsed"
            elif row["attempt"] >= 3:
                state, event = "failed", "attempts_exhausted"
            else:
                state, event = "queued", "lease_lost"
            self._transition(db, row, state, event, now + 2 ** row["attempt"])

    def _transition(self, db, row, state, event, ready):
        db.execute("UPDATE jobs SET state=?, ready=?, session=NULL, lease=NULL WHERE job=?",
                   (state, ready, row["job"]))
        self._event(db, row, event)

    def submit(self, owner, key, experiment: Experiment):
        with self.transaction() as db:
            now = self.clock()
            self._schedule(db, now)
            previous = db.execute("SELECT * FROM jobs WHERE owner=? AND request_key=?",
                                  (owner, key)).fetchone()
            if previous:
                if previous["backend"] != experiment.backend:
                    raise QueueConflict("Request key already binds another experiment")
                return previous["job"]
            if db.execute("SELECT stopped FROM control").fetchone()[0]:
                raise QueueConflict("Emergency stop is set")
            if db.execute("SELECT count(*) FROM jobs").fetchone()[0] >= 1000:
                raise QueueConflict("Sandbox storage limit reached")
            job = uuid4().hex
            db.execute("""INSERT INTO jobs(job,owner,request_key,backend,deadline,ready,state)
                          VALUES (?,?,?,?,?,?,'queued')""",
                       (job, owner, key, experiment.backend, now + 120, now))
            self._event(db, {"owner": owner, "job": job, "attempt": 0}, "submitted")
            return job

    def claim(self):
        with self.transaction() as db:
            now = self.clock()
            self._schedule(db, now)
            if db.execute("SELECT stopped FROM control").fetchone()[0]:
                return None
            if db.execute("SELECT count(*) FROM jobs WHERE state='running'").fetchone()[0] >= 2:
                return None
            row = db.execute("""SELECT * FROM jobs WHERE state='queued' AND ready <= ?
                                ORDER BY ready, rowid LIMIT 1""", (now,)).fetchone()
            if row is None:
                return None
            session = uuid4().hex
            attempt = row["attempt"] + 1
            db.execute("""UPDATE jobs SET state='running', attempt=?, session=?, lease=?
                          WHERE job=?""", (attempt, session, min(now + 10, row["deadline"]), row["job"]))
            claimed = dict(row, attempt=attempt, session=session)
            self._event(db, claimed, "claimed")
            return claimed

    def heartbeat(self, job, session):
        with self.transaction() as db:
            now = self.clock()
            self._schedule(db, now)
            return bool(db.execute("""UPDATE jobs SET lease=min(?, deadline)
                WHERE job=? AND session=? AND state='running'""", (now + 10, job, session)).rowcount)

    def finish(self, job, session, result=None):
        with self.transaction() as db:
            now = self.clock()
            self._schedule(db, now)
            row = db.execute("SELECT * FROM jobs WHERE job=? AND session=? AND state='running'",
                             (job, session)).fetchone()
            if row is None:
                return False
            if result is None:
                state = "queued" if row["attempt"] < 3 else "failed"
                self._transition(db, row, state, "execution_failed", now + 2 ** row["attempt"])
            else:
                payload = json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False)
                digest = hashlib.sha256(payload.encode()).hexdigest()
                self._transition(db, row, "succeeded", "result_committed", now)
                db.execute("UPDATE jobs SET result=?, digest=? WHERE job=?", (payload, digest, job))
            return True

    def status(self):
        with self.transaction() as db:
            self._schedule(db, self.clock())
            counts = db.execute("SELECT state, count(*) FROM jobs GROUP BY state")
            return {"stopped": bool(db.execute("SELECT stopped FROM control").fetchone()[0]),
                    "jobs": dict(counts.fetchall())}

    def set_stop(self, stopped):
        with self.transaction() as db:
            now = self.clock()
            self._schedule(db, now)
            if db.execute("SELECT stopped FROM control").fetchone()[0] == stopped:
                return
            db.execute("UPDATE control SET stopped=?", (stopped,))
            self._event(db, {"owner": "system", "job": "control", "attempt": 0},
                        "emergency_stop" if stopped else "resumed")
            if stopped:
                for row in db.execute("SELECT * FROM jobs WHERE state IN ('queued','running')").fetchall():
                    self._transition(db, row, "cancelled", "emergency_stop", now)

    def evidence(self, owner, job):
        with self.transaction() as db:
            self._schedule(db, self.clock())
            row = db.execute("""SELECT state,attempt,backend,result,digest FROM jobs
                                WHERE owner=? AND job=?""", (owner, job)).fetchone()
            if row is None:
                return None
            events = db.execute("""SELECT seq,at,event,attempt FROM audit WHERE owner=? AND job=?
                                   ORDER BY seq""", (owner, job))
            return dict(row, owner=owner, job=job, result=json.loads(row["result"] or "null"),
                        audit=[dict(event) for event in events])
