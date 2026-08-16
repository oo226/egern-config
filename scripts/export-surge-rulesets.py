#!/usr/bin/env python3
"""Export Egern Routing/*.yaml → Surge rule files under surge/Rules/.

Formats (per Surge manual + Sukka / blackmatrix7 practice):
  *.list       RULE-SET  — full mix (DOMAIN / IP-CIDR / IP-ASN / …)
  *.domainset  DOMAIN-SET — plain hostnames; leading '.' = suffix
  *.ip.list    RULE-SET  — IP-CIDR / IP-CIDR6 / IP-ASN only (optional)

Egern YAML cannot be loaded by Surge directly.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ROOT, ROUTING
from routing_list_utils import SET_KEYS, count_sets, parse_egern_sets

DEST_ROOT = ROOT / "surge" / "Rules"
STAGING = ROOT / "surge" / ".Rules-export-tmp"

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

# VIF + always-real-ip → socket is IP:port; domain RULE-SET must match TLS SNI.
# Bake into each domain line so users can fix routing by updating external
# resources only (no Surge.conf / subscription re-import).
EXTMATCH_RULES = frozenset(
    {
        "DOMAIN",
        "DOMAIN-SUFFIX",
        "DOMAIN-KEYWORD",
        "DOMAIN-WILDCARD",
        "DOMAIN-REGEX",
    }
)

DOMAIN_KEYS = ("domain_set", "domain_suffix_set")
IP_KEYS = ("ip_cidr_set", "ip_cidr6_set", "asn_set")
NON_IP_EXTRA_KEYS = (
    "domain_keyword_set",
    "domain_wildcard_set",
    "domain_regex_set",
    "url_regex_set",
    "user_agent_set",
)

SKIP_NAMES = {"manifest.yaml", "README.md"}
# External RULE-SET on Surge iOS rejects these (Invalid line); keep them out of .list
UNSUPPORTED_RULESET_KEYS = frozenset({"domain_regex_set", "url_regex_set"})
DOMAIN_HOST_KEYS = frozenset({"domain_set", "domain_suffix_set"})


def to_ascii_host(host: str) -> str | None:
    """Punycode IDN labels so DOMAIN-SET/RULE-SET stay ASCII (e.g. .mi.中国)."""
    prefix = ""
    body = host.strip()
    if body.startswith("."):
        prefix = "."
        body = body[1:]
    if not body:
        return None
    try:
        return prefix + body.encode("idna").decode("ascii")
    except Exception:
        # drop unencodable junk rather than break the whole set
        return None


def clean_value(key: str, value: str) -> str | None:
    clean = value.split(",")[0].strip()
    if not clean:
        return None
    if key == "asn_set":
        return clean.upper().removeprefix("AS")
    if key in ("domain_set", "domain_suffix_set"):
        if any(ord(c) > 127 for c in clean):
            return to_ascii_host(clean)
        return clean
    return clean


def ruleset_lines(sets: dict[str, set[str]], keys: tuple[str, ...] | None = None) -> list[str]:
    keys = keys or tuple(k for k in SET_KEYS if k not in UNSUPPORTED_RULESET_KEYS)
    lines: list[str] = []
    for key in keys:
        if key in UNSUPPORTED_RULESET_KEYS:
            continue
        rule = BUCKET_TO_RULE[key]
        for value in sorted(sets.get(key) or set(), key=str.lower):
            clean = clean_value(key, value)
            if not clean:
                continue
            if rule in EXTMATCH_RULES:
                lines.append(f"{rule},{clean},extended-matching")
            else:
                lines.append(f"{rule},{clean}")
    return lines


def domainset_lines(sets: dict[str, set[str]]) -> list[str]:
    """Surge DOMAIN-SET: exact host, or '.suffix' for suffix match (ASCII/punycode)."""
    lines: list[str] = []
    for value in sorted(sets.get("domain_set") or set(), key=str.lower):
        clean = clean_value("domain_set", value)
        if clean:
            lines.append(clean.lstrip("."))
    for value in sorted(sets.get("domain_suffix_set") or set(), key=str.lower):
        clean = clean_value("domain_suffix_set", value)
        if clean:
            lines.append(f".{clean.lstrip('.')}")
    return lines


def write_text(path: Path, header: list[str], body: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(header + body) + ("\n" if body or header else ""), encoding="utf-8")


def export_one(src: Path, dest_stem: Path) -> dict[str, int]:
    sets = parse_egern_sets(src)
    total = count_sets(sets)
    rel = src.relative_to(ROUTING)
    counts: dict[str, int] = {"total": total}

    full = ruleset_lines(sets)
    write_text(
        dest_stem.with_suffix(".list"),
        [
            f"# AUTO-EXPORTED from Routing/{rel}",
            "# Format: Surge RULE-SET (no policy). scripts/export-surge-rulesets.py",
            "# Domain lines include extended-matching (SNI hit under always-real-ip / VIF).",
            f"# Total entries: {len(full)}",
            "",
        ],
        full,
    )
    counts["list"] = len(full)

    dlines = domainset_lines(sets)
    if dlines:
        write_text(
            dest_stem.with_suffix(".domainset"),
            [
                f"# AUTO-EXPORTED from Routing/{rel}",
                "# Format: Surge DOMAIN-SET (leading '.' = suffix). scripts/export-surge-rulesets.py",
                f"# Total entries: {len(dlines)}",
                "",
            ],
            dlines,
        )
        counts["domainset"] = len(dlines)

    ip_lines = ruleset_lines(sets, IP_KEYS)
    extra_non_ip = ruleset_lines(sets, NON_IP_EXTRA_KEYS)
    # Only emit .ip.list when the full set mixes domains with IPs (China-Direct etc.)
    if ip_lines and (dlines or extra_non_ip):
        write_text(
            Path(str(dest_stem) + ".ip.list"),
            [
                f"# AUTO-EXPORTED from Routing/{rel}",
                "# Format: Surge RULE-SET — IP / ASN only. Place after domain rules.",
                f"# Total entries: {len(ip_lines)}",
                "",
            ],
            ip_lines,
        )
        counts["ip"] = len(ip_lines)

    return counts


def main() -> None:
    if STAGING.exists():
        shutil.rmtree(STAGING)

    written = 0
    for src in sorted(ROUTING.rglob("*.yaml")):
        if "_upstream" in src.parts or "Surge" in src.parts:
            continue
        if src.name in SKIP_NAMES:
            continue
        rel = src.relative_to(ROUTING)
        dest_stem = STAGING / rel.with_suffix("")
        counts = export_one(src, dest_stem)
        written += 1
        bits = ", ".join(f"{k}={v}" for k, v in counts.items() if k != "total")
        print(f"  {rel} -> {bits}")

    (STAGING / "README.md").write_text(
        "\n".join(
            [
                "# Surge Rules（从 Egern Routing YAML 导出）",
                "",
                "| 后缀 | Surge 用法 | 说明 |",
                "| --- | --- | --- |",
                "| `.list` | `RULE-SET,url,策略` | 完整规则（blackmatrix7 同款；不含 DOMAIN/URL-REGEX） |",
                "| `.domainset` | `DOMAIN-SET,url,策略` | 纯域名；`.` 前缀=后缀；中文域名已转 punycode |",
                "| `.ip.list` | `RULE-SET,url,策略,no-resolve` | 仅 IP/ASN；放在域名规则之后 |",
                "",
                "注意：外部 RULE-SET 不含 `DOMAIN-REGEX` / `URL-REGEX`（Surge iOS 会报 Invalid line）。",
                "中文等 IDN 在 domainset/list 中转为 `xn--…` punycode。",
                "域名行自带 `extended-matching`：只更新外部资源即可按 SNI 命中（不必改 Surge.conf）。",
                "",
                "主配置在 `surge` 分支根目录 `Surge.conf`。",
                "Egern 继续用 `main` 的 `Routing/*.yaml`，互不覆盖。",
                "",
            ]
        ),
        encoding="utf-8",
    )

    if DEST_ROOT.exists():
        shutil.rmtree(DEST_ROOT)
    DEST_ROOT.parent.mkdir(parents=True, exist_ok=True)
    STAGING.rename(DEST_ROOT)

    # Remove legacy path under Routing/Surge (Egern tree stays clean)
    legacy = ROUTING / "Surge"
    if legacy.exists():
        shutil.rmtree(legacy)
        print(f"removed legacy {legacy}")

    print(f"exported {written} sources -> {DEST_ROOT}")


if __name__ == "__main__":
    main()
