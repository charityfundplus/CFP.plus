"""Opt-in NVIDIA readiness checks for the HUB 69 sandbox."""

import json
import os
import re
from importlib import import_module
from urllib.error import HTTPError, URLError

from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def sdk_status(module_name, *, load_module=import_module):
    try:
        module = load_module(module_name)
    except ModuleNotFoundError as error:
        reason = "not_installed" if error.name == module_name else "dependency_unavailable"
        return {"status": reason}
    except (ImportError, OSError, RuntimeError):
        return {"status": "load_failed"}
    return {"status": "imported", "version": str(getattr(module, "__version__", "unknown"))}


# Only deployment operators may configure the requested and approved origins.
# Remote origins rely on operator-controlled DNS and deployment egress policy.
_LOOPBACK = {"127.0.0.1", "[::1]"}
_ORIGIN = re.compile(
    r"(https?)://(\[::1\]|[a-zA-Z0-9.-]+)(?::([1-9][0-9]{0,4}))?/?",
    re.ASCII,
)
_DNS_NAME = re.compile(
    r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z](?:[a-z0-9-]{0,61}[a-z0-9])?"
)


def _parse_origin(origin):
    match = _ORIGIN.fullmatch(origin)
    if match is None:
        return None
    scheme, host, port = match.groups()
    host = host.lower()
    if port is not None and int(port) > 65535:
        return None
    if host == "localhost" and scheme == "http":
        host = "127.0.0.1"
    if host not in _LOOPBACK and (
        scheme != "https" or len(host) > 253 or _DNS_NAME.fullmatch(host) is None
    ):
        return None
    return scheme, host, int(port) if port else (443 if scheme == "https" else 80)


def service_status(origin, *, approved_origin=None, opener=None):
    if origin is None or origin == "":
        return {"status": "not_configured"}

    destination = _parse_origin(origin)
    if destination is None:
        return {"status": "invalid_origin"}
    scheme, host, port = destination
    if host not in _LOOPBACK and (
        not approved_origin or _parse_origin(approved_origin) != destination
    ):
        return {"status": "origin_not_approved"}

    default_port = 443 if scheme == "https" else 80
    authority = host if port == default_port else f"{host}:{port}"
    health_url = f"{scheme}://{authority}/v1/health/ready"
    opener = opener if opener is not None else build_opener(ProxyHandler({}), NoRedirect())
    try:
        with opener.open(Request(health_url, method="GET"), timeout=3) as response:
            code = response.status
    except HTTPError as error:
        code = error.code
        error.close()
    except (URLError, OSError):
        return {"status": "unreachable"}
    return {"status": "ready" if code == 200 else "not_ready", "http_status": code}


def readiness(env):
    return {
        "cudaq": sdk_status("cudaq"),
        "cuquantum": sdk_status("cuquantum"),
        "nim": service_status(
            env.get("HUB69_NIM_ORIGIN"),
            approved_origin=env.get("HUB69_NIM_APPROVED_ORIGIN"),
        ),
        "ace_audio2face": service_status(
            env.get("HUB69_ACE_ORIGIN"),
            approved_origin=env.get("HUB69_ACE_APPROVED_ORIGIN"),
        ),
    }


if __name__ == "__main__":
    print(json.dumps(readiness(os.environ), sort_keys=True))


