"""Kiểm tra payload ngay khi nhận Job (fail-fast), tránh Job rác vào hàng đợi.

Mọi giới hạn ở đây phải khớp SPEC.md §6. Lỗi trả ValueError để API đổi thành 422.
"""

from __future__ import annotations

import math

MAX_EDGES = 5000
MAX_TIME_S = 60.0


def _finite(x, name: str) -> float:
    try:
        v = float(x)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} phải là số") from exc
    if not math.isfinite(v):
        raise ValueError(f"{name} phải hữu hạn (không NaN/Inf)")
    return v


def _time_limit(payload: dict) -> None:
    if "time_limit_s" in payload:
        t = _finite(payload["time_limit_s"], "time_limit_s")
        if not 0 < t <= MAX_TIME_S:
            raise ValueError(f"time_limit_s phải trong (0, {MAX_TIME_S}]")


def _edges(n: int, edges, max_edges: int = MAX_EDGES) -> None:
    if not isinstance(edges, list) or not 1 <= len(edges) <= max_edges:
        raise ValueError(f"edges phải là danh sách 1..{max_edges} cạnh")
    for e in edges:
        if not isinstance(e, (list, tuple)) or len(e) != 3:
            raise ValueError("mỗi cạnh là [u, v, w]")
        u, v = int(e[0]), int(e[1])
        _finite(e[2], "w")
        if not (0 <= u < n and 0 <= v < n) or u == v:
            raise ValueError(f"Cạnh không hợp lệ: {(u, v)}")


def validate_payload(kind: str, payload: dict) -> None:
    if not isinstance(payload, dict):
        raise ValueError("payload phải là object")
    if kind == "maxcut":
        n = int(payload["n"])
        if not 1 <= n <= 200:
            raise ValueError("n phải trong 1..200")
        _edges(n, payload["edges"])
        _time_limit(payload)
    elif kind == "qaoa_maxcut":
        n = int(payload["n"])
        if not 2 <= n <= 12:
            raise ValueError("QAOA mô phỏng: 2 ≤ n ≤ 12")
        _edges(n, payload["edges"], max_edges=n * (n - 1) // 2)
        grid = int(payload.get("grid", 16))
        if not 1 <= grid <= 32:
            raise ValueError("grid phải trong 1..32")
    elif kind == "assign_tasks":
        costs, cap = payload["costs"], payload["capacity"]
        if not isinstance(costs, list) or not isinstance(cap, list):
            raise ValueError("costs/capacity phải là danh sách")
        nt, nk = len(costs), len(cap)
        if not 1 <= nt <= 500 or not 1 <= nk <= 200 or nt * nk > 20_000:
            raise ValueError("kích thước costs/capacity vượt giới hạn (≤500×200, ≤20000 ô)")
        for row in costs:
            if not isinstance(row, list) or len(row) != nk:
                raise ValueError("mỗi dòng costs phải có đúng len(capacity) phần tử")
            for c in row:
                if c is not None:
                    _finite(c, "cost")
        for k in cap:
            if int(k) < 0:
                raise ValueError("capacity không âm")
        _time_limit(payload)
