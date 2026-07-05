#!/usr/bin/env python3
"""Publish Matrix Unbreak rules into Routing/Unbreak.yaml."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ROUTING, ROUTING_UPSTREAM

SRC = ROUTING_UPSTREAM / "matrix" / "Unbreak.yaml"
DEST = ROUTING / "Unbreak.yaml"


def main() -> None:
    if not SRC.is_file():
        print(f"skip: missing {SRC}")
        return
    DEST.parent.mkdir(parents=True, exist_ok=True)
    text = SRC.read_text(encoding="utf-8")
    header = (
        "# AUTO-PUBLISHED by scripts/publish-unbreak-rules.py\n"
        "# 类型: 分流规则 — 规则修正（避免误杀，强制 DIRECT）\n"
        "# Source: Centralmatrix3/Matrix-io Egern/Ruleset/Unbreak.yaml\n"
        "# Do not edit manually. Updated by GitHub Actions after upstream sync.\n\n"
    )
    if text.startswith("# 规则名称:"):
        body = text
    else:
        body = text
    DEST.write_text(header + body, encoding="utf-8")
    print(f"wrote {DEST.name} ({len(DEST.read_text().splitlines())} lines)")


if __name__ == "__main__":
    main()
