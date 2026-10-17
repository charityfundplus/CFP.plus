"""Offline only. Fake credentials and IDs; no external services or Notion writes."""
import copy
import hashlib
import hmac
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from urllib.error import HTTPError, URLError
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "cmp/executor"))
from notion_bridge import BridgeError, Journal, Model, NoRedirect, Notion, Policy, Transport, digest, execute, prepare

SOURCE = "11111111-1111-4111-8111-111111111111"
PARENT = "22222222-2222-4222-8222-222222222222"
CREATED = "33333333-3333-4333-8333-333333333333"
KEY = "test-governance-key-" * 3
POLICY = Policy(frozenset({SOURCE}), frozenset({PARENT}), True,
                frozenset({"gemini", "meta"}), frozenset({SOURCE}))


def blocks(text):
    return [{"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": text}]}}]


def approve(plan):
    claims = {"plan_sha256": digest(plan), "action": "sandbox_create", "environment": "sandbox",
              "reviewer": "independent-human-fixture", "expires_at": 1200}
    signature = hmac.new(KEY.encode(), json.dumps(claims, sort_keys=True, separators=(",", ":"),
                                                  ensure_ascii=False).encode(), hashlib.sha256).hexdigest()
    return {"claims": claims, "signature": signature}


class FakeTransport:
    def __init__(self, provider="gemini"):
        self.calls, self.provider, self.payload = [], provider, None
        self.source, self.wrong_body, self.wrong_parent = "Allowed synthetic text", False, False

    def request(self, method, url, headers, payload=None):
        self.calls.append((method, url, headers, payload))
        if "googleapis" in url:
            return {"candidates": [{"content": {"parts": [{"text": "Synthetic summary"}]}}]}
        if "api.llama.com" in url:
            return {"completion_message": {"content": {"type": "text", "text": "Synthetic summary"}}}
        if method == "POST":
            self.payload = payload
            return {"id": CREATED}
        identity = url.split("/v1/")[1].split("/")[1].split("?")[0]
        if "/children?" in url:
            text = self.source if identity == SOURCE else ""
            if identity == CREATED:
                text = "mismatch" if self.wrong_body else self.payload["children"][0]["paragraph"]["rich_text"][0]["text"]["content"]
            return {"results": blocks(text), "has_more": False}
        result = {"id": identity, "archived": False}
        if identity == CREATED:
            result.update(parent={"type": "page_id", "page_id": SOURCE if self.wrong_parent else PARENT},
                          properties={"title": {"title": self.payload["properties"]["title"]["title"]}})
        return result


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.journal = Journal(self.directory.name + "/journal.sqlite")
        self.addCleanup(self.journal.db.close)
        self.transport = FakeTransport()
        self.notion = Notion("fake-notion-secret", self.transport)
        self.events = []

    def plan(self, provider="gemini"):
        return prepare(POLICY, self.notion, Model(provider, "fixture-model", "fake-model-secret", self.transport),
                       "fixture-run", SOURCE, PARENT, self.events.append)

    def run_plan(self, plan, approval=None, policy=POLICY, audit=None):
        return execute(policy, self.notion, plan, approval if approval is not None else approve(plan),
                       KEY, self.journal, audit or self.events.append, now=1000)

    def writes(self):
        return [c for c in self.transport.calls if c[0] == "POST" and "api.notion.com" in c[1]]

    def test_gemini_read_create_readback(self):
        plan = self.plan()
        receipt = self.run_plan(plan)
        self.assertEqual(receipt["readback"], "PASS")
        self.assertEqual(len(self.writes()), 1)
        self.assertEqual(self.writes()[0][3]["parent"], {"page_id": PARENT})
        self.assertNotIn("Synthetic summary", json.dumps(receipt))
        self.assertNotIn("fake-", json.dumps(self.events))

    def test_meta_read_create_readback_native_contract(self):
        receipt = self.run_plan(self.plan("meta"))
        self.assertEqual(receipt["provider"], "meta")
        call = next(c for c in self.transport.calls if "api.llama.com" in c[1])
        self.assertEqual(call[1], "https://api.llama.com/v1/chat/completions")
        self.assertEqual(call[3]["max_completion_tokens"], 512)

    def test_meta_string_content(self):
        with patch.object(self.transport, "request", return_value={"completion_message": {"content": "summary"}}):
            self.assertEqual(Model("meta", "fixture", "token", self.transport).generate("source"), "summary")

    def test_prepare_never_writes(self):
        self.plan()
        self.assertEqual(self.writes(), [])

    def test_unsigned_approval_denied_before_network(self):
        plan = self.plan()
        count = len(self.transport.calls)
        with self.assertRaisesRegex(BridgeError, "APPROVAL_REQUIRED"):
            self.run_plan(plan, {})
        self.assertEqual(len(self.transport.calls), count)

    def test_tampering_approval_denied(self):
        plan = self.plan()
        approval = approve(plan)
        approval["claims"]["reviewer"] = "attacker"
        with self.assertRaisesRegex(BridgeError, "SIGNATURE_INVALID"):
            self.run_plan(plan, approval)
        self.assertEqual(self.writes(), [])

    def test_plan_changes_invalidate_approval(self):
        for field, value in [("body", "changed"), ("provider", "meta"), ("model", "other")]:
            plan = self.plan()
            approval = approve(plan)
            plan[field] = value
            with self.assertRaisesRegex(BridgeError, "SCOPE_MISMATCH"):
                self.run_plan(plan, approval)
        self.assertEqual(self.writes(), [])

    def test_expired_approval_denied(self):
        plan = self.plan()
        with self.assertRaisesRegex(BridgeError, "EXPIRED"):
            execute(POLICY, self.notion, plan, approve(plan), KEY, self.journal, self.events.append, now=1300)

    def test_private_parent_and_egress_gates(self):
        for policy, code in [(Policy(frozenset({SOURCE}), frozenset({PARENT})), "PROVIDER_ACCESS_BLOCKED"),
                             (Policy(frozenset({SOURCE}), frozenset({PARENT}), True, frozenset({"gemini"})), "EGRESS_DENIED"),
                             (Policy(frozenset({SOURCE}), frozenset({PARENT}), False, frozenset({"gemini"}), frozenset({SOURCE})), "PRIVATE_PARENT")]:
            with self.assertRaisesRegex(BridgeError, code):
                prepare(policy, self.notion, Model("gemini", "fixture", "token", self.transport), "run", SOURCE, PARENT, self.events.append)
        self.assertEqual(self.transport.calls, [])

    def test_unlisted_source_and_parent_denied(self):
        for source, parent in [(CREATED, PARENT), (SOURCE, CREATED), (SOURCE, SOURCE)]:
            with self.assertRaises(BridgeError):
                prepare(POLICY, self.notion, Model("gemini", "fixture", "token", self.transport), "run", source, parent, self.events.append)
        self.assertEqual(self.transport.calls, [])

    def test_source_changed_blocks_write(self):
        plan = self.plan()
        self.transport.source = "Changed after review"
        with self.assertRaisesRegex(BridgeError, "SOURCE_CHANGED"):
            self.run_plan(plan)
        self.assertEqual(self.writes(), [])

    def test_failed_readback_never_passes(self):
        for attribute, expected in [("wrong_body", "CONTENT_MISMATCH"), ("wrong_parent", "PARENT_MISMATCH")]:
            plan = self.plan()
            plan["execution_id"] = attribute
            plan["title"] = "CFP+ sandbox " + attribute
            setattr(self.transport, attribute, True)
            with self.assertRaisesRegex(BridgeError, expected):
                self.run_plan(plan)
            setattr(self.transport, attribute, False)
        self.assertTrue(all(e.get("status") != "PASS" for e in self.events))

    def test_durable_reservation_prevents_replay(self):
        plan = self.plan()
        self.run_plan(plan)
        with self.assertRaisesRegex(BridgeError, "ALREADY_RESERVED"):
            self.run_plan(plan)
        self.assertEqual(len(self.writes()), 1)

    def test_uncertain_create_is_reserved_and_not_retried(self):
        plan = self.plan()
        with patch.object(self.notion, "create", side_effect=BridgeError("TRANSPORT_ERROR")) as create:
            with self.assertRaisesRegex(BridgeError, "TRANSPORT_ERROR"):
                self.run_plan(plan)
            with self.assertRaisesRegex(BridgeError, "ALREADY_RESERVED"):
                self.run_plan(plan)
            self.assertEqual(create.call_count, 1)
        self.assertTrue(self.events[-1]["reconcile_required"])

    def test_audit_failure_blocks_create(self):
        plan = self.plan()
        def fail(event):
            raise OSError("storage unavailable")
        with self.assertRaises(OSError):
            self.run_plan(plan, audit=fail)
        self.assertEqual(self.writes(), [])

    def test_credentials_only_in_headers(self):
        self.plan()
        for method, url, headers, payload in self.transport.calls:
            self.assertNotIn("fake-", url)
            self.assertNotIn("fake-", json.dumps(payload))
        model_call = next(c for c in self.transport.calls if "googleapis" in c[1])
        self.assertIn("x-goog-api-key", model_call[2])

    def test_bad_model_and_tool_response_fail_closed(self):
        with self.assertRaisesRegex(BridgeError, "INVALID_MODEL"):
            Model("gemini", "../../evil?key=", "token", self.transport)
        with patch.object(self.transport, "request", return_value={"tool_calls": [{"name": "write"}]}):
            with self.assertRaisesRegex(BridgeError, "RESPONSE_INVALID"):
                Model("gemini", "fixture", "token", self.transport).generate("text")

    def test_top_level_pagination(self):
        responses = [{"id": SOURCE}, {"results": blocks("first"), "has_more": True, "next_cursor": "next"},
                     {"results": blocks("second"), "has_more": False}]
        with patch.object(self.transport, "request", side_effect=responses):
            _, result = self.notion.read(SOURCE)
        self.assertEqual(len(result), 2)

    def test_repeated_cursor_fails_closed(self):
        responses = [{"id": SOURCE}] + [{"results": [], "has_more": True, "next_cursor": "same"}] * 2
        with patch.object(self.transport, "request", side_effect=responses):
            with self.assertRaisesRegex(BridgeError, "INVALID_CURSOR"):
                self.notion.read(SOURCE)


