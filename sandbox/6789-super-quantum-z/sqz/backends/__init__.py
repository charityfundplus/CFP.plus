"""Kiến trúc Adapter mở. Quy ước chung: bitstring và statevector đặt q0 ở bit trái nhất.

Phân loại tính toán (trường `nature` của mọi kết quả):
  CLASSICAL           • thuật toán cổ điển (OR-Tools, vét cạn)
  QUANTUM_SIMULATION  • mô phỏng mạch lượng tử trên CPU/GPU cổ điển
  HYBRID_SIMULATION   • vòng lặp lai: tối ưu cổ điển + mạch lượng tử MÔ PHỎNG
  QPU                 • phần cứng lượng tử thật (mặc định TẮT, cần Human Governance)

Thêm nền tảng mới: kế thừa `Backend` rồi gọi `register()`, hoặc khai báo entry point
nhóm `sqz.backends` trong gói riêng. Không cần sửa lõi.
"""

from __future__ import annotations

import importlib.util
import math
from collections import Counter

import numpy as np

from ..circuit import Circuit, check_shots

_S2 = 1 / math.sqrt(2)
_MATS = {
    "h": np.array([[_S2, _S2], [_S2, -_S2]], dtype=complex),
    "x": np.array([[0, 1], [1, 0]], dtype=complex),
    "y": np.array([[0, -1j], [1j, 0]], dtype=complex),
    "z": np.array([[1, 0], [0, -1]], dtype=complex),
    "s": np.array([[1, 0], [0, 1j]], dtype=complex),
    "t": np.array([[1, 0], [0, np.exp(1j * math.pi / 4)]], dtype=complex),
}


def _rot(name: str, theta: float) -> np.ndarray:
    c, s = math.cos(theta / 2), math.sin(theta / 2)
    if name == "rx":
        return np.array([[c, -1j * s], [-1j * s, c]], dtype=complex)
    if name == "ry":
        return np.array([[c, -s], [s, c]], dtype=complex)
    return np.array([[np.exp(-1j * theta / 2), 0], [0, np.exp(1j * theta / 2)]], dtype=complex)


def _sample(probs: np.ndarray, n: int, shots: int, seed: int | None) -> dict[str, int]:
    rng = np.random.default_rng(seed)
    probs = np.clip(probs.real, 0, None)
    probs = probs / probs.sum()
    idx = rng.choice(len(probs), size=shots, p=probs)
    return dict(Counter(format(i, f"0{n}b") for i in idx))


class Backend:
    name = "base"
    library = ""
    kind = "SIMULATOR"
    nature = "QUANTUM_SIMULATION"

    def available(self) -> bool:
        return importlib.util.find_spec(self.library) is not None if self.library else True

    def statevector(self, circuit: Circuit) -> np.ndarray:
        raise NotImplementedError

    def run(self, circuit: Circuit, shots: int = 1000, seed: int | None = None) -> dict[str, int]:
        check_shots(shots)
        sv = self.statevector(circuit)
        return _sample(np.abs(sv) ** 2, circuit.n_qubits, shots, seed)

    def info(self) -> dict:
        return {"name": self.name, "library": self.library or "numpy (nội tại)",
                "kind": self.kind, "nature": self.nature, "available": self.available()}


class NumpyBackend(Backend):
    """Bộ mô phỏng statevector nội tại, không phụ thuộc bên ngoài (chuẩn đối chiếu)."""

    name = "numpy"
    library = "numpy"

    def statevector(self, circuit: Circuit) -> np.ndarray:
        n = circuit.n_qubits
        psi = np.zeros((2,) * n, dtype=complex)
        psi[(0,) * n] = 1
        for g in circuit.gates:
            if g.name in ("cx", "cz"):
                c, t = g.qubits
                psi = np.moveaxis(psi, (c, t), (0, 1)).copy()
                if g.name == "cx":
                    psi[1] = psi[1][::-1].copy()
                else:
                    psi[1, 1] *= -1
                psi = np.moveaxis(psi, (0, 1), (c, t))
            else:
                m = _rot(g.name, g.param) if g.param is not None else _MATS[g.name]
                q = g.qubits[0]
                psi = np.moveaxis(np.tensordot(m, psi, axes=([1], [q])), 0, q)
        return psi.reshape(-1)


