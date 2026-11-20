#!/bin/sh
# Local preview of the existing FastAPI sandbox. Install requirements in .venv first.
set -eu
CFP_SANDBOX_PYTHON=${CFP_SANDBOX_PYTHON:-.venv/bin/python}
if [ ! -x "$CFP_SANDBOX_PYTHON" ]; then CFP_SANDBOX_PYTHON=python3; fi
export CFP_SANDBOX_EPHEMERAL=1
export CFP_EPHEMERAL_DIR=${CFP_EPHEMERAL_DIR:-$(mktemp -d -t cfp-preview-XXXXXX)}
CFP_SANDBOX_HOST=0.0.0.0
CFP_SANDBOX_PORT=${PORT:-3000}
while [ "$#" -gt 0 ]; do
    case "$1" in
        --host) CFP_SANDBOX_HOST=$2; shift 2 ;;
        --port) CFP_SANDBOX_PORT=$2; shift 2 ;;
        --strictPort) shift ;; # uvicorn fails if the requested port is occupied.
        *) echo "Unknown preview argument: $1" >&2; exit 2 ;;
    esac
done
exec "$CFP_SANDBOX_PYTHON" -m uvicorn services.forum.asgi:app --host "$CFP_SANDBOX_HOST" --port "$CFP_SANDBOX_PORT" --workers 1
