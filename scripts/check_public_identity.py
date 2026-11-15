"""Read-only checks for publication references; never allocate or repair a record."""
import json
import re
from pathlib import Path

def canonical_url(identity):
    if not isinstance(identity, str) or not re.fullmatch(r'[0-9]+', identity):
        raise ValueError('Canonical ID must be an unchanged ASCII digit string')
    return 'https://cfp.plus/' + identity

def check_entities(records):
    findings = []
    for identity, record in records.items():
        if identity.startswith('_'):
            continue
        canonical_url(identity)
        if record.get('id') != identity:
            raise ValueError('Key/Canonical ID mismatch: ' + identity)
        public_link = record.get('public_link')
        if public_link is not None:
            expected = canonical_url(identity)
            if public_link == expected + '/':
                findings.append({'id': identity, 'finding': 'Legacy trailing slash; canonical presentation is ' + expected})
            elif public_link != expected:
                raise ValueError('Canonical URL/ID mismatch: ' + identity)
        # DID is optional in these legacy records. Absence is a finding, never
        # permission to synthesize an identifier or a revision path.
        if 'did' in record and record['did'] != identity:
            raise ValueError('DID/Canonical ID mismatch: ' + identity)
        parent = record.get('parent_id')
        if parent is not None:
            canonical_url(parent)
            if parent == identity or parent not in records:
                raise ValueError('Missing/self Parent: ' + identity)
        visited = {identity}
        cursor = parent
        while cursor:
            if cursor in visited:
                raise ValueError('Parent cycle: ' + identity)
            visited.add(cursor)
            cursor = records[cursor].get('parent_id')
            if cursor and cursor not in records:
                raise ValueError('Missing ancestor: ' + identity)
        if not parent:
            findings.append({'id': identity, 'finding': 'Parent absent; country context is not Parent evidence'})
        if 'did' not in record:
            findings.append({'id': identity, 'finding': 'DID field absent; no DID binding verified'})
    return findings

def main():
    root = Path(__file__).resolve().parents[1]
    records = json.loads((root/'registry/ai-entity-registry.json').read_text())
    findings = check_entities(records)
    print(json.dumps({'structural_checks': 'PASS', 'governance_acceptance': 'NOT VERIFIED',
                      'source': 'registry/ai-entity-registry.json', 'findings': findings}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