class CirqBackend(Backend):
    name = "cirq"
    library = "cirq"

    def _build(self, circuit: Circuit):
        import cirq

        qs = cirq.LineQubit.range(circuit.n_qubits)
        ops = []
        for g in circuit.gates:
            q = [qs[i] for i in g.qubits]
            if g.name in ("rx", "ry", "rz"):
                ops.append(getattr(cirq, g.name)(g.param)(*q))
            else:
                ops.append({"h": cirq.H, "x": cirq.X, "y": cirq.Y, "z": cirq.Z, "s": cirq.S,
                            "t": cirq.T, "cx": cirq.CNOT, "cz": cirq.CZ}[g.name](*q))
        c = cirq.Circuit(ops)
        c.append(cirq.I.on_each(*qs))  # giữ đủ qubit kể cả khi không có cổng
        return cirq, qs, c

    def statevector(self, circuit: Circuit) -> np.ndarray:
        cirq, qs, c = self._build(circuit)
        return cirq.Simulator().simulate(c, qubit_order=qs).final_state_vector.astype(complex)


class QiskitBackend(Backend):
    name = "qiskit"
    library = "qiskit"

    def _build(self, circuit: Circuit):
        from qiskit import QuantumCircuit

        qc = QuantumCircuit(circuit.n_qubits)
        for g in circuit.gates:
            if g.param is not None:
                getattr(qc, g.name)(g.param, *g.qubits)
            else:
                getattr(qc, g.name)(*g.qubits)
        return qc

    def statevector(self, circuit: Circuit) -> np.ndarray:
        from qiskit.quantum_info import Statevector

        sv = np.asarray(Statevector(self._build(circuit)).data)
        n = circuit.n_qubits  # Qiskit little-endian → đảo về q0 trái nhất
        return sv.reshape((2,) * n).transpose(tuple(range(n))[::-1]).reshape(-1)

    def run(self, circuit: Circuit, shots: int = 1000, seed: int | None = None) -> dict[str, int]:
        check_shots(shots)
        if importlib.util.find_spec("qiskit_aer") is None:
            return super().run(circuit, shots, seed)
        from qiskit_aer import AerSimulator

        qc = self._build(circuit)
        qc.measure_all()
        result = AerSimulator(seed_simulator=seed).run(qc, shots=shots).result().get_counts()
        return {k.replace(" ", "")[::-1]: v for k, v in result.items()}


class PennyLaneBackend(Backend):
    name = "pennylane"
    library = "pennylane"

    def statevector(self, circuit: Circuit) -> np.ndarray:
        import pennylane as qml

        dev = qml.device("default.qubit", wires=circuit.n_qubits)
        ops = {"h": qml.Hadamard, "x": qml.PauliX, "y": qml.PauliY, "z": qml.PauliZ,
               "s": qml.S, "t": qml.T, "cx": qml.CNOT, "cz": qml.CZ,
               "rx": qml.RX, "ry": qml.RY, "rz": qml.RZ}

        @qml.qnode(dev)
        def qnode():
            for g in circuit.gates:
                if g.param is not None:
                    ops[g.name](g.param, wires=g.qubits[0])
                else:
                    ops[g.name](wires=list(g.qubits))
            return qml.state()

        return np.asarray(qnode(), dtype=complex)


