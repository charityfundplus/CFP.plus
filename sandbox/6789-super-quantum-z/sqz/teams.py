"""Phân công Team, phân bổ tài nguyên và thay phiên SI AI (OR-Tools CP-SAT, CLASSICAL).

- `form_teams`: xếp Siêu Bộ Tam vào Team. Mỗi Team ≥ `min_size` thành viên; một Siêu Bộ Tam
  được ở nhiều Team nhưng tối đa `max_teams_per_trio`. Mục tiêu: tối đa độ phù hợp
  (affinity), cân bằng tải, và phủ đủ 5 Nhóm trong mỗi Team khi có thể.
- `route_tasks`: giao nhiệm vụ cho Team theo ưu tiên, năng lực và sức chứa (một nhiệm vụ,
  một Team chủ trì).
- `rotate_reviewer`: chọn reviewer theo vòng, khác chủ trì và khác người vừa review.
"""

from __future__ import annotations

from collections import Counter, defaultdict

from .ids import classify

GROUPS = ("000", "135", "246", "789")


def capacity_check(n_trios: int, n_teams: int, min_size: int, max_teams_per_trio: int) -> dict:
    need, have = n_teams * min_size, n_trios * max_teams_per_trio
    return {"slots_needed": need, "slots_available": have, "feasible": have >= need and n_trios >= min_size,
            "min_teams_per_trio_required": -(-need // n_trios) if n_trios else None}


def form_teams(trio_ids: list[str], n_teams: int, min_size: int = 33, max_teams_per_trio: int = 40,
               affinity: dict[tuple[str, int], int] | None = None, time_limit_s: float = 30.0) -> dict:
    from ortools.sat.python import cp_model

    if len(set(trio_ids)) != len(trio_ids):
        raise ValueError("trio_ids trùng")
    info = {t: classify(t) for t in trio_ids}
    cap = capacity_check(len(trio_ids), n_teams, min_size, max_teams_per_trio)
    if not cap["feasible"]:
        return {"status": "INFEASIBLE", "nature": "CLASSICAL", "capacity": cap, "teams": None}
    affinity = affinity or {}
    m = cp_model.CpModel()
    x = {(t, k): m.NewBoolVar(f"x_{t}_{k}") for t in trio_ids for k in range(n_teams)}
    for k in range(n_teams):
        m.Add(sum(x[t, k] for t in trio_ids) >= min_size)
    loads = []
    for t in trio_ids:
        load = sum(x[t, k] for k in range(n_teams))
        m.Add(load <= max_teams_per_trio)
        m.Add(load >= 1)  # không bỏ sót Siêu Bộ Tam nào
        loads.append(load)
    # Phủ Nhóm: mỗi Team có ít nhất một thành viên từ mỗi Nhóm hiện diện trong dữ liệu.
    present = sorted({i["group"] for i in info.values()})
    cover = []
    for k in range(n_teams):
        for g in present:
            members = [x[t, k] for t in trio_ids if info[t]["group"] == g]
            c = m.NewBoolVar(f"cover_{k}_{g}")
            m.AddMaxEquality(c, members)
            cover.append(c)
    max_load = m.NewIntVar(0, n_teams, "max_load")
    m.AddMaxEquality(max_load, loads)
    m.Maximize(1000 * sum(cover) + sum(affinity.get((t, k), 0) * x[t, k] for t, k in x)
               - 10 * max_load - sum(x.values()))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = time_limit_s
    s.parameters.num_workers = 4
    status = s.Solve(m)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {"status": s.StatusName(status), "nature": "CLASSICAL", "capacity": cap, "teams": None}
    teams = [[t for t in trio_ids if s.Value(x[t, k])] for k in range(n_teams)]
    per_trio = Counter(t for team in teams for t in team)
    return {"status": s.StatusName(status), "nature": "CLASSICAL", "capacity": cap, "teams": teams,
            "team_sizes": [len(tm) for tm in teams], "max_teams_per_trio_used": max(per_trio.values()),
            "groups_covered_all_teams": all(
                {info[t]["group"] for t in tm} >= set(present) for tm in teams),
            "wall_time_s": s.WallTime()}


def route_tasks(tasks: list[dict], teams: list[dict]) -> dict:
    """tasks: {id, priority, capability, effort}; teams: {id, capabilities, capacity}.

    Tối đa tổng ưu tiên được giao (nhiệm vụ ưu tiên cao được chọn trước khi thiếu sức chứa).
    """
    from ortools.sat.python import cp_model

    m = cp_model.CpModel()
    x = {}
    for i, t in enumerate(tasks):
        for j, tm in enumerate(teams):
            if t["capability"] in tm["capabilities"]:
                x[i, j] = m.NewBoolVar(f"r{i}_{j}")
        m.Add(sum(v for (a, _), v in x.items() if a == i) <= 1)
    for j, tm in enumerate(teams):
        m.Add(sum(tasks[i]["effort"] * v for (i, b), v in x.items() if b == j) <= tm["capacity"])
    m.Maximize(sum((tasks[i]["priority"] * 100 - j) * v for (i, j), v in x.items()))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = 10
    status = s.Solve(m)
    plan = {tasks[i]["id"]: teams[j]["id"] for (i, j), v in x.items() if s.Value(v)}
    return {"status": s.StatusName(status), "nature": "CLASSICAL", "assignment": plan,
            "unassigned": [t["id"] for t in tasks if t["id"] not in plan]}


def rotate_reviewer(pool: list[str], owner_id: str, history: list[str]) -> str:
    """Chọn reviewer ít lượt nhất trong `history`, khác chủ trì và khác người vừa review."""
    for p in pool:
        classify(p)
    candidates = [p for p in pool if p != owner_id]
    if history and len(candidates) > 1:
        candidates = [p for p in candidates if p != history[-1]]
    if not candidates:
        raise ValueError("Không có reviewer độc lập trong pool")
    counts = defaultdict(int, Counter(history))
    return min(candidates, key=lambda p: (counts[p], pool.index(p)))
