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
    return {"solver": "ortools-cp-sat", "nature": "CLASSICAL", "status": s.StatusName(status),
            "optimal": status == cp_model.OPTIMAL, "cut": cut_value(assign, edges),
            "assignment": assign, "wall_time_s": s.WallTime()}


# ---------------------------------------------------------------- bài toán thực tế
def assign_tasks(costs: list[list[float]], capacity: list[int], time_limit_s: float = 10.0) -> dict:
    """Phân công nhiệm vụ cho Team với chi phí nhỏ nhất (OR-Tools CP-SAT).

    costs[t][k]: chi phí khi Team k làm nhiệm vụ t (None = không đủ năng lực).
    capacity[k]: số nhiệm vụ tối đa của Team k. Mỗi nhiệm vụ đúng một Team chủ trì
    (nguyên tắc "một nhiệm vụ, một chủ trì").
    """
    from ortools.sat.python import cp_model

    nt, nk = len(costs), len(capacity)
    if not 1 <= nt <= 500 or not 1 <= nk <= 200 or any(len(r) != nk for r in costs):
        raise ValueError("Kích thước costs/capacity không hợp lệ")
    scale = 1000
    m = cp_model.CpModel()
    x = {(t, k): m.NewBoolVar(f"x{t}_{k}") for t in range(nt) for k in range(nk) if costs[t][k] is not None}
    for t in range(nt):
        m.AddExactlyOne([x[t, k] for k in range(nk) if (t, k) in x])
    for k in range(nk):
        m.Add(sum(x[t, k] for t in range(nt) if (t, k) in x) <= int(capacity[k]))
    m.Minimize(sum(int(round(costs[t][k] * scale)) * v for (t, k), v in x.items()))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = time_limit_s
    s.parameters.num_workers = 4
    status = s.Solve(m)
    feasible = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    plan = {t: k for (t, k), v in x.items() if feasible and s.Value(v)}
    return {"solver": "ortools-cp-sat", "nature": "CLASSICAL", "status": s.StatusName(status),
            "optimal": status == cp_model.OPTIMAL, "assignment": [plan.get(t) for t in range(nt)],
            "cost": sum(costs[t][k] for t, k in plan.items()) if feasible else None,
            "wall_time_s": s.WallTime()}


def assign_brute(costs, capacity) -> float | None:
    import itertools

    best = None
    for combo in itertools.product(range(len(capacity)), repeat=len(costs)):
        if any(costs[t][k] is None for t, k in enumerate(combo)):
            continue
        if any(combo.count(k) > capacity[k] for k in range(len(capacity))):
            continue
        c = sum(costs[t][k] for t, k in enumerate(combo))
        best = c if best is None or c < best else best
    return best


# ---------------------------------------------------------------- tính toán lai
def qaoa_maxcut(n: int, edges, backend: str | None = None, grid: int = 24, shots: int = 4000,
                seed: int = 6789) -> dict:
    """QAOA p=1 cho MaxCut: tối ưu tham số cổ điển (grid) + mạch lượng tử MÔ PHỎNG.

    Trả về tỉ lệ xấp xỉ so với lời giải tối ưu của OR-Tools để đánh giá trung thực,
    không tuyên bố lợi thế lượng tử.
    """
    import math

    import numpy as np

    from . import backends as bk
    from .circuit import Circuit

    if not 2 <= n <= 12:
        raise ValueError("QAOA mô phỏng: 2 ≤ n ≤ 12")
    edges = [(int(u), int(v), float(w)) for u, v, w in edges]
    _validate(n, edges)
    name = backend or bk.default_backend()
    b = bk.get(name)
    cuts = np.array([cut_value([int(c) for c in format(i, f"0{n}b")], edges) for i in range(2 ** n)])

    def build(gamma: float, beta: float) -> Circuit:
        c = Circuit(n)
        for q in range(n):
            c.add("h", q)
        for u, v, w in edges:  # exp(-i γ w Z_u Z_v / 2) = CX · RZ(γw) · CX
            c.add("cx", u, v).add("rz", v, param=gamma * w).add("cx", u, v)
        for q in range(n):
            c.add("rx", q, param=2 * beta)
        return c

    best = (-1.0, 0.0, 0.0)
    for gi in range(grid):
        for bi in range(grid):
            g, be = math.pi * gi / grid, math.pi / 2 * bi / grid
            p = np.abs(b.statevector(build(g, be))) ** 2
            e = float(p @ cuts)
            if e > best[0]:
                best = (e, g, be)
    exp_cut, gamma, beta = best
    counts = b.run(build(gamma, beta), shots, seed)
    top = max(counts, key=lambda k: cut_value([int(c) for c in k], edges))
    optimum = maxcut_ortools(n, edges)["cut"]
    return {"algorithm": "QAOA p=1", "nature": "HYBRID_SIMULATION", "backend": name,
            "gamma": gamma, "beta": beta, "expected_cut": exp_cut,
            "best_sampled": top, "best_sampled_cut": cut_value([int(c) for c in top], edges),
            "classical_optimum": optimum, "approximation_ratio": exp_cut / optimum if optimum else None,
            "evaluations": grid * grid, "shots": shots}
