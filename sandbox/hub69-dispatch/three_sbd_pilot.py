"""Run the existing #207 autopilot and #195 Office using isolated sandbox fixtures."""
import argparse
import hashlib
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "tests"))
from office_harness import OfficeServer, office_src
from hub69_dispatch.adapters import FileSource
from hub69_dispatch.autopilot import Autopilot
from hub69_dispatch.cli import load_config
from hub69_dispatch.office_client import OfficeClient, OfficeError, RetryPolicy


def run(out: Path):
    out.mkdir(parents=True, exist_ok=False)
    overlay = HERE / "fixtures/three-sbd-overlay.json"
    os.environ["CFP_SANDBOX_EPHEMERAL"] = "1"
    os.environ["HUB69_SANDBOX_REGISTRY_OVERLAY"] = str(overlay)
    os.environ["HUB69_SANDBOX_REGISTRY_SHA256"] = hashlib.sha256(overlay.read_bytes()).hexdigest()
    src = office_src()
    if src is None:
        raise RuntimeError("HUB69_OFFICE_SRC must identify the patched #195 checkout")
    agents_doc, policy = load_config()
    agents = {row["key"]: row for row in agents_doc["agents"]}
    source = FileSource(str(HERE / "fixtures/three-sbd.json"))
    server = OfficeServer(src, out / "office")
    pilot = None
    now = datetime.now(timezone.utc)
    try:
        server.start()
        pilot = Autopilot(base=server.base, state_dir=out / "state", agents=agents, policy=policy,
                          secrets=server.secrets, evidence_base="https://github.com/charityfundplus/CFP.plus/"
                          "blob/codex/hub69-windows-sandbox-20261121/review/hub69-windows-20261121/results",
                          office_src=src, retry=RetryPolicy(attempts=2, base_delay=0), sleep=lambda _: None)
        ticks = [pilot.tick(source, now, "initial")]
        keys = ["sbd#2633-01", "sbd#6535-01", "sbd#267-01"]
        for key in keys:
            assert pilot.store.task(key)["stage"] == "HANDED_TO_REVIEWER", pilot.store.status()
        original = {key: pilot.readback(key) for key in keys}
        ticks.append(pilot.tick(source, now + timedelta(minutes=1), "replay"))
        server.stop()
        server.start()
        ticks.append(pilot.tick(source, now + timedelta(minutes=2), "restart"))
        readbacks = {key: pilot.readback(key) for key in keys}
        assert readbacks == original
        for key, receipt in readbacks.items():
            file = out / "state/results" / (key.replace("#", "-") + ".json")
            sha = hashlib.sha256(file.read_bytes()).hexdigest()
            assert any(evidence["sha"] == sha for evidence in receipt["evidence"])
            ref = receipt["entity_reference"]
            view = pilot.client("gov").get(
                f"/api/office/entities/{ref['did']}/{ref['entity_type']}/{ref['entity_record_id']}/tasks")
            assert [task["id"] for task in view["tasks"]] == [receipt["office_tid"]]
            assert receipt["source"] and receipt["work_order_code"] and receipt["result_link"]
        first = readbacks[keys[0]]
        tid = first["office_tid"]
        ref = first["entity_reference"]
        dispatcher = pilot.client("dispatcher")
        other_pair = dispatcher.post("/api/office/pairs", {
            "canonical_id": ref["did"], "software": "Synthetic second software record",
            "lead_user_id": pilot.client("2633").user["id"]})["id"]
        other_task = dispatcher.post("/api/office/tasks", {
            "pair_id": other_pair, "title": "Synthetic second record task",
            "reviewer_id": pilot.client("ReviewSI").user["id"],
            "acceptance": "Separate Entity Record", "idempotency_key": "synthetic-second-record"})["id"]
        scoped = pilot.client("gov").get(
            f"/api/office/entities/{ref['did']}/SUPER_SOFTWARE/{ref['entity_record_id']}/tasks")
        assert [task["id"] for task in scoped["tasks"]] == [tid]
        assert other_task not in [task["id"] for task in scoped["tasks"]]
        for did, kind, record in [
            (ref["did"], "SI_AI", ref["entity_record_id"]),
            ("6535", "SUPER_SOFTWARE", ref["entity_record_id"]),
            (ref["did"], "SUPER_SOFTWARE", 999999)]:
            try:
                pilot.client("gov").get(f"/api/office/entities/{did}/{kind}/{record}/tasks")
            except OfficeError as error:
                assert error.status == 404
            else:
                raise AssertionError("foreign Entity Record returned data")

        # Eight real HTTP requests race on the existing Office idempotency contract.
        agent = pilot.client("2633")
        pair_id = pilot.store.account("2633")["pair_id"]
        reviewer = pilot.client("ReviewSI").user["id"]
        body = {"pair_id": pair_id, "title": "Synthetic concurrent request",
                "acceptance": "Exactly one task", "reviewer_id": reviewer,
                "idempotency_key": "synthetic-eight-request-race",
                "source": str(source.path.resolve()), "work_order_code": "synthetic-eight-request-race"}
        def create(_):
            client = OfficeClient(server.base)
            client.login("hub69-dispatch@sandbox.invalid", server.secrets["agent_password"])
            return client.post("/api/office/tasks", body)["id"]
        with ThreadPoolExecutor(max_workers=8) as pool:
            race = list(pool.map(create, range(8)))
        assert len(set(race)) == 1
        board = pilot.client("gov").get("/api/office/offices/2633")
        assert sum(task["id"] == race[0] for task in board["tasks"]) == 1
        result = {"platform": sys.platform, "office_source": str(src), "ticks": ticks,
                  "readbacks": readbacks, "race_task_ids": race,
                  "readback_verified": True, "review": "PENDING_REAL_REVIEWER",
                  "executor_kind": "AUTOMATED_TOOL / SYNTHETIC_FIXTURE",
                  "overlay_sha256": os.environ["HUB69_SANDBOX_REGISTRY_SHA256"]}
        result["second_record_isolated"] = True
        (out / "readback.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        (out / "run-log.jsonl").write_text(
            "\n".join(json.dumps(row, ensure_ascii=False) for row in pilot.store.logs()) + "\n", encoding="utf-8")
        return result
    finally:
        if pilot:
            pilot.close()
        server.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.out)
    print(json.dumps({"tasks": len(result["readbacks"]), "readback_verified": True,
                      "race_unique_tasks": len(set(result["race_task_ids"])), "platform": sys.platform}))
