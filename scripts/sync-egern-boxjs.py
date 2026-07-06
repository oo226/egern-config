#!/usr/bin/env python3
"""Build unified Modules/egern.boxjs.json for all BoxJS-capable scripts in this repo."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from egern_boxjs import EGERN_BOXJS_SUBSCRIPTION, build_egern_boxjs, sync_egern_boxjs


def main() -> None:
    output, stats = sync_egern_boxjs()
    app_count = len(build_egern_boxjs()["apps"])
    print(f"wrote {output} ({app_count} apps)")
    for line in stats:
        print(f"  {line}")
    print(f"subscribe in BoxJS: {EGERN_BOXJS_SUBSCRIPTION}")


if __name__ == "__main__":
    main()
