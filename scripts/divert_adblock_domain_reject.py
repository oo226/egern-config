#!/usr/bin/env python3
"""Divert DOMAIN*/IP-CIDR REJECT from an adblock module [Rule] into Routing YAML.

Whole-host rejects belong in 分流 (Reject-Merged / Reject-Extra / Reject-Module).
Modules keep MITM + URL Rewrite + Script + AND/URL-REGEX rules.

Usage:
  python3 scripts/divert-adblock-domain-reject.py Modules/adblock-collection.module
  python3 scripts/divert-adblock-domain-reject.py MODULE --write-routing Routing/Reject-Module.yaml
  python3 scripts/divert-adblock-domain-reject.py MODULE --strip-only   # no routing write
"""

from __future__ import annotations

import argparse
import ipaddress
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import REJECT_MERGED, ROOT, ROUTING
from routing_list_utils import parse_egern_sets

REJECT_EXTRA = ROUTING / "Reject-Extra.yaml"
DEFAULT_OUT = ROUTING / "Reject-Module.yaml"

_IP_HOST_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")


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
    # policy often REJECT; allow REJECT-DROP etc.
    policy = parts[2].upper() if len(parts) >= 3 else ""
    if policy and not policy.startswith("REJECT"):
        # DOMAIN,foo,DIRECT — do not divert
        return None
    if kind in ("DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"):
        return kind, value
    if kind in ("IP-CIDR", "IP-CIDR6"):
        return kind, value
    return None


def load_existing_reject_sets() -> dict[str, set[str]]:
    sets: dict[str, set[str]] = {
        "domain_set": set(),
        "domain_suffix_set": set(),
        "domain_keyword_set": set(),
        "ip_cidr_set": set(),
        "ip_cidr6_set": set(),
    }
    for path in (REJECT_MERGED, REJECT_EXTRA):
        if not path.is_file():
            continue
        parsed = parse_egern_sets(path)
        for key in sets:
            sets[key] |= {x.lower() for x in (parsed.get(key) or set())}
    return sets


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
    new_sets: dict[str, set[str]] = {
        "domain_set": set(),
        "domain_suffix_set": set(),
        "domain_keyword_set": set(),
        "ip_cidr_set": set(),
        "ip_cidr6_set": set(),
    }
    stats = {
        "diverted": 0,
        "skipped_covered": 0,
        "kept_rule": 0,
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
        stats["diverted"] += 1
        low = value.lower()

        if kind == "DOMAIN":
            if _is_ipv4_host(low):
                cidr = f"{low}/32"
                if cidr.lower() in existing["ip_cidr_set"] or cidr in new_sets["ip_cidr_set"]:
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
            if low in existing["domain_keyword_set"] or low in new_sets["domain_keyword_set"]:
                stats["skipped_covered"] += 1
            else:
                new_sets["domain_keyword_set"].add(low)
        elif kind == "IP-CIDR":
            if low in existing["ip_cidr_set"] or low in new_sets["ip_cidr_set"]:
                stats["skipped_covered"] += 1
            else:
                new_sets["ip_cidr_set"].add(value)  # keep original case/format
        elif kind == "IP-CIDR6":
            if low in existing["ip_cidr6_set"] or low in new_sets["ip_cidr6_set"]:
                stats["skipped_covered"] += 1
            else:
                new_sets["ip_cidr6_set"].add(value)

        # drop line from module (do not append)

    # Drop empty comment-only noise: consecutive blank lines collapse later
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


def write_reject_module_yaml(path: Path, new_sets: dict[str, set[str]]) -> int:
    total = sum(len(v) for v in new_sets.values())
    lines = [
        "# AUTO-GENERATED by scripts/divert-adblock-domain-reject.py",
        "# 类型: 分流规则 — 从去广告合集 [Rule] 抽出的整域/IP REJECT",
        "# 与 Reject-Merged / Reject-Extra 去重；合集只保留 MITM / URL Rewrite / Script / AND",
        "# Do not edit manually. Regenerated when adblock modules are merged.",
        "",
    ]
    key_order = (
        "domain_set",
        "domain_suffix_set",
        "domain_keyword_set",
        "ip_cidr_set",
        "ip_cidr6_set",
    )
    for key in key_order:
        values = sorted(new_sets.get(key) or set(), key=str.lower)
        if not values:
            continue
        lines.append(f"{key}:")
        for v in values:
            lines.append(f'  - "{v}"' if any(c in v for c in ":*") else f"  - {v}")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return total


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("module", type=Path, help="adblock module path")
    ap.add_argument(
        "--write-routing",
        type=Path,
        default=None,
        help=f"write diverted hosts here (default {DEFAULT_OUT} unless --strip-only)",
    )
    ap.add_argument(
        "--strip-only",
        action="store_true",
        help="only strip module; do not write/update Reject-Module.yaml",
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

    out = args.write_routing or DEFAULT_OUT
    if not out.is_absolute():
        out = ROOT / out
    n = write_reject_module_yaml(out, new_sets)
    print(f"wrote {out.relative_to(ROOT)} ({n} entries)")


if __name__ == "__main__":
    main()
