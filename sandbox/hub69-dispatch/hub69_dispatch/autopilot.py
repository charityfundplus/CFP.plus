"""HUB 69 autopilot: forum/Working Link → shared queue (#207) → PR #195 Office API → executor → reviewer.

One ``tick`` does, without anyone relaying messages:

  1. INTAKE    read the source (GitHub #201 read-only, or a Working Link export), parse with protocol.py,
               record newly seen comment refs (dedupe log), fold with engine.py (rules + 5 slots + routing).
  2. PERSIST   for every task the queue DISPATCHED to an agent that has an automated executor for the
               task's capability: create the task in the #195 Office (idempotency_key derived from the
               native task key → the same task is never created twice, even after a crash).
  3. EXECUTE   as the agent's SANDBOX Office account: ACK → start → run the executor → Evidence (sha256 of
               the result file) → submit. Each step first re-reads the task status from the Office and only
               does what is still missing (reconcile), so a re-run after any crash is safe.
  4. HANDOFF   status IN_REVIEW in the Office + read-back AS THE REVIEWER (the reviewer account must see the
               task assigned to it) + a NEED_REVIEW draft for #201. The autopilot never reviews.
  5. REPORT    run log (JSONL), read-back JSON, drafts for #201 (HOLD: never posted here).

Honesty labels carried in every record:
  intake_channel   working_link_file | github_issue
  author           SANDBOX_FIXTURE (written for the test) | relayed_by_operator | direct_bound_login | …
  executor_kind    AUTOMATED_TOOL  — deterministic code run under the agent's Working Link, NOT the LLM
  office_identity  SANDBOX_ACCOUNT — an account in an ephemeral #195 instance, not the agent's own login
  review           PENDING_REAL_REVIEWER until a real ReviewSI/SecuritySI submits a verdict

Failure handling: transient Office errors (connection, 5xx, 429, WIP limit) → retry with backoff across ticks;
permanent errors (403/404/422) → dead-letter with reason (``requeue`` revives after a fix); a file lock stops two
ticks from running at once.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import sqlite3
import sys
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .engine import Queue
from .office_client import OfficeClient, OfficeError, RetryPolicy
from .protocol import DISPATCH_MARKER, parse_comment

REPO_ROOT = Path(__file__).resolve().parents[3]
MAX_ATTEMPTS = 5
STAGES = ("NEW", "OFFICE_CREATED", "ACKED", "STARTED", "EXECUTED", "EVIDENCE_STORED", "HANDED_TO_REVIEWER",
          "REVIEWED")


class Busy(Exception):
    """Another tick holds the lock."""


class SimulatedCrash(Exception):
    """Test hook: the process 'dies' after a named step."""


# ====================================================================== store
class Store:
    """Local autopilot state (SQLite): what was seen, where each task is, attempts, dead letters, run log.
    The Office (#195) stays the source of truth for task state; this store only remembers the mapping
    native task key → Office task id and retry bookkeeping."""

    def __init__(self, state_dir: Path):
        self.dir = Path(state_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.dir / "autopilot.db", isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            create table if not exists seen(ref text primary key, kind text, task text, first_seen text);
            create table if not exists tasks(key text primary key, office_tid integer, assignee text, reviewer text,
                capability text, stage text not null default 'NEW', attempts integer not null default 0,
                next_retry text, last_error text, dead integer not null default 0, result_sha text,
                evidence_url text, updated text);
            create table if not exists accounts(key text primary key, user_id integer, pair_id integer);
            create table if not exists log(id integer primary key autoincrement, at text, run text, task text,
                step text, outcome text, detail text);
        """)

    @contextmanager
    def lock(self):
        fh = open(self.dir / "autopilot.lock", "w")
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            fh.close()
            raise Busy("another autopilot tick is running")
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)
            fh.close()

    def task(self, key: str) -> dict | None:
        r = self.db.execute("select * from tasks where key=?", (key,)).fetchone()
        return dict(r) if r else None

    def upsert(self, key: str, now: str, **kw):
        if not self.task(key):
            self.db.execute("insert into tasks(key, updated) values(?, ?)", (key, now))
        if kw:
            cols = ", ".join(f"{k}=?" for k in kw)
            self.db.execute(f"update tasks set {cols}, updated=? where key=?", (*kw.values(), now, key))

    def log(self, run: str, now: str, task: str | None, step: str, outcome: str, detail: dict | None = None):
        self.db.execute("insert into log(at, run, task, step, outcome, detail) values(?,?,?,?,?,?)",
                        (now, run, task, step, outcome, json.dumps(detail or {}, ensure_ascii=False, sort_keys=True)))

    def logs(self, run: str | None = None) -> list[dict]:
        q = "select * from log" + (" where run=?" if run else "") + " order by id"
        return [{**dict(r), "detail": json.loads(r["detail"])} for r in self.db.execute(q, (run,) if run else ())]

    def account(self, key: str) -> dict | None:
        r = self.db.execute("select * from accounts where key=?", (key,)).fetchone()
        return dict(r) if r else None

    def set_account(self, key: str, user_id: int, pair_id: int | None):
        self.db.execute("insert into accounts(key, user_id, pair_id) values(?,?,?) on conflict(key) do update set "
                        "user_id=excluded.user_id, pair_id=coalesce(excluded.pair_id, accounts.pair_id)",
                        (key, user_id, pair_id))


