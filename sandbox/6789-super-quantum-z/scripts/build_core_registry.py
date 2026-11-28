"""Tạo snapshot Registry cho resolver của cfp-gateway từ kiểm kê 87788 (đã có nguồn và sha).

Mọi bản ghi mang trạng thái INVENTORY_REVIEW: đây là kiểm kê làm việc, KHÔNG phải Canonical.
python scripts/build_core_registry.py --out ../../../cfp-gateway/config/core_registry.json
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / "87788-super-trio"))

import trio  # noqa: E402
from sqz.idformula import validate  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out", type=Path, default=ROOT / "evidence" / "core_registry.snapshot.json")
a = ap.parse_args()
rows, excluded, prov = trio.load_inventory()
active = trio.check_inventory(rows, excluded)["active"]
records, rejected = [], []
for r in active:
    v = validate(r["id"])
    if not v["valid"]:
        rejected.append({"id": r["id"], "errors": v["errors"]})
        continue
    records.append({"id": r["id"], "name": r.get("name", ""), "link": r.get("link") or None,
                    "status": "INVENTORY_REVIEW", "chapter": v["chapter"], "group": v["group"]})
snap = {"format": "cfp-core-registry-snapshot-v1",
        "source": "CFP.plus sandbox/87788-super-trio inventory (PR #206 index + Notion additions)",
        "provenance": prov, "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status_note": "INVENTORY_REVIEW = kiểm kê làm việc, chưa phải Canonical; Human Governance chốt",
        "records": sorted(records, key=lambda x: x["id"]), "rejected": rejected}
a.out.parent.mkdir(parents=True, exist_ok=True)
a.out.write_text(json.dumps(snap, ensure_ascii=False, indent=1) + "\n")
print(json.dumps({"out": str(a.out), "records": len(records), "rejected": len(rejected)}))
