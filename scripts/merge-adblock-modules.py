#!/usr/bin/env python3
"""Download and merge ad-block modules into 模块/去广告净化合集.module."""

from __future__ import annotations

import re
import ssl
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import MANIFEST, MIRRORED_SCRIPT_REWRITES, MODULES, UPSTREAM_CACHE

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

CTX = ssl.create_default_context()
MIRROR = "https://ghproxy.net/"

MERGE_SECTIONS = (
    "General",
    "Rule",
    "URL Rewrite",
    "Script",
    "MITM",
)

HEADER_KEYS = ("#!name=", "#!desc=", "#!author=", "#!category=", "#!system=")

# Fallback fixes when upstream modules reference deleted scripts
DEFAULT_SCRIPT_URL_FIXES = {
    "https://raw.githubusercontent.com/limbopro/Adblock4limbo/main/Adguard/cnys.js": (
        "https://raw.githubusercontent.com/limbopro/Adblock4limbo/main/Adguard/Adblock4limbo.js"
    ),
}


def apply_script_url_fixes(text: str, fixes: dict[str, str]) -> str:
    if not fixes:
        return text
    for old, new in fixes.items():
        if old in text:
            text = text.replace(old, new)
    return text


def mirror_script_paths(text: str) -> str:
    for old, new in MIRRORED_SCRIPT_REWRITES:
        if old in text:
            text = text.replace(old, new)
    return text


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "egern-config-sync/1.0"})
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=120) as resp:
            data = resp.read()
    except Exception:
        mirror_url = MIRROR + url if not url.startswith(MIRROR) else url
        req = urllib.request.Request(mirror_url, headers={"User-Agent": "egern-config-sync/1.0"})
        with urllib.request.urlopen(req, context=CTX, timeout=120) as resp:
            data = resp.read()
    text = data.decode("utf-8", errors="replace")
    if text.lstrip().startswith("<!DOCTYPE") or text.lstrip().startswith("<html"):
        raise ValueError("upstream returned HTML instead of module content")
    return text


def load_manifest(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if yaml:
        return yaml.safe_load(text) or {}
    raise SystemExit("PyYAML required: pip install pyyaml")


def parse_module(text: str) -> tuple[list[str], dict[str, list[str]]]:
    header: list[str] = []
    sections: dict[str, list[str]] = {}
    current: str | None = None
    in_header = True

    for line in text.splitlines():
        if in_header:
            if line.startswith("[") and line.endswith("]"):
                in_header = False
                current = line[1:-1]
                sections.setdefault(current, [])
                continue
            if line.startswith("#!") or not line.strip():
                header.append(line)
            continue

        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1]
            sections.setdefault(current, [])
            continue
        if current is not None:
            sections[current].append(line)

    return header, sections


def rule_key(line: str) -> str | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if " - " in stripped:
        return stripped.rsplit(" - ", 1)[0].strip().strip('"').strip("'")
    return stripped


def script_key(line: str) -> str | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    match = re.search(r"pattern=(\"[^\"]+\"|'[^']+'|[^,]+)", stripped)
    if match:
        return match.group(1).strip("\"'")
    return stripped


def parse_hostnames(line: str) -> list[str]:
    if "=" not in line:
        return []
    rhs = line.split("=", 1)[1].strip()
    rhs = rhs.replace("%APPEND%", "").strip()
    return [h.strip() for h in rhs.split(",") if h.strip()]


def format_hostnames(hosts: set[str]) -> str:
    ordered = sorted(hosts, key=str.lower)
    return "hostname = %APPEND% " + ", ".join(ordered)


def merge_general_lines(primary: list[str], supplements: list[list[str]]) -> list[str]:
    force_hosts: set[str] = set()
    skip_proxy: list[str] = []
    other: list[str] = []

    for lines in [primary, *supplements]:
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            lower = stripped.lower()
            if lower.startswith("force-http-engine-hosts"):
                force_hosts.update(parse_hostnames(stripped))
            elif lower.startswith("skip-proxy"):
                skip_proxy.append(stripped)
            else:
                other.append(stripped)

    merged: list[str] = []
    if force_hosts:
        merged.append(
            "force-http-engine-hosts = %APPEND% " + ", ".join(sorted(force_hosts, key=str.lower))
        )
    merged.extend(skip_proxy)
    merged.extend(other)
    return merged


def merge_section(
    section: str,
    primary_lines: list[str],
    supplement_blocks: list[tuple[str, list[str]]],
) -> list[str]:
    if section == "General":
        supp_lines = [lines for _, lines in supplement_blocks]
        return merge_general_lines(primary_lines, supp_lines)

    if section == "MITM":
        hosts: set[str] = set()
        comments: list[str] = []
        for line in primary_lines:
            if line.strip().startswith("#") or not line.strip():
                comments.append(line)
            else:
                hosts.update(parse_hostnames(line))
        for _, lines in supplement_blocks:
            for line in lines:
                if line.strip().startswith("#") or not line.strip():
                    continue
                hosts.update(parse_hostnames(line))
        if not hosts:
            return primary_lines
        return comments + [format_hostnames(hosts)]

    seen: set[str] = set()
    output: list[str] = []

    for line in primary_lines:
        key = rule_key(line) if section != "Script" else script_key(line)
        if key:
            seen.add(key)
        output.append(line)

    for source_name, lines in supplement_blocks:
        unique: list[str] = []
        for line in lines:
            key = rule_key(line) if section != "Script" else script_key(line)
            if not key:
                unique.append(line)
                continue
            if key in seen:
                continue
            seen.add(key)
            unique.append(line)
        if unique:
            output.append("")
            output.append(f"# >>> merged from {source_name} (unique only)")
            output.extend(unique)

    return output


