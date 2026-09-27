#!/usr/bin/env python3
import hashlib, json, pathlib, re, subprocess, sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
REV=ROOT/"nco/69115/revisions/rev_69115_2026-09-26_001.json"
POINTER=ROOT/"nco/69115/published.json"
POLICY=ROOT/"policies/meta-69115.policy.json"
HTML=ROOT/"69115/index.html"

def fail(msg):
    print("FAIL:", msg)
    sys.exit(1)

n=json.loads(REV.read_text())
p=json.loads(POINTER.read_text())
policy=json.loads(POLICY.read_text())
html=HTML.read_text()

required=["identity","overview","ai_and_models","developer_and_api","products_and_services","evidence","governance","working_links"]
if n["canonical_id"]!="69115" or n["entity"]["public_route"]!="/69115": fail("canonical route/id mismatch")
if n["revision_id"]!=REV.stem: fail("revision filename/id mismatch")
if n["governance"]!=policy["governance"]: fail("Meta governance policy drift")
if sorted(n["render_contract"]["required_sections"])!=sorted(required): fail("required sections mismatch")
for node in n["ai_and_models"]["taxonomy"]:
    if node.get("stable_id_status")=="pending_verification" and node.get("canonical_id") is not None:
        fail("pending working node has canonical_id")
if p["production_lock"] is not True or p["current_published_revision_id"] is not None:
    fail("P0 pointer must remain locked and unpublished")
if 'name="cfp-published-revision"' in html:
    fail("candidate HTML must not claim a published revision")
if 'name="cfp-publication-state" content="candidate-not-published"' not in html:
    fail("candidate publication state marker missing")

copy=json.loads(REV.read_text())
expected=copy["integrity"]["content_hash"]
del copy["integrity"]["content_hash"]
canonical=json.dumps(copy,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")
actual="sha256:"+hashlib.sha256(canonical).hexdigest()
if actual!=expected: fail(f"content hash mismatch: {actual} != {expected}")

for forbidden in ["Direct Runtime","Connected Runtime","Active Runtime"]:
    if forbidden in html: fail("unsupported runtime claim in HTML")

print("PASS: Meta 69115 NCO baseline validation")
