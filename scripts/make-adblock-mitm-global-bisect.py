#!/usr/bin/env python3
"""
Global MITM bisect variants for adblock-collection.module.

The user confirmed: MITM-off makes Gemini work. But Google-ish-only bisect
variants all work, so the culprit may be elsewhere in the MITM hostnames list.

This script generates two variants:
- mitm-h1: keep first half of MITM hostnames (sorted case-insensitive)
- mitm-h2: keep second half

All rules / URL Rewrite / scripts remain unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Modules" / "adblock-collection.module"


@dataclass(frozen=True)
class Variant:
    name: str
    keep: set[str]
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


def build_variant(v: Variant, base_lines: list[str], idx: int, all_hosts: list[str]) -> Path:
    out = ROOT / "Modules" / f"adblock-collection.{v.name}.module"
    lines = list(base_lines)
    kept = [h for h in all_hosts if h in v.keep]
    lines[idx] = "hostname = %APPEND% " + ", ".join(kept)

    for i, line in enumerate(lines[:200]):
        if line.startswith("#!name="):
            lines[i] = f"#!name=广告拦截&净化合集（{v.title}）"
        elif line.startswith("#!desc="):
            lines[i] = f"#!desc={v.desc}"

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def main() -> None:
    base_lines = SRC.read_text(encoding="utf-8", errors="replace").splitlines()
    idx, hosts = parse_hostname_line(base_lines)
    if idx is None:
        raise SystemExit("No [MITM] hostname line found")

    hosts_sorted = sorted(hosts, key=lambda s: s.lower())
    n = len(hosts_sorted)
    half = n // 2
    h1 = hosts_sorted[:half]
    h2 = hosts_sorted[half:]

    v1 = Variant(
        name="mitm-h1",
        keep=set(h1),
        title=f"MITM 二分 H1：保留前半（{len(h1)}/{n}）",
        desc="调试版：仅保留 MITM hostnames 前半（按字母排序），用于全量二分定位 Gemini 误伤",
    )
    v2 = Variant(
        name="mitm-h2",
        keep=set(h2),
        title=f"MITM 二分 H2：保留后半（{len(h2)}/{n}）",
        desc="调试版：仅保留 MITM hostnames 后半（按字母排序），用于全量二分定位 Gemini 误伤",
    )

    for v in (v1, v2):
        p = build_variant(v, base_lines, idx, hosts_sorted)
        print("wrote", p)


if __name__ == "__main__":
    main()

