from datetime import datetime, timezone
import os
import unittest
from unittest.mock import patch

from services.forum.github_results import GitHubResults, REPO, SOURCES, normalize


def record(kind, number):
    path = "pull" if kind == "pulls" else kind
    return {
        "number": number, "html_url": f"https://github.com/{REPO}/{path}/{number}",
        "title": "CFP+ test", "state": "open", "updated_at": "2026-11-21T10:15:00+07:00",
        "assignees": [{"login": "owner"}], "head": {"sha": "a" * 40},
    }


class GitHubResultsTest(unittest.TestCase):
    def test_normalize_preserves_attribution_and_utc(self):
        output = normalize(record("pulls", 214), "SecuritySI", "pulls", 214)
        self.assertEqual(output["owner"], "owner")
        self.assertEqual(output["updated_at"], "2026-11-21T03:15:00+00:00")
        self.assertEqual(output["evidence_urls"], [output["url"] + "/commits/" + "a" * 40])
        self.assertFalse(normalize(record("issues", 238), "ChatGPT", "issues", 238)["evidence_urls"])

    def test_rejects_record_from_wrong_source(self):
        with self.assertRaises(ValueError):
            normalize(record("pulls", 216), "SecuritySI", "pulls", 214)

    def test_disabled_cache_and_failed_refresh(self):
        calls = []

        def fetch(kind, number):
            calls.append(number)
            if number == 214 and calls.count(number) > 1:
                raise OSError
            return record(kind, number)

        feed = GitHubResults(fetch)
        with patch.dict(os.environ, {"CFP_HUB69_GITHUB_PUBLIC_SYNC": "0"}):
            self.assertEqual(feed.snapshot()["state"], "disabled")
        self.assertEqual(calls, [])
        with patch.dict(os.environ, {"CFP_HUB69_GITHUB_PUBLIC_SYNC": "1"}):
            self.assertEqual(feed.snapshot()["state"], "current")
            self.assertEqual(feed.snapshot()["state"], "current")
            self.assertEqual(len(calls), len(SOURCES))
            feed.next_refresh = 0
            partial = feed.snapshot()
        self.assertEqual(partial["state"], "partial")
        self.assertEqual(partial["errors"], ["pulls/214"])
        self.assertEqual([r["url"].split("/")[-1] for r in partial["rows"] if r["stale"]], ["214"])
        self.assertEqual(datetime.fromisoformat(partial["checked_at"]).tzinfo, timezone.utc)
