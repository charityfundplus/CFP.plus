#!/usr/bin/env python3
"""Controlled audit-chain verifier. It performs no write, dispatch, provider, MCP or automation action."""
import argparse
import hashlib
import json
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode('utf-8')


def event_hash(event):
    copy = dict(event)
    claimed = copy.pop('event_hash', None)
    return 'sha256:' + hashlib.sha256(canonical(copy)).hexdigest(), claimed


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--events', required=True, help='JSON array ordered by ledger sequence')
    args = p.parse_args()
    events = json.loads(Path(args.events).read_text(encoding='utf-8'))
    previous = 'GENESIS'
    failures = []
    for index, event in enumerate(events):
        calculated, claimed = event_hash(event)
        if event.get('previous_event_hash') != previous:
            failures.append({'index': index, 'reason': 'previous_event_hash_mismatch'})
        if claimed != calculated:
            failures.append({'index': index, 'reason': 'event_hash_mismatch'})
        previous = claimed or previous
    result = {
        'verifier': 'cmp-controlled-audit-verifier.v1',
        'event_count': len(events),
        'verification': 'PASS' if not failures else 'FAIL',
        'failures': failures,
        'last_event_hash': previous
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if not failures else 2


if __name__ == '__main__':
    raise SystemExit(main())
