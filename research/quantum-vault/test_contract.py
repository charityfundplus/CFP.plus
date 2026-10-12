"""Offline-only standard-library smoke checks; no external connections."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
schema = json.loads((ROOT / 'schema.json').read_text(encoding='utf-8'))
assert schema['additionalProperties'] is False
assert {'experiment_ref', 'backend_type', 'source_uri', 'evidence_sha256', 'review_status', 'created_at'} <= set(schema['required'])
assert schema['properties']['backend_type']['enum'] == ['simulator', 'quantum_inspired', 'physical_qpu']
assert len(schema['properties']['evidence_sha256']['pattern']) > 0
print('PASS: schema contract smoke checks (not full JSON Schema validation)')