# ====================================================================== executors (AUTOMATED_TOOL)
def _office_registry(office_src: Path | None):
    """Reuse the PR #195 Registry loader (services.forum.registry) — same rules as its worker job."""
    if office_src and str(office_src) not in sys.path:
        sys.path.insert(0, str(office_src))
    from services.forum.registry import Registry  # noqa: WPS433
    return Registry


def exec_registry_integrity(task: dict, ctx: dict) -> dict:
    """Same invariants as #195 worker job `registry_integrity`, run on THIS repo's registry/ (read only)."""
    Registry = _office_registry(ctx.get("office_src"))
    reg = Registry(root=REPO_ROOT)
    # #195 Registry walks registry/*.md with an unsorted glob(); a registry_record's inferred parent then depends
    # on file-system order (seen in CI: digest differed between two runners). Recompute it order-independently.
    ids = set(reg.entities)
    order_dependent = sorted(e.id for e in reg.entities.values()
                             if e.type == "registry_record" and e.id[:-1] in ids
                             and reg.entities[e.id[:-1]].type == "registry_record")

    def parent(e):
        if e.type == "registry_record":
            return e.id[:-1] if e.id[:-1] in ids else ""
        return e.parent_id or ""
    rows = sorted((e.id, parent(e), e.type) for e in reg.entities.values())
    digest = hashlib.sha256(json.dumps(rows, ensure_ascii=False).encode()).hexdigest()
    chain = [x["id"] for x in reg.chain("691121")]
    problems = []
    if chain != ["911", "6911", "69112", "691121"]:
        problems.append(f"chain 691121 wrong: {chain}")
    bad = [e.id for e in reg.entities.values() if not e.id.isdigit()]
    if bad:
        problems.append(f"non-numeric IDs: {bad[:5]}")
    orphans = sorted(e.id for e in reg.entities.values() if e.parent_id and e.parent_id not in reg.entities
                     and e.type != "registry_record")
    finding = {"id": "PR195-REGISTRY-GLOB-ORDER", "severity": "LOW",
               "detail": "services/forum/registry.py: `for md in reg.glob('*.md')` is unsorted, so the inferred "
                         "parent of these registry_record IDs depends on directory order; worker "
                         "registry_integrity can report false drift across instances. Fix: sorted(reg.glob('*.md')).",
               "affected_ids": order_dependent} if order_dependent else None
    return {"check": "registry_integrity", "implementation": "services.forum.registry.Registry (PR #195) + worker rules",
            "entities": len(rows), "digest": digest, "chain_691121": chain, "orphans": orphans,
            "problems": problems, "digest_basis": "order-independent parents (see finding)",
            "finding_for_195": finding, "verdict_by_tool": "PASS" if not problems else "FAIL"}


