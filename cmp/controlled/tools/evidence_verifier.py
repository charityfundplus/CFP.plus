#!/usr/bin/env python3
"""Controlled evidence integrity verifier. It performs no network, provider, MCP, queue or runtime execution."""
import argparse
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return 'sha256:' + h.hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--manifest', required=True)
    p.add_argument('--object', required=True)
    args = p.parse_args()
    manifest = json.loads(Path(args.manifest).read_text(encoding='utf-8'))
    actual = sha256_file(Path(args.object))
    expected = manifest['integrity']['content_hash']
    result = {
        'verifier': 'cmp-controlled-evidence-verifier.v1',
        'manifest_id': manifest.get('evidence_manifest_id'),
        'expected_hash': expected,
        'actual_hash': actual,
        'verification': 'VERIFIED' if actual == expected else 'FAILED'
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if actual == expected else 2


if __name__ == '__main__':
    raise SystemExit(main())
