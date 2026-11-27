"""Loopback integration test for MCP, CMP and delivery replay after API downtime."""

import asyncio
import json
import os
import subprocess
import sys
import time

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
        "0229": {"token": token, "backends": ["ortools"]},
    }}))

    def start_api():
        return subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "super_quantum_z.api:app",
             "--host", "127.0.0.1", "--port", "8000"],
            env=dict(os.environ, SUPER_QUANTUM_Z_QUEUE_CONFIG=str(config)),
        )

    async def run():
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        params = StdioServerParameters(
            command=sys.executable, args=["-m", "super_quantum_z.mcp_server"],
            env=dict(os.environ, SUPER_QUANTUM_Z_MCP_ID="0229",
                     SUPER_QUANTUM_Z_MCP_TOKEN=token),
        )
        api = start_api()
        try:
            async with stdio_client(params) as (read, write), ClientSession(read, write) as mcp_client:
                await mcp_client.initialize()
                assert {tool.name for tool in (await mcp_client.list_tools()).tools} == {
                    "submit_work_order", "read_evidence",
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
        finally:
            if api.poll() is None:
                api.terminate()
                api.wait(timeout=5)

    asyncio.run(run())
