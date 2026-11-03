"""Bounded real local worker for assigned Forum tasks; no shell, network or AI calls."""
import argparse
import json
import sqlite3
import time
from pathlib import Path
from operations import Operations, OperationError


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--state-dir', type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--once', action='store_true')
    mode.add_argument('--poll-seconds', type=float)
    parser.add_argument('--provision-worker', action='store_true', help='Explicitly provision local software-worker account and SI forum grant; no external identity')
    args = parser.parse_args()
    if args.poll_seconds is not None and not 0.5 <= args.poll_seconds <= 60:
        parser.error('--poll-seconds must be 0.5..60')
    token = None
    service = None
    try:
        service = Operations(args.state_dir)
        if args.provision_worker:
            service.provision_worker()
        token = service.worker_session()
        renewal = time.monotonic() + 600
        while True:
            if time.monotonic() >= renewal:
                service.logout(token)
                token = service.worker_session()
                renewal = time.monotonic() + 600
            print(json.dumps(service.worker_tick(token), ensure_ascii=False), flush=True)
            if args.once:
                return 0
            time.sleep(args.poll_seconds)
    except KeyboardInterrupt:
        return 0
    except (OperationError, sqlite3.Error, OSError):
        print(json.dumps({'result': 'BLOCKED', 'error': 'WORKER_UNAVAILABLE; CHECK AUTHORIZED LOCAL STATE'}), flush=True)
        return 1
    finally:
        if token and service:
            try:
                service.logout(token)
            except (OperationError, sqlite3.Error, OSError):
                pass


if __name__ == '__main__':
    raise SystemExit(main())
