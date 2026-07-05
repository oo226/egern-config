#!/usr/bin/env python3
"""Deprecated wrapper — use scripts/merge-adblock-modules.py directly."""

from __future__ import annotations

import runpy
from pathlib import Path

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).with_name("merge-adblock-modules.py")), run_name="__main__")
