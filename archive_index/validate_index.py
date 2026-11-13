#!/usr/bin/env python3
"""Read-only CFP+ archive index validator. Standard library only."""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

STATUS = {"PENDING", "REVIEW", "VERIFIED", "BLOCKED"}
GROUPS = {"V/D", "000", "135", "246", "789"}
STORES = {"GitHub", "Notion", "Google", "Cloud", "Web", "Quantum", "other"}

def validate(item):
    errors = []
    for field in ("asset_key", "title", "chapter", "source_uri", "review_status"):
        if field not in item or item[field] in (None, ""):
            errors.append(f"missing {field}")
    chapter = item.get("chapter")
    if type(chapter) is not int or chapter not in range(10):
        errors.append("chapter must be integer 0..9")
    if item.get("group") is not None and item["group"] not in GROUPS:
        errors.append("unknown group")
    if item.get("store") is not None and item["store"] not in STORES:
        errors.append("unknown store")
    if item.get("review_status") not in STATUS:
        errors.append("invalid review_status")
    cid = item.get("canonical_entity_id")
    if cid is not None:
        if not isinstance(cid, str) or not re.fullmatch(r"[0-9]+", cid):
            errors.append("canonical_entity_id must be numeric string")
        elif type(chapter) is int and int(cid[0]) != chapter:
            errors.append("canonical_entity_id root digit differs from chapter")
    for day in item.get("calendar_days", []):
        if not isinstance(day, str) or not re.fullmatch(r"\d{2}-\d{2}", day):
            errors.append(f"invalid MM-DD: {day!r}")
            continue
        try:
            date(2000, int(day[:2]), int(day[3:]))
        except ValueError:
            errors.append(f"invalid calendar date: {day}")
    if item.get("review_status") == "VERIFIED" and not item.get("evidence_uris"):
        errors.append("VERIFIED requires evidence_uris")
    return errors

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path, help="JSON array of asset records")
    args = parser.parse_args()
    records = json.loads(args.file.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise SystemExit("Expected a JSON array")
    failures = 0
    seen = set()
    for i, item in enumerate(records):
        errs = validate(item) if isinstance(item, dict) else ["record is not an object"]
        if isinstance(item, dict):
            key = item.get("asset_key")
            if key in seen:
                errs.append("duplicate asset_key")
            seen.add(key)
        if errs:
            failures += 1
            print(f"record {i}: {'; '.join(errs)}", file=sys.stderr)
    print(f"checked={len(records)} failed={failures}")
    return 1 if failures else 0

if __name__ == "__main__":
    sys.exit(main())
