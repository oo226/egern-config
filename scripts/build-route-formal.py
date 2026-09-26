#!/usr/bin/env python3
"""Formal Route tree: Route/{lists,modules} — 分流规则自托管合并。

Layout:
  Route/
    lists/                 # 上游规则原样（对标 Adblock/js）
      repcz/
      skk/
      vpsdance/
      rabbit/
      eulac/
      apps/
    modules/               # 预留（分流少用 sgmodule）
    Reject-Merged.yaml
    China-Direct.yaml
    Foreign/*.yaml
    Unbreak.yaml
    Bootstrap-Direct.yaml  # 从本仓 Routing 复制本地件
    ...
    UPSTREAM.md
"""

from __future__ import annotations

import hashlib
import os
import ssl
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from routing_list_utils import (  # noqa: E402
    SET_KEYS,
    count_sets,
    empty_sets,
    merge_set_dicts,
    parse_egern_sets,
    parse_surge_list,
    write_egern_sets,
)

ROOT = Path(__file__).resolve().parent.parent
ROUTE = ROOT / "Route"
LISTS = ROUTE / "lists"
MOD = ROUTE / "modules"
REPORT = ROUTE / "UPSTREAM.md"
SHA_FILE = ROUTE / "SHA256SUMS"

BRANCH = (
    os.environ.get("ADBLOCK_BRANCH")
    or os.environ.get("GITHUB_REF_NAME")
    or "cursor/adblock-formal-f611"
)
GITHUB_RAW = f"https://raw.githubusercontent.com/oo226/egern-config/refs/heads/{BRANCH}"

CTX = ssl.create_default_context()
UA = {"User-Agent": "egern-config-route-formal/1.0"}
MIRROR = "https://ghproxy.net/"

REPCZ_BASE = "https://raw.githubusercontent.com/Repcz/Tool/X/Egern/Rules"
REPCZ_MERGE = (
    "Reject",
    "Direct",
    "WeChat",
    "Bilibili",
    "AppleCN",
    "ChinaDomain",
    "ChinaIP",
    "ChinaASN",
)
REPCZ_FOREIGN = (
    "AI",
    "Telegram",
    "Twitter",
    "TikTok",
    "YouTube",
    "Netflix",
    "Disney",
    "Spotify",
    "Emby",
    "Google",
    "Github",
    "Microsoft",
    "AppleServers",
    "Game",
    "ProxyGFW",
    "Proxy",
)

SKK_REJECT = "https://ruleset.skk.moe/List/domainset/reject.conf"
SKK_AI = "https://ruleset.skk.moe/List/non_ip/ai.conf"
VPS_AI = "https://cdn.jsdelivr.net/gh/VPSDance/ai-proxy-rules@main/rules/egern/all.yaml"
MATRIX_UNBREAK = (
    "https://raw.githubusercontent.com/Centralmatrix3/Matrix-io/master/Egern/Ruleset/Unbreak.yaml"
)
RABBIT_BASE = "https://raw.githubusercontent.com/Rabbit-Spec/Surge/Master/Rules"
EULAC_BASE = "https://raw.githubusercontent.com/eulac-dev/Proxy/refs/heads/main/Loon/Rules"

FALSE_POSITIVE_EXCLUDES = frozenset(
    {
        "audio-ak-spotify-com.akamaized.net",
        "audio-ak.cdn.spotify.com",
        "heads-fa.spotify.com",
        "heads4-ak-spotify-com.akamaized.net",
        "video-ak.cdn.spotify.com",
        "spotify-com.akamaized.net",
    }
)

STATS: dict = {"fetched": [], "failed": [], "outputs": {}}


def fetch(url: str, *, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=timeout) as resp:
            data = resp.read()
    except Exception:
        req = urllib.request.Request(MIRROR + url, headers=UA)
        with urllib.request.urlopen(req, context=CTX, timeout=timeout) as resp:
            data = resp.read()
    if data.lstrip()[:20].lower().startswith((b"<!doctype", b"<html")):
        raise ValueError(f"HTML for {url}")
    return data


