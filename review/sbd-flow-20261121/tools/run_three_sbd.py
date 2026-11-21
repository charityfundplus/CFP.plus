"""Independent review run: autopilot (PR #207) + Office (PR #195 @287ce64) with fake 3-SBD fixture."""
import json, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path
HERE = Path(sys.argv[1]).resolve(); FIX = sys.argv[2]; OUT = Path(sys.argv[3]); OUT.mkdir(parents=True, exist_ok=True)
sys.path[:0] = [str(HERE), str(HERE / "tests")]
from hub69_dispatch.adapters import FileSource
from hub69_dispatch.autopilot import Autopilot
from hub69_dispatch.cli import load_config
from office_harness import OfficeServer, office_src
agents_doc, policy = load_config(); agents = {x["key"]: x for x in agents_doc["agents"]}
state = Path(tempfile.mkdtemp(prefix="cc-review-")); srv = OfficeServer(office_src()).start(); srv.grant_securitysi()
out = {"ticks": []}
try:
    mk = lambda: Autopilot(base=srv.base, state_dir=state, agents=agents, policy=policy, secrets=srv.secrets,
                           evidence_base="https://sandbox.invalid/claude-review/results", office_src=office_src())
    t0 = datetime(2026, 11, 21, 8, 10, tzinfo=timezone.utc)
    for i, lab in enumerate(["tick-1", "tick-2-rerun", "tick-3-after-office-restart"]):
        if i == 2: srv.stop(); srv.start()
        r = mk().tick(FileSource(FIX), t0.replace(minute=10 + i), lab)
        out["ticks"].append({k: v for k, v in r.items() if k != "snapshot"})
    p = mk()
    out["tasks"] = [dict(r) for r in p.store.db.execute("select key, office_tid, assignee, reviewer, capability, stage, attempts, dead, result_sha, evidence_url from tasks order by key")]
    done = [t["key"] for t in out["tasks"] if t["stage"] == "HANDED_TO_REVIEWER"]
    out["readback"] = {k: p.readback(k) for k in done}
    out["run_log"] = p.store.logs()
finally:
    srv.stop()
(OUT / "result.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str))
for t in out["tasks"]: print(json.dumps(t, ensure_ascii=False))
for tk in out["ticks"]: print(json.dumps(tk, ensure_ascii=False)[:400])
