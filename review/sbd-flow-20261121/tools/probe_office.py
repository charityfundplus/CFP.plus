"""Independent probe of PR #195 Office @287ce64 (ephemeral SQLite). Fake data only."""
import json, sys, threading
from pathlib import Path
H = Path(sys.argv[1]).resolve(); sys.path[:0] = [str(H), str(H / "tests")]
from office_harness import OfficeServer, office_src
from hub69_dispatch.office_client import OfficeClient, OfficeError
srv = OfficeServer(office_src()).start(); srv.grant_securitysi(); R = {}
def gov():
    c = OfficeClient(srv.base); c.login(*srv.secrets["gov"]); return c
try:
    g = gov(); me = g.get("/api/auth/me"); uid = me.get("user", me).get("id"); R["gov_uid"] = uid
    rv = OfficeClient(srv.base); rv.login(*srv.secrets["reviewer"]["ReviewSI"]); rid = rv.get("/api/auth/me"); rid = rid.get("user", rid).get("id")
    # P1: open office for the three SBD DIDs
    for did in ("2633", "6535", "267"):
        try: g.post("/api/office/offices", {"canonical_id": did, "platform": "Notion agent (fake)"}); R[f"office_{did}"] = "201 CREATED"
        except OfficeError as e: R[f"office_{did}"] = f"{e.status} {e.detail}"
    # P2: one DID with two Entity Records (pairs) -> what does the DID listing return?
    did = "691121"
    try: g.post("/api/office/offices", {"canonical_id": did, "platform": "Claude (fake)"})
    except OfficeError as e: R["office_691121"] = f"{e.status} {e.detail}"
    p1 = g.post("/api/office/pairs", {"canonical_id": did, "software": "Code Runner (fake)", "lead_user_id": uid})["id"]
    p2 = g.post("/api/office/pairs", {"canonical_id": did, "software": "Learning Kit (fake)", "lead_user_id": uid})["id"]
    t1 = g.post("/api/office/tasks", {"pair_id": p1, "title": "fake task A", "acceptance": "readback", "reviewer_id": rid, "idempotency_key": "cc-review:A:0001"})
    t2 = g.post("/api/office/tasks", {"pair_id": p2, "title": "fake task B", "acceptance": "readback", "reviewer_id": rid, "idempotency_key": "cc-review:B:0001"})
    v = g.get(f"/api/office/offices/{did}"); vf = g.get(f"/api/office/offices/{did}?pair_id={p1}&entity_type=SUPER_SOFTWARE")
    R["listing_by_did"] = [{"task": t["id"], "pair_id": t["pair_id"], "title": t["title"]} for t in v["tasks"]]
    R["listing_filter_ignored"] = len(vf["tasks"]) == len(v["tasks"])
    R["office_fields"] = sorted(v["office"].keys()); R["task_fields"] = sorted(k for k in v["tasks"][0] if k not in ("evidence","reviews","history","discussions"))
    # P3: concurrent duplicate submission with same idempotency_key
    out = []
    def fire():
        c = gov()
        try: out.append(("ok", c.post("/api/office/tasks", {"pair_id": p1, "title": "race", "acceptance": "readback", "reviewer_id": rid, "idempotency_key": "cc-review:race:0001"}).get("id")))
        except OfficeError as e: out.append(("err", e.status))
    th = [threading.Thread(target=fire) for _ in range(8)]; [t.start() for t in th]; [t.join() for t in th]
    v2 = g.get(f"/api/office/offices/{did}")
    R["race_results"] = out; R["race_rows_created"] = sum(1 for t in v2["tasks"] if t["title"] == "race")
finally:
    srv.stop()
print(json.dumps(R, ensure_ascii=False, indent=1))
