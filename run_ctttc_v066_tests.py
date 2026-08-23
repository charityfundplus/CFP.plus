import json
import sys
import urllib.request
from pathlib import Path
from datetime import datetime, timezone, timedelta
import jsonschema
from jsonschema import Draft202012Validator, FormatChecker

from tests.ctttc.calendar_validator_v066 import validate_calendar_and_cross_fields
from tests.ctttc.state_machine_v066 import validate_state_transition
from tests.ctttc.evidence_verifier_v066 import verify_evidence_artifact, classify_claim_support, PINNED_README_URL, EXPECTED_README_SHA256
from tests.ctttc.duplicate_control_v066 import control_duplicate

ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = ROOT / "schemas" / "ctttc-universal-record.schema.v0.6.6.json"

def schema_validate(data, schema):
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(data)

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
            print(f"[{'PASS' if result else 'FAIL'}] {kind} fixture {path.name}: {msg}")
            passed += int(result)
            failed += int(not result)

    transitions = [
        ("RUNNING", "REACHED_TARGET", True),
        ("RUNNING", "OCCURRED", False),
        ("REACHED_TARGET", "VERIFY_ACTUAL_OUTCOME", True),
        ("ARCHIVED", "RUNNING", False),
        ("VERIFY_ACTUAL_OUTCOME", "OCCURRED", True),
        ("OCCURRED", "ARCHIVED", True),
    ]
    for before, after, expected in transitions:
        got = validate_state_transition(before, after)
        result = got == expected
        print(f"[{'PASS' if result else 'FAIL'}] transition {before}->{after} expected={expected} got={got}")
        passed += int(result)
        failed += int(not result)

    try:
        positive = verify_evidence_artifact(PINNED_README_URL, EXPECTED_README_SHA256)
        result = positive["verification_result"] == "PASS_INTEGRITY"
        print(f"[{'PASS' if result else 'FAIL'}] Evidence Positive")
        print(json.dumps(positive, ensure_ascii=False))
    except Exception as exc:
        result = False
        print("[FAIL] Evidence Positive Fetch Error:", repr(exc))
    passed += int(result)
    failed += int(not result)

    try:
        negative = verify_evidence_artifact(PINNED_README_URL, "0" * 64)
        result = negative["verification_result"] == "FAIL_HASH_MISMATCH" and not negative["hash_match"]
        print(f"[{'PASS' if result else 'FAIL'}] Evidence Negative: {negative['verification_result']}")
    except Exception as exc:
        result = False
        print("[FAIL] Evidence Negative Fetch Error:", repr(exc))
    passed += int(result)
    failed += int(not result)

    try:
        req = urllib.request.Request(PINNED_README_URL, headers={"User-Agent": "CFP-Plus-CTTTC-CI/0.6.6"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            source_text = resp.read().decode("utf-8", errors="ignore")
        classification, ratio = classify_claim_support(
            {"title": "Charity Fund Plus Ecosystem Architecture", "summary": "Universal record schema and governance protocols for CFP ecosystem."},
            source_text,
        )
        result = classification == "SEMANTIC_REVIEW_REQUIRED"
        print(f"[{'PASS' if result else 'FAIL'}] Claim Support: {classification} overlap={ratio:.4f}")
    except Exception as exc:
        result = False
        print("[FAIL] Claim Support Fetch Error:", repr(exc))
    passed += int(result)
    failed += int(not result)

    existing = [{"day_key": "08-23", "title": "A", "exact_fingerprint": "f" * 64}]
    duplicate_tests = [
        ({"day_key": "01-01", "title": "B", "exact_fingerprint": "f" * 64}, "EXACT_DUPLICATE"),
        ({"day_key": "08-23", "title": "A", "exact_fingerprint": "e" * 64}, "SIMILARITY_REVIEW"),
        ({"day_key": "08-24", "title": "C", "exact_fingerprint": "d" * 64}, "DISTINCT_EVENT"),
    ]
    for record, expected in duplicate_tests:
        got = control_duplicate(record, existing)
        result = got == expected
        print(f"[{'PASS' if result else 'FAIL'}] Duplicate expected={expected} got={got}")
        passed += int(result)
        failed += int(not result)

    print("Total Passed:", passed)
    print("Total Failed:", failed)
    print("Exit Code:", 0 if failed == 0 else 1)
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    raise SystemExit(main())
