import copy
import json
import sys
import urllib.request
from pathlib import Path
from datetime import datetime, timezone, timedelta
import jsonschema
from jsonschema import Draft202012Validator, FormatChecker

from tests.ctttc.calendar_validator_v066 import validate_calendar_and_cross_fields
from tests.ctttc.state_machine_v066 import VALID_TRANSITIONS, validate_state_transition
from tests.ctttc.evidence_verifier_v066 import verify_evidence_artifact, classify_claim_support, PINNED_README_URL, EXPECTED_README_SHA256
from tests.ctttc.duplicate_control_v066 import control_duplicate

ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = ROOT / "schemas" / "ctttc-universal-record.schema.v0.6.6.json"


def schema_validate(data, schema):
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(data)


def record_test(result, label, passed, failed):
    print(f"[{'PASS' if result else 'FAIL'}] {label}")
    return passed + int(result), failed + int(not result)


def main():
    tz = timezone(timedelta(hours=7))
    print("=== CFP+ CTTTC TEST RUNNER v0.6.6 ===")
    print("Execution Timestamp:", datetime.now(tz).isoformat(timespec="seconds"))
    print("Python Version:", sys.version.split()[0])
    print("jsonschema Version:", jsonschema.__version__)

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    passed = 0
    failed = 0

    for kind, expect_valid in (("valid", True), ("invalid", False)):
        folder = ROOT / "tests" / "ctttc" / "fixtures" / kind
        for path in sorted(folder.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            try:
                schema_validate(data, schema)
                ok, msg = validate_calendar_and_cross_fields(data)
                accepted = ok
            except Exception as exc:
                accepted = False
                msg = str(exc)
            result = accepted == expect_valid
            passed, failed = record_test(result, f"{kind} fixture {path.name}: {msg}", passed, failed)

    # Exhaustive state-machine verification: every state pair must exactly match
    # the declarative VALID_TRANSITIONS matrix. This covers allowed transitions,
    # forbidden transitions, self-loops, terminal states, and ARCHIVED behavior.
    states = sorted(VALID_TRANSITIONS)
    for before in states:
        for after in states:
            expected = after in VALID_TRANSITIONS[before]
            got = validate_state_transition(before, after)
            passed, failed = record_test(
                got == expected,
                f"transition {before}->{after} expected={expected} got={got}",
                passed,
                failed,
            )

    # Unknown states must fail closed.
    unknown_transition_tests = [
        ("UNKNOWN", "RUNNING"),
        ("RUNNING", "UNKNOWN"),
        ("", "ARCHIVED"),
    ]
    for before, after in unknown_transition_tests:
        got = validate_state_transition(before, after)
        passed, failed = record_test(
            got is False,
            f"unknown transition {before!r}->{after!r} fails closed",
            passed,
            failed,
        )

    # Cross-field regression: a final outcome may not remain FUTURE.
    future_template = json.loads((ROOT / "tests" / "ctttc" / "fixtures" / "valid" / "03_future.json").read_text(encoding="utf-8"))
    outcome_evidence = {
        "evidence_id": "E-OUTCOME-1",
        "source_url": "https://example.org/outcome",
        "content_hash": "a" * 64,
        "evidence_type": "Official Document",
        "description": "Outcome evidence",
        "verified_at": "2026-08-23",
        "verification_actor": "CTTTC test",
    }
    final_outcome_tests = ["OCCURRED", "CANCELLED", "NOT_VERIFIED"]
    for status in final_outcome_tests:
        record = copy.deepcopy(future_template)
        record["event_status"] = status
        record["future_metadata"]["actual_outcome_status"] = status
        record["future_metadata"]["actual_outcome_evidence"] = [] if status == "NOT_VERIFIED" else [outcome_evidence]
        ok, msg = validate_calendar_and_cross_fields(record)
        passed, failed = record_test(
            ok is False and "cannot remain temporal_class=FUTURE" in msg,
            f"temporal reconcile rejects FUTURE + {status}: {msg}",
            passed,
            failed,
        )

    # CHANGED and DELAYED are intermediate states and may retain a future target.
    for status in ("CHANGED", "DELAYED"):
        record = copy.deepcopy(future_template)
        record["event_status"] = status
        record["future_metadata"]["actual_outcome_status"] = status
        record["future_metadata"]["actual_outcome_evidence"] = [outcome_evidence]
        ok, msg = validate_calendar_and_cross_fields(record)
        passed, failed = record_test(
            ok is True,
            f"temporal reconcile allows FUTURE + {status}: {msg}",
            passed,
            failed,
        )

    try:
        positive = verify_evidence_artifact(PINNED_README_URL, EXPECTED_README_SHA256)
        result = positive["verification_result"] == "PASS_INTEGRITY"
        passed, failed = record_test(result, "Evidence Positive", passed, failed)
        print(json.dumps(positive, ensure_ascii=False))
    except Exception as exc:
        passed, failed = record_test(False, f"Evidence Positive Fetch Error: {exc!r}", passed, failed)

    try:
        negative = verify_evidence_artifact(PINNED_README_URL, "0" * 64)
        result = negative["verification_result"] == "FAIL_HASH_MISMATCH" and not negative["hash_match"]
        passed, failed = record_test(result, f"Evidence Negative: {negative['verification_result']}", passed, failed)
    except Exception as exc:
        passed, failed = record_test(False, f"Evidence Negative Fetch Error: {exc!r}", passed, failed)

    try:
        req = urllib.request.Request(PINNED_README_URL, headers={"User-Agent": "CFP-Plus-CTTTC-CI/0.6.6"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            source_text = resp.read().decode("utf-8", errors="ignore")
        classification, ratio = classify_claim_support(
            {"title": "Charity Fund Plus Ecosystem Architecture", "summary": "Universal record schema and governance protocols for CFP ecosystem."},
            source_text,
        )
        result = classification == "SEMANTIC_REVIEW_REQUIRED"
        passed, failed = record_test(result, f"Claim Support: {classification} overlap={ratio:.4f}", passed, failed)
    except Exception as exc:
        passed, failed = record_test(False, f"Claim Support Fetch Error: {exc!r}", passed, failed)

    existing = [
        {
            "day_key": "08-23",
            "title": "Sự Kiện AI Toàn Cầu",
            "domain": "AI & Technology",
            "scale": "Global",
            "exact_fingerprint": "f" * 64,
        }
    ]
    duplicate_tests = [
        (
            {
                "day_key": "01-01",
                "title": "Other",
                "domain": "Other",
                "scale": "Local",
                "exact_fingerprint": "f" * 64,
            },
            "EXACT_DUPLICATE",
            "exact fingerprint is authoritative across presentation fields",
        ),
        (
            {
                "day_key": "08-23",
                "title": "  SU KIEN ai—toàn cầu!!! ",
                "domain": "ai & technology",
                "scale": " GLOBAL ",
                "exact_fingerprint": "e" * 64,
            },
            "SIMILARITY_REVIEW",
            "normalized case/whitespace/punctuation/diacritics",
        ),
        (
            {
                "day_key": "08-23",
                "title": "Sự Kiện AI Toàn Cầu",
                "domain": "Health",
                "scale": "Global",
                "exact_fingerprint": "d" * 64,
            },
            "DISTINCT_EVENT",
            "same title/day but different domain avoids coarse false positive",
        ),
        (
            {
                "day_key": "08-24",
                "title": "Sự Kiện AI Toàn Cầu",
                "domain": "AI & Technology",
                "scale": "Global",
                "exact_fingerprint": "c" * 64,
            },
            "DISTINCT_EVENT",
            "different structural day remains distinct without exact fingerprint match",
        ),
    ]
    for record, expected, reason in duplicate_tests:
        got = control_duplicate(record, existing)
        passed, failed = record_test(
            got == expected,
            f"Duplicate expected={expected} got={got}: {reason}",
            passed,
            failed,
        )

    print("Total Passed:", passed)
    print("Total Failed:", failed)
    print("Exit Code:", 0 if failed == 0 else 1)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
