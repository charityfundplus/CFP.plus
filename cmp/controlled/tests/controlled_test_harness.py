#!/usr/bin/env python3
"""CMP 267 controlled test harness scaffold.

This harness intentionally does not execute queue dispatch, assignment, lease, provider/MCP runtime,
automation, Stable ID actions, Canonical Lock or Production Release. It records NOT_RUN unless
an approved controlled environment and explicitly supplied fixtures are available.
"""
import argparse
import json
from datetime import datetime, timezone

ALL_TESTS = [f'A01-AT-{i:02d}' for i in range(1, 11)] + [f'A06-AT-{i:02d}' for i in range(1, 13)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--status-template', action='store_true')
    args = parser.parse_args()
    if args.list:
        print('\n'.join(ALL_TESTS))
        return 0
    if args.status_template:
        print(json.dumps({
            'harness': 'cmp-267-controlled-test-harness.v1',
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'scope_guardrails': ['no_queue_dispatch', 'no_assignment', 'no_lease', 'no_provider_mcp_runtime', 'no_production_automation', 'no_stable_id_action', 'no_canonical_lock', 'no_production_release'],
            'tests': [{'id': test_id, 'status': 'NOT_RUN'} for test_id in ALL_TESTS]
        }, indent=2, sort_keys=True))
        return 0
    parser.error('Use --list or --status-template. Test execution requires an approved controlled environment and fixtures.')


if __name__ == '__main__':
    raise SystemExit(main())
