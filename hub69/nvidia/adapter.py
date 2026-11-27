"""Shared NVIDIA sandbox adapter for HUB 69."""

import argparse
import json
from threading import Lock
from urllib import request


_cudaq_target_lock = Lock()


def bell_pair(target="qpp-cpu", shots=256):
    """Run a Bell circuit on CPU, or on the cuStateVec GPU backend."""
    if target not in {"qpp-cpu", "nvidia"} or shots < 1:
        raise ValueError("Select qpp-cpu or nvidia and a positive shot count")

    import cudaq

    with _cudaq_target_lock:
        previous = cudaq.get_target().name
        cudaq.set_target(target)
        try:
            kernel = cudaq.make_kernel()
            qubits = kernel.qalloc(2)
            kernel.h(qubits[0])
            kernel.cx(qubits[0], qubits[1])
            kernel.mz(qubits)
            return dict(cudaq.sample(kernel, shots_count=shots).items())
        finally:
            cudaq.set_target(previous)


def nim_chat(base_url, model, messages, *, api_key=None, timeout=15):
    """Send a chat request to an explicitly configured NIM endpoint."""
    class NoRedirect(request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    data = json.dumps(
        {"model": model, "messages": messages, "stream": False}
    ).encode("utf-8")
    req = request.Request(
        f"{base_url.rstrip('/')}/v1/chat/completions",
        data=data,
        headers=headers,
        method="POST",
    )
    with request.build_opener(NoRedirect).open(req, timeout=timeout) as response:
        return json.load(response)


def ace_health(target, *, service="", secure=True, timeout=5):
    """Query the standard gRPC health service on a configured ACE endpoint."""
    import grpc
    from grpc_health.v1 import health_pb2, health_pb2_grpc

    channel = (
        grpc.secure_channel(target, grpc.ssl_channel_credentials())
        if secure
        else grpc.insecure_channel(target)
    )
    with channel:
        stub = health_pb2_grpc.HealthStub(channel)
        response = stub.Check(
            health_pb2.HealthCheckRequest(service=service), timeout=timeout
        )
    return health_pb2.HealthCheckResponse.ServingStatus.Name(response.status)


def main():
    parser = argparse.ArgumentParser(description="HUB 69 NVIDIA Bell pair smoke test")
    parser.add_argument("--target", choices=("qpp-cpu", "nvidia"), default="qpp-cpu")
    parser.add_argument("--shots", type=int, default=256)
    args = parser.parse_args()
    counts = bell_pair(args.target, args.shots)
    print(json.dumps({"target": args.target, "counts": counts}, sort_keys=True))
    return int(not set(counts) <= {"00", "11"} or sum(counts.values()) != args.shots)


if __name__ == "__main__":
    raise SystemExit(main())
