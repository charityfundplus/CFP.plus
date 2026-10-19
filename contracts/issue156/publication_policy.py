"""Offline reference policy only. No HTTP listener, network, credentials or storage writes.
Trusted caller supplies a VERIFIED approval from external Governance, never an HTTP body.
This module does not verify signatures or establish approval authority.
"""
import copy, hashlib, json
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker
from datetime import datetime, timezone

def digest(record):
    return hashlib.sha256(json.dumps(record,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()

def project(record, approval, *, trusted_revision, now):
    """Verify exact-content/field/revision/expiry binding after external signature verification.
    Fail closed; retain all source values including ID/Parent/DID. No identity normalization.
    """
    if now.tzinfo is None: raise ValueError('TIMEZONE_REQUIRED')
    if not isinstance(approval,dict) or approval.get('signatureVerified') is not True:
        raise ValueError('EXTERNAL_APPROVAL_REQUIRED')
    if approval.get('audience') != 'public' or approval.get('sourceRevision') != trusted_revision:
        raise ValueError('APPROVAL_SCOPE_DENIED')
    if not isinstance(approval.get('decisionURL'),str) or not approval['decisionURL'].startswith('https://'):
        raise ValueError('DECISION_EVIDENCE_REQUIRED')
    try: expiry=datetime.fromisoformat(approval['expiresAt'].replace('Z','+00:00'))
    except (ValueError,KeyError,TypeError): raise ValueError('APPROVAL_EXPIRY_INVALID')
    if expiry.tzinfo is None or expiry<=now: raise ValueError('APPROVAL_EXPIRED')
    if approval.get('recordHash') != digest(record) or record.get('sourceRevision') != trusted_revision:
        raise ValueError('SOURCE_CHANGED')
    if sorted(approval.get('fields',[])) != sorted(record): raise ValueError('FIELD_APPROVAL_REQUIRED')
    if record.get('status') not in ('approved','active') or not record.get('evidence'):
        raise ValueError('PUBLICATION_NOT_APPROVED')
    if record.get('readOnly') is not True or record.get('activationAllowed') is not False:
        raise ValueError('HOLD_REQUIRED')
    spec=json.loads((Path(__file__).parent/"openapi.json").read_text())
    Draft202012Validator({"$ref":"#/components/schemas/PublishedRecord","components":spec["components"]},format_checker=FormatChecker()).validate(record)
    return copy.deepcopy(record)

def retry_delay(status, attempt, retry_after=None, *, random_fraction=0.5):
    """Design helper: attempts numbered 1..3; no retry of auth, 4xx, parsing or conflict.
    Long Retry-After stops this budget rather than retrying earlier than requested.
    Transport failures require proven safe GET and the same source pin by the caller.
    """
    if status not in (429,502,503,504) or attempt>=3: return None
    if retry_after is not None:
        if not isinstance(retry_after,int) or retry_after<0 or retry_after>5: return None
        return retry_after
    if not 0<=random_fraction<=1: raise ValueError('JITTER_INVALID')
    return min(5,2**(attempt-1))*random_fraction
