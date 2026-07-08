#!/usr/bin/env python3
"""
Generate a debug copy of adblock-collection.module with MITM hostnames disabled.

This helps distinguish:
- Issue caused by URL Rewrite / Script rules that require MITM, vs
- Issue caused by MITM itself (intercepting sensitive domains).
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Modules" / "adblock-collection.module"
OUT = ROOT / "Modules" / "adblock-collection.mitm-off.module"


def main() -> None:
    lines = SRC.read_text(encoding="utf-8", errors="replace").splitlines()
    new: list[str] = []
    in_mitm = False
    replaced = 0

    for line in lines:
        if line.strip() == "[MITM]":
            in_mitm = True
            new.append(line)
            continue
        if in_mitm and line.startswith("[") and line.endswith("]"):
            in_mitm = False

        if in_mitm and line.strip().lower().startswith("hostname"):
            # Disable all MITM hostnames in this module.
            new.append("# DEBUG-MITM-OFF: " + line)
            new.append("hostname = %APPEND%")
            replaced += 1
            continue

        new.append(line)

    # tweak metadata
    for i, line in enumerate(new[:200]):
        if line.startswith("#!name="):
            new[i] = "#!name=广告拦截&净化合集（DEBUG：MITM 关闭）"
        elif line.startswith("#!desc="):
            new[i] = "#!desc=调试版：禁用本模块 MITM hostnames（用于判断是否 MITM 误伤）"

    OUT.write_text("\n".join(new) + "\n", encoding="utf-8")
    print(f"wrote {OUT} (replaced {replaced} hostname lines)")


if __name__ == "__main__":
    main()

