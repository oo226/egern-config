#!/usr/bin/env python3
"""Post-process Egern mega adblock after merge.

- Rewrite Map Local / script asset URLs from GitHub raw refs/heads → jsDelivr
  (avoids intermittent raw CDN 404s on freshly restored Scripts/*).
- Publish stable aliases so existing Egern module URLs keep working.
"""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "Modules" / "adblock-collection.module"

OLD_RAW = "https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Scripts/"
NEW_CDN = "https://cdn.jsdelivr.net/gh/oo226/egern-config@main/Scripts/"

ALIASES = (
    "adblock-egern.module",
    "adblock-egern-v0815b.module",
    "adblock-egern-v0815c.module",
)


def main() -> None:
    if not SRC.is_file():
        raise SystemExit(f"missing {SRC}")

    text = SRC.read_text(encoding="utf-8")
    count = text.count(OLD_RAW)
    if count:
        text = text.replace(OLD_RAW, NEW_CDN)
        print(f"rewrote {count} Map Local/script asset URL(s) → jsDelivr")
    else:
        print("no raw refs/heads Scripts URLs to rewrite")

    # Keep a clear desc for forced module refresh UX
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines[:40]):
        if line.startswith("#!desc="):
            if "皮皮虾" not in line:
                lines[i] = (
                    "#!desc=已合并皮皮虾单独模块（QingRex+福利/我的）·强制更新本模块即可\n"
                )
            break
    text = "".join(lines)
    SRC.write_text(text, encoding="utf-8")

    for name in ALIASES:
        dest = ROOT / "Modules" / name
        shutil.copy2(SRC, dest)
        print(f"alias -> Modules/{name}")


if __name__ == "__main__":
    main()
