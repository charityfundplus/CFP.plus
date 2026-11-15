"""Guest-network-namespace egress watchdog; unarmed by default.

Reads kernel tx_bytes for EVERY visible NIC, including IPv6/TLS/proxy-bypass
traffic on those NICs. This is not provider billing or an outer-cloud firewall.
Do not run on a host until owner-approved configuration and boot arming exist.
"""
import fcntl
import json
import os
import tempfile
import threading
import time
from pathlib import Path


def kernel_sample():
    root = Path('/sys/class/net')
    return {p.name: int((p/'statistics/tx_bytes').read_text())
            for p in root.iterdir()}


def boot_id():
    return Path('/proc/sys/kernel/random/boot_id').read_text().strip()


def atomic_save(path, value):
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix='.egress-')
    try:
        with os.fdopen(fd, 'w') as out:
            json.dump(value, out, allow_nan=False)
            out.flush(); os.fsync(out.fileno())
        os.replace(temp, path)
        fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        if os.path.exists(temp): os.unlink(temp)


class KernelEgressGuard:
    def __init__(self, state, quote, close_https, *, interval=.05):
        self.state, self.quote = Path(state), Path(quote)
        self.close_https = close_https
        self.interval = interval
        self.stopped = threading.Event()
        self.closed = threading.Event()
        self.reason = None
        self.error = None
        self.trigger_error = None

    def arm(self, *, limit, expires, approval=False):
        """Bootstrap seam, not authentication of real Human Governance authority.

        No re-arm existing state, no default permission. Approval/quote booleans
        are fixture/operator inputs; real host must authenticate them externally.
        """
        if not approval or type(limit) is not int or limit <= 0:
            return False
        if type(expires) is not int or expires <= int(time.time()):
            return False
        self.state.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with open(str(self.state)+'.lock', 'a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            if self.state.exists(): return False
            q = self._quote()
            if q['gross_monthly_cents'] > 1500: return False
            value = dict(format=1, status='OPEN', boot=boot_id(),
                         expires=expires, limit=limit, used=0,
                         last=kernel_sample(), time=int(time.time()))
            atomic_save(self.state, value)
        self.thread = threading.Thread(target=self._watch, daemon=True)
        self.thread.start()
        return True

    def _quote(self):
        q = json.loads(self.quote.read_text())
        if q.get('verified') is not True: raise ValueError('QUOTE_MISSING')
        if type(q.get('gross_monthly_cents')) is not int or q['gross_monthly_cents'] < 0:
            raise ValueError('QUOTE_INVALID')
        now = int(time.time())
        if type(q.get('meter_at')) is not int or not 0 <= now-q['meter_at'] <= 60:
            raise ValueError('QUOTE_STALE')
        return q

    def _watch(self):
        while not self.stopped.wait(self.interval):
            reason = None
            try:
                with open(str(self.state)+'.lock', 'a') as lock:
                    fcntl.flock(lock, fcntl.LOCK_EX)
                    value = json.loads(self.state.read_text())
                    if value.get('status') != 'OPEN': reason = 'STATE_CLOSED'
                    elif value['boot'] != boot_id(): reason = 'BOOT_CHANGED'
                    elif int(time.time()) < value['time']: reason = 'CLOCK_ROLLBACK'
                    elif int(time.time()) >= value['expires']: reason = 'LEASE_EXPIRED'
                    else:
                        q = self._quote()
                        current = kernel_sample()
                        if current.keys() != value['last'].keys(): reason = 'INTERFACE_SET_CHANGED'
                        elif any(current[k] < value['last'][k] for k in current): reason = 'COUNTER_RESET'
                        elif q['gross_monthly_cents'] > 1500: reason = 'BUDGET_EXCEEDED'
                        else:
                            value['used'] += sum(current[k]-value['last'][k] for k in current)
                            value['last'], value['time'] = current, int(time.time())
                            if value['used'] >= value['limit']: reason = 'EGRESS_LIMIT'
                    if reason: value.update(status='CLOSED', reason=reason)
                    atomic_save(self.state, value)
            except (OSError, ValueError, KeyError, TypeError, AttributeError) as e:
                reason = 'METER_STATE_OR_QUOTE_INVALID'
                self.trigger_error = type(e).__name__
                try: atomic_save(self.state, dict(format=1, status='CLOSED', reason=reason))
                except OSError: self.error = 'PERSISTENCE_FAILED'
            if reason:
                self._close(reason)
                return

    def _close(self, reason):
        self.reason = reason
        try: self.close_https()
        except Exception as e: self.error = type(e).__name__
        finally:
            self.closed.set(); self.stopped.set()

    def stop(self):
        """End local rehearsal without implicit re-arm; do not use as host teardown."""
        self.stopped.set()
        if hasattr(self, 'thread'): self.thread.join(2)