def build_merged_module(
    primary_text: str,
    supplements: list[tuple[str, str]],
    *,
    header_lines: list[str] | None = None,
    primary_desc: str | None = None,
) -> str:
    primary_header, primary_sections = parse_module(primary_text)

    supp_parsed: list[tuple[str, dict[str, list[str]]]] = []
    for name, text in supplements:
        _, sections = parse_module(text)
        supp_parsed.append((name, sections))

    # Preserve primary-only sections verbatim (Body Rewrite, Map Local, etc.)
    all_section_names: list[str] = []
    for name in primary_sections:
        if name not in all_section_names:
            all_section_names.append(name)
    for _, sections in supp_parsed:
        for name in sections:
            if name not in all_section_names:
                all_section_names.append(name)

    merge_header = header_lines or [
        "# AUTO-MERGED by scripts/merge-adblock-modules.py",
        "# 类型: 模块 — 去广告/去开屏/净化（URL Rewrite + MITM + Script）",
        "# Primary: fmz200 blockAds | Supplements: blackmatrix7 + 本仓库 NB/银行补全",
        "# Do not edit manually. Updated by GitHub Actions after upstream sync.",
        "",
    ]

    # Refresh primary metadata (optional override via manifest merge.primary_desc)
    refreshed_header: list[str] = []
    for line in primary_header:
        if line.startswith("#!desc=") and primary_desc:
            refreshed_header.append(f"#!desc={primary_desc}")
        elif line.startswith("#!desc=") and primary_desc is None and header_lines:
            refreshed_header.append(line)
        elif line.startswith("#!desc="):
            refreshed_header.append(
                "#!desc=多源合并去重：奶思 + blackmatrix7 + 银行税务NB（Actions 每日同步）"
            )
        else:
            refreshed_header.append(line)

    out_lines = merge_header + refreshed_header + [""]

    for section in all_section_names:
        primary_lines = primary_sections.get(section, [])
        if section not in MERGE_SECTIONS:
            if not primary_lines:
                continue
            out_lines.append(f"[{section}]")
            out_lines.extend(primary_lines)
            out_lines.append("")
            continue

        supplement_blocks = [
            (name, sections.get(section, []))
            for name, sections in supp_parsed
            if sections.get(section)
        ]
        merged_lines = merge_section(section, primary_lines, supplement_blocks)
        if not merged_lines:
            continue
        out_lines.append(f"[{section}]")
        out_lines.extend(merged_lines)
        out_lines.append("")

    while out_lines and not out_lines[-1].strip():
        out_lines.pop()

    return "\n".join(out_lines) + "\n"


def main() -> None:
    manifest_path = Path(sys.argv[1]) if len(sys.argv) > 1 else MANIFEST
    data = load_manifest(manifest_path)
    merge_cfg = data.get("merge") or {}
    output_name = merge_cfg.get("output", "adblock-collection.module")
    output_path = MODULES / output_name
    header_lines = merge_cfg.get("header_lines")
    primary_desc = merge_cfg.get("primary_desc")
    script_url_fixes = {**DEFAULT_SCRIPT_URL_FIXES, **(merge_cfg.get("script_url_fixes") or {})}

    UPSTREAM_CACHE.mkdir(parents=True, exist_ok=True)

    modules = data.get("modules", [])
    if not modules:
        raise SystemExit("no modules in manifest")

    loaded: list[tuple[str, str, str]] = []
    for item in modules:
        name = item["name"]
        cache_name = item.get("cache") or item.get("file") or f"{name}.module"
        if item.get("local"):
            local_path = MODULES / cache_name
            if not local_path.exists():
                raise SystemExit(f"missing local module {local_path}")
            text = local_path.read_text(encoding="utf-8")
            print(f"OK local {name} <- {local_path.name}")
        else:
            cache_path = UPSTREAM_CACHE / cache_name
            text = fetch(item["upstream"])
            text = apply_script_url_fixes(text, script_url_fixes)
            text = mirror_script_paths(text)
            cache_path.write_text(text, encoding="utf-8")
            print(f"OK upstream {name} -> {cache_path.name}")
        loaded.append((name, item.get("role", "supplement"), text))

    primary = next((x for x in loaded if x[1] == "primary"), loaded[0])
    supplements = [
        (n, t) for n, role, t in loaded if (n, role, t) != primary and role != "skip"
    ]

    merged = build_merged_module(
        primary[2], supplements, header_lines=header_lines, primary_desc=primary_desc
    )
    merged = apply_script_url_fixes(merged, script_url_fixes)
    merged = mirror_script_paths(merged)
    output_path.write_text(merged, encoding="utf-8")
    print(f"wrote {output_path.name} ({len(merged.splitlines())} lines)")


if __name__ == "__main__":
    main()