def mirror(url: str, dest: Path) -> bool:
    try:
        data = fetch(url)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        STATS["fetched"].append(f"{dest.relative_to(ROUTE)} <- {url}")
        return True
    except Exception as exc:
        STATS["failed"].append(f"{dest.name}: {exc}")
        print(f"  ! {dest}: {exc}")
        return False


def parse_skk(path: Path) -> tuple[set[str], set[str]]:
    domains: set[str] = set()
    suffixes: set[str] = set()
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("."):
            suffixes.add(s[1:])
        else:
            domains.add(s)
    return domains, suffixes


def write_reject(repcz: Path, skk: Path, out: Path) -> int:
    parts = []
    if repcz.is_file():
        parts.append(parse_egern_sets(repcz))
    if skk.is_file():
        dom, suf = parse_skk(skk)
        s = empty_sets()
        s["domain_set"].update(dom)
        s["domain_suffix_set"].update(suf)
        parts.append(s)
    sets = merge_set_dicts(parts) if parts else empty_sets()
    for key in SET_KEYS:
        sets[key] -= FALSE_POSITIVE_EXCLUDES
    write_egern_sets(
        out,
        sets,
        header_lines=[
            "# Route/Reject-Merged — formal tree",
            f"# built_at={datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ')}",
            "# sources: Repcz Reject.yaml + Sukka reject.conf",
        ],
    )
    n = count_sets(sets)
    STATS["outputs"]["Reject-Merged.yaml"] = n
    return n


def write_china(lists_root: Path, out: Path) -> int:
    parts = []
    for name in REPCZ_MERGE:
        if name == "Reject":
            continue
        path = lists_root / "repcz" / f"{name}.yaml"
        if path.is_file():
            parts.append(parse_egern_sets(path))
    rabbit_china = lists_root / "rabbit" / "China.list"
    if rabbit_china.is_file():
        parts.append(parse_surge_list(rabbit_china.read_text(encoding="utf-8", errors="replace")))
    rabbit_cidr = lists_root / "rabbit" / "ChinaCIDR.list"
    if rabbit_cidr.is_file():
        parts.append(parse_surge_list(rabbit_cidr.read_text(encoding="utf-8", errors="replace")))
    for name in ("ResourceSite", "PanVod"):
        path = lists_root / "eulac" / f"{name}.lsr"
        if path.is_file():
            parts.append(parse_surge_list(path.read_text(encoding="utf-8", errors="replace")))
    sets = merge_set_dicts(parts) if parts else empty_sets()
    write_egern_sets(
        out,
        sets,
        header_lines=[
            "# Route/China-Direct — formal tree",
            f"# built_at={datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ')}",
            "# sources: Repcz Direct/WeChat/Bilibili/AppleCN/China* + Rabbit + eulac",
        ],
    )
    n = count_sets(sets)
    STATS["outputs"]["China-Direct.yaml"] = n
    return n


def write_foreign(lists_root: Path, foreign_dir: Path) -> None:
    foreign_dir.mkdir(parents=True, exist_ok=True)
    ai_parts = []
    repcz_ai = lists_root / "repcz" / "AI.yaml"
    if repcz_ai.is_file():
        ai_parts.append(parse_egern_sets(repcz_ai))
    skk_ai = lists_root / "skk" / "ai.conf"
    if skk_ai.is_file():
        dom, suf = parse_skk(skk_ai)
        s = empty_sets()
        s["domain_set"].update(dom)
        s["domain_suffix_set"].update(suf)
        ai_parts.append(s)
    vps = lists_root / "vpsdance" / "all.yaml"
    if vps.is_file():
        ai_parts.append(parse_egern_sets(vps))
    if ai_parts:
        sets = merge_set_dicts(ai_parts)
        write_egern_sets(
            foreign_dir / "AI.yaml",
            sets,
            header_lines=[
                "# Route/Foreign/AI.yaml — Repcz + Sukka AI + VPSDance",
                f"# built_at={datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ')}",
            ],
        )
        STATS["outputs"]["Foreign/AI.yaml"] = count_sets(sets)

    for name in REPCZ_FOREIGN:
        if name == "AI":
            continue
        src = lists_root / "repcz" / f"{name}.yaml"
        if src.is_file():
            header = (
                f"# Route/Foreign/{name}.yaml — from Repcz/Tool\n"
                f"# built_at={datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ')}\n\n"
            )
            (foreign_dir / f"{name}.yaml").write_text(
                header + src.read_text(encoding="utf-8", errors="replace"),
                encoding="utf-8",
            )
            STATS["outputs"][f"Foreign/{name}.yaml"] = "mirrored"


