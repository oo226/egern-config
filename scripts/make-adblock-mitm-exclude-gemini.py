#!/usr/bin/env python3
"""
Build a test adblock module that keeps everything the same except removes a
small set of MITM hostnames that were identified to break Gemini.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Modules" / "adblock-collection.module"
OUT = ROOT / "Modules" / "adblock-collection.mitm-exclude-gemini.module"

EXCLUDES = {
    "*.g.doubleclick-cn.net",
    "*.g.doubleclick.net",
    "*.gamersky.com",
    "*.gdt.qq.com",
    "*.gliacloud.com",
    "*.google.cn",
    "*.googleapis.com",
    "*.googlevideo.com",
}


def main() -> None:
    lines = SRC.read_text(encoding="utf-8", errors="replace").splitlines()
    in_mitm = False
    replaced = False
    removed = 0

    for i, line in enumerate(lines):
        if line.strip() == "[MITM]":
            in_mitm = True
            continue
        if in_mitm and line.startswith("[") and line.endswith("]"):
            in_mitm = False
        if in_mitm and line.strip().lower().startswith("hostname"):
            rhs = line.split("=", 1)[1]
            rhs = rhs.replace("%APPEND%", "").strip()
            hosts = [h.strip() for h in rhs.split(",") if h.strip()]
            new_hosts = []
            for h in hosts:
                if h in EXCLUDES:
                    removed += 1
                    continue
                new_hosts.append(h)
            lines[i] = "hostname = %APPEND% " + ", ".join(new_hosts)
            replaced = True
            break

    if not replaced:
        raise SystemExit("No [MITM] hostname line found")

    for j, l in enumerate(lines[:200]):
        if l.startswith("#!name="):
            lines[j] = "#!name=广告拦截&净化合集（测试：MITM 排除 Gemini 误伤项）"
        elif l.startswith("#!desc="):
            lines[j] = (
                "#!desc=测试版：仅从 [MITM] hostnames 移除 8 条（doubleclick/gdt/google*)，其余规则不变"
            )

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT} (removed {removed} hostnames)")


if __name__ == "__main__":
    main()

