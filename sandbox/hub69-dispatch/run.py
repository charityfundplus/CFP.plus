#!/usr/bin/env python3
"""Entry point: python3 sandbox/hub69-dispatch/run.py plan --source ... --out ..."""
import sys
from pathlib import Path

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hub69_dispatch.cli import main  # noqa: E402

sys.exit(main())