def copy_local_routing() -> None:
    """Copy stable local policy files from Routing/ into Route/."""
    for name in (
        "Bootstrap-Direct.yaml",
        "Lan.yaml",
        "Privacy-Reject.yaml",
        "Tailscale-Direct.yaml",
        "Zhuifeng.yaml",
        "Direct-Priority.yaml",
        "Reject-Hot.yaml",
    ):
        src = ROOT / "Routing" / name
        if src.is_file():
            dest = ROUTE / name
            dest.write_bytes(src.read_bytes())
            STATS["outputs"][name] = "copied-from-Routing"


def write_report(sha_lines: list[str]) -> None:
    lines = [
        "# 分流 — 上游合并说明",
        "",
        f"构建时间（UTC）：{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
        f"分支：`{BRANCH}`",
        "",
        "## 目录",
        "",
        "```",
        "Route/",
        "  lists/          # 上游规则原样（≈ Adblock/js）",
        "    repcz/ skk/ vpsdance/ rabbit/ eulac/ apps/",
        "  modules/        # 预留",
        "  Reject-Merged.yaml / China-Direct.yaml / Foreign/",
        "  UPSTREAM.md",
        "```",
        "",
        "## 上游",
        "",
        "| 源 | 用途 |",
        "|----|------|",
        "| Repcz/Tool Egern Rules | Reject / China* / Foreign* |",
        "| Sukka reject.conf + ai.conf | 去广告域名 + AI |",
        "| VPSDance ai-proxy-rules | AI 补充 |",
        "| Rabbit-Spec China/ChinaCIDR | 国内直连补充 |",
        "| eulac ResourceSite/PanVod | 资源站/网盘 |",
        "| Matrix-io Unbreak | Unbreak.yaml |",
        "| 本仓 Routing 本地件 | Bootstrap/Lan/Privacy/追风等 |",
        "",
        f"拉取成功：{len(STATS['fetched'])}　失败：{len(STATS['failed'])}",
        "",
        "## 产出条目数",
        "",
    ]
    for k, v in STATS["outputs"].items():
        lines.append(f"- `{k}`: {v}")
    lines += [
        "",
        "## 订阅示例",
        "",
        "```",
        f"{GITHUB_RAW}/Route/Reject-Merged.yaml",
        f"{GITHUB_RAW}/Route/China-Direct.yaml",
        f"{GITHUB_RAW}/Route/Foreign/AI.yaml",
        "```",
        "",
        "重建：`python3 scripts/build-route-formal.py`",
        "",
        "说明：本树与 sync 日更的 `Routing/` 并行；Egern 主配置仍默认定 `Routing/`，本分支用 `Route/` 试验。",
        "",
    ]
    if STATS["failed"]:
        lines.append("## 拉取失败")
        lines.append("")
        for x in STATS["failed"]:
            lines.append(f"- {x}")
        lines.append("")
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    SHA_FILE.write_text("\n".join(sha_lines) + "\n", encoding="utf-8")


