"""Opt-in NVIDIA readiness checks for the HUB 69 sandbox."""

import json
import os
from importlib import import_module
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
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


def service_status(origin, *, opener=None):
    if not origin:
        return {"status": "not_configured"}
    try:
        url = urlsplit(origin)
        port = url.port
    except ValueError:
        return {"status": "invalid_origin"}
    local = url.hostname in {"localhost", "127.0.0.1", "::1"}
    if (
        not url.hostname
        or url.username is not None
        or url.password is not None
        or url.path not in {"", "/"}
        or url.query
        or url.fragment
        or port == 0
        or (url.scheme != "https" and not (local and url.scheme == "http"))
    ):
        return {"status": "invalid_origin"}

    health_url = url._replace(path="/v1/health/ready").geturl()
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

