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


# Only deployment operators may configure these origins. Do not pass request
# input here. Remote DNS names must belong to the approved deployment network.
_LOOPBACK = {"127.0.0.1", "[::1]", "localhost"}
_ORIGIN = re.compile(
    r"(https?)://(\[::1\]|[a-zA-Z0-9.-]+)(?::([1-9][0-9]{0,4}))?/?",
    re.ASCII,
)
_DNS_NAME = re.compile(
    r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z](?:[a-z0-9-]{0,61}[a-z0-9])?"
)


def service_status(origin, *, opener=None):
    if origin is None or origin == "":
        return {"status": "not_configured"}

    match = _ORIGIN.fullmatch(origin)
    if match is None:
        return {"status": "invalid_origin"}
    scheme, host, port = match.groups()
    host = host.lower()
    if port is not None and int(port) > 65535:
        return {"status": "invalid_origin"}
    if host not in _LOOPBACK and (
        scheme != "https" or len(host) > 253 or _DNS_NAME.fullmatch(host) is None
    ):
        return {"status": "invalid_origin"}

    authority = host if port is None else f"{host}:{port}"
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
        "nim": service_status(env.get("HUB69_NIM_ORIGIN")),
        "ace_audio2face": service_status(env.get("HUB69_ACE_ORIGIN")),
    }


if __name__ == "__main__":
    print(json.dumps(readiness(os.environ), sort_keys=True))


