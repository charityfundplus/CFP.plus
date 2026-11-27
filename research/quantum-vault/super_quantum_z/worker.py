"""Run the sandbox worker against a local persistent queue."""

import argparse
import json
import sqlite3
import time

from .core import BackendUnavailable, Experiment
from .isolation import ExperimentCancelled, ExperimentFailed, ExperimentTimedOut, execute_isolated
from .queue import Queue


def work_once(queue):
    claim = queue.claim()
    if claim is None:
        return False
    job, session = claim["job"], claim["session"]
    try:
        result = execute_isolated(
            Experiment(backend=claim["backend"]),
            keep_running=lambda: queue.heartbeat(job, session),
        )
    except ExperimentCancelled:
        return True
    except (BackendUnavailable, ExperimentFailed, ExperimentTimedOut):
        result = None
    queue.finish(job, session, result)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database")
    parser.add_argument("action", choices=["worker", "stop", "resume", "status"])
    args = parser.parse_args()
    queue = Queue(args.database)
    if args.action == "status":
        print(json.dumps(queue.status()))
        return
    if args.action != "worker":
        queue.set_stop(args.action == "stop")
        return
    while True:
        try:
            if work_once(queue):
                continue
        except sqlite3.OperationalError as error:
            print(f"Sandbox queue unavailable: {error}", flush=True)
        time.sleep(1)


if __name__ == "__main__":
    main()
