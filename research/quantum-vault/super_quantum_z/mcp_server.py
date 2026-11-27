"""MCP stdio adapter to the loopback CMP API for one sandbox ID."""

import os

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import TypeAdapter

from .access import JobID, RecordID, WorkOrder
from .evidence_bus import Receipt, Review

server = FastMCP("CFP+ Super Quantum Z Sandbox")


def request(method, path, **kwargs):
    owner = TypeAdapter(RecordID).validate_python(os.environ["SUPER_QUANTUM_Z_MCP_ID"])
    token = os.environ["SUPER_QUANTUM_Z_MCP_TOKEN"]
    response = httpx.request(
        method, f"http://127.0.0.1:8000/sandbox/cmp/{owner}/{path}",
        headers={"Authorization": f"Bearer {token}"}, timeout=5, trust_env=False, **kwargs,
    )
    response.raise_for_status()
    return response.json()


@server.tool()
def submit_work_order(order: WorkOrder) -> dict:
    """Submit one fixed simulator experiment using an idempotent CMP work order ID."""
    return request("POST", "work-orders", json=order.model_dump())


@server.tool()
def read_evidence(job: JobID) -> dict:
    """Read the result digest and audit history of a job owned by this ID."""
    return request("GET", f"evidence/{job}")


@server.tool()
def publish_handoff(job: JobID) -> dict:
    """Publish a completed work order to its preconfigured recipient and reviewer."""
    return request("POST", f"handoffs/{job}")


@server.tool()
def read_handoff(job: JobID) -> dict:
    """Read a signed Evidence packet as an authorized participant."""
    return request("GET", f"handoffs/{job}")


@server.tool()
def acknowledge_handoff(job: JobID, receipt: Receipt) -> dict:
    """Record recipient readback against the signed packet digest."""
    return request("POST", f"handoffs/{job}/ack", json=receipt.model_dump())


@server.tool()
def review_handoff(job: JobID, review: Review) -> dict:
    """Record an independent review by the designated reviewer."""
    return request("POST", f"handoffs/{job}/review", json=review.model_dump())


if __name__ == "__main__":
    server.run(transport="stdio")
