"""Chạy phân công 115 Team trên kiểm kê thật của 87788 và ghi Evidence JSON.

python scripts/run_team_formation.py --teams 115 --min-size 33 --max-per-trio 40
"""

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / "87788-super-trio"))

import trio  # noqa: E402  (bộ kiểm kê 87788, tái sử dụng)
from sqz.teams import form_teams  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--teams", type=int, default=115)
ap.add_argument("--min-size", type=int, default=33)
ap.add_argument("--max-per-trio", type=int, default=40)
ap.add_argument("--time-limit", type=float, default=60)
ap.add_argument("--out", type=Path, default=ROOT / "evidence" / "team_formation.json")
a = ap.parse_args()
rows, excluded, prov = trio.load_inventory()
ids = [r["id"] for r in trio.check_inventory(rows, excluded)["active"]]
t0 = time.time()
r = form_teams(ids, a.teams, a.min_size, a.max_per_trio, time_limit_s=a.time_limit)
summary = {"inventory_ids": len(ids), "inventory_sources": prov, "params": vars(a) | {"out": str(a.out.name)},
           "status": r["status"], "capacity": r["capacity"], "team_sizes_min": min(r["team_sizes"] or [0]),
           "team_sizes_max": max(r["team_sizes"] or [0]), "max_teams_per_trio_used": r.get("max_teams_per_trio_used"),
           "groups_covered_all_teams": r.get("groups_covered_all_teams"), "elapsed_s": round(time.time() - t0, 1),
           "teams_sha256": hashlib.sha256(json.dumps(r["teams"]).encode()).hexdigest(), "teams": r["teams"]}
a.out.parent.mkdir(exist_ok=True)
a.out.write_text(json.dumps(summary, ensure_ascii=False, indent=1))
print(json.dumps({k: v for k, v in summary.items() if k != "teams"}, ensure_ascii=False, default=str))
