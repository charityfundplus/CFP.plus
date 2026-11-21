"""Regression coverage for native file locking and named assignment validation."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "tests"))

from hub69_dispatch.autopilot import Busy, Store
from hub69_dispatch.engine import Queue, run
from test_dispatch import AGENTS, POLICY, NOW, Thread
from hub69_dispatch.protocol import parse_comment


class NativeLockTests(unittest.TestCase):
    def test_exclusive_between_stores_and_release_after_exception(self):
        with tempfile.TemporaryDirectory() as directory:
            first, second = Store(Path(directory)), Store(Path(directory))
            try:
                with self.assertRaisesRegex(RuntimeError, "exercise"):
                    with first.lock():
                        with self.assertRaises(Busy):
                            with second.lock():
                                self.fail("second tick acquired held lock")
                        raise RuntimeError("exercise")
                with second.lock():
                    pass
            finally:
                first.db.close()
                second.db.close()

    def test_process_exit_releases_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            child = (
                "import sys;from pathlib import Path;"
                "sys.path.insert(0,sys.argv[1]);"
                "from hub69_dispatch.autopilot import Store;"
                "s=Store(Path(sys.argv[2]));"
                "lock=s.lock();lock.__enter__();print('LOCKED',flush=True);sys.stdin.readline()"
            )
            process = subprocess.Popen(
                [sys.executable, "-u", "-c", child, str(HERE), directory],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            store = None
            try:
                self.assertEqual(process.stdout.readline().strip(), "LOCKED")
                store = Store(Path(directory))
                with self.assertRaises(Busy):
                    with store.lock():
                        self.fail("child lock ignored")
                process.terminate()
                process.wait(timeout=10)
                with store.lock():
                    pass
            finally:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=10)
                for stream in (process.stdin, process.stdout, process.stderr):
                    stream.close()
                if store:
                    store.db.close()


class NamedAssignmentTests(unittest.TestCase):
    def snapshot(self, assignee, agents=None, capability=""):
        thread = Thread()
        thread.task("Synthetic named task", assignee, "ReviewSI")
        if capability:
            thread.comments[0]["body"] += "\n**Năng lực:** " + capability
        messages = parse_comment(thread.comments[0], "test", {"charityfundplus"}, {})
        return run(messages, POLICY, agents or AGENTS, NOW)[0]

    def test_unknown_explicit_ids_fail_closed(self):
        for key in ("2633", "6535", "267", "unknown-agent"):
            with self.subTest(key=key):
                snapshot = self.snapshot(key)
                self.assertEqual(snapshot["tasks"], [])
                self.assertIn("not in agents config", snapshot["rejections"][0]["reason"])

    def test_forged_numeric_binding_and_capability_are_rejected(self):
        agents = copy.deepcopy(AGENTS)
        agents["2633"] = {**agents["691121"], "key": "2633"}
        snapshot = self.snapshot("2633", agents)
        self.assertIn("Registry binding", snapshot["rejections"][0]["reason"])
        snapshot = self.snapshot("691121", capability="notion")
        self.assertIn("lacks capability", snapshot["rejections"][0]["reason"])

    def test_existing_named_agent_and_pending_role_preserve_planning(self):
        self.assertEqual(self.snapshot("691121", capability="code")["tasks"][0]["assignee"], "691121")
        self.assertEqual(self.snapshot("Codex 1")["tasks"][0]["assignee"], "Codex 1")
        queue = Queue(POLICY, AGENTS)
        self.assertEqual(queue.route("registry_check"), "691121")

    def test_dedupe_uses_code_and_source_while_titles_only_warn(self):
        thread = Thread()
        first = thread.task("Shared title", "691121", "ReviewSI")
        second = thread.task("Shared title", "691121", "ReviewSI")
        duplicate = thread.task("Renamed title", "691121", "ReviewSI")
        thread.comments[-1]["body"] += "\n**Work Order ID:** " + first
        other_source = dict(thread.comments[-1])
        other_source["ref"] = "different#99"
        other_source["source_identity"] = "different-authorized-source"
        thread.comments.append(other_source)
        snapshot, _ = thread.run()
        self.assertEqual([task["key"] for task in snapshot["tasks"]], [first, second, "different#99"])
        self.assertTrue(snapshot["warnings"])
        self.assertEqual(snapshot["rejections"][0]["ref"], duplicate)
        self.assertIn("duplicate", snapshot["rejections"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
