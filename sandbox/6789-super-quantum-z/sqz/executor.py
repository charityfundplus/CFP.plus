"""Thực thi một Job theo loại. Mọi kết quả ghi rõ là MÔ PHỎNG."""

from __future__ import annotations

import time

from . import backends
from .circuit import Circuit, bell, check_shots
from .optimize import assign_tasks, maxcut_ortools, qaoa_maxcut

BELL_TOLERANCE = 0.05


KINDS = {"circuit", "bell_selftest", "maxcut", "assign_tasks", "qaoa_maxcut"}


def bell_selftest(backend: str | None = None, shots: int = 2000, seed: int | None = 6789) -> dict:
    backend = backend or backends.default_backend()
    counts = backends.get(backend).run(bell(), shots, seed)
    p00 = counts.get("00", 0) / shots
    p11 = counts.get("11", 0) / shots
    leak = 1 - p00 - p11
    ok = leak < 1e-9 and abs(p00 - 0.5) <= BELL_TOLERANCE and abs(p11 - 0.5) <= BELL_TOLERANCE
    return {"backend": backend, "shots": shots, "counts": counts, "p00": p00, "p11": p11,
            "pass": ok, "expected": "00/11 ≈ 50% mỗi trạng thái", "nature": "QUANTUM_SIMULATION"}


def execute(kind: str, payload: dict) -> dict:
    t0 = time.perf_counter()
    if kind == "circuit":
        c = Circuit.from_dict(payload["circuit"])
        shots = check_shots(int(payload.get("shots", 1000)))
        b = payload.get("backend") or backends.default_backend()
        be = backends.get(b)
        out = {"backend": b, "shots": shots, "counts": be.run(c, shots, payload.get("seed")),
               "nature": be.nature}
    elif kind == "bell_selftest":
        out = bell_selftest(payload.get("backend"))
    elif kind == "maxcut":
        out = maxcut_ortools(int(payload["n"]), [tuple(e) for e in payload["edges"]],
                             min(float(payload.get("time_limit_s", 10)), 60.0))
    elif kind == "assign_tasks":
        out = assign_tasks(payload["costs"], payload["capacity"],
                           min(float(payload.get("time_limit_s", 10)), 60.0))
    elif kind == "qaoa_maxcut":
        out = qaoa_maxcut(int(payload["n"]), [tuple(e) for e in payload["edges"]],
                          payload.get("backend"), min(int(payload.get("grid", 16)), 32))
    else:
        raise ValueError(f"Loại Job không hỗ trợ: {kind}")
    out["elapsed_s"] = round(time.perf_counter() - t0, 6)
    return out
