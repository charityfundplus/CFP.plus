"""Codex 2 adversarial offline checks. No live services or real credentials."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "cmp/executor"))
from notion_bridge import BridgeError, Journal, Model, Notion, texts
from bridge_cli import private_json, save_private
from test_notion_bridge import FakeTransport, SOURCE


class IndependentReviewTests(unittest.TestCase):
    def test_private_json_rejects_symlink_and_public_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "policy.json"
            target.write_text('{"secret":"synthetic"}')
            target.chmod(0o600)
            link = Path(directory) / "link.json"
            link.symlink_to(target)
            with self.assertRaises(BridgeError):
                private_json(link)
            target.chmod(0o644)
            with self.assertRaises(BridgeError):
                private_json(target)

    def test_private_json_rejects_fifo_without_blocking(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fifo"
            os.mkfifo(path, 0o600)
            with self.assertRaises(BridgeError):
                private_json(path)

    def test_plan_save_is_private_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plan.json"
            save_private(path, {"body": "synthetic"})
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(private_json(path), {"body": "synthetic"})
            with self.assertRaises(BridgeError):
                save_private(path, {"body": "changed"})
            self.assertEqual(private_json(path), {"body": "synthetic"})

    def test_malformed_gemini_parts_are_safe_errors(self):
        malformed = [None, "upstream-private-text", 123]
        for part in malformed:
            with self.subTest(part=part):
                transport = FakeTransport()
                with patch.object(transport, "request", return_value={
                        "candidates": [{"content": {"parts": [part]}}]}):
                    with self.assertRaises(BridgeError):
                        Model("gemini", "fixture", "fake-token", transport).generate("text")

    def test_malformed_notion_blocks_are_safe_errors(self):
        for block in [None, "upstream-private-text", 123]:
            with self.subTest(block=block):
                with self.assertRaises(BridgeError):
                    texts([block])

    def test_malformed_notion_richtext_are_safe_errors(self):
        for richtext in [[None], ["upstream-private-text"], [{"text": None}]]:
            with self.subTest(richtext=richtext):
                with self.assertRaises(BridgeError):
                    texts([{"type": "paragraph", "paragraph": {"rich_text": richtext}}])

    def test_journal_rejects_symlink_without_touching_target(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target"
            target.write_text("private unrelated file")
            target.chmod(0o640)
            link = Path(directory) / "journal.sqlite"
            link.symlink_to(target)
            with self.assertRaises((BridgeError, OSError)):
                Journal(str(link))
            self.assertEqual(target.stat().st_mode & 0o777, 0o640)
            self.assertEqual(target.read_text(), "private unrelated file")

    def test_invalid_metadata_does_not_escape_safe_error(self):
        transport = FakeTransport()
        with patch.object(transport, "request", return_value={"id": SOURCE,
                                                               "archived": False}):
            # Missing results must stop reads rather than be interpreted as empty text.
            with self.assertRaises(BridgeError):
                Notion("fake-token", transport).read(SOURCE)


if __name__ == "__main__":
    unittest.main()
