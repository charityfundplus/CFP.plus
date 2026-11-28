"""Biểu diễn mạch trung lập với backend, kèm giới hạn an toàn."""

from __future__ import annotations

from dataclasses import dataclass, field

ONE_QUBIT = {"h", "x", "y", "z", "s", "t", "rx", "ry", "rz"}
TWO_QUBIT = {"cx", "cz"}
PARAM = {"rx", "ry", "rz"}
MAX_QUBITS = 20
MAX_GATES = 5000
MAX_SHOTS = 100_000


class CircuitError(ValueError):
    pass


@dataclass(frozen=True)
class Gate:
    name: str
    qubits: tuple[int, ...]
    param: float | None = None


@dataclass
class Circuit:
    n_qubits: int
    gates: list[Gate] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.n_qubits, int) or not 1 <= self.n_qubits <= MAX_QUBITS:
            raise CircuitError(f"n_qubits phải trong 1..{MAX_QUBITS}")

    def add(self, name: str, *qubits: int, param: float | None = None) -> "Circuit":
        name = name.lower()
        if name in ONE_QUBIT:
            arity = 1
        elif name in TWO_QUBIT:
            arity = 2
        else:
            raise CircuitError(f"Cổng không hỗ trợ: {name}")
        if len(qubits) != arity or len(set(qubits)) != arity:
            raise CircuitError(f"{name} cần {arity} qubit khác nhau")
        if any(not isinstance(q, int) or not 0 <= q < self.n_qubits for q in qubits):
            raise CircuitError("Chỉ số qubit ngoài phạm vi")
        if (name in PARAM) != (param is not None):
            raise CircuitError(f"Tham số sai cho {name}")
        if len(self.gates) >= MAX_GATES:
            raise CircuitError(f"Quá {MAX_GATES} cổng")
        self.gates.append(Gate(name, tuple(qubits), None if param is None else float(param)))
        return self

    @classmethod
    def from_dict(cls, data: dict) -> "Circuit":
        c = cls(int(data["n_qubits"]))
        for g in data.get("gates", []):
            c.add(g["name"], *[int(q) for q in g["qubits"]], param=g.get("param"))
        return c

    def to_dict(self) -> dict:
        return {"n_qubits": self.n_qubits,
                "gates": [{"name": g.name, "qubits": list(g.qubits),
                           **({"param": g.param} if g.param is not None else {})} for g in self.gates]}


def bell() -> Circuit:
    return Circuit(2).add("h", 0).add("cx", 0, 1)


def ghz(n: int) -> Circuit:
    c = Circuit(n).add("h", 0)
    for i in range(n - 1):
        c.add("cx", i, i + 1)
    return c


def check_shots(shots: int) -> int:
    if not isinstance(shots, int) or not 1 <= shots <= MAX_SHOTS:
        raise CircuitError(f"shots phải trong 1..{MAX_SHOTS}")
    return shots
