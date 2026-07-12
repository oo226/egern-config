#!/usr/bin/env python3
"""Exit non-zero when catalog health checks find broken links."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "site" / "catalog.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="Exit 1 on any failure")
    parser.add_argument("--report", action="store_true", help="Print markdown report")
    args = parser.parse_args()

    if not CATALOG.is_file():
        print("catalog.json missing")
        raise SystemExit(1)

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    local_broken = [i for i in catalog.get("items") or [] if i.get("health") == "fail"]
    upstream = catalog.get("upstream_health") or {}
    upstream_broken = upstream.get("broken") or []

    lines = ["## Catalog health report", ""]
    if local_broken:
        lines.append(f"### Local raw URLs failed ({len(local_broken)})")
        for item in local_broken[:20]:
            lines.append(f"- `{item.get('id')}` — {item.get('url')}")
        lines.append("")
    if upstream_broken:
        lines.append(f"### Upstream script-path failed ({upstream.get('fail', 0)})")
        for row in upstream_broken:
            lines.append(f"- {row.get('url')}")
        lines.append("")
    if not local_broken and not upstream_broken:
        lines.append("All checked links OK.")

    report = "\n".join(lines)
    if args.report:
        print(report)

    failed = bool(local_broken or upstream_broken)
    if failed:
        print(f"health: FAIL local={len(local_broken)} upstream={upstream.get('fail', 0)}")
    else:
        print("health: OK")

    if args.strict and failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
