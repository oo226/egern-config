#!/usr/bin/env python3
"""Merge must-direct-before-proxy service rule-sets into Direct-Priority.yaml."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ROUTING, ROUTING_FOREIGN
from routing_list_utils import count_sets, merge_set_dicts, parse_egern_sets, write_egern_sets

DEST = ROUTING / "Direct-Priority.yaml"

# 须在 ProxyGFW/China-Direct 之前直连的服务域（合并为一条规则，替代 Egern 里多行 DIRECT）
SOURCES = [
    ROUTING_FOREIGN / "App" / "WeChat.yaml",
    ROUTING_FOREIGN / "Microsoft.yaml",
    ROUTING_FOREIGN / "AppleServers.yaml",
    ROUTING_FOREIGN / "App" / "TestFlight.yaml",
]

# 用户指定须优先直连（在 Proxy 规则之前）：PingMe / 起点 / 120399 / 特斯拉中国
EXTRA_SUFFIXES: tuple[str, ...] = (
    "120399.xyz",
    "qidian.com",
    "pingmeapp.net",
    # 特斯拉中国 App（误进 Proxy 会「无网络」；须在代理列表前）
    "tesla.cn",
    "tesla.com.cn",
    "teslamotors.cn",
    "teslamotors.com.cn",
    "tesla-cdn.thron.cn",
    "tesla.com",
    "teslamotors.com",
    "tesla.services",
    "teslaenergy.services",
    "tesla-cdn.thron.com",
    "teslazta.net",
    "ts.la",
    "solarcity.com",
)


def main() -> None:
    parts = []
    labels = []
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

    header = [
        "# AUTO-PUBLISHED by scripts/publish-direct-priority.py",
        "# 类型: 分流规则 — 国内/系统服务优先直连（须在 Proxy 类规则之前匹配）",
        "# Do not edit manually. Updated by GitHub Actions after upstream sync.",
        f"# Merged: {', '.join(labels)}",
    ]
    write_egern_sets(DEST, merged, header_lines=header)
    print(f"Direct-Priority total: {count_sets(merged)} entries")


if __name__ == "__main__":
    main()
