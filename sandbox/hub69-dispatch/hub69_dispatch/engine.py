"""Shared HUB 69 task queue: fold protocol messages into task state, grant execution slots, draft replies.

Pure function of (messages, policy, agents, now) → state. No network, no clock reads, so every run is
reproducible from the same inputs and can be re-checked by an independent reviewer.

Lifecycle (Luật Thép: TASK OFFERED ≠ ACK, OUTPUT ≠ VERIFIED, no Evidence = not DONE, maker ≠ reviewer):

    OFFERED ─slot granted→ DISPATCHED ─ACK→ ACKED ─RESULT→ RESULT_READY ─EVIDENCE→ IN_REVIEW
        IN_REVIEW ─REVIEW PASS→ VERIFIED (awaits Human Governance decision; never auto-closed)
        IN_REVIEW ─REVIEW FAIL→ ACKED (rework, keeps its slot)
    any active ─BLOCKED→ BLOCKED (keeps its slot so the blocker stays visible; next RESULT/ACK resumes)
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .protocol import Message, DISPATCH_MARKER

ACTIVE = ("DISPATCHED", "ACKED", "RESULT_READY", "IN_REVIEW", "BLOCKED")
PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


@dataclass
class Task:
    key: str
    title: str
    priority: str
    assignee: str
    reviewer: str
    opened_by: str
    opened_at: str
    source_url: str | None
    acceptance: str = ""
    capability: str = ""
    routed: str = "named"              # "auto" = chosen by capability + Working Link + load
    state: str = "OFFERED"
    slot: str | None = None            # "shared" | "reserved_p0"
    ack: dict | None = None
    results: list = field(default_factory=list)
    evidence: list = field(default_factory=list)
    reviews: list = field(default_factory=list)
    blockers: list = field(default_factory=list)
    history: list = field(default_factory=list)
    last_activity: str | None = None


def _ts(s: str | None) -> datetime | None:
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _norm_priority(p: str | None) -> str:
    p = (p or "").upper()
    for k in PRIORITY_ORDER:
        if k in p:
            return k
    return "P2"


class Queue:
    def __init__(self, policy: dict, agents: dict):
        self.policy = policy
        self.agents = agents  # key: numeric ID or PENDING name → agent record
        self.tasks: dict[str, Task] = {}
        self.rejections: list[dict] = []
        self.warnings: list[dict] = []
        self.max_parallel = int(policy["max_parallel"])
        self.reserved_owners = set(policy["reserved_p0"]["owners"])

    # ---------- identity ----------
    def resolve(self, who: str | None) -> str:
        """Map a declared name or ID to the canonical agent key; unknown stays as given (never invented)."""
        if not who:
            return "UNKNOWN"
        w = who.strip()
        if w in self.agents:
            return w
        lw = w.lower()
        for key, a in self.agents.items():
            names = [a.get("name", "")] + a.get("aliases", [])
            if any(lw == n.lower() or lw.startswith(n.lower() + " ") for n in names if n):
                return key
        return w

    # ---------- routing ----------
    def route(self, capability: str, exclude: set | None = None) -> str | None:
        """Pick an agent for a capability. Deterministic: must hold the capability AND a Working Link
        (published Link Mẫu page); prefer agents with an automated executor for it (can actually work),
        then lowest active load, then key. Never returns an excluded agent (maker ≠ checker)."""
        exclude = exclude or set()
        load = {}
        for t in self.tasks.values():
            if t.state in ACTIVE:
                load[t.assignee] = load.get(t.assignee, 0) + 1
        def reachable(a):  # executors need a Working Link; reviewers need an Office account to receive the review
            return a.get("working_link") or (capability == "review" and a.get("office_account"))
        cands = [k for k, a in self.agents.items()
                 if capability in a.get("capabilities", []) and reachable(a) and k not in exclude]
        if not cands:
            return None
        return min(cands, key=lambda k: (0 if capability in self.agents[k].get("executors", {}) else 1,
                                         load.get(k, 0), k))

    # ---------- folding ----------
    def _reject(self, m: Message, reason: str):
        self.rejections.append({"ref": m.source["ref"], "url": m.source.get("url"), "kind": m.kind,
                                "task": m.task, "actor": m.actor, "reason": reason})

    def apply(self, m: Message):
        actor = self.resolve(m.actor)
        if m.kind == "TASK":
            return self._open(m, actor)
        if not m.task:
            return self._reject(m, "no task reference: add '**Task:** <issue>#<comment id>' of the TASK")
        t = self.tasks.get(m.task)
        if not t:
            return self._reject(m, f"unknown task {m.task}")
        step = {"kind": m.kind, "actor": actor, "at": m.source.get("created_at"), "ref": m.source["ref"],
                "url": m.source.get("url"), "provenance": m.provenance}
        handler = getattr(self, "_" + m.kind.lower())
        err = handler(t, m, actor, step)
        if err:
            return self._reject(m, err)
        t.history.append(step)
        t.last_activity = m.source.get("created_at")

    def _open(self, m: Message, actor: str):
        f = m.fields
        title = (f.get("title") or "").strip()
        if not title:
            return self._reject(m, "TASK needs '**Nhiệm vụ:**' (title)")
        cap = (f.get("capability") or "").strip().lower()
        want_auto = (f.get("assignee") or "").strip().lower() in ("", "auto") and cap
        if want_auto:
            assignee = self.route(cap)
            if not assignee:
                return self._reject(m, f"no agent with capability '{cap}' and a Working Link")
        else:
            assignee = self.resolve(f.get("assignee") or f.get("actor_id") or m.actor)
        rv = (f.get("reviewer") or "").strip()
        reviewer = self.route("review", exclude={assignee}) if rv.lower() == "auto" else self.resolve(rv)
        if reviewer in (None, "", "UNKNOWN"):
            return self._reject(m, "TASK needs an independent '**Reviewer:**'")
        if reviewer == assignee:
            return self._reject(m, "reviewer must differ from assignee (maker ≠ checker)")
        norm = " ".join(title.lower().split())
        for other in self.tasks.values():
            if " ".join(other.title.lower().split()) == norm and other.state != "VERIFIED":
                return self._reject(m, f"duplicate of open task {other.key}")
        t = Task(key=m.task, title=title, priority=_norm_priority(f.get("priority")), assignee=assignee,
                 reviewer=reviewer, opened_by=actor, opened_at=m.source.get("created_at") or "",
                 source_url=m.source.get("url"), acceptance=f.get("acceptance", ""), capability=cap,
                 routed="auto" if want_auto else "named")
        t.history.append({"kind": "TASK", "actor": actor, "at": t.opened_at, "ref": m.source["ref"],
                          "url": t.source_url, "provenance": m.provenance})
        t.last_activity = t.opened_at
        for who in (assignee, reviewer):
            if who not in self.agents:
                self.warnings.append({"task": t.key, "warning": f"{who} not in agents config (ID PENDING?)"})
        self.tasks[t.key] = t

    def _ack(self, t, m, actor, step):
        if actor != t.assignee:
            return f"ACK must come from assignee {t.assignee}, got {actor}"
        if t.state == "OFFERED":
            return "no execution slot granted yet (queue full); ACK not accepted — wait for DISPATCHED"
        if t.state not in ("DISPATCHED", "BLOCKED"):
            return f"ACK not valid in state {t.state}"
        t.ack = step
        t.state = "ACKED"

    def _result(self, t, m, actor, step):
        if actor != t.assignee:
            return f"RESULT must come from assignee {t.assignee}"
        if t.state not in ("ACKED", "RESULT_READY", "BLOCKED"):
            return f"RESULT not valid in state {t.state} (ACK first)"
        t.results.append({**step, "urls": m.urls, "text": m.fields.get("result", "")[:500]})
        t.state = "RESULT_READY"

    def _evidence(self, t, m, actor, step):
        if actor != t.assignee:
            return f"EVIDENCE must come from assignee {t.assignee}"
        if not m.urls:
            return "EVIDENCE needs at least one URL"
        if t.state not in ("RESULT_READY", "IN_REVIEW"):
            return f"EVIDENCE not valid in state {t.state} (RESULT first)"
        t.evidence.append({**step, "urls": m.urls})
        t.state = "IN_REVIEW"

    def _review(self, t, m, actor, step):
        if actor == t.assignee:
            return "self-review rejected (maker ≠ checker)"
        if actor != t.reviewer:
            return f"REVIEW must come from assigned reviewer {t.reviewer}"
        if t.state != "IN_REVIEW":
            return f"REVIEW not valid in state {t.state} (needs EVIDENCE)"
        if m.verdict not in ("PASS", "FAIL"):
            return "REVIEW needs verdict PASS or FAIL"
        t.reviews.append({**step, "verdict": m.verdict})
        t.state = "VERIFIED" if m.verdict == "PASS" else "ACKED"
        if t.state == "VERIFIED":
            t.slot = None  # frees the slot; closing still needs Human Governance

    def _blocked(self, t, m, actor, step):
        if actor not in (t.assignee, t.reviewer):
            return "BLOCKED must come from assignee or reviewer"
        if t.state not in ACTIVE:
            return f"BLOCKED not valid in state {t.state}"
        t.blockers.append({**step, "text": m.fields.get("next", "")[:500]})
        t.state = "BLOCKED"

    # ---------- slots ----------
    def _is_reserved_eligible(self, t: Task) -> bool:
        return t.priority == "P0" and t.assignee in self.reserved_owners

    def allocate(self):
        """Grant slots by priority then age. Max N active; one slot only for P0 of the reserved owners."""
        active = [t for t in self.tasks.values() if t.state in ACTIVE]
        shared_cap = self.max_parallel - 1
        used_shared = sum(1 for t in active if t.slot == "shared")
        used_reserved = sum(1 for t in active if t.slot == "reserved_p0")
        waiting = sorted((t for t in self.tasks.values() if t.state == "OFFERED"),
                         key=lambda t: (PRIORITY_ORDER[t.priority], t.opened_at))
        for t in waiting:
            if self._is_reserved_eligible(t) and used_reserved == 0:
                t.slot, t.state = "reserved_p0", "DISPATCHED"
                used_reserved += 1
            elif used_shared < shared_cap:
                t.slot, t.state = "shared", "DISPATCHED"
                used_shared += 1
        assert used_shared + used_reserved <= self.max_parallel

    # ---------- outbox ----------
    def outbox(self, now: datetime) -> list[dict]:
        stale_after = timedelta(hours=float(self.policy["nudge_after_hours"]))
        out = []

        def add(kind, task, to, text):
            key = hashlib.sha256(f"{kind}|{task.key if task else '-'}|{to}|{task.state if task else ''}"
                                 .encode()).hexdigest()[:16]
            body = f"{DISPATCH_MARKER} key={key} -->\n{text}\n\n_HUB69 dispatch • SANDBOX • HOLD ACTIVATION_"
            out.append({"key": key, "kind": kind, "task": task.key if task else None, "to": to, "body": body})

        for t in sorted(self.tasks.values(), key=lambda t: (PRIORITY_ORDER[t.priority], t.opened_at)):
            name = lambda k: self.agents.get(k, {}).get("name", k)  # noqa: E731
            link = f"**Task:** {t.key}"
            if t.state == "DISPATCHED":
                add("DISPATCH", t, t.assignee,
                    f"**TASK DISPATCHED** • {t.priority} • slot `{t.slot}`\n{link}\n**Nhiệm vụ:** {t.title}\n"
                    f"**Người thực thi:** {name(t.assignee)} ({t.assignee}) • **Reviewer:** {name(t.reviewer)} ({t.reviewer})\n"
                    f"Trả lời ACK bằng mẫu #201 kèm dòng Task ở trên. Chưa có ACK thật = chưa nhận việc.")
            elif t.state == "OFFERED":
                add("WAITING_SLOT", t, t.assignee,
                    f"**QUEUED** • {t.priority} • đủ {self.max_parallel} việc song song, chờ slot.\n{link}")
            elif t.state == "IN_REVIEW":
                add("NEED_REVIEW", t, t.reviewer,
                    f"**CẦN REVIEW ĐỘC LẬP** • {link}\nEvidence: " + ", ".join(u for e in t.evidence for u in e["urls"]) +
                    f"\nReviewer {name(t.reviewer)} ({t.reviewer}): trả lời `**Trạng thái:** REVIEW` + `**Verdict:** PASS|FAIL`.")
            elif t.state == "VERIFIED":
                add("HUMAN_DECISION", t, "human_governance",
                    f"**VERIFIED bởi reviewer độc lập** • {link}\nChờ Human Governance quyết định đóng/áp dụng. "
                    f"Không tự merge/deploy/publish.")
            elif t.state == "BLOCKED":
                add("BLOCKER", t, "cmp_267", f"**BLOCKED** • {link}\n" + (t.blockers[-1]["text"] if t.blockers else ""))
            if t.state in ("DISPATCHED", "ACKED", "RESULT_READY") and t.last_activity:
                if now - _ts(t.last_activity) > stale_after:
                    add("NUDGE", t, t.assignee, f"**NHẮC** • {link} • không có cập nhật > {stale_after}.")
        for r in self.rejections:
            key = hashlib.sha256(("REJECT|" + r["ref"]).encode()).hexdigest()[:16]
            out.append({"key": key, "kind": "REJECTED", "task": r["task"], "to": r["actor"],
                        "body": f"{DISPATCH_MARKER} key={key} -->\n**KHÔNG GHI NHẬN** {r['kind']} ({r['ref']}): "
                                f"{r['reason']}\n\n_HUB69 dispatch • SANDBOX • HOLD ACTIVATION_"})
        return out

    def snapshot(self) -> dict:
        tasks = []
        for t in self.tasks.values():
            d = dict(t.__dict__)
            tasks.append(d)
        active = [t for t in self.tasks.values() if t.state in ACTIVE]
        return {
            "slots": {"max_parallel": self.max_parallel,
                      "active": len(active),
                      "reserved_p0_owners": sorted(self.reserved_owners),
                      "reserved_p0_in_use": any(t.slot == "reserved_p0" for t in active)},
            "tasks": tasks, "rejections": self.rejections, "warnings": self.warnings,
        }


def run(messages: list[Message], policy: dict, agents: dict, now: datetime) -> tuple[dict, list[dict]]:
    """Fold messages in time order, allocating slots after every step (as a live dispatcher would)."""
    q = Queue(policy, agents)
    ordered = sorted(messages, key=lambda m: (m.source.get("created_at") or "", m.source["ref"]))
    q.allocate()
    for m in ordered:
        q.apply(m)
        q.allocate()
    return q.snapshot(), q.outbox(now)
