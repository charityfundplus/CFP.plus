"""Offline reference policy only. No HTTP listener, network, credentials or storage writes.
Trusted caller supplies a VERIFIED approval from external Governance, never an HTTP body.
This module does not verify signatures or establish approval authority.
"""
import copy, hashlib, json
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError
import re
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
    expires_at = approval.get('expiresAt')
    if not isinstance(expires_at, str):
        raise ValueError('APPROVAL_EXPIRY_INVALID')
    try: expiry=datetime.fromisoformat(expires_at.replace('Z','+00:00'))
    except ValueError: raise ValueError('APPROVAL_EXPIRY_INVALID')
    if expiry.tzinfo is None or expiry<=now: raise ValueError('APPROVAL_EXPIRED')
    if approval.get('recordHash') != digest(record) or record.get('sourceRevision') != trusted_revision:
        raise ValueError('SOURCE_CHANGED')
    fields = approval.get('fields')
    if not isinstance(fields, list) or not all(isinstance(field, str) for field in fields):
        raise ValueError('APPROVAL_FIELDS_INVALID')
    if sorted(fields) != sorted(record): raise ValueError('FIELD_APPROVAL_REQUIRED')
    if record.get('status') != 'approved' or not record.get('evidence'):
        raise ValueError('PUBLICATION_NOT_APPROVED')
    if record.get('readOnly') is not True or record.get('activationAllowed') is not False:
        raise ValueError('HOLD_REQUIRED')
    spec=json.loads((Path(__file__).parent/"openapi.json").read_text())
    Draft202012Validator({"$ref":"#/components/schemas/PublishedRecord","components":spec["components"]},format_checker=FormatChecker()).validate(record)
    return copy.deepcopy(record)

def published_page(records, approvals, *, trusted_revision, now, query='', limit=30,
                   offset=0, revision=None, approval_revision=None):
    """Offline facade model. Caller supplies one atomic current source/auth snapshot.
    Real transport MUST externally verify signatures, revocation, linked-field disclosure
    and audit each outcome. No fallback to an older authorization snapshot is permitted.
    Invalid/unapproved records are excluded before counts or offsets; source failure is fatal.
    """
    if not isinstance(trusted_revision,str) or not re.fullmatch('[a-f0-9]{40}',trusted_revision):
        raise ValueError('SOURCE_REVISION_INVALID')
    if not isinstance(records,list) or not isinstance(approvals,dict):
        raise ValueError('INPUT_INVALID')
    if type(limit) is not int or not 1<=limit<=100 or type(offset) is not int or not 0<=offset<=10000 or not isinstance(query,str) or len(query)>160:
        raise ValueError('QUERY_INVALID')
    if offset and (revision is None or approval_revision is None):
        raise ValueError('PAGINATION_PIN_REQUIRED')
    if revision is not None and revision!=trusted_revision:
        raise ValueError('PUBLICATION_SNAPSHOT_CHANGED')
    visible=[]; receipts=[]; seen=set()
    for record in records:
        if not isinstance(record,dict) or record.get('sourceRevision')!=trusted_revision:
            raise ValueError('SOURCE_CHANGED')
        identifier=record.get('id')
        if not isinstance(identifier,str) or identifier in seen:
            raise ValueError('REGISTRY_ID_CONFLICT')
        seen.add(identifier)
        approval=approvals.get(identifier)
        try:
            output=project(record,approval,trusted_revision=trusted_revision,now=now)
        except (ValueError,ValidationError):
            continue
        visible.append(output)
        receipts.append({'id':identifier,'recordHash':digest(output),'approvalHash':digest(approval)})
    pin=digest(sorted(receipts,key=lambda r:r['id']))
    if approval_revision is not None and approval_revision!=pin:
        raise ValueError('PUBLICATION_SNAPSHOT_CHANGED')
    filtered=sorted([r for r in visible if query.casefold() in r['name'].casefold() or query.casefold() in r['id'].casefold()],key=lambda r:r['id'])
    return {'records':filtered[offset:offset+limit],'total':len(filtered),'limit':limit,
            'offset':offset,'sourceRevision':trusted_revision,'approvalSetRevision':pin,
            'readOnly':True,'registryWrites':0,'activationAllowed':False}


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
