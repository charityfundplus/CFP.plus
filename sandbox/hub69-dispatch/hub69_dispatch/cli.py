"""hub69-dispatch CLI.

  python3 sandbox/hub69-dispatch/run.py plan --source file:fixtures/x.json --out evidence/run1 [--now ISO]
  python3 sandbox/hub69-dispatch/run.py plan --source github:charityfundplus/CFP.plus#201 --out /tmp/x
  python3 sandbox/hub69-dispatch/run.py post --source github:...#201 --out ...   # HOLD unless gate open

`post` sends only outbox items whose idempotency key is not already present in the channel, and only when
BOTH HUB69_DISPATCH_ENABLED=1 and HUB69_HUMAN_APPROVAL=<link to the Human Governance decision> are set.
Otherwise it exits 3 with HOLD ACTIVATION and sends nothing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from .adapters import CMP267Sink, NotionSink, make_source
from .engine import run
from .protocol import DISPATCH_MARKER, parse_comment

HERE = Path(__file__).resolve().parent.parent


def load_config():
    agents = json.loads((HERE / "config" / "agents.json").read_text(encoding="utf-8"))
    policy = json.loads((HERE / "config" / "policy.json").read_text(encoding="utf-8"))
    return agents, policy


def build(source_spec: str, now: datetime):
    agents_doc, policy = load_config()
    agents = {a["key"]: a for a in agents_doc["agents"]}
    by_login = {a["github_login"].lower(): a["key"] for a in agents_doc["agents"] if a.get("github_login")}
    src = make_source(source_spec)
    comments = src.fetch()
    msgs = []
    for c in comments:
        msgs += parse_comment(c, src.channel, set(x.lower() for x in policy["operator_logins"]), by_login)
    snapshot, outbox = run(msgs, policy, agents, now)
    existing = {line.split("key=")[1].split()[0] for c in comments for line in (c.get("body") or "").splitlines()
                if DISPATCH_MARKER in line and "key=" in line}
    for o in outbox:
        o["already_posted"] = o["key"] in existing
    channels = [src.status(), NotionSink().status(), CMP267Sink().status()]
    return src, comments, msgs, snapshot, outbox, channels


def board_md(snapshot: dict, outbox: list[dict], channels: list[dict], meta: dict) -> str:
    s = snapshot["slots"]
    lines = [f"# HUB 69 • Hàng đợi điều phối • {meta['now']}", "",
             "**SANDBOX PRACTICE GO • HOLD ACTIVATION • PRODUCTION NO GO**", "",
             f"Nguồn: `{meta['source']}` • {meta['comments']} bình luận • {meta['messages']} thông điệp giao thức • "
             f"input sha256 `{meta['input_sha256'][:16]}`", "",
             f"Slot: **{s['active']}/{s['max_parallel']}** đang thực thi • slot P0 dành riêng cho "
             f"{', '.join(s['reserved_p0_owners'])}: {'đang dùng' if s['reserved_p0_in_use'] else 'trống'}", "",
             "| Task | P | Trạng thái | Slot | Người thực thi | Reviewer | ACK (nguồn gốc) | Evidence |",
             "|---|---|---|---|---|---|---|---|"]
    for t in snapshot["tasks"]:
        ack = (t["ack"] or {}).get("provenance", "—")
        ev = "<br>".join(u for e in t["evidence"] for u in e["urls"]) or "—"
        ref = f"[{t['key']}]({t['source_url']})" if t['source_url'] else f"`{t['key']}`"
        lines.append(f"| {ref} {t['title'][:60]} | {t['priority']} | **{t['state']}** | "
                     f"{t['slot'] or '—'} | {t['assignee']} | {t['reviewer']} | {ack} | {ev} |")
    if snapshot["rejections"]:
        lines += ["", "## Không ghi nhận (vi phạm quy tắc)", ""]
        lines += [f"- `{r['ref']}` {r['kind']} từ {r['actor']}: {r['reason']}" for r in snapshot["rejections"]]
    if snapshot["warnings"]:
        lines += ["", "## Cảnh báo", ""] + [f"- {w['task']}: {w['warning']}" for w in snapshot["warnings"]]
    lines += ["", "## Kênh", ""] + [f"- {json.dumps(c, ensure_ascii=False)}" for c in channels]
    lines += ["", f"## Hộp thư đi ({len(outbox)}; chưa gửi — HOLD)", ""]
    lines += [f"- `{o['key']}` {o['kind']} → {o['to']} • task {o['task']}"
              f"{' • đã có trên kênh' if o['already_posted'] else ''}" for o in outbox]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="hub69-dispatch")
    ap.add_argument("cmd", choices=["plan", "post"])
    ap.add_argument("--source", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--now", help="ISO time for reproducible runs (default: current UTC)")
    a = ap.parse_args(argv)
    now = datetime.fromisoformat(a.now.replace("Z", "+00:00")) if a.now else datetime.now(timezone.utc)

    src, comments, msgs, snapshot, outbox, channels = build(a.source, now)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(comments, ensure_ascii=False, sort_keys=True).encode()
    meta = {"now": now.isoformat(), "source": a.source, "comments": len(comments), "messages": len(msgs),
            "input_sha256": hashlib.sha256(raw).hexdigest()}
    (out / "input.json").write_text(json.dumps(comments, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "state.json").write_text(json.dumps({"meta": meta, "channels": channels, **snapshot},
                                               ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "outbox.json").write_text(json.dumps(outbox, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "notion_rows.json").write_text(json.dumps(NotionSink().payload(snapshot), ensure_ascii=False, indent=2),
                                          encoding="utf-8")
    (out / "cmp267_plan.json").write_text(json.dumps(CMP267Sink().payload(snapshot), ensure_ascii=False, indent=2),
                                          encoding="utf-8")
    (out / "BOARD.md").write_text(board_md(snapshot, outbox, channels, meta), encoding="utf-8")
    print(f"plan: {len(snapshot['tasks'])} tasks, {snapshot['slots']['active']}/{snapshot['slots']['max_parallel']} "
          f"active, {len(snapshot['rejections'])} rejected, {len(outbox)} outbox → {out}")

    if a.cmd == "post":
        approval = os.environ.get("HUB69_HUMAN_APPROVAL", "")
        if os.environ.get("HUB69_DISPATCH_ENABLED") != "1" or not approval.startswith("https://"):
            print("HOLD ACTIVATION: set HUB69_DISPATCH_ENABLED=1 and HUB69_HUMAN_APPROVAL=<decision URL>. Nothing sent.")
            return 3
        sent = []
        for o in outbox:
            if not o["already_posted"]:
                sent.append({**src.post_comment(o["body"] + f"\n\nApproval: {approval}"), "key": o["key"]})
        (out / "sent.json").write_text(json.dumps(sent, indent=2), encoding="utf-8")
        print(f"posted {len(sent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
