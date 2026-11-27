"""Fixed sandbox experiments. No provider accounts or hardware access."""

import hashlib
import json
from datetime import datetime, timezone
from threading import Lock
from typing import Literal

from pydantic import BaseModel, ConfigDict

Backend = Literal["cirq", "qiskit", "pennylane", "ortools", "cudaq"]
_CUDAQ_LOCK = Lock()


class BackendUnavailable(Exception):
    """An optional sandbox simulator is unavailable."""


class Experiment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    backend: Backend


def run(experiment: Experiment) -> dict:
    backend = experiment.backend
    if backend == "ortools":
        from ortools.sat.python import cp_model

        model = cp_model.CpModel()
        x = model.new_int_var(0, 7, "x")
        y = model.new_int_var(0, 7, "y")
        model.add(x + 2 * y <= 7)
        model.maximize(2 * x + 3 * y)
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 2
        solver.parameters.num_search_workers = 1
        status = solver.solve(model)
        if status != cp_model.OPTIMAL:
            raise RuntimeError("CP-SAT did not prove optimality within the sandbox budget")
        return {
            "result": {
                "backend": backend,
                "experiment": "bounded-integer-optimization",
                "execution_type": "classical_optimization",
                "solution": [solver.value(x), solver.value(y)],
                "objective": int(solver.objective_value),
            }
        }

    if backend == "cirq":
        import cirq
        import numpy as np

        first, second = cirq.LineQubit.range(2)
        circuit = cirq.Circuit(cirq.H(first), cirq.CNOT(first, second))
        simulator = cirq.Simulator(dtype=np.complex128)
        probabilities = abs(simulator.simulate(circuit).final_state_vector) ** 2
        circuit.append([cirq.H(first), cirq.H(second)])
        x_probabilities = abs(simulator.simulate(circuit).final_state_vector) ** 2
    elif backend == "qiskit":
        from qiskit import QuantumCircuit
        from qiskit.quantum_info import Statevector

        circuit = QuantumCircuit(2)
        circuit.h(0)
        circuit.cx(0, 1)
        probabilities = Statevector.from_instruction(circuit).probabilities()
        circuit.h([0, 1])
        x_probabilities = Statevector.from_instruction(circuit).probabilities()
    elif backend == "cudaq":
        try:
            import cudaq
        except ModuleNotFoundError as error:
            if error.name != "cudaq":
                raise
            raise BackendUnavailable("CUDA-Q CPU simulator is not installed") from error
        import numpy as np

        # CUDA-Q target selection is process-wide.
        with _CUDAQ_LOCK:
            cudaq.set_target("qpp-cpu")
            kernel = cudaq.make_kernel()
            qubits = kernel.qalloc(2)
            kernel.h(qubits[0])
            kernel.cx(qubits[0], qubits[1])
            probabilities = abs(np.array(cudaq.get_state(kernel), dtype=complex)) ** 2
            kernel.h(qubits[0])
            kernel.h(qubits[1])
            x_probabilities = abs(np.array(cudaq.get_state(kernel), dtype=complex)) ** 2
    else:
        import pennylane as qml

        @qml.qnode(qml.device("default.qubit", wires=2))
        def circuit(x_basis):
            qml.Hadamard(wires=0)
            qml.CNOT(wires=[0, 1])
            if x_basis:
                qml.Hadamard(wires=0)
                qml.Hadamard(wires=1)
            return qml.probs(wires=[0, 1])

        probabilities = circuit(False)
        x_probabilities = circuit(True)

    zz = float(probabilities[0] + probabilities[3] - probabilities[1] - probabilities[2])
    xx = float(x_probabilities[0] + x_probabilities[3] - x_probabilities[1] - x_probabilities[2])
    result = {
        "backend": backend,
        "experiment": "bell-state",
        "method": "exact_simulator_probabilities",
        "expectation": {"XX": round(xx, 12), "ZZ": round(zz, 12)},
        "basis": ["00", "01", "10", "11"],
        "probabilities": [round(float(value), 12) for value in probabilities],
    }
    if backend == "cudaq":
        result["target"] = "qpp-cpu"
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    return {
        "result": result,
        "evidence": {
            "experiment_ref": f"bell-state/{backend}",
            "backend_type": "simulator",
            "source_uri": f"urn:sha256:{digest}",
            "evidence_sha256": digest,
            "review_status": "HUMAN_REVIEW",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    }