def exec_working_link_audit(task: dict, ctx: dict) -> dict:
    """Every agent with a Registry ID in config/agents.json must have its Link Mẫu page and a Registry entry
    whose parent matches config. Read only."""
    Registry = _office_registry(ctx.get("office_src"))
    reg = Registry(root=REPO_ROOT)
    raw = json.loads((REPO_ROOT / "registry" / "ai-entity-registry.json").read_text(encoding="utf-8"))
    rows, problems = [], []
    for a in ctx["agents"].values():
        if not a["key"].isdigit():
            continue
        page = REPO_ROOT / (a.get("working_link") or "")
        e = reg.get(a["key"])
        ok_page = bool(a.get("working_link")) and page.is_file()
        # compare with the recorded parent_id (as test_dispatch does); #195's loader falls back to ai_country_id
        # for developers, reported separately so the two semantics are not confused
        ok_parent = a["key"] in raw and raw[a["key"]].get("parent_id") == a.get("parent")
        rows.append({"key": a["key"], "working_link": a.get("working_link"), "page_exists": ok_page,
                     "registry": bool(e), "parent_matches": ok_parent,
                     "parent_recorded": raw.get(a["key"], {}).get("parent_id"),
                     "parent_resolved_by_195": e.parent_id if e else None,
                     "page_sha256": hashlib.sha256(page.read_bytes()).hexdigest() if ok_page else None})
        if not (ok_page and ok_parent):
            problems.append(a["key"])
    return {"check": "working_link_audit", "agents": rows, "problems": problems,
            "verdict_by_tool": "PASS" if not problems else "FAIL"}


EXECUTORS = {"registry_integrity": exec_registry_integrity, "working_link_audit": exec_working_link_audit}


# ====================================================================== autopilot
def _task_idem(key: str) -> str:
    return "hub69-" + hashlib.sha256(key.encode()).hexdigest()[:32]


def _safe(key: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in key)