def main() -> None:
    LISTS.mkdir(parents=True, exist_ok=True)
    MOD.mkdir(parents=True, exist_ok=True)
    sha_lines = [f"# Route checksums @ {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ')}", ""]

    print("fetch Repcz…")
    for name in (*REPCZ_MERGE, *REPCZ_FOREIGN, "Lan"):
        url = f"{REPCZ_BASE}/{name}.yaml"
        dest = LISTS / "repcz" / f"{name}.yaml"
        if mirror(url, dest):
            sha_lines.append(f"{hashlib.sha256(dest.read_bytes()).hexdigest()}  lists/repcz/{name}.yaml")

    print("fetch Sukka / VPSDance / Unbreak…")
    for url, dest in (
        (SKK_REJECT, LISTS / "skk" / "reject.conf"),
        (SKK_AI, LISTS / "skk" / "ai.conf"),
        (VPS_AI, LISTS / "vpsdance" / "all.yaml"),
        (MATRIX_UNBREAK, LISTS / "matrix" / "Unbreak.yaml"),
    ):
        if mirror(url, dest):
            sha_lines.append(f"{hashlib.sha256(dest.read_bytes()).hexdigest()}  {dest.relative_to(ROUTE)}")

    print("fetch Rabbit / eulac…")
    for name, url in (
        ("China.list", f"{RABBIT_BASE}/China.list"),
        ("ChinaCIDR.list", f"{RABBIT_BASE}/ChinaCIDR.list"),
        ("ResourceSite.lsr", f"{EULAC_BASE}/ResourceSite.lsr"),
        ("PanVod.lsr", f"{EULAC_BASE}/PanVod.lsr"),
    ):
        folder = "rabbit" if name.endswith(".list") else "eulac"
        dest = LISTS / folder / name
        if mirror(url, dest):
            sha_lines.append(f"{hashlib.sha256(dest.read_bytes()).hexdigest()}  lists/{folder}/{name}")

    # Reject
    print("merge Reject-Merged…")
    write_reject(LISTS / "repcz" / "Reject.yaml", LISTS / "skk" / "reject.conf", ROUTE / "Reject-Merged.yaml")

    print("merge China-Direct…")
    write_china(LISTS, ROUTE / "China-Direct.yaml")

    print("foreign…")
    write_foreign(LISTS, ROUTE / "Foreign")

    # Unbreak
    unbreak_src = LISTS / "matrix" / "Unbreak.yaml"
    if unbreak_src.is_file():
        (ROUTE / "Unbreak.yaml").write_bytes(unbreak_src.read_bytes())
        STATS["outputs"]["Unbreak.yaml"] = "from Matrix-io"

    # Lan from repcz
    lan = LISTS / "repcz" / "Lan.yaml"
    if lan.is_file():
        (ROUTE / "Lan.yaml").write_bytes(lan.read_bytes())
        STATS["outputs"]["Lan.yaml"] = "from Repcz"

    copy_local_routing()

    (ROUTE / "README.md").write_text(
        "\n".join(
            [
                "# Route — 分流（本分支正式树）",
                "",
                "| 路径 | 内容 |",
                "|------|------|",
                "| `lists/` | 上游规则原样 |",
                "| `modules/` | 预留 |",
                "| `Reject-Merged.yaml` 等 | 合并产出 |",
                "| `UPSTREAM.md` | 合并明细 |",
                "",
                "与仓库根目录 `Routing/`（sync 日更）并行，互不覆盖。",
                "",
                "```",
                f"{GITHUB_RAW}/Route/Reject-Merged.yaml",
                "```",
                "",
                "重建：`python3 scripts/build-route-formal.py`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (LISTS / "README.md").write_text("# lists — 分流上游原样副本\n", encoding="utf-8")
    (MOD / "README.md").write_text("# modules — 分流模块预留\n", encoding="utf-8")

    write_report(sha_lines)
    print(f"done outputs={STATS['outputs']}")
    print(f"fetched={len(STATS['fetched'])} failed={len(STATS['failed'])}")


if __name__ == "__main__":
    main()