class TransportTests(unittest.TestCase):
    def test_long_retry_after_is_deferred_not_retried_early(self):
        transport = Transport(sleep=lambda _: self.fail("must defer to operator"))
        with patch.object(transport.opener, "open", side_effect=HTTPError("https://api.notion.com", 429, "", {"Retry-After": "120"}, None)) as op:
            with self.assertRaisesRegex(BridgeError, "RATE_LIMIT_DEFERRED"):
                transport.request("GET", "https://api.notion.com", {})
        self.assertEqual(op.call_count, 1)

    def test_get_rate_limit_retry_after(self):
        delays = []
        transport = Transport(sleep=delays.append)
        response = io.BytesIO(b'{"ok": true}')
        with patch.object(transport.opener, "open", side_effect=[HTTPError("https://api.notion.com", 429, "private", {"Retry-After": "2"}, None), response]) as op:
            self.assertEqual(transport.request("GET", "https://api.notion.com", {}), {"ok": True})
        self.assertEqual(delays, [2])
        self.assertEqual(op.call_count, 2)

    def test_post_and_auth_errors_never_retry_or_expose_body(self):
        for method, status in [("POST", 429), ("POST", 503), ("GET", 401), ("GET", 403)]:
            transport = Transport(sleep=lambda _: self.fail("unexpected retry"))
            with patch.object(transport.opener, "open", side_effect=HTTPError("https://api.notion.com", status, "SECRET", {}, None)) as op:
                with self.assertRaisesRegex(BridgeError, "HTTP_" + str(status)) as error:
                    transport.request(method, "https://api.notion.com", {})
            self.assertNotIn("SECRET", str(error.exception))
            self.assertEqual(op.call_count, 1)

    def test_redirects_disabled(self):
        self.assertIsNone(NoRedirect().redirect_request(None, None, 302, "", {}, "https://attacker.invalid"))

    def test_network_error_redacted(self):
        transport = Transport()
        with patch.object(transport.opener, "open", side_effect=URLError("SECRET")):
            with self.assertRaisesRegex(BridgeError, "TRANSPORT_ERROR") as error:
                transport.request("GET", "https://api.notion.com", {})
        self.assertNotIn("SECRET", str(error.exception))

    def test_oversized_and_invalid_json_fail_closed(self):
        for raw, code in [(b'x' * 1_000_001, "RESPONSE_TOO_LARGE"), (b'not-json SECRET', "INVALID_RESPONSE")]:
            transport = Transport()
            with patch.object(transport.opener, "open", return_value=io.BytesIO(raw)):
                with self.assertRaisesRegex(BridgeError, code):
                    transport.request("GET", "https://api.notion.com", {})


if __name__ == "__main__":
    unittest.main()
