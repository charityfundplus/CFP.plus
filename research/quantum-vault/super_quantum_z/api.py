"""Opt-in HTTP access to fixed local experiments."""

import os
import secrets

from fastapi import FastAPI, Header, HTTPException

from .core import BackendUnavailable, Experiment, run

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


@app.post("/sandbox/experiment")
def experiment(request: Experiment, authorization: str = Header(default="")) -> dict:
    token = os.getenv("SUPER_QUANTUM_Z_SANDBOX_TOKEN")
    if not token:
        raise HTTPException(status_code=503, detail="Sandbox experiments are disabled")
    expected = f"Bearer {token}".encode("utf-8")
    if not secrets.compare_digest(authorization.encode("utf-8"), expected):
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        return run(request)
    except BackendUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
