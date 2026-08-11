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

# 用户指定须优先直连（在 Proxy 规则之前）：PingMe / 起点 / 120399
EXTRA_SUFFIXES: tuple[str, ...] = (
    "120399.xyz",
    "qidian.com",
    "pingmeapp.net",
)

# 皮皮虾等国内字节 snssdk：须排在 TikTok 之前直连。
# 主配置若不能更新，靠强制更新本 rule_set（已在 Egern 第 1 段引用）即可生效。
EXTRA_DOMAINS: tuple[str, ...] = (
    "effect.snssdk.com",
    "iu-lq.snssdk.com",
    "lf-lq.snssdk.com",
)
EXTRA_KEYWORDS: tuple[str, ...] = (
    "lq.snssdk.com",
    "hl.snssdk.com",
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
    merged.setdefault("domain_set", set()).update(EXTRA_DOMAINS)
    merged.setdefault("domain_keyword_set", set()).update(EXTRA_KEYWORDS)

    header = [
        "# AUTO-PUBLISHED by scripts/publish-direct-priority.py",
        "# 类型: 分流规则 — 国内/系统服务优先直连（须在 Proxy 类规则之前匹配）",
        "# Do not edit manually. Updated by GitHub Actions after upstream sync.",
        f"# Merged: {', '.join(labels)}",
        "# Extra: Pipixia CN snssdk (effect / *-lq|hl) before TikTok",
    ]
    write_egern_sets(DEST, merged, header_lines=header)
    print(f"Direct-Priority total: {count_sets(merged)} entries")


if __name__ == "__main__":
    main()
