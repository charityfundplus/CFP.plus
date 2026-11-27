"""Tối ưu tổ hợp bằng Google OR-Tools (CP-SAT) kèm baseline cổ điển vét cạn để kiểm chứng."""

from __future__ import annotations

import itertools

MAX_BRUTE_NODES = 16


def _validate(n: int, edges: list[tuple[int, int, float]]) -> None:
    if not 1 <= n <= 200:
        raise ValueError("n phải trong 1..200")
    for u, v, _ in edges:
        if not (0 <= u < n and 0 <= v < n) or u == v:
            raise ValueError(f"Cạnh không hợp lệ: {(u, v)}")


def cut_value(assign: list[int], edges) -> float:
    return sum(w for u, v, w in edges if assign[u] != assign[v])


def maxcut_brute(n: int, edges) -> tuple[float, list[int]]:
    if n > MAX_BRUTE_NODES:
        raise ValueError("Vét cạn chỉ cho n ≤ 16")
    best = (-1.0, [])
    for bits in itertools.product((0, 1), repeat=n - 1):
        a = [0, *bits]
        val = cut_value(a, edges)
        if val > best[0]:
            best = (val, a)
    return best


def maxcut_ortools(n: int, edges, time_limit_s: float = 10.0) -> dict:
    from ortools.sat.python import cp_model

    edges = [(int(u), int(v), float(w)) for u, v, w in edges]
    _validate(n, edges)
    scale = 1000
    m = cp_model.CpModel()
    x = [m.NewBoolVar(f"x{i}") for i in range(n)]
    m.Add(x[0] == 0)  # phá đối xứng
    terms = []
    for k, (u, v, w) in enumerate(edges):
        y = m.NewBoolVar(f"y{k}")  # y = x_u XOR x_v
        m.Add(y <= x[u] + x[v])
        m.Add(y <= 2 - x[u] - x[v])
        m.Add(y >= x[u] - x[v])
        m.Add(y >= x[v] - x[u])
        terms.append(int(round(w * scale)) * y)
    m.Maximize(sum(terms))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = time_limit_s
    s.parameters.num_workers = 4
    status = s.Solve(m)
    assign = [int(s.Value(v)) for v in x]
    return {"solver": "ortools-cp-sat", "status": s.StatusName(status),
            "optimal": status == cp_model.OPTIMAL, "cut": cut_value(assign, edges),
            "assignment": assign, "wall_time_s": s.WallTime()}