class CudaQBackend(Backend):
    """NVIDIA CUDA-Q. Dùng target GPU (cuQuantum) nếu có, không thì qpp-cpu."""

    name = "cudaq"
    library = "cudaq"

    def target(self) -> str:
        import cudaq

        return cudaq.get_target().name

    def info(self) -> dict:
        d = super().info()
        if d["available"]:
            t = self.target()
            d["target"] = t
            d["cuquantum_gpu"] = t in {"nvidia", "nvidia-mgpu", "tensornet"}
        return d

    def _kernel(self, circuit: Circuit):
        import cudaq

        k = cudaq.make_kernel()
        q = k.qalloc(circuit.n_qubits)
        for g in circuit.gates:
            if g.name == "cx":
                k.cx(q[g.qubits[0]], q[g.qubits[1]])
            elif g.name == "cz":
                k.cz(q[g.qubits[0]], q[g.qubits[1]])
            elif g.param is not None:
                getattr(k, g.name)(g.param, q[g.qubits[0]])
            else:
                getattr(k, g.name)(q[g.qubits[0]])
        return cudaq, k

    def statevector(self, circuit: Circuit) -> np.ndarray:
        cudaq, k = self._kernel(circuit)
        sv = np.array(cudaq.get_state(k), dtype=complex)
        n = circuit.n_qubits  # CUDA-Q đánh chỉ số little-endian → đảo về q0 trái nhất
        return sv.reshape((2,) * n).transpose(tuple(range(n))[::-1]).reshape(-1)

    def run(self, circuit: Circuit, shots: int = 1000, seed: int | None = None) -> dict[str, int]:
        check_shots(shots)
        cudaq, k = self._kernel(circuit)
        if seed is not None:
            cudaq.set_random_seed(seed)
        res = cudaq.sample(k, shots_count=shots)
        return {bits: int(res.count(bits)) for bits in res}


class QPUBackend(Backend):
    """Lane phần cứng lượng tử thật. TẮT mặc định; không bao giờ tự gửi job.

    Chỉ được xem là sẵn sàng khi đủ ba điều kiện: thư viện nhà cung cấp đã cài,
    `SQZ_QPU_ENABLED=1` do Human Governance đặt, và có credential của nhà cung cấp.
    Ngay cả khi đó, lõi vẫn từ chối chạy: việc nộp lên QPU (có chi phí) phải đi qua
    adapter riêng được review. Mục đích: đánh dấu rõ ranh giới mô phỏng ↔ phần cứng.
    """

    kind = "QPU"
    nature = "QPU"
    credential_env = ""

    def available(self) -> bool:
        import os

        return (super().available() and os.getenv("SQZ_QPU_ENABLED") == "1"
                and bool(os.getenv(self.credential_env)))

    def statevector(self, circuit: Circuit) -> np.ndarray:
        raise PermissionError("QPU không trả statevector")

    def run(self, circuit: Circuit, shots: int = 1000, seed: int | None = None) -> dict[str, int]:
        raise PermissionError("HUMAN_GOVERNANCE_REQUIRED: lõi không gửi job lên QPU thật")


class IBMQuantumQPU(QPUBackend):
    name = "ibm-quantum-qpu"
    library = "qiskit_ibm_runtime"
    credential_env = "QISKIT_IBM_TOKEN"


class GoogleQuantumQPU(QPUBackend):
    name = "google-quantum-qpu"
    library = "cirq_google"
    credential_env = "GOOGLE_APPLICATION_CREDENTIALS"


REGISTRY: dict[str, Backend] = {}


def register(backend: Backend) -> Backend:
    if not backend.name or backend.name in REGISTRY:
        raise ValueError(f"Tên backend trống hoặc trùng: {backend.name!r}")
    REGISTRY[backend.name] = backend
    return backend


for _b in (NumpyBackend(), CirqBackend(), QiskitBackend(), PennyLaneBackend(), CudaQBackend(),
           IBMQuantumQPU(), GoogleQuantumQPU()):
    register(_b)


def _load_entry_points() -> None:
    from importlib.metadata import entry_points

    for ep in entry_points(group="sqz.backends"):
        try:
            obj = ep.load()
            register(obj() if isinstance(obj, type) else obj)
        except Exception:  # plugin lỗi không làm hỏng lõi
            continue


_load_entry_points()


def default_backend() -> str:
    """Ưu tiên Google Cirq; không có thì dùng bộ mô phỏng nội tại."""
    return "cirq" if REGISTRY["cirq"].available() else "numpy"


def get(name: str) -> Backend:
    if name not in REGISTRY:
        raise KeyError(f"Backend không tồn tại: {name}")
    b = REGISTRY[name]
    if not b.available():
        if b.kind == "QPU":
            raise PermissionError(f"{name}: QPU TẮT (cần SQZ_QPU_ENABLED, credential và Human Governance)")
        raise RuntimeError(f"Backend {name} chưa cài thư viện {b.library}")
    return b


def list_backends() -> list[dict]:
    return [b.info() for b in REGISTRY.values()]
