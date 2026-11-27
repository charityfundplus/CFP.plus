"""Loopback integration test for MCP, CMP and delivery replay after API downtime."""

import asyncio
import json
import os
import subprocess
import sys
import time
from contextlib import AsyncExitStack
from hashlib import sha256
from sqlite3 import connect

import httpx
import pytest

from super_quantum_z.queue import Queue
from super_quantum_z.worker import work_once

mcp = pytest.importorskip("mcp")


def test_mcp_cmp_recovery(tmp_path):
    db = tmp_path / "queue.db"
    config = tmp_path / "config.json"
    token = "a" * 32
    config.write_text(json.dumps({"database": str(db), "principals": {
        "0229": {"token": token, "backends": ["ortools"], "work_orders": ["CMP-replay"]},
        "6776": {"token": "b" * 32, "backends": []},
        "87783": {"token": "c" * 32, "backends": []},
        "87788": {"token": "d" * 32, "backends": []},
    }, "evidence_grants": {"0229": {"CMP-replay": {
        "recipient": "6776", "reviewer": "87783",
    }}}}))

    def start_api():
        return subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "super_quantum_z.api:app",
             "--host", "127.0.0.1", "--port", "8000"],
            env=dict(os.environ, SUPER_QUANTUM_Z_QUEUE_CONFIG=str(config),
                     SUPER_QUANTUM_Z_EVIDENCE_KEY="e" * 32),
        )

    async def run():
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        async def client(stack, owner, secret):
            params = StdioServerParameters(
                command=sys.executable, args=["-m", "super_quantum_z.mcp_server"],
                env=dict(os.environ, SUPER_QUANTUM_Z_MCP_ID=owner,
                         SUPER_QUANTUM_Z_MCP_TOKEN=secret),
            )
            read, write = await stack.enter_async_context(stdio_client(params))
            session = await stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            return session

        async def result(session, tool, args):
            reply = await session.call_tool(tool, args)
            assert not reply.isError, reply.content
            return json.loads(reply.content[0].text)

        api = start_api()
        try:
            async with AsyncExitStack() as stack:
                mcp_client = await client(stack, "0229", token)
                recipient = await client(stack, "6776", "b" * 32)
                reviewer = await client(stack, "87783", "c" * 32)
                outsider = await client(stack, "87788", "d" * 32)
                assert {tool.name for tool in (await mcp_client.list_tools()).tools} == {
                    "submit_work_order", "read_evidence", "publish_handoff",
                    "read_handoff", "acknowledge_handoff", "review_handoff",
                }
                payload = {"order": {"work_order_id": "CMP-replay",
                                     "experiment": {"backend": "ortools"}}}

                async def submit_when_ready():
                    deadline = time.monotonic() + 10
                    while time.monotonic() < deadline:
                        assert api.poll() is None
                        reply = await mcp_client.call_tool("submit_work_order", payload)
                        if not reply.isError:
                            return json.loads(reply.content[0].text)["job"]
                        await asyncio.sleep(0.1)
                    pytest.fail("MCP could not reach the CMP API")

                job = await submit_when_ready()
                api.terminate()
                api.wait(timeout=5)
                with pytest.raises(httpx.ConnectError):
                    httpx.get("http://127.0.0.1:8000", trust_env=False)
                assert (await mcp_client.call_tool("submit_work_order", payload)).isError
                assert work_once(Queue(db))
                api = start_api()
                assert await submit_when_ready() == job
                evidence = await mcp_client.call_tool("read_evidence", {"job": job})
                assert not evidence.isError
                record = json.loads(evidence.content[0].text)
                assert record["state"] == "succeeded"
                assert record["owner"] == "0229"
                assert (await mcp_client.call_tool("submit_work_order", {"order": {
                    "work_order_id": "outside-scope", "experiment": {"backend": "ortools"},
                }})).isError

                args = {"job": job}
                packet = await result(mcp_client, "publish_handoff", args)
                assert await result(mcp_client, "publish_handoff", args) == packet
                assert (await outsider.call_tool("read_handoff", args)).isError
                received = await result(recipient, "read_handoff", args)
                serialized = json.dumps(received["envelope"], sort_keys=True, separators=(",", ":"))
                assert sha256(serialized.encode()).hexdigest() == received["sha256"]
                assert received["verified_by_server"] and received["envelope"]["owner"] == "0229"
                ack = dict(args, receipt={"digest": received["sha256"]})
                review = dict(args, review={"digest": received["sha256"], "verdict": "accepted"})
                assert (await reviewer.call_tool("review_handoff", review)).isError
                assert (await mcp_client.call_tool("acknowledge_handoff", ack)).isError
                assert (await recipient.call_tool("acknowledge_handoff",
                                                 dict(args, receipt={"digest": "0" * 64}))).isError
                assert (await result(recipient, "acknowledge_handoff", ack))["status"]["acknowledged"]
                assert (await result(reviewer, "review_handoff", review))["status"]["verdict"] == "accepted"
                api.terminate()
                api.wait(timeout=5)
                api = start_api()
                assert await submit_when_ready() == job
                recovered = await result(reviewer, "read_handoff", args)
                assert recovered["sha256"] == received["sha256"]
                assert [event["actor"] for event in recovered["history"]] == ["0229", "6776", "87783"]
                with connect(db) as storage:
                    storage.execute("UPDATE evidence_handoffs SET signature=? WHERE job=?", ("0" * 64, job))
                assert (await recipient.call_tool("read_handoff", args)).isError
        finally:
            if api.poll() is None:
                api.terminate()
                api.wait(timeout=5)

    asyncio.run(run())