class Autopilot:
    def __init__(self, *, base: str, state_dir: Path, agents: dict, policy: dict, secrets: dict,
                 evidence_base: str, office_src: Path | None = None, retry: RetryPolicy | None = None,
                 sleep=None, transport=None, crash_after: str | None = None):
        self.base, self.agents, self.policy = base, agents, policy
        self.secrets = secrets  # {"gov": (email, pw), "agent_password": pw, "reviewer": {key: (email, pw)}}
        self.store = Store(state_dir)
        self.results_dir = Path(state_dir) / "results"
        self.evidence_base = evidence_base.rstrip("/")
        if not self.evidence_base.startswith("https://"):
            raise ValueError("evidence_base must be https:// (the #195 Evidence contract)")
        self.office_src = office_src
        self.retry = retry or RetryPolicy()
        self.sleep = sleep
        self.transport = transport
        self.crash_after = crash_after
        self._clients: dict[str, OfficeClient] = {}
        self.run_id = ""
        self.now = ""

    # ---------------------------------------------------------------- helpers
    def _log(self, task, step, outcome, **detail):
        self.store.log(self.run_id, self.now, task, step, outcome, detail)

    def _crash(self, step: str):
        if self.crash_after == step:
            raise SimulatedCrash(step)

    def client(self, who: str) -> OfficeClient:
        """Logged-in client for: 'gov', 'dispatcher', an agent key, or a reviewer key."""
        if who in self._clients:
            return self._clients[who]
        kw = {"retry": self.retry, "transport": self.transport,
              "log": lambda ev, d: self._log(None, "http", ev, **d)}
        if self.sleep:
            kw["sleep"] = self.sleep
        c = OfficeClient(self.base, **kw)
        if who == "gov":
            c.login(*self.secrets["gov"])
        elif who == "dispatcher":
            c.login("hub69-dispatch@sandbox.invalid", self.secrets["agent_password"],
                    register_name="HUB69 dispatcher (sandbox)")
        elif who in self.secrets.get("reviewer", {}):
            email, pw = self.secrets["reviewer"][who]
            c.login(email, pw, register_name=f"{who} (sandbox placeholder)")  # role comes only from #195 governance
        else:
            acct = self.agents[who].get("office_account")
            if not acct:
                raise OfficeError(None, f"agent {who} has no sandbox office_account", permanent=True)
            c.login(acct, self.secrets["agent_password"], register_name=f"{self.agents[who]['name']} {who} (sandbox)")
        self._clients[who] = c
        return c

    # ---------------------------------------------------------------- setup (sandbox only)
    def ensure_pair(self, key: str) -> tuple[int, int]:
        """Office + Siêu Bộ Đôi pair for an agent with a Registry ID. Idempotent: 409 → look it up."""
        acct = self.store.account(key)
        if acct and acct["pair_id"]:
            return acct["user_id"], acct["pair_id"]
        agent_c = self.client(key)
        uid = agent_c.user["id"]
        gov, disp = self.client("gov"), self.client("dispatcher")
        a = self.agents[key]
        gov.post("/api/office/offices", {"canonical_id": key, "platform": a["name"],
                                         "capabilities": ", ".join(a.get("capabilities", [])),
                                         "limits": "SANDBOX • HOLD ACTIVATION • không deploy, không cấp ID"},
                 ok=(201, 409))
        gov.post(f"/api/office/offices/{key}/maintainers/{disp.user['id']}", ok=(200, 201, 409))
        software = f"HUB69 autopilot executor ({key})"
        try:
            pid = disp.post("/api/office/pairs", {"canonical_id": key, "software": software, "lead_user_id": uid})["id"]
        except OfficeError as e:
            if e.status != 409:
                raise
            view = disp.get(f"/api/office/offices/{key}")
            pid = next(p["id"] for p in view["pairs"] if p.get("lead_user_id") == uid)
        self.store.set_account(key, uid, pid)
        self._log(None, "setup", "pair_ready", agent=key, user_id=uid, pair_id=pid)
        return uid, pid

    # ---------------------------------------------------------------- intake
    def intake(self, source) -> tuple[dict, list, list]:
        comments = source.fetch()
        by_login = {a["github_login"].lower(): k for k, a in self.agents.items() if a.get("github_login")}
        ops = {x.lower() for x in self.policy["operator_logins"]}
        msgs = []
        for c in comments:
            ms = parse_comment(c, source.channel, ops, by_login)
            msgs += ms
            for m in ms:
                cur = self.store.db.execute("insert or ignore into seen(ref, kind, task, first_seen) values(?,?,?,?)",
                                            (c["ref"] + ":" + m.kind, m.kind, m.task, self.now))
                if cur.rowcount:
                    self._log(m.task, "intake", "new_message", ref=c["ref"], kind=m.kind,
                              channel=source.channel, author=c.get("author_kind") or m.provenance,
                              actor=m.actor)
        q = Queue(self.policy, self.agents)
        q.allocate()
        for m in sorted(msgs, key=lambda m: (m.source.get("created_at") or "", m.source["ref"])):
            q.apply(m)
            q.allocate()
        snap = q.snapshot()
        for r in snap["rejections"]:
            if self.store.db.execute("insert or ignore into seen(ref, kind, task, first_seen) values(?,?,?,?)",
                                     ("reject:" + r["ref"], "REJECT", r["task"], self.now)).rowcount:
                self._log(r["task"], "intake", "rejected", ref=r["ref"], reason=r["reason"])
        return snap, comments, msgs

    # ---------------------------------------------------------------- per task
    def executor_for(self, t: dict) -> str | None:
        return self.agents.get(t["assignee"], {}).get("executors", {}).get(t.get("capability") or "")

    def process(self, t: dict) -> str:
        key = t["key"]
        rec = self.store.task(key) or {}
        uid, pair_id = self.ensure_pair(t["assignee"])
        reviewer_c = self.client(t["reviewer"])
        rid = reviewer_c.user["id"]
        agent = self.client(t["assignee"])
        disp = self.client("dispatcher")

        tid = rec.get("office_tid")
        if not tid:
            body = {"pair_id": pair_id, "title": t["title"][:200],
                    "description": f"HUB69 task {key} • source {t.get('source_url') or 'working link'} • "
                                   f"routed={t.get('routed')} capability={t.get('capability')}",
                    "acceptance": t.get("acceptance") or "Evidence (sha256) + independent review",
                    "reviewer_id": rid, "idempotency_key": _task_idem(key), "refs": [f"registry:{t['assignee']}"]}
            res = disp.post("/api/office/tasks", body)
            tid = res["id"]
            self.store.upsert(key, self.now, office_tid=tid, assignee=t["assignee"], reviewer=t["reviewer"],
                              capability=t.get("capability"), stage="OFFICE_CREATED")
            self._log(key, "office_create", "duplicate_reused" if res.get("duplicate") else "created",
                      office_tid=tid, idempotency_key=body["idempotency_key"], by="dispatcher (SANDBOX_ACCOUNT)")
            self._crash("office_create")

        for _ in range(8):  # reconcile loop: re-read, do the one missing step, repeat
            status = agent.get(f"/api/office/tasks/{tid}/loop")["status"]
            if status == "QUEUED":
                self._transition(agent, key, tid, "ack", "AUTO ACK • hub69 autopilot • AUTOMATED_TOOL", "ACKED")
            elif status in ("ACKED", "CHANGES_REQUESTED"):
                try:
                    self._transition(agent, key, tid, "start", "AUTO start", "STARTED")
                except OfficeError as e:
                    if e.status == 409 and "song song" in e.detail:  # #195 WIP limit = transient
                        raise OfficeError(409, "Office WIP limit reached; retry later", permanent=False)
                    raise
            elif status == "IN_PROGRESS":
                self._execute_and_submit(agent, key, tid, t)
            elif status == "IN_REVIEW":
                return self._handoff(reviewer_c, key, tid, rid, t)
            elif status in ("ACCEPTED", "CLOSED"):
                self.store.upsert(key, self.now, stage="REVIEWED")
                return "REVIEWED"
            else:
                raise OfficeError(None, f"unexpected Office status {status}", permanent=True)
        raise OfficeError(None, "reconcile loop did not converge", permanent=False)

    def _transition(self, agent, key, tid, action, note, stage):
        try:
            agent.post(f"/api/office/tasks/{tid}/{action}", {"note": note}, ok=(200,))
            self._log(key, action, "ok", office_tid=tid, actor=f"{agent.user['email']} (SANDBOX_ACCOUNT)")
        except OfficeError as e:
            if e.status == 409 and "Không thể" in e.detail:  # already moved by a previous (crashed) run
                self._log(key, action, "already_done", office_tid=tid, detail=e.detail)
            else:
                raise
        self.store.upsert(key, self.now, stage=stage)
        self._crash(action)

    def _execute_and_submit(self, agent, key, tid, t):
        exe = self.executor_for(t)
        fn = EXECUTORS[exe]
        self.results_dir.mkdir(parents=True, exist_ok=True)
        path = self.results_dir / f"{_safe(key)}.json"
        rec = self.store.task(key) or {}
        if path.is_file() and rec.get("result_sha") == hashlib.sha256(path.read_bytes()).hexdigest():
            sha = rec["result_sha"]
            self._log(key, "execute", "reused_result", file=path.name, sha256=sha)
        else:
            out = fn(t, {"agents": self.agents, "office_src": self.office_src})
            doc = {"task": key, "title": t["title"], "assignee": t["assignee"], "executor": exe,
                   "executor_kind": "AUTOMATED_TOOL (deterministic code, not an LLM decision)",
                   "office_tid": tid, "result": out}
            raw = (json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
            path.write_bytes(raw)
            sha = hashlib.sha256(raw).hexdigest()
            self.store.upsert(key, self.now, stage="EXECUTED", result_sha=sha)
            self._log(key, "execute", "ok", executor=exe, file=path.name, sha256=sha,
                      tool_verdict=out.get("verdict_by_tool"))
        self._crash("execute")
        url = f"{self.evidence_base}/{path.name}"
        try:
            agent.post(f"/api/office/tasks/{tid}/evidence",
                       {"kind": "test_report", "url": url, "sha": sha,
                        "description": f"{exe} output for {key}; sha256 of the committed result file"})
            self._log(key, "evidence", "stored", office_tid=tid, url=url, sha256=sha)
        except OfficeError as e:
            if e.status == 409:  # same Evidence already stored by an earlier run
                self._log(key, "evidence", "already_stored", office_tid=tid)
            else:
                raise
        self.store.upsert(key, self.now, stage="EVIDENCE_STORED", evidence_url=url)
        self._crash("evidence")
        self._transition(agent, key, tid, "submit", "AUTO submit → independent review", "EVIDENCE_STORED")

    def _handoff(self, reviewer_c, key, tid, rid, t) -> str:
        loop = reviewer_c.get(f"/api/office/tasks/{tid}/loop")  # read-back AS the reviewer
        if loop["status"] != "IN_REVIEW" or loop["reviewer_id"] != rid:
            raise OfficeError(None, f"handoff read-back mismatch: {loop['status']} reviewer {loop['reviewer_id']}",
                              permanent=True)
        rec = self.store.task(key) or {}
        if rec.get("stage") != "HANDED_TO_REVIEWER":
            self._log(key, "handoff", "visible_to_reviewer", office_tid=tid, reviewer=t["reviewer"],
                      reviewer_user_id=rid, next_stage=loop["next_stage"], review="PENDING_REAL_REVIEWER")
        self.store.upsert(key, self.now, stage="HANDED_TO_REVIEWER", attempts=0, last_error=None, next_retry=None)
        return "HANDED_TO_REVIEWER"

    # ---------------------------------------------------------------- tick
    def tick(self, source, now: datetime, run_id: str) -> dict:
        self.run_id, self.now = run_id, now.isoformat()
        with self.store.lock():
            snap, comments, msgs = self.intake(source)
            handled = []
            for t in snap["tasks"]:
                key = t["key"]
                exe = self.executor_for(t)
                rec = self.store.task(key) or {}
                if t["state"] == "OFFERED":
                    continue  # no slot yet (engine enforces max 5 + reserved P0)
                if not exe:
                    if not rec:
                        self.store.upsert(key, self.now, assignee=t["assignee"], reviewer=t["reviewer"],
                                          capability=t.get("capability"), stage="AWAITING_REAL_AGENT")
                        self._log(key, "route", "awaiting_real_agent", assignee=t["assignee"],
                                  reason="no automated executor for this capability; needs the real agent")
                    continue
                if rec.get("dead"):
                    continue
                if rec.get("stage") in ("HANDED_TO_REVIEWER", "REVIEWED") and rec.get("office_tid"):
                    # still verify cheaply that the reviewer has it; keeps stage honest if Office changed
                    pass
                if rec.get("next_retry") and rec["next_retry"] > self.now:
                    continue
                if not rec:
                    self.store.upsert(key, self.now, assignee=t["assignee"], reviewer=t["reviewer"],
                                      capability=t.get("capability"))
                    self._log(key, "route", "assigned", assignee=t["assignee"], reviewer=t["reviewer"],
                              capability=t.get("capability"), routed=t.get("routed"), executor=exe,
                              working_link=self.agents[t["assignee"]].get("working_link"), slot=t.get("slot"))
                before = rec.get("stage")
                try:
                    stage = self.process(t)
                    handled.append({"task": key, "stage": stage, "changed": stage != before})
                except SimulatedCrash:
                    raise
                except OfficeError as e:
                    rec = self.store.task(key) or {}
                    attempts = (rec.get("attempts") or 0) + 1
                    dead = e.permanent or attempts >= MAX_ATTEMPTS
                    nxt = (now + timedelta(seconds=min(30 * 2 ** (attempts - 1), 3600))).isoformat()
                    self.store.upsert(key, self.now, attempts=attempts, last_error=str(e), dead=int(dead),
                                      next_retry=None if dead else nxt)
                    self._log(key, "process", "dead_letter" if dead else "retry_scheduled", error=str(e),
                              attempts=attempts, next_retry=None if dead else nxt)
                    handled.append({"task": key, "stage": "DEAD_LETTER" if dead else "RETRY", "error": str(e)})
            return {"run": run_id, "now": self.now, "comments": len(comments), "messages": len(msgs),
                    "tasks": len(snap["tasks"]), "rejections": snap["rejections"], "handled": handled,
                    "snapshot": snap}

    def requeue(self, key: str, now: datetime):
        self.now = now.isoformat()
        self.store.upsert(key, self.now, dead=0, attempts=0, next_retry=None, last_error=None)
        self._log(key, "requeue", "ok")

    # ---------------------------------------------------------------- read-back + drafts
    def readback(self, key: str) -> dict:
        """Independent read of what the Office stored, from three viewpoints."""
        rec = self.store.task(key)
        tid = rec["office_tid"]
        gov_view = self.client("gov").get(f"/api/office/offices/{rec['assignee']}")
        task = next(x for x in gov_view["tasks"] if x["id"] == tid)
        rev = self.client(rec["reviewer"])
        return {
            "task_key": key, "office_tid": tid, "office_status": task["status"],
            "assignee": rec["assignee"], "reviewer": rec["reviewer"],
            "history": [{"from": h["from_status"], "to": h["to_status"], "actor_id": h["actor_id"], "note": h.get("note")}
                        for h in task["history"]],
            "evidence": [{"kind": e["kind"], "url": e["url"], "sha": e["sha"]} for e in task["evidence"]],
            "reviews": task["reviews"],
            "reviewer_loop": rev.get(f"/api/office/tasks/{tid}/loop"),
            "reviewer_board": [x for x in rev.get("/api/office/board")["tasks"] if x["id"] == tid],
            "guest_board_counts": OfficeClient(self.base).get("/api/office/board")["counts"],
        }

    def forum_drafts(self, keys: list[str]) -> list[dict]:
        """#201-template replies the autopilot WOULD post (HOLD). Same marker/idempotency scheme as cli post."""
        out = []
        for key in keys:
            rec = self.store.task(key)
            if not rec or rec["stage"] != "HANDED_TO_REVIEWER":
                continue
            a = self.agents[rec["assignee"]]
            for kind, body in (
                ("ACK+OUTPUT", f"**SI AI / Siêu Bộ Đôi:** {a['name']} (AUTOMATED_TOOL qua Working Link)\n"
                               f"**Link riêng / ID:** {rec['assignee']}\n**Task:** {key}\n**Trạng thái:** OUTPUT READY\n"
                               f"**Kết quả và Evidence URL:** {rec['evidence_url']} (sha256 `{rec['result_sha']}`)"),
                ("NEED_REVIEW", f"**CẦN REVIEW ĐỘC LẬP** • **Task:** {key}\nReviewer {rec['reviewer']}: Văn Phòng #195 "
                                f"task {rec['office_tid']} đang IN_REVIEW. Trả lời `**Trạng thái:** REVIEW` + "
                                f"`**Verdict:** PASS|FAIL`."),
            ):
                k = hashlib.sha256(f"autopilot|{kind}|{key}|{rec['result_sha']}".encode()).hexdigest()[:16]
                out.append({"key": k, "kind": kind, "task": key, "posted": False, "gate": "HOLD ACTIVATION",
                            "body": f"{DISPATCH_MARKER} key={k} -->\n{body}\n\n_HUB69 autopilot • SANDBOX • HOLD_"})
        return out


def secrets_from_env() -> dict:
    """Sandbox credentials come only from the environment (never committed)."""
    need = ["HUB69_SANDBOX_GOV_EMAIL", "HUB69_SANDBOX_GOV_PASSWORD", "HUB69_SANDBOX_AGENT_PASSWORD"]
    miss = [n for n in need if not os.environ.get(n)]
    if miss:
        raise SystemExit("missing env: " + ", ".join(miss))
    reviewers = {}
    for k, env in (("ReviewSI", "HUB69_SANDBOX_REVIEWSI"), ("SecuritySI", "HUB69_SANDBOX_SECURITYSI")):
        v = os.environ.get(env)  # "email:password"
        if v and ":" in v:
            email, pw = v.split(":", 1)
            reviewers[k] = (email, pw)
    return {"gov": (os.environ["HUB69_SANDBOX_GOV_EMAIL"], os.environ["HUB69_SANDBOX_GOV_PASSWORD"]),
            "agent_password": os.environ["HUB69_SANDBOX_AGENT_PASSWORD"], "reviewer": reviewers}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
