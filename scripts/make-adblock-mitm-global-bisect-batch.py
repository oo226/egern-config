#!/usr/bin/env python3
"""
Batch bisect for the currently identified bad MITM range.

User observations:
- mitm-h1 abnormal; mitm-h2 normal
- mitm-h1a abnormal
- mitm-h1a1 abnormal
- mitm-h1a1a abnormal
- mitm-h1a1a1 abnormal
- both mitm-h1a1a1a and mitm-h1a1a1b abnormal

So the culprit(s) are within the 1/32 segment (h1a1a1), and likely multiple.
Instead of doing one more binary split at a time, generate 8 modules at once:
split h1a1a1a into 4 chunks and h1a1a1b into 4 chunks.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Modules" / "adblock-collection.module"


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


@dataclass(frozen=True)
class Variant:
    name: str
    keep: set[str]
    title: str
    desc: str


def chunk4(xs: list[str]) -> list[list[str]]:
    # split into 4 nearly-equal chunks
    n = len(xs)
    base = n // 4
    rem = n % 4
    out: list[list[str]] = []
    i = 0
    for k in range(4):
        size = base + (1 if k < rem else 0)
        out.append(xs[i : i + size])
        i += size
    return out


def build_variant(v: Variant, base_lines: list[str], idx: int, all_hosts_sorted: list[str]) -> Path:
    out = ROOT / "Modules" / f"adblock-collection.{v.name}.module"
    lines = list(base_lines)
    kept = [h for h in all_hosts_sorted if h in v.keep]
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

    # reproduce the same slicing used by previous H* modules
    half = n // 2
    h1 = hosts_sorted[:half]
    q = half // 2
    h1a = h1[:q]
    e = q // 2
    h1a1 = h1a[:e]
    s = e // 2
    h1a1a = h1a1[:s]
    t = s // 2
    h1a1a1 = h1a1a[:t]  # this is the known-bad 1/32 window
    u = t // 2
    h1a1a1a = h1a1a1[:u]  # bad
    h1a1a1b = h1a1a1[u:]  # bad

    a_chunks = chunk4(h1a1a1a)
    b_chunks = chunk4(h1a1a1b)

    variants: list[Variant] = []
    for i, ch in enumerate(a_chunks, start=1):
        variants.append(
            Variant(
                name=f"mitm-h1a1a1a{i}",
                keep=set(ch),
                title=f"MITM 批量定位 A{i}/4：仅保留第1/64-A{i}",
                desc="调试版：仅保留一小段 MITM hostnames（A 段 1/4），用于快速定位多个 culprit",
            )
        )
    for i, ch in enumerate(b_chunks, start=1):
        variants.append(
            Variant(
                name=f"mitm-h1a1a1b{i}",
                keep=set(ch),
                title=f"MITM 批量定位 B{i}/4：仅保留第2/64-B{i}",
                desc="调试版：仅保留一小段 MITM hostnames（B 段 1/4），用于快速定位多个 culprit",
            )
        )

    for v in variants:
        p = build_variant(v, base_lines, idx, hosts_sorted)
        print("wrote", p)


if __name__ == "__main__":
    main()

