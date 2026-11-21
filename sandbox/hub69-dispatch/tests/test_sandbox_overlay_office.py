"""Actual loopback Office regressions for sandbox overlay, failure and recovery."""
import hashlib
import json
import os
import sys
import tempfile
import unittest
from contextlib import closing
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "tests"))
from hub69_dispatch.adapters import FileSource
from hub69_dispatch.autopilot import Autopilot, EXECUTORS
from hub69_dispatch.cli import load_config
from hub69_dispatch.office_client import OfficeError, RetryPolicy
from cfp_sandbox_overlay import load_overlay
from office_harness import OfficeServer, office_src, deps_ok
from test_autopilot_office import T0


@unittest.skipUnless(deps_ok() and office_src(), "patched Office checkout/dependencies required")
class OverlayOfficeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="hub69-overlay-test-")
        overlay = HERE / "fixtures/three-sbd-overlay.json"
        self.env = patch.dict(os.environ, {
            "CFP_SANDBOX_EPHEMERAL": "1",
            "HUB69_SANDBOX_REGISTRY_OVERLAY": str(overlay),
            "HUB69_SANDBOX_REGISTRY_SHA256": hashlib.sha256(overlay.read_bytes()).hexdigest()})
        self.env.start()
        self.server = OfficeServer(office_src(), Path(self.tmp.name) / "office").start()
        agents, self.policy = load_config()
        self.agents = {agent["key"]: agent for agent in agents["agents"]}
        self.pilot = Autopilot(
            base=self.server.base, state_dir=Path(self.tmp.name) / "state",
            agents=self.agents, policy=self.policy, secrets=self.server.secrets,
            evidence_base="https://example.org/synthetic-evidence", office_src=office_src(),
            retry=RetryPolicy(attempts=1, base_delay=0), sleep=lambda _: None)
        doc = json.loads((HERE / "fixtures/three-sbd.json").read_text(encoding="utf-8"))
        self.fixture = Path(self.tmp.name) / "one-task.json"
        self.fixture.write_text(json.dumps({"comments": doc["comments"][:1]}), encoding="utf-8")
        self.source = FileSource(str(self.fixture))

    def tearDown(self):
        self.pilot.close()
        self.server.stop()
        self.env.stop()
        self.tmp.cleanup()

    def test_overlay_gates_and_checksum(self):
        self.assertEqual(set(load_overlay({})), {"2633", "6535", "267"})
        with self.assertRaisesRegex(ValueError, "EPHEMERAL"):
            load_overlay({}, ephemeral=False)
        with self.assertRaisesRegex(ValueError, "BINDING"):
            load_overlay({"2633"})
        with patch.dict(os.environ, {"HUB69_SANDBOX_REGISTRY_SHA256": "0" * 64}):
            with self.assertRaisesRegex(ValueError, "CHECKSUM"):
                load_overlay({})

    def test_executor_failure_readback_and_requeue(self):
        def failed(*args):
            raise RuntimeError("synthetic failure")
        with patch.dict(EXECUTORS, {"registry_integrity": failed}):
            result = self.pilot.tick(self.source, T0, "executor-failure")
        key = "sbd#2633-01"
        self.assertEqual(result["handled"][0]["stage"], "DEAD_LETTER")
        readback = self.pilot.readback(key)
        self.assertIn("RuntimeError", json.dumps(readback["history"]))
        self.assertIn("AUTOPILOT_ERROR", json.dumps(readback["history"]))
        self.pilot.requeue(key, T0 + timedelta(minutes=1))
        self.pilot.tick(self.source, T0 + timedelta(minutes=2), "requeue")
        self.assertEqual(self.pilot.readback(key)["office_status"], "IN_REVIEW")
        self.assertIn("RuntimeError", json.dumps(self.pilot.readback(key)["history"]))

    def test_legacy_task_audit_defaults_preserve_idempotency(self):
        self.pilot.tick(self.source, T0, "setup")
        dispatcher = self.pilot.client("dispatcher")
        body = {"pair_id": self.pilot.store.account("2633")["pair_id"],
                "title": "Synthetic legacy task", "acceptance": "Keep one task",
                "reviewer_id": self.pilot.client("ReviewSI").user["id"],
                "idempotency_key": "synthetic-legacy-audit"}
        task_id = dispatcher.post("/api/office/tasks", body)["id"]
        import sqlite3
        database = Path(self.tmp.name) / "office/office.db"
        with closing(sqlite3.connect(database)) as connection:
            row_id, raw = connection.execute(
                "select id,data from audit_log where ref=? and action='task.create'",
                (f"task:{task_id}",)).fetchone()
            original = json.loads(raw)
            original.pop("source")
            original.pop("work_order_code")
            connection.execute("update audit_log set data=? where id=?", (json.dumps(original), row_id))
            connection.commit()
        replay = dispatcher.post("/api/office/tasks", body)
        self.assertTrue(replay["duplicate"])
        self.assertEqual(replay["id"], task_id)

    def test_office_unavailable_and_transient_503_preserve_error_history(self):
        key = "sbd#2633-01"
        self.server.stop()
        result = self.pilot.tick(self.source, T0, "offline")
        self.assertEqual(result["handled"][0]["stage"], "RETRY")
        self.assertTrue(self.pilot.store.task(key)["last_error"])
        self.server.start()
        self.pilot.tick(self.source, T0 + timedelta(minutes=2), "online")
        self.assertIn("transport", json.dumps(self.pilot.readback(key)["history"]))
        self.assertEqual(self.pilot.readback(key)["office_status"], "IN_REVIEW")
        original = self.pilot.process
        self.pilot.process = lambda task: (_ for _ in ()).throw(
            OfficeError(503, "synthetic Office unavailable", permanent=False))
        try:
            result = self.pilot.tick(self.source, T0 + timedelta(minutes=3), "503")
        finally:
            self.pilot.process = original
        self.assertEqual(result["handled"][0]["stage"], "RETRY")
        self.assertIn("503", json.dumps(self.pilot.readback(key)["history"]))
        self.pilot.tick(self.source, T0 + timedelta(minutes=5), "503-recovered")
        self.assertEqual(self.pilot.readback(key)["office_status"], "IN_REVIEW")


if __name__ == "__main__":
    unittest.main()
