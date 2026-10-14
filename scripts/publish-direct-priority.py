#!/usr/bin/env python3
"""Merge must-direct-before-proxy service rule-sets into Direct-Priority.yaml.

整表合并：基表（WeChat/Microsoft/Apple…）+ eulac 网盘点播/视频资源站
+ PingMe + 散落后缀（120399/起点）+ DoH 钉死 IP。
Profile 只挂这一张「优先直连」，勿再散落单行。

WeChat/TestFlight 源表若缺失，保留现有 Direct-Priority 已烘焙条目（set 并集，幂等）。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import EGERN_ROUTING, ROUTING, ROUTING_FOREIGN, YUANBAN_FENLIU
from routing_list_utils import count_sets, merge_set_dicts, parse_egern_sets, write_egern_sets

# guize 分流在 Egern/Routing；sync 日更可能在 Routing/
_ROUTING = EGERN_ROUTING if (EGERN_ROUTING / "Direct-Priority.yaml").is_file() else ROUTING
_FOREIGN = (
    EGERN_ROUTING / "Foreign"
    if (EGERN_ROUTING / "Foreign").is_dir()
    else ROUTING_FOREIGN
)
DEST = _ROUTING / "Direct-Priority.yaml"

# 须在 ProxyGFW/China-Direct 之前直连的服务域
SOURCES = [
    _FOREIGN / "App" / "WeChat.yaml",
    _FOREIGN / "Microsoft.yaml",
    _FOREIGN / "AppleServers.yaml",
    _FOREIGN / "App" / "TestFlight.yaml",
    _ROUTING / "PanVod-Direct.yaml",
    _ROUTING / "ResourceSite-Direct.yaml",
    _ROUTING / "PingMe-Direct.yaml",
    YUANBAN_FENLIU / "eulac-网盘点播.yaml",
    YUANBAN_FENLIU / "eulac-视频资源站.yaml",
]

EXTRA_SUFFIXES: tuple[str, ...] = (
    "120399.xyz",
    "qidian.com",
    "pingmeapp.net",
)
EXTRA_DOMAINS: tuple[str, ...] = ("api.pingmeapp.net",)
EXTRA_IP_CIDR: tuple[str, ...] = ("120.53.245.215/32",)


def main() -> None:
    parts = []
    labels = []

    # 源表缺失时保留已烘焙条目（如 WeChat）
    if DEST.is_file():
        parts.append(parse_egern_sets(DEST))
        labels.append("Direct-Priority(base)")

    for path in SOURCES:
        if not path.is_file():
            print(f"skip missing {path.name}")
            continue
        parts.append(parse_egern_sets(path))
        labels.append(path.name)

    if not parts:
        print("skip: no direct-priority sources")
        return

    merged = merge_set_dicts(parts)
    merged["domain_suffix_set"].update(EXTRA_SUFFIXES)
    merged["domain_set"].update(EXTRA_DOMAINS)
    merged["ip_cidr_set"].update(EXTRA_IP_CIDR)

    header = [
        "# AUTO-PUBLISHED by scripts/publish-direct-priority.py",
        "# 类型: 分流规则 — 优先直连整表（须在 Proxy 类规则之前匹配）",
        "# 含: 基表 + eulac 网盘点播/视频资源站 + PingMe + 120399/起点 + DoH IP",
        "# Do not edit manually. Updated by GitHub Actions after upstream sync.",
        f"# Merged: {', '.join(labels)}, extras(pingme/qidian/120399/doh-ip)",
    ]
    write_egern_sets(DEST, merged, header_lines=header)
    print(f"Direct-Priority total: {count_sets(merged)} entries")


if __name__ == "__main__":
    main()
