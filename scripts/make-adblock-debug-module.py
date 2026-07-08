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
    # DEBUG slice: comment out active URL Rewrite rules in [start, start+n)
    debug_id = 6
    start = 100  # skip first 100 active rules (debug-1..5), disable the next 20
    n = 20
    out = ROOT / "Modules" / f"adblock-collection.debug-{debug_id}.module"

    lines = SRC.read_text(encoding="utf-8", errors="replace").splitlines()
    in_url_rewrite = False
    active_seen = 0
    commented = 0
    new_lines: list[str] = []

    for line in lines:
        if line.strip() == "[URL Rewrite]":
            in_url_rewrite = True
            new_lines.append(line)
            continue
        if in_url_rewrite and line.startswith("[") and line.endswith("]"):
            in_url_rewrite = False

        if in_url_rewrite and is_active_rule_line(line):
            if start <= active_seen < start + n:
                new_lines.append(f"# DEBUG{debug_id}-OFF({active_seen+1}): {line}")
                commented += 1
            else:
                new_lines.append(line)
            active_seen += 1
        else:
            new_lines.append(line)

    # tweak metadata for clarity
    for i, line in enumerate(new_lines[:200]):
        if line.startswith("#!name="):
            new_lines[i] = f"#!name=广告拦截&净化合集（DEBUG {debug_id}：URL Rewrite 关闭第{start+1}-{start+n}条）"
        elif line.startswith("#!desc="):
            new_lines[i] = (
                f"#!desc=调试版：自动注释 [URL Rewrite] 中第 {start+1}-{start+n} 条有效规则，用于定位 Gemini 误伤"
            )

    out.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print(f"wrote {out} (commented {commented} url-rewrite rules)")


if __name__ == "__main__":
    main()

