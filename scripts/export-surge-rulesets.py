#!/usr/bin/env python3
"""Export Egern Routing/*.yaml rule-sets to Surge RULE-SET .list files.

Surge cannot load Egern YAML (domain_suffix_set / …). This script mirrors the
Routing tree under Routing/Surge/ as plain Surge lists for RULE-SET URLs.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ROUTING
from routing_list_utils import SET_KEYS, count_sets, parse_egern_sets

DEST_ROOT = ROUTING / "Surge"
STAGING = ROUTING / ".Surge-export-tmp"

# Egern bucket → Surge rule type (no policy; RULE-SET supplies it)
BUCKET_TO_RULE = {
    "domain_set": "DOMAIN",
    "domain_suffix_set": "DOMAIN-SUFFIX",
    "domain_keyword_set": "DOMAIN-KEYWORD",
    "domain_wildcard_set": "DOMAIN-WILDCARD",
    "domain_regex_set": "DOMAIN-REGEX",
    "ip_cidr_set": "IP-CIDR",
    "ip_cidr6_set": "IP-CIDR6",
    "asn_set": "IP-ASN",
    "url_regex_set": "URL-REGEX",
    "user_agent_set": "USER-AGENT",
}

SKIP_NAMES = {"manifest.yaml", "README.md"}
REGEX_KEYS = {"domain_regex_set", "url_regex_set"}


def unescape_yaml_backslash(value: str) -> str:
    """Line parser keeps YAML ``\\\\`` as two chars; Surge needs one ``\\``."""
    return value.replace("\\\\", "\\")


def egern_yaml_to_surge_lines(sets: dict[str, set[str]]) -> list[str]:
    lines: list[str] = []
    for key in SET_KEYS:
        rule = BUCKET_TO_RULE[key]
        values = sorted(sets.get(key) or set(), key=str.lower)
        for value in values:
            clean = value.split(",")[0].strip()
            if not clean:
                continue
            if key in REGEX_KEYS:
                clean = unescape_yaml_backslash(clean)
            if key == "asn_set":
                clean = clean.upper().removeprefix("AS")
            lines.append(f"{rule},{clean}")
    return lines


def export_one(src: Path, dest: Path) -> int:
    sets = parse_egern_sets(src)
    total = count_sets(sets)
    body = egern_yaml_to_surge_lines(sets)
    header = [
        f"# AUTO-EXPORTED by scripts/export-surge-rulesets.py from {src.relative_to(ROUTING)}",
        "# Surge RULE-SET format (no policy). Do not edit manually.",
        f"# Total entries: {total}",
        "",
    ]
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(header + body) + "\n", encoding="utf-8")
    return total


def main() -> None:
    if STAGING.exists():
        shutil.rmtree(STAGING)

    written = 0
    entries = 0
    for src in sorted(ROUTING.rglob("*.yaml")):
        if "_upstream" in src.parts or "Surge" in src.parts or ".Surge-export-tmp" in src.parts:
            continue
        if src.name in SKIP_NAMES:
            continue
        rel = src.relative_to(ROUTING)
        dest = STAGING / rel.with_suffix(".list")
        n = export_one(src, dest)
        written += 1
        entries += n
        print(f"  {rel} -> Surge/{rel.with_suffix('.list')} ({n})")

    (STAGING / "README.md").write_text(
        "\n".join(
            [
                "# Surge RULE-SET 镜像",
                "",
                "由 `scripts/export-surge-rulesets.py` 从同目录结构的 Egern `*.yaml` 自动导出。",
                "",
                "Surge **不能**直接引用 `Routing/*.yaml`（Egern 的 `domain_suffix_set` 语法）。",
                "请用本目录下的 `.list`，例如：",
                "",
                "```",
                "RULE-SET,https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Routing/Surge/China-Direct.list,DIRECT,no-resolve",
                "```",
                "",
                "主配置见仓库根目录 `Surge.conf`。",
                "",
            ]
        ),
        encoding="utf-8",
    )

    if DEST_ROOT.exists():
        shutil.rmtree(DEST_ROOT)
    STAGING.rename(DEST_ROOT)
    print(f"exported {written} lists, {entries} total entries -> {DEST_ROOT}")


if __name__ == "__main__":
    main()
