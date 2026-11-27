"""Worker • Scheduler • Heartbeat. Dừng ngay khi Emergency Stop bật."""

from __future__ import annotations

import socket
import threading
import time

from . import __version__, backends
from .executor import execute
from .store import Store

SELFTEST_OWNER = "6789"


class Worker(threading.Thread):
    def __init__(self, store: Store, name: str | None = None, poll_s: float = 0.5,
                 lease_s: float = 60.0, max_running_per_owner: int | None = None) -> None:
        super().__init__(daemon=True, name=name or f"sqz-{socket.gethostname()}-{id(self) % 10000}")
        self.store, self.poll_s, self.lease_s = store, poll_s, lease_s
        self.max_running_per_owner = max_running_per_owner
        self._halt = threading.Event()
        self.processed = 0

    def stop(self) -> None:
        self._halt.set()

    def step(self) -> bool:
        """Một vòng: heartbeat, nhận và chạy tối đa một Job. Trả True nếu đã chạy Job."""
        stopped = self.store.stopped()
        self.store.beat(self.name, {"state": "STOPPED" if stopped else "READY",
                                    "processed": self.processed, "version": __version__})
        if stopped:
            return False
        job = self.store.claim(self.name, self.lease_s, max_running_per_owner=self.max_running_per_owner)
        if job is None:
            return False
        try:
            result = execute(job["kind"], job["payload"])
            self.store.finish(job["id"], self.name, result=result, fence=job["fence"])
        except Exception as exc:  # ghi lỗi, không làm chết worker
            self.store.finish(job["id"], self.name, error=f"{type(exc).__name__}: {exc}", fence=job["fence"])
        self.processed += 1
        return True

    def run(self) -> None:
        while not self._halt.is_set():
            if not self.step():
                self._halt.wait(self.poll_s)


class Scheduler(threading.Thread):
    """Định kỳ gửi Bell self-test cho mọi backend sẵn có (cảnh báo sớm khi sai lệch)."""

    def __init__(self, store: Store, interval_s: float = 300.0) -> None:
        super().__init__(daemon=True, name="sqz-scheduler")
        self.store, self.interval_s = store, interval_s
        self._halt = threading.Event()

    def stop(self) -> None:
        self._halt.set()

    def tick(self) -> list[str]:
        if self.store.stopped():
            return []
        return [self.store.submit(SELFTEST_OWNER, "bell_selftest", {"backend": b["name"]}, "scheduler")
                for b in backends.list_backends() if b["available"]]

    def run(self) -> None:
        while not self._halt.is_set():
            self.tick()
            self._halt.wait(self.interval_s)
