#!/usr/bin/env python3
"""
Generate a debug copy of adblock-collection.module with the first N active
URL Rewrite rules commented out. This helps bisect which rewrite breaks Gemini
when no explicit failure entry is shown in the connection log.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Modules" / "adblock-collection.module"


def is_active_rule_line(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if s.startswith("#"):
        return False
    # Surge/Egern rewrite syntax often starts with ^https?:// or https?://
    if s.startswith("^https?://") or s.startswith("https?://") or s.startswith("^http"):
        return True
    # Also allow " - reject" style without regex anchor
    if " - reject" in s:
        return True
    return False


def main() -> None:
    out = ROOT / "Modules" / "adblock-collection.debug-1.module"
    n = 20

    lines = SRC.read_text(encoding="utf-8", errors="replace").splitlines()
    in_url_rewrite = False
    commented = 0
    new_lines: list[str] = []

    for line in lines:
        if line.strip() == "[URL Rewrite]":
            in_url_rewrite = True
            new_lines.append(line)
            continue
        if in_url_rewrite and line.startswith("[") and line.endswith("]"):
            in_url_rewrite = False

        if in_url_rewrite and commented < n and is_active_rule_line(line):
            new_lines.append(f"# DEBUG-OFF({commented+1}): {line}")
            commented += 1
        else:
            new_lines.append(line)

    # tweak metadata for clarity
    for i, line in enumerate(new_lines[:200]):
        if line.startswith("#!name="):
            new_lines[i] = "#!name=广告拦截&净化合集（DEBUG 1：URL Rewrite 前20条关闭）"
        elif line.startswith("#!desc="):
            new_lines[i] = (
                "#!desc=调试版：自动注释 [URL Rewrite] 中前 20 条有效规则，用于定位 Gemini 误伤"
            )

    out.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print(f"wrote {out} (commented {commented} url-rewrite rules)")


if __name__ == "__main__":
    main()

