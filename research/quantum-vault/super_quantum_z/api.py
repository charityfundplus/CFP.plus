"""Opt-in HTTP access to fixed local experiments."""

import os
import secrets
from threading import BoundedSemaphore

from fastapi import FastAPI, Header, HTTPException

from . import access
from .access import JobID, RecordID, WorkOrder
from .core import BackendUnavailable, Experiment
from .isolation import ExperimentFailed, ExperimentTimedOut, execute_isolated

from .queue import QueueConflict

_slots = BoundedSemaphore(2)

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


@app.post("/sandbox/experiment")
def experiment(request: Experiment, authorization: str = Header(default="")) -> dict:
    if os.getenv("SUPER_QUANTUM_Z_QUEUE_CONFIG"):
        raise HTTPException(status_code=503, detail="Use the queued CMP sandbox endpoint")
    token = os.getenv("SUPER_QUANTUM_Z_SANDBOX_TOKEN")
    if not token:
        raise HTTPException(status_code=503, detail="Sandbox experiments are disabled")
    expected = f"Bearer {token}".encode("utf-8")
    if not secrets.compare_digest(authorization.encode("utf-8"), expected):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not _slots.acquire(blocking=False):
        raise HTTPException(status_code=503, detail="Sandbox workers are busy")
    try:
        return execute_isolated(request)
    except ExperimentTimedOut as error:
        raise HTTPException(status_code=504, detail="Sandbox experiment timed out") from error
    except ExperimentFailed as error:
        raise HTTPException(status_code=500, detail="Sandbox experiment failed") from error
    except BackendUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    finally:
        _slots.release()


@app.post("/sandbox/cmp/{owner}/work-orders", status_code=202)
def submit_work_order(owner: RecordID, order: WorkOrder, authorization: str = Header(default="")):
    try:
        return access.submit(access.configuration(), owner, authorization, order)
    except access.AccessDenied as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except QueueConflict as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@app.get("/sandbox/cmp/{owner}/evidence/{job}")
def read_evidence(owner: RecordID, job: JobID, authorization: str = Header(default="")):
    try:
        record = access.evidence(access.configuration(), owner, authorization, job)
    except access.AccessDenied as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    if record is None:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return record
