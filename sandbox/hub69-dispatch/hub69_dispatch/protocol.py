"""Parse forum comments into HUB 69 protocol messages.

Two input shapes are accepted, both plain text that any SI AI (or its human operator) can type:

1. The existing #201 template (bold labels), plus an optional ``**Task:**`` line:

       **SI AI / Siêu Bộ Đôi:** Claude Code
       **Link riêng / ID:** 691121
       **Task:** 201#6813472700
       **Trạng thái:** ACK
       **Kết quả và Evidence URL:** https://...

2. A compact header, one per comment:

       HUB69 ACK 201#6813472700
       actor: 691121

Task keys are NOT new IDs: a task is keyed by the native reference of the message that opened it
(``<issue>#<comment id>`` on GitHub, the page id on Notion, the row id in a Working Link file).
Nothing here allocates a CFP+ numeric ID.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field, asdict

KINDS = ("TASK", "ACK", "RESULT", "EVIDENCE", "REVIEW", "BLOCKED")
DISPATCH_MARKER = "<!-- hub69-dispatch"
URL_RE = re.compile(r"https?://[^\s)\]>\"'`]+")
COMPACT_RE = re.compile(r"^\s*HUB69\s+(TASK|ACK|RESULT|EVIDENCE|REVIEW|BLOCKED)\b\s*([^\s]*)", re.I | re.M)
TASK_REF_RE = re.compile(r"^[0-9A-Za-z_.:-]+#[0-9A-Za-z_.:-]+$")

# #201 template status → protocol kind. VERIFIED is a REVIEW claim and is checked like any review.
STATUS_MAP = {
    "OPEN": "TASK", "TASK": "TASK",
    "ACK": "ACK", "WORKING": "ACK",
    "OUTPUT READY": "RESULT", "RESULT": "RESULT",
    "EVIDENCE": "EVIDENCE",
    "BLOCKED": "BLOCKED",
    "VERIFIED": "REVIEW", "REVIEW": "REVIEW",
}


def _fold(s: str) -> str:
    """Lowercase + strip Vietnamese diacritics so 'Trạng thái' == 'trang thai'."""
    s = unicodedata.normalize("NFD", s.replace("đ", "d").replace("Đ", "D"))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower().strip()


# folded label → field
LABELS = {
    "si ai / sieu bo doi": "actor_name", "si ai": "actor_name", "actor": "actor", "agent": "actor",
    "link rieng / id": "actor_id", "id": "actor_id",
    "task": "task", "task id": "task", "nhiem vu id": "task",
    "nhiem vu": "title", "title": "title",
    "trang thai": "status", "status": "status",
    "ket qua va evidence url": "result", "ket qua": "result", "result": "result", "evidence": "evidence",
    "vuong mac / next action": "next", "blocker": "next", "next action": "next",
    "assignee": "assignee", "nguoi thuc thi": "assignee",
    "reviewer": "reviewer", "nguoi review": "reviewer",
    "priority": "priority", "uu tien": "priority",
    "verdict": "verdict", "ket luan": "verdict",
    "acceptance": "acceptance", "tieu chi nghiem thu": "acceptance",
    "office": "office", "working link": "office",
}
LABEL_LINE = re.compile(r"^\s*(?:[-*•]\s*)?\*\*([^*]+?):?\*\*:?\s*(.*)$")
PLAIN_LINE = re.compile(r"^\s*([A-Za-zÀ-ỹđĐ /]+?)\s*:\s*(.*)$")


@dataclass
class Message:
    kind: str
    task: str | None            # task key (native ref of the opening TASK) or None
    actor: str                  # numeric Registry ID if given, else declared name, else "UNKNOWN"
    actor_name: str
    source: dict                # channel, ref, url, author_login, created_at
    fields: dict = field(default_factory=dict)
    urls: list = field(default_factory=list)
    verdict: str | None = None  # PASS | FAIL for REVIEW
    provenance: str = "unverified"

    def to_dict(self) -> dict:
        return asdict(self)


def _first_numeric_id(s: str) -> str | None:
    m = re.search(r"(?<![\d])(\d{2,})(?![\d])", s or "")
    return m.group(1) if m else None


def _parse_fields(body: str) -> dict:
    out: dict[str, str] = {}
    last = None
    for line in body.splitlines():
        m = LABEL_LINE.match(line) or PLAIN_LINE.match(line)
        if m:
            key = LABELS.get(_fold(m.group(1)))
            if key:
                out[key] = m.group(2).strip()
                last = key
                continue
        if last and line.strip() and not line.lstrip().startswith(("**", "#")):
            out[last] = (out[last] + "\n" + line.strip()).strip()
        elif not line.strip():
            last = None if last not in ("result", "evidence", "next") else last
    return out


def _status_kind(status: str) -> str | None:
    s = status.upper().replace("*", "").strip()
    for k in sorted(STATUS_MAP, key=len, reverse=True):  # "OUTPUT READY" before "OUTPUT"
        if s.startswith(k):
            return STATUS_MAP[k]
    return None


def parse_comment(comment: dict, channel: str, operator_logins: set[str], agents_by_login: dict) -> list[Message]:
    """Return 0..2 protocol messages for one comment. Dispatcher-authored comments are ignored (anti-loop)."""
    body = comment.get("body") or ""
    if DISPATCH_MARKER in body:
        return []
    ref = comment["ref"]
    login = (comment.get("author_login") or "").lower()
    source = {"channel": channel, "ref": ref, "url": comment.get("url"), "author_login": login,
              "created_at": comment.get("created_at")}
    f = _parse_fields(body)
    compact = COMPACT_RE.search(body)
    kind = None
    task = f.get("task")
    if compact:
        kind = compact.group(1).upper()
        task = compact.group(2) or task
    elif "status" in f:
        kind = _status_kind(f["status"])
    if not kind:
        return []
    if task:
        task = task.strip().strip("`").split()[0]
        if not TASK_REF_RE.match(task):
            task = None
    if kind == "TASK":
        task = ref  # the opening comment's own native ref is the task key — no ID is invented

    actor_name = f.get("actor_name") or f.get("actor") or ""
    actor = _first_numeric_id(f.get("actor_id", "")) or _first_numeric_id(f.get("actor", "")) \
        or (actor_name.split("(")[0].strip() or "UNKNOWN")

    # Who really wrote it? A comment posted from the operator's account on behalf of an AI is a relay,
    # not a runtime ACK by that AI. Only a login bound to the agent in config counts as direct.
    bound = agents_by_login.get(login)
    if bound and bound == actor:
        provenance = "direct_bound_login"
    elif login in operator_logins:
        provenance = "relayed_by_operator"
    else:
        provenance = "unverified_login"

    urls = URL_RE.findall("\n".join([f.get("result", ""), f.get("evidence", "")])) if kind != "TASK" else []
    verdict = None
    if kind == "REVIEW":
        v = (f.get("verdict") or f.get("status") or "").upper()
        verdict = "FAIL" if "FAIL" in v else ("PASS" if ("PASS" in v or "VERIFIED" in v) else None)

    msg = Message(kind=kind, task=task, actor=actor, actor_name=actor_name or actor, source=source,
                  fields=f, urls=urls, verdict=verdict, provenance=provenance)
    msgs = [msg]
    # Template "OUTPUT READY" with URLs carries both the RESULT and its EVIDENCE.
    if kind == "RESULT" and urls and not compact:
        msgs.append(Message(kind="EVIDENCE", task=task, actor=actor, actor_name=msg.actor_name, source=source,
                            fields=f, urls=urls, provenance=provenance))
    return msgs
