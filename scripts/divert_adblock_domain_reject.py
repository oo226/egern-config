#!/usr/bin/env python3
"""Divert DOMAIN*/IP-CIDR REJECT from an adblock module [Rule] into Reject-Merged.

Whole-host rejects belong in 分流 Reject-Merged (upstream + 合集补全).
Modules keep MITM + URL Rewrite + Script + AND/URL-REGEX rules.

Lines tagged `# @keep` are still merged into Reject-Merged, but left in the
module text (dual-layer) so updating 合集 alone cannot open a gap when
Reject-Merged is stale.

Usage:
  python3 scripts/divert_adblock_domain_reject.py Modules/adblock-collection.module
  python3 scripts/divert_adblock_domain_reject.py MODULE --strip-only
"""

from __future__ import annotations

import argparse
import ipaddress
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import REJECT_MERGED, ROOT
from routing_list_utils import SET_KEYS, empty_sets, parse_egern_sets

_IP_HOST_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")

# 整域 REJECT 会误杀业务 CDN；微信 wxs 改走 Reject-Hot（Direct-Priority 前，对齐 QingRex）。
# 勿再并入 Reject-Merged（日更 divert 也会跳过；顺序错了拦不住）。
NEVER_REJECT_SUFFIXES = frozenset(
    {
        "wxs.qq.com",  # Reject-Hot 早拦；合集 Map Local + wxgzhad 处理接口
    }
)
NEVER_REJECT_DOMAINS = frozenset(
    {
        "wximg.wxs.qq.com",
        "wxsmw.wxs.qq.com",
        "wxa.wxs.qq.com",
    }
)


def _is_never_reject(kind: str, value: str) -> bool:
    """Hosts that must not land in Reject-Merged (path-level ads instead)."""
    host = value.lower().strip()
    if host in NEVER_REJECT_DOMAINS or host in NEVER_REJECT_SUFFIXES:
        return True
    if kind == "DOMAIN-SUFFIX" and host in NEVER_REJECT_SUFFIXES:
        return True
    return False


def _is_ipv4_host(host: str) -> bool:
    if not _IP_HOST_RE.match(host):
        return False
    try:
        ipaddress.IPv4Address(host)
        return True
    except ValueError:
        return False


def _parse_rule_line(line: str) -> tuple[str, str] | None:
    """Return (kind, value) for divertible REJECT lines; else None."""
    s = line.strip()
    if not s or s.startswith("#"):
        return None
    parts = [p.strip() for p in s.split(",")]
    if len(parts) < 2:
        return None
    kind = parts[0].upper()
    value = parts[1]
    policy = parts[2].upper() if len(parts) >= 3 else ""
    if policy and not policy.startswith("REJECT"):
        return None
    if kind in ("DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"):
        return kind, value
    if kind in ("IP-CIDR", "IP-CIDR6"):
        return kind, value
    return None


def load_existing_reject_sets() -> dict[str, set[str]]:
    if not REJECT_MERGED.is_file():
        return empty_sets()
    return parse_egern_sets(REJECT_MERGED)


def _suffix_covered(suf: str, existing: dict[str, set[str]]) -> bool:
    suf = suf.lower()
    if suf in existing["domain_suffix_set"] or suf in existing["domain_set"]:
        return True
    for ps in existing["domain_suffix_set"]:
        if suf == ps or suf.endswith("." + ps):
            return True
    return False


def _domain_covered(host: str, existing: dict[str, set[str]]) -> bool:
    host = host.lower()
    if host in existing["domain_set"]:
        return True
    for suf in existing["domain_suffix_set"]:
        if host == suf or host.endswith("." + suf):
            return True
    for kw in existing["domain_keyword_set"]:
        if kw and kw in host:
            return True
    return False


def divert_module_text(
    text: str,
    *,
    existing: dict[str, set[str]] | None = None,
) -> tuple[str, dict[str, set[str]], dict[str, int]]:
    """Strip divertible [Rule] lines; return (new_text, new_sets, stats)."""
    existing = existing or load_existing_reject_sets()
    new_sets = empty_sets()
    stats = {
        "diverted": 0,
        "skipped_covered": 0,
        "kept_rule": 0,
        "kept_dual": 0,
    }

    section: str | None = None
    out: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped[1:-1]
            out.append(line)
            continue
        if section != "Rule":
            out.append(line)
            continue

        parsed = _parse_rule_line(stripped)
        if not parsed:
            if stripped and not stripped.startswith("#"):
                stats["kept_rule"] += 1
            out.append(line)
            continue

        kind, value = parsed
        # 误杀业务 CDN：从合集剔除，且不进 Reject-Merged
        if _is_never_reject(kind, value):
            stats["skipped_covered"] += 1
            continue

        # `# @keep` — still merge into Reject-Merged, but leave the line in the
        # module so更新合集 alone cannot open a gap if Reject-Merged is stale.
        keep_dual = "# @keep" in stripped
        stats["diverted"] += 1
        low = value.lower()

        if kind == "DOMAIN":
            if _is_ipv4_host(low):
                cidr = f"{low}/32"
                if cidr.lower() in {x.lower() for x in existing["ip_cidr_set"]} or cidr in new_sets["ip_cidr_set"]:
                    stats["skipped_covered"] += 1
                else:
                    new_sets["ip_cidr_set"].add(cidr)
            elif _domain_covered(low, existing) or low in new_sets["domain_set"]:
                stats["skipped_covered"] += 1
            else:
                new_sets["domain_set"].add(low)
        elif kind == "DOMAIN-SUFFIX":
            if _suffix_covered(low, existing) or low in new_sets["domain_suffix_set"]:
                stats["skipped_covered"] += 1
            else:
                new_sets["domain_suffix_set"].add(low)
        elif kind == "DOMAIN-KEYWORD":
            if low in {x.lower() for x in existing["domain_keyword_set"]} or low in new_sets["domain_keyword_set"]:
                stats["skipped_covered"] += 1
            else:
                new_sets["domain_keyword_set"].add(low)
        elif kind == "IP-CIDR":
            if low in {x.lower() for x in existing["ip_cidr_set"]} or low in new_sets["ip_cidr_set"]:
                stats["skipped_covered"] += 1
            else:
                new_sets["ip_cidr_set"].add(value)
        elif kind == "IP-CIDR6":
            if low in {x.lower() for x in existing["ip_cidr6_set"]} or low in new_sets["ip_cidr6_set"]:
                stats["skipped_covered"] += 1
            else:
                new_sets["ip_cidr6_set"].add(value)

        if keep_dual:
            stats["kept_dual"] += 1
            out.append(line)

    cleaned: list[str] = []
    blank_run = 0
    for line in out:
        if not line.strip():
            blank_run += 1
            if blank_run <= 1:
                cleaned.append(line)
            continue
        blank_run = 0
        cleaned.append(line)

    return "\n".join(cleaned) + ("\n" if cleaned else ""), new_sets, stats


