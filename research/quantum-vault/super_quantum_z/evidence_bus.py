"""Scoped Evidence handoff in the existing 6789 SQLite database."""

import hashlib
import hmac
import json
import os
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints

from .access import AccessDenied, authorize
from .queue import Queue, QueueConflict

Digest = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]


class Receipt(BaseModel):
    model_config = ConfigDict(extra="forbid")
    digest: Digest


class Review(Receipt):
    verdict: Literal["accepted", "needs_changes"]


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def process(config, actor, authorization, job, action, receipt=None):
    authorize(config, actor, authorization)
    key = os.environ.get("SUPER_QUANTUM_Z_EVIDENCE_KEY", "").encode()
    if len(key) < 32 or any(hmac.compare_digest(key, p.token.encode()) for p in config.principals.values()):
        raise AccessDenied("Evidence Bus is disabled")
    queue = Queue(config.database)
    with queue.transaction() as db:
        row = db.execute("SELECT * FROM jobs WHERE job=?", (job,)).fetchone()
        if row is None:
            return None
        owner = row["owner"]
        order = row["request_key"]
        grant = config.evidence_grants.get(owner, {}).get(order)
        if grant is None:
            return None
        recipient, reviewer = grant.recipient, grant.reviewer
        members = {owner, recipient, reviewer}
        if len(members) != 3 or not members <= config.principals.keys() or actor not in members:
            return None
        if action != "read" and actor != {
            "publish": owner, "ack": recipient, "review": reviewer,
        }[action]:
            raise AccessDenied("Action is outside this ID's role")
        db.execute("""CREATE TABLE IF NOT EXISTS evidence_handoffs (
            job TEXT PRIMARY KEY, envelope TEXT NOT NULL, digest TEXT NOT NULL,
            signature TEXT NOT NULL, acknowledged REAL, reviewed REAL, verdict TEXT)""")
        packet = db.execute("SELECT * FROM evidence_handoffs WHERE job=?", (job,)).fetchone()
        if action == "publish" and packet is None:
            if row["state"] != "succeeded":
                raise QueueConflict("A succeeded work order is required")
            if db.execute("SELECT stopped FROM control").fetchone()[0]:
                raise QueueConflict("Emergency stop is set")
            events = db.execute(
                "SELECT seq, at, event, attempt FROM audit WHERE job=? ORDER BY seq", (job,),
            )
            envelope = {
                "schema": "cfp.6789.evidence.v1", "job": job, "work_order_id": order,
                "owner": owner, "recipient": recipient, "reviewer": reviewer,
                "backend": row["backend"], "result": json.loads(row["result"]),
                "result_sha256": row["digest"], "execution_audit": [dict(e) for e in events],
            }
            content = canonical(envelope)
            digest = hashlib.sha256(content).hexdigest()
            signature = hmac.digest(key, content, "sha256").hex()
            db.execute("""INSERT INTO evidence_handoffs(job,envelope,digest,signature)
                          VALUES (?,?,?,?)""", (job, content.decode(), digest, signature))
            queue._event(db, row, "evidence_published")
            packet = db.execute("SELECT * FROM evidence_handoffs WHERE job=?", (job,)).fetchone()
        if packet is None:
            return None

        envelope = json.loads(packet["envelope"])
        if (envelope["job"], envelope["owner"], envelope["work_order_id"]) != (job, owner, order):
            raise QueueConflict("Evidence belongs to another work order")
        if (envelope["recipient"], envelope["reviewer"]) != (recipient, reviewer):
            raise QueueConflict("Current grant differs from the signed handoff")
        content = canonical(envelope)
        digest = hashlib.sha256(content).hexdigest()
        signature = hmac.digest(key, content, "sha256").hex()
        result_digest = hashlib.sha256(canonical(envelope["result"])).hexdigest()
        if not all((
            hmac.compare_digest(digest, packet["digest"]),
            hmac.compare_digest(signature, packet["signature"]),
            hmac.compare_digest(result_digest, envelope["result_sha256"]),
        )):
            raise QueueConflict("Evidence integrity verification failed")
        if receipt is not None and not hmac.compare_digest(receipt.digest, digest):
            raise QueueConflict("Receipt digest differs from the signed evidence")
        if action == "ack" and packet["acknowledged"] is None:
            db.execute("UPDATE evidence_handoffs SET acknowledged=? WHERE job=?", (queue.clock(), job))
            queue._event(db, dict(row, owner=actor), "evidence_acknowledged")
        if action == "review":
            if packet["acknowledged"] is None:
                raise QueueConflict("Recipient readback is required before independent review")
            if packet["verdict"] is None:
                db.execute("UPDATE evidence_handoffs SET reviewed=?, verdict=? WHERE job=?",
                           (queue.clock(), receipt.verdict, job))
                queue._event(db, dict(row, owner=actor), "evidence_reviewed")
            elif packet["verdict"] != receipt.verdict:
                raise QueueConflict("The review verdict has already been recorded")
        status = db.execute(
            "SELECT acknowledged, reviewed, verdict FROM evidence_handoffs WHERE job=?", (job,),
        ).fetchone()
        history = db.execute("""SELECT seq,at,owner AS actor,event FROM audit
                                WHERE job=? AND event LIKE 'evidence_%' ORDER BY seq""", (job,))
        return {"envelope": envelope, "sha256": digest, "hmac_sha256": signature,
                "verified_by_server": True, "status": dict(status),
                "history": [dict(event) for event in history]}
