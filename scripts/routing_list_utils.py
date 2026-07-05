"""Parse Surge/Loon/QuantumultX list files into Egern rule-set buckets."""

from __future__ import annotations

from pathlib import Path

SET_KEYS = (
    "domain_set",
    "domain_suffix_set",
    "domain_keyword_set",
    "domain_wildcard_set",
    "domain_regex_set",
    "ip_cidr_set",
    "ip_cidr6_set",
    "asn_set",
    "url_regex_set",
    "user_agent_set",
)


def empty_sets() -> dict[str, set[str]]:
    return {k: set() for k in SET_KEYS}


def parse_surge_list(text: str) -> dict[str, set[str]]:
    sets = empty_sets()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("#!"):
            continue
        upper = line.upper()
        if upper.startswith("DOMAIN-SUFFIX,"):
            sets["domain_suffix_set"].add(line.split(",", 1)[1].strip())
        elif upper.startswith("HOST-SUFFIX,"):
            sets["domain_suffix_set"].add(line.split(",", 1)[1].strip())
        elif upper.startswith("DOMAIN-KEYWORD,"):
            sets["domain_keyword_set"].add(line.split(",", 1)[1].strip())
        elif upper.startswith("HOST-KEYWORD,"):
            sets["domain_keyword_set"].add(line.split(",", 1)[1].strip())
        elif upper.startswith("DOMAIN,"):
            value = line.split(",", 1)[1].strip()
            if value:
                sets["domain_set"].add(value)
        elif upper.startswith("HOST,"):
            value = line.split(",", 1)[1].strip()
            if value:
                sets["domain_set"].add(value)
        elif upper.startswith("IP-CIDR6,"):
            value = line.split(",", 1)[1].strip().split(",")[0].strip()
            sets["ip_cidr6_set"].add(value)
        elif upper.startswith("IP-CIDR,"):
            value = line.split(",", 1)[1].strip().split(",")[0].strip()
            sets["ip_cidr_set"].add(value)
        elif upper.startswith("IP-ASN,"):
            sets["asn_set"].add(line.split(",", 1)[1].strip())
        elif upper.startswith("USER-AGENT,"):
            sets["user_agent_set"].add(line.split(",", 1)[1].strip())
        elif upper.startswith("URL-REGEX,"):
            sets["url_regex_set"].add(line.split(",", 1)[1].strip())
    return sets


def parse_egern_sets(path: Path) -> dict[str, set[str]]:
    sets = empty_sets()
    current: str | None = None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        for key in SET_KEYS:
            if stripped == f"{key}:":
                current = key
                break
        else:
            if current and stripped.startswith("- "):
                value = stripped[2:].strip().strip('"').strip("'")
                if value:
                    sets[current].add(value)
            elif stripped.endswith(":") and not stripped.startswith("-"):
                current = None
    return sets


def merge_set_dicts(parts: list[dict[str, set[str]]]) -> dict[str, set[str]]:
    merged = empty_sets()
    for part in parts:
        for key in SET_KEYS:
            merged[key].update(part.get(key, set()))
    return merged


def count_sets(sets: dict[str, set[str]]) -> int:
    return sum(len(sets[k]) for k in SET_KEYS)


def write_egern_sets(
    path: Path,
    sets: dict[str, set[str]],
    *,
    header_lines: list[str],
    no_resolve: bool = True,
) -> None:
    total = count_sets(sets)
    lines = header_lines + [f"# Total unique entries: {total}", ""]
    if no_resolve:
        lines.append("no_resolve: true")
    for key in SET_KEYS:
        values = sorted(sets[key], key=str.lower)
        if not values:
            continue
        lines.append(f"{key}:")
        for value in values:
            if any(c in value for c in ':"[]{}#&*!|>\\'):
                lines.append(f'  - "{value}"')
            else:
                lines.append(f"  - {value}")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {path.name}: {total} entries")
