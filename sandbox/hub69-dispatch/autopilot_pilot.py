"""Full autopilot cycle on sandbox data, against a REAL PR #195 backend started locally.

  python3 sandbox/hub69-dispatch/autopilot_pilot.py --out sandbox/hub69-dispatch/evidence/autopilot-pilot

Steps: start #195 (ephemeral SQLite) → tick 1 (intake + route + Office + execute + handoff) → tick 2 (must be a
no-op: dedupe) → restart #195 on the same data dir → tick 3 (still a no-op, state survived) → read back from the
Office as governance, as the reviewer and as a guest → write the run log, read-back, #201 drafts (HOLD).
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "tests"))

from hub69_dispatch.adapters import FileSource  # noqa: E402
from hub69_dispatch.autopilot import Autopilot  # noqa: E402
from hub69_dispatch.cli import load_config  # noqa: E402
from office_harness import OFFICE_SHA, OfficeServer, office_src  # noqa: E402

BRANCH = "claude/cool-euler-gnwkfm"
FIXTURE = HERE / "fixtures" / "autopilot-working-link.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    try:
        rel = out.resolve().relative_to(HERE.parent.parent).as_posix()
    except ValueError:  # scratch run outside the repo: URL points at the committed pilot folder
        rel = "sandbox/hub69-dispatch/evidence/autopilot-pilot"
    evidence_base = f"https://github.com/charityfundplus/CFP.plus/blob/{BRANCH}/{rel}/results"
    src = office_src()
    if not src:
        print("BLOCKED: PR #195 source not available (set HUB69_OFFICE_SRC)")
        return 2
    agents_doc, policy = load_config()
    agents = {x["key"]: x for x in agents_doc["agents"]}
    state = Path(tempfile.mkdtemp(prefix="hub69-autopilot-"))
    srv = OfficeServer(src).start()
    srv.grant_securitysi()
    summary = {"office_backend": {"pr": 195, "sha": OFFICE_SHA, "mode": "CFP_SANDBOX_EPHEMERAL=1 (local uvicorn, SQLite)",
                                  "base": "http://127.0.0.1:<random port>"},
               "intake": {"channel": "working_link_file", "fixture": FIXTURE.relative_to(HERE).as_posix(),
                          "author_kind": "SANDBOX_FIXTURE"},
               "ticks": []}
    try:
        def pilot():
            return Autopilot(base=srv.base, state_dir=state, agents=agents, policy=policy, secrets=srv.secrets,
                             evidence_base=evidence_base, office_src=src)

        t0 = datetime(2026, 11, 13, 13, 5, tzinfo=timezone.utc)
        for i, label in enumerate(["tick-1", "tick-2-dedupe", "tick-3-after-office-restart"]):
            if label.startswith("tick-3"):
                srv.stop()
                srv.start()
            p = pilot()
            res = p.tick(FileSource(str(FIXTURE)), t0.replace(minute=5 + i), label)
            summary["ticks"].append({k: v for k, v in res.items() if k != "snapshot"})
            if i == 0:
                summary["queue_after_tick_1"] = [
                    {k: t[k] for k in ("key", "title", "state", "slot", "assignee", "reviewer", "capability", "routed")}
                    for t in res["snapshot"]["tasks"]]
        p = pilot()
        done = [r["key"] for r in p.store.db.execute("select key from tasks where stage='HANDED_TO_REVIEWER' order by key")]
        readback = {k: p.readback(k) for k in done}
        drafts = p.forum_drafts(done)
        logs = p.store.logs()
        tasks = [dict(r) for r in p.store.db.execute("select key, office_tid, assignee, reviewer, capability, stage, "
                                                      "attempts, dead, result_sha, evidence_url from tasks order by key")]
    finally:
        srv.stop()

    for gen in ("results", "run-log.jsonl", "summary.json", "readback.json", "forum201_drafts_HOLD.json"):
        g = out / gen  # remove only generated files; hand-written REPORT.md stays
        shutil.rmtree(g) if g.is_dir() else g.unlink(missing_ok=True)
    (out / "results").mkdir(parents=True)
    for f in sorted((state / "results").glob("*.json")):
        shutil.copy(f, out / "results" / f.name)
    for f in (out / "results").glob("*.json"):  # Evidence sha in the Office must match the committed file
        import hashlib
        sha = hashlib.sha256(f.read_bytes()).hexdigest()
        assert any(e["sha"] == sha for r in readback.values() for e in r["evidence"]), f.name
    for lg in logs:  # strip volatile per-run values (random port / user agent) — none expected, keep explicit
        lg["detail"].pop("base", None)
    (out / "run-log.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in logs),
                                       encoding="utf-8")
    summary["tasks"] = tasks
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                                      encoding="utf-8")
    (out / "readback.json").write_text(json.dumps(readback, ensure_ascii=False, indent=2, sort_keys=True,
                                                  default=str) + "\n", encoding="utf-8")
    (out / "forum201_drafts_HOLD.json").write_text(json.dumps(drafts, ensure_ascii=False, indent=2) + "\n",
                                                   encoding="utf-8")
    print(json.dumps({"handed_to_reviewer": done, "tasks": tasks}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
