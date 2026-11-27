"""Run a bounded sandbox experiment in a fresh process."""

from multiprocessing import get_context
from time import monotonic
from multiprocessing.connection import Connection

from .core import BackendUnavailable, Experiment, run

_CONTEXT = get_context("spawn")


class ExperimentTimedOut(Exception):
    pass


class ExperimentFailed(Exception):
    pass


def _execute(request: Experiment, reply: Connection) -> None:
    with reply:
        try:
            result = run(request)
        except BackendUnavailable as error:
            reply.send(("unavailable", str(error)))
        except Exception:
            reply.send(("failed", None))
        else:
            reply.send(("ok", result))


class ExperimentCancelled(Exception):
    pass


def execute_isolated(request: Experiment, timeout: float = 30.0, keep_running=None) -> dict:
    return _await_result(_execute, request, timeout, keep_running)


def _await_result(target, request: Experiment, timeout: float, keep_running=None) -> dict:
    receiver, sender = _CONTEXT.Pipe(duplex=False)
    process = _CONTEXT.Process(target=target, args=(request, sender), daemon=True)
    with receiver, sender:
        process.start()
        sender.close()
        try:
            deadline = monotonic() + timeout
            while True:
                remaining = deadline - monotonic()
                if remaining <= 0:
                    raise ExperimentTimedOut()
                interval = remaining if keep_running is None else min(remaining, 1.0)
                if receiver.poll(interval):
                    break
                if keep_running is not None and not keep_running():
                    raise ExperimentCancelled()
            try:
                status, payload = receiver.recv()
            except EOFError as error:
                raise ExperimentFailed() from error
            if status == "ok":
                return payload
            if status == "unavailable":
                raise BackendUnavailable(payload)
            raise ExperimentFailed()
        finally:
            process.join(0.1)
            if process.is_alive():
                process.terminate()
                process.join(0.25)
            if process.is_alive():
                process.kill()
                process.join()
            process.close()
