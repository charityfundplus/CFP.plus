"""Thực thi một Job theo loại. Mọi kết quả ghi rõ là MÔ PHỎNG."""

from __future__ import annotations

import time

from . import backends
from .circuit import Circuit, bell, check_shots
from .optimize import maxcut_ortools

BELL_TOLERANCE = 0.05


def bell_selftest(backend: str, shots: int = 2000, seed: int | None = 6789) -> dict:
    counts = backends.get(backend).run(bell(), shots, seed)
    p00 = counts.get("00", 0) / shots
    p11 = counts.get("11", 0) / shots
    leak = 1 - p00 - p11
    ok = leak < 1e-9 and abs(p00 - 0.5) <= BELL_TOLERANCE and abs(p11 - 0.5) <= BELL_TOLERANCE
    return {"backend": backend, "shots": shots, "counts": counts, "p00": p00, "p11": p11,
            "pass": ok, "expected": "00/11 ≈ 50% mỗi trạng thái", "nature": "SIMULATION"}


def execute(kind: str, payload: dict) -> dict:
    t0 = time.perf_counter()
    if kind == "circuit":
        c = Circuit.from_dict(payload["circuit"])
        shots = check_shots(int(payload.get("shots", 1000)))
        b = payload.get("backend", "numpy")
        out = {"backend": b, "shots": shots,
               "counts": backends.get(b).run(c, shots, payload.get("seed")), "nature": "SIMULATION"}
    elif kind == "bell_selftest":
        out = bell_selftest(payload.get("backend", "numpy"))
    elif kind == "maxcut":
        out = maxcut_ortools(int(payload["n"]), [tuple(e) for e in payload["edges"]],
                             float(payload.get("time_limit_s", 10)))
    else:
        raise ValueError(f"Loại Job không hỗ trợ: {kind}")
    out["elapsed_s"] = round(time.perf_counter() - t0, 6)
    return out