def _format_value(value: str) -> str:
    if any(c in value for c in ':"[]{}#&*!|>\\'):
        return f'  - "{value}"'
    return f"  - {value}"


def merge_into_reject_merged(new_sets: dict[str, set[str]]) -> int:
    """Union diverted hosts into Reject-Merged.yaml; return count of newly added."""
    if not REJECT_MERGED.is_file():
        raise SystemExit(f"missing {REJECT_MERGED}")

    # Preserve header notes up to first set key / no_resolve
    raw = REJECT_MERGED.read_text(encoding="utf-8")
    header_lines: list[str] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped == "no_resolve: true" or stripped.endswith("_set:") or (
            stripped and not stripped.startswith("#") and stripped != "no_resolve: true"
        ):
            break
        header_lines.append(line)

    existing = parse_egern_sets(REJECT_MERGED)
    added = 0
    for key in SET_KEYS:
        before = len(existing[key])
        # case-insensitive dedupe for domains
        if key.startswith("domain") or key.startswith("ip_"):
            lower_map = {x.lower(): x for x in existing[key]}
            for v in new_sets.get(key) or set():
                if v.lower() not in lower_map:
                    lower_map[v.lower()] = v
                    added += 1
            existing[key] = set(lower_map.values())
        else:
            for v in new_sets.get(key) or set():
                if v not in existing[key]:
                    existing[key].add(v)
                    added += 1
        _ = before

    total = sum(len(existing[k]) for k in SET_KEYS)
    module_added = sum(len(new_sets.get(k) or ()) for k in SET_KEYS)

    lines = [
        "# AUTO-GENERATED by scripts/merge-reject-rules.py + divert_adblock_domain_reject.py",
        "# 类型: 分流规则 — 去广告域名 REJECT（上游 + 去广告合集整域补全）",
        "# Do not edit manually. Updated by GitHub Actions after upstream sync / adblock merge.",
        "#",
        f"# Includes ~{module_added} unique hosts diverted from 去广告合集 [Rule] (DOMAIN/IP REJECT).",
        f"# Total unique entries: {total}",
        "",
        "no_resolve: true",
    ]
    for key in SET_KEYS:
        values = sorted(existing[key], key=str.lower)
        if not values:
            continue
        lines.append(f"{key}:")
        for value in values:
            lines.append(_format_value(value))
    lines.append("")

    REJECT_MERGED.write_text("\n".join(lines), encoding="utf-8")
    return added


# Back-compat name used by merge-adblock-modules.py
def write_reject_module_yaml(_path: Path, new_sets: dict[str, set[str]]) -> int:
    return merge_into_reject_merged(new_sets)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("module", type=Path, help="adblock module path")
    ap.add_argument(
        "--write-routing",
        type=Path,
        default=None,
        help="ignored; diverted hosts always merge into Reject-Merged.yaml",
    )
    ap.add_argument(
        "--strip-only",
        action="store_true",
        help="only strip module; do not update Reject-Merged.yaml",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="print stats; do not write files",
    )
    args = ap.parse_args()
    mod = args.module if args.module.is_absolute() else ROOT / args.module
    if not mod.is_file():
        raise SystemExit(f"missing {mod}")

    text = mod.read_text(encoding="utf-8")
    new_text, new_sets, stats = divert_module_text(text)
    total_new = sum(len(v) for v in new_sets.values())
    print(
        f"diverted={stats['diverted']} kept_rule={stats['kept_rule']} "
        f"kept_dual={stats.get('kept_dual', 0)} "
        f"new_routing_entries={total_new} skipped_covered≈{stats['skipped_covered']}"
    )
    for k, v in new_sets.items():
        if v:
            print(f"  {k}: {len(v)}")

    if args.dry_run:
        return

    mod.write_text(new_text, encoding="utf-8")
    print(f"stripped DOMAIN/IP REJECT from {mod.relative_to(ROOT)}")

    if args.strip_only:
        return

    n = merge_into_reject_merged(new_sets)
    print(f"merged into {REJECT_MERGED.relative_to(ROOT)} (+{n} new)")


if __name__ == "__main__":
    main()
