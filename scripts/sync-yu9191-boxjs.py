#!/usr/bin/env python3
"""Download Yu9191 pear.boxjs.json and publish a local BoxJS subscription."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from boxjs_player import YU9191_BOXJS_SUBSCRIPTION, sync_yu9191_boxjs_subscription


def main() -> None:
    output = sync_yu9191_boxjs_subscription()
    print(f"wrote {output}")
    print(f"subscribe in BoxJS: {YU9191_BOXJS_SUBSCRIPTION}")


if __name__ == "__main__":
    main()
