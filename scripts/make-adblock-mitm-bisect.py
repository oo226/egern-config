#!/usr/bin/env python3
"""
Generate MITM-bisect variants of adblock-collection.module.

Goal: keep all rules/rewrite/scripts intact, only modify [MITM] hostname list to
exclude/restore a small suspicious subset (Google-ish MITM hostnames) to find
the minimal culprit breaking Gemini.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Modules" / "adblock-collection.module"


GOOGLEISH_HOSTS = [
    "*.google.cn",
    "*.googleapis.com",
    "*.googlevideo.com",
    "-redirector*.googlevideo.com",
    "adservice.google.com",
    "blog.google",
    "dplus-ph-google-v2.prod-vod.h264.io",
    "manifest.googlevideo.com",
    "pagead2.googleadservices.com",
    "pagead2.googlesyndication.com",
    "redirector.googlevideo.com",
    "rr*.googlevideo.com",
    "ssl.googlesyndication.com",
    "www.google.com",
    "www.google.com.hk",
    "youtubei.googleapis.com",
]


@dataclass(frozen=True)
class Variant:
    name: str
    keep_googleish: set[str]
    title: str
    desc: str


def parse_mitm_hosts(lines: list[str]) -> tuple[int | None, list[str]]:
    """Return (line_index_of_hostname, hosts_list)."""
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


def build_variant(v: Variant) -> Path:
    out = ROOT / "Modules" / f"adblock-collection.{v.name}.module"
    lines = SRC.read_text(encoding="utf-8", errors="replace").splitlines()
    idx, hosts = parse_mitm_hosts(lines)
    if idx is None:
        raise SystemExit("No [MITM] hostname line found in source module")

    base_set = hosts
    googleish_set = set(GOOGLEISH_HOSTS)

    # Remove all googleish not explicitly kept.
    filtered = [h for h in base_set if h not in googleish_set or h in v.keep_googleish]

    # Replace hostname line.
    lines[idx] = "hostname = %APPEND% " + ", ".join(filtered)

    # tweak metadata (first 200 lines)
    for i, line in enumerate(lines[:200]):
        if line.startswith("#!name="):
            lines[i] = f"#!name=广告拦截&净化合集（{v.title}）"
        elif line.startswith("#!desc="):
            lines[i] = f"#!desc={v.desc}"

    out.write_text("\\n".join(lines) + "\\n", encoding="utf-8")
    return out


def main() -> None:
    # Variant 0: exclude all googleish MITM hostnames (keep none)
    v0 = Variant(
        name="mitm-g00",
        keep_googleish=set(),
        title="MITM 调试 G00：禁用全部 Google 相关 MITM",
        desc="调试版：仅从 [MITM] hostnames 移除 16 条 Google 相关域名，其它规则不变",
    )
    # Variant 1/2: add back half to bisect quickly
    half = len(GOOGLEISH_HOSTS) // 2
    q = len(GOOGLEISH_HOSTS) // 4
    v1 = Variant(
        name="mitm-g01",
        keep_googleish=set(GOOGLEISH_HOSTS[:half]),
        title="MITM 调试 G01：仅启用前半 Google 相关 MITM",
        desc="调试版：在 G00 基础上，仅加回前半（8条）Google 相关 MITM，用于二分定位",
    )
    v2 = Variant(
        name="mitm-g02",
        keep_googleish=set(GOOGLEISH_HOSTS[half:]),
        title="MITM 调试 G02：仅启用后半 Google 相关 MITM",
        desc="调试版：在 G00 基础上，仅加回后半（8条）Google 相关 MITM，用于二分定位",
    )

    # Round 2: since G01/G02 both work but full set fails, test cross-half combinations.
    # Base on G01 (first 8), add 4 from second half (bisect).
    second = GOOGLEISH_HOSTS[half:]
    v3 = Variant(
        name="mitm-g03",
        keep_googleish=set(GOOGLEISH_HOSTS[:half] + second[:q]),
        title="MITM 调试 G03：前半 + 后半前4条",
        desc="调试版：在 G01 基础上，加回后半前 4 条（跨半区二分定位）",
    )
    v4 = Variant(
        name="mitm-g04",
        keep_googleish=set(GOOGLEISH_HOSTS[:half] + second[q:]),
        title="MITM 调试 G04：前半 + 后半后4条",
        desc="调试版：在 G01 基础上，加回后半后 4 条（跨半区二分定位）",
    )

    # Symmetric: base on G02 (last 8), add 4 from first half.
    first = GOOGLEISH_HOSTS[:half]
    v5 = Variant(
        name="mitm-g05",
        keep_googleish=set(GOOGLEISH_HOSTS[half:] + first[:q]),
        title="MITM 调试 G05：后半 + 前半前4条",
        desc="调试版：在 G02 基础上，加回前半前 4 条（跨半区二分定位）",
    )
    v6 = Variant(
        name="mitm-g06",
        keep_googleish=set(GOOGLEISH_HOSTS[half:] + first[q:]),
        title="MITM 调试 G06：后半 + 前半后4条",
        desc="调试版：在 G02 基础上，加回前半后 4 条（跨半区二分定位）",
    )

    outs = [build_variant(v) for v in (v0, v1, v2, v3, v4, v5, v6)]
    for p in outs:
        print("wrote", p)


if __name__ == "__main__":
    main()

