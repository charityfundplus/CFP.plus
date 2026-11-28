"""MCP server (stdio) cho Claude Code, Codex và các client MCP cục bộ.

Chỉ công cụ mô phỏng có giới hạn; tôn trọng Emergency Stop trong SQZ_DATABASE_URL hoặc SQZ_DB_PATH.
Chạy: python -m sqz.mcp_server
"""

from __future__ import annotations

import os

from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from . import backends
from .executor import bell_selftest, execute
from .store import Store

READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True,
                            openWorldHint=False)
store = Store(os.getenv("SQZ_DATABASE_URL") or os.getenv("SQZ_DB_PATH", ":memory:"))
mcp = MCPServer("CFP+ 6789 Super Quantum Z",
                instructions="Mô phỏng lượng tử và tối ưu cổ điển trong sandbox. Không có QPU thật.")


def _guard() -> None:
    if store.stopped():
        raise RuntimeError("EMERGENCY_STOP đang bật")


@mcp.tool(annotations=READ_ONLY)
def sqz_list_backends() -> list[dict]:
    """Liệt kê backend mô phỏng và trạng thái cài đặt thực tế."""
    return backends.list_backends()


@mcp.tool(annotations=READ_ONLY)
def sqz_bell_selftest(backend: str = "numpy") -> dict:
    """Chạy bài nghiệm thu Bell (kỳ vọng 00/11 ≈ 50%)."""
    _guard()
    r = bell_selftest(backend)
    store.audit("mcp", "BELL_SELFTEST", {"backend": backend, "pass": r["pass"]})
    return r


@mcp.tool(annotations=READ_ONLY)
def sqz_simulate(circuit: dict, backend: str = "numpy", shots: int = 1000, seed: int | None = None) -> dict:
    """Mô phỏng mạch {n_qubits, gates:[{name, qubits, param?}]} (≤20 qubit, ≤100000 shots)."""
    _guard()
    return execute("circuit", {"circuit": circuit, "backend": backend, "shots": shots, "seed": seed})


@mcp.tool(annotations=READ_ONLY)
def sqz_maxcut(n: int, edges: list[list[float]], time_limit_s: float = 10.0) -> dict:
    """Giải MaxCut bằng OR-Tools CP-SAT. edges: [[u, v, w], ...]."""
    _guard()
    return execute("maxcut", {"n": n, "edges": edges, "time_limit_s": min(time_limit_s, 60.0)})


@mcp.tool(annotations=READ_ONLY)
def sqz_assign_tasks(costs: list[list[float | None]], capacity: list[int]) -> dict:
    """Phân công nhiệm vụ cho Team chi phí nhỏ nhất (OR-Tools, CLASSICAL). costs[t][k], None = không làm được."""
    _guard()
    return execute("assign_tasks", {"costs": costs, "capacity": capacity})


@mcp.tool(annotations=READ_ONLY)
def sqz_qaoa_maxcut(n: int, edges: list[list[float]], backend: str | None = None, grid: int = 16) -> dict:
    """QAOA p=1 (HYBRID_SIMULATION, ưu tiên Cirq) kèm tỉ lệ xấp xỉ so với tối ưu OR-Tools."""
    _guard()
    return execute("qaoa_maxcut", {"n": n, "edges": edges, "backend": backend, "grid": grid})


@mcp.tool(annotations=READ_ONLY)
def sqz_evaluate_agent(response: str, expected_id: str, allowed_sources: list[str],
                       require_bilingual: bool = True) -> dict:
    """6788: chấm câu trả lời Agent (danh tính, nguồn hợp lệ, song ngữ, chống phóng đại)."""
    from .si6788 import EvalCase, evaluate_response

    return evaluate_response(response, EvalCase(expected_id, allowed_sources, require_bilingual))


@mcp.tool(annotations=READ_ONLY)
def sqz_validate_evidence(report: dict) -> dict:
    """6776: kiểm báo cáo Evidence theo schema chung CFP+ v1."""
    from .ops6776 import validate_evidence

    return validate_evidence(report)


if __name__ == "__main__":
    mcp.run()
