#!/usr/bin/env python3
"""
Generate 8 isolate variants:
- Start from full adblock module
- Remove the 8 suspected MITM hostnames
- Then add back exactly ONE of the 8 (to test which single hostname triggers)

All rules / URL Rewrite / scripts remain unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Modules" / "adblock-collection.module"

SUSPECTS = [
    "*.g.doubleclick-cn.net",
    "*.g.doubleclick.net",
    "*.gamersky.com",
    "*.gdt.qq.com",
    "*.gliacloud.com",
    "*.google.cn",
    "*.googleapis.com",
    "*.googlevideo.com",
]


@dataclass(frozen=True)
class Variant:
    name: str
    keep_one: str
    title: str
    desc: str


def parse_hostname_line(lines: list[str]) -> tuple[int | None, list[str]]:
    in_mitm = False
    for i, line in enumerate(lines):
        if line.strip() == "[MITM]":
            in_mitm = True
            continue
        if in_mitm and line.startswith("[") and line.endswith("]"):
            break
        if in_mitm and line.strip().lower().startswith("hostname"):
            rhs = line.split("=", 1)[1]
            rhs = rhs.replace("%APPEND%", "").strip()
            hosts = [h.strip() for h in rhs.split(",") if h.strip()]
            return i, hosts
    return None, []


def build(v: Variant) -> Path:
    out = ROOT / "Modules" / f"adblock-collection.mitm-exclude-gemini-{v.name}.module"
    lines = SRC.read_text(encoding="utf-8", errors="replace").splitlines()
    idx, hosts = parse_hostname_line(lines)
    if idx is None:
        raise SystemExit("No [MITM] hostname line found")

    suspects = set(SUSPECTS)
    new_hosts = []
    for h in hosts:
        if h in suspects and h != v.keep_one:
            continue
        new_hosts.append(h)

    lines[idx] = "hostname = %APPEND% " + ", ".join(new_hosts)

    for i, line in enumerate(lines[:200]):
        if line.startswith("#!name="):
            lines[i] = f"#!name=广告拦截&净化合集（测试：仅加回 {v.keep_one}）"
        elif line.startswith("#!desc="):
            lines[i] = f"#!desc={v.desc}"

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def main() -> None:
    variants: list[Variant] = []
    for i, h in enumerate(SUSPECTS, start=1):
        variants.append(
            Variant(
                name=f"one{i}",
                keep_one=h,
                title=h,
                desc=f"调试版：在“剔除 8 条嫌疑 MITM”基础上，仅加回 {h}（其余 7 条仍剔除）",
            )
        )

    for v in variants:
        p = build(v)
        print("wrote", p)


if __name__ == "__main__":
    main()

