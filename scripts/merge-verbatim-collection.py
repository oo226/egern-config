#!/usr/bin/env python3
"""Build a verbatim adblock collection from upstream modules.

Unlike merge-adblock-modules.py this path:
  - stores each upstream file byte-for-byte under Modules/vendors/
  - merges sections with dedupe only
  - never rewrites script URLs, never excludes content lines,
    never diverts REJECT rules, never injects local patches
"""

from __future__ import annotations

import hashlib
import re
import ssl
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

ROOT = Path(__file__).resolve().parent.parent
MODULES = ROOT / "Modules"
DEFAULT_MANIFEST = MODULES / "manifest.verbatim.yaml"
CTX = ssl.create_default_context()
MIRROR = "https://ghproxy.net/"

MERGE_SECTIONS_DEFAULT = (
    "General",
    "Rule",
    "URL Rewrite",
    "Header Rewrite",
    "Body Rewrite",
    "Map Local",
    "Script",
    "MITM",
)


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "egern-config-verbatim/1.0"})
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=120) as resp:
            data = resp.read()
    except Exception:
        mirror_url = MIRROR + url if not url.startswith(MIRROR) else url
        req = urllib.request.Request(mirror_url, headers={"User-Agent": "egern-config-verbatim/1.0"})
        with urllib.request.urlopen(req, context=CTX, timeout=120) as resp:
            data = resp.read()
    text_probe = data[:200].lstrip().lower()
    if text_probe.startswith(b"<!doctype") or text_probe.startswith(b"<html"):
        raise ValueError(f"upstream returned HTML: {url}")
    return data


def load_manifest(path: Path) -> dict:
    if not yaml:
        raise SystemExit("PyYAML required: pip install pyyaml")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


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
    name_m = re.match(r"^([^=]+?)\s*=", stripped)
    type_m = re.search(r"type\s*=\s*([^,\s]+)", stripped, re.IGNORECASE)
    pattern_m = re.search(r"pattern\s*=\s*(\"[^\"]+\"|'[^']+'|[^,]+)", stripped, re.IGNORECASE)
    parts: list[str] = []
    if name_m:
        parts.append(name_m.group(1).strip().lower())
    if type_m:
        parts.append(type_m.group(1).strip().lower())
    if pattern_m:
        parts.append(pattern_m.group(1).strip().strip("\"'"))
    return "|".join(parts) if parts else stripped


def dedupe_lines(lines: list[str], *, section: str) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for line in lines:
        key_fn = script_key if section == "Script" else rule_key
        key = key_fn(line)
        if key is None:
            out.append(line)
            continue
        if key in seen:
            continue
        seen.add(key)
        out.append(line)
    return out


def split_mitm_hosts(lines: list[str]) -> list[str]:
    hosts: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # hostname = %APPEND% a, b, c  OR  hostname = a, b
        if "hostname" in stripped.lower() and "=" in stripped:
            _, _, rhs = stripped.partition("=")
            rhs = rhs.strip()
            rhs = re.sub(r"^%APPEND%\s*", "", rhs, flags=re.IGNORECASE)
            for part in rhs.split(","):
                h = part.strip()
                if h:
                    hosts.append(h)
        else:
            for part in stripped.split(","):
                h = part.strip()
                if h and not h.startswith("#"):
                    hosts.append(h)
    # preserve order, unique case-insensitive
    seen: set[str] = set()
    ordered: list[str] = []
    for h in hosts:
        k = h.lower()
        if k in seen:
            continue
        seen.add(k)
        ordered.append(h)
    return ordered


def build_verbatim(
    sources: list[tuple[str, str]],
    *,
    primary_name: str,
    primary_desc: str,
    header_lines: list[str],
    merge_sections: tuple[str, ...],
) -> str:
    """sources: list of (id, text). First entry is primary for section order seed."""
    parsed: list[tuple[str, dict[str, list[str]]]] = []
    for sid, text in sources:
        _, sections = parse_module(text)
        parsed.append((sid, sections))

    section_order: list[str] = []
    for name in merge_sections:
        section_order.append(name)
    for _, sections in parsed:
        for name in sections:
            if name not in section_order:
                section_order.append(name)

    out: list[str] = [
        f"#!name={primary_name}",
        f"#!desc={primary_desc}",
        "#!category=去广告",
        *header_lines,
    ]
    if out[-1].strip():
        out.append("")

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    out.append(f"# built_at={stamp}")
    out.append("# sources:")
    for sid, _ in sources:
        out.append(f"#   - {sid}")
    out.append("")

    for section in section_order:
        blocks: list[tuple[str, list[str]]] = []
        for sid, sections in parsed:
            lines = sections.get(section)
            if lines:
                blocks.append((sid, lines))
        if not blocks:
            continue

        out.append(f"[{section}]")
        if section == "MITM":
            all_hosts: list[str] = []
            for sid, lines in blocks:
                all_hosts.extend(split_mitm_hosts(lines))
            # re-unique preserving order
            seen: set[str] = set()
            hosts: list[str] = []
            for h in all_hosts:
                k = h.lower()
                if k in seen:
                    continue
                seen.add(k)
                hosts.append(h)
            if hosts:
                # chunk for readability
                chunk: list[str] = []
                for h in hosts:
                    chunk.append(h)
                    if len(chunk) >= 40:
                        out.append("hostname = %APPEND% " + ", ".join(chunk))
                        chunk = []
                if chunk:
                    out.append("hostname = %APPEND% " + ", ".join(chunk))
            out.append("")
            continue

        merged: list[str] = []
        for sid, lines in blocks:
            merged.append(f"# >>> {sid}")
            merged.extend(lines)
            if lines and lines[-1].strip():
                merged.append("")
        merged = dedupe_lines(merged, section=section)
        out.extend(merged)
        if out[-1].strip():
            out.append("")

    return "\n".join(out).rstrip() + "\n"


def vendor_filename(module_id: str, upstream_url: str) -> str:
    suffix = ".sgmodule" if upstream_url.rstrip("/").endswith(".sgmodule") else ".module"
    return f"{module_id}{suffix}"


def main() -> None:
    manifest_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_MANIFEST
    data = load_manifest(manifest_path)
    merge_cfg = data.get("merge") or {}
    modules = data.get("modules") or []
    if not modules:
        raise SystemExit("no modules in manifest")

    vendors_dir = MODULES / str(merge_cfg.get("vendors_dir") or "vendors")
    vendors_dir.mkdir(parents=True, exist_ok=True)

    sources: list[tuple[str, str]] = []
    sha_lines: list[str] = [
        "# Verbatim vendor checksums (sha256 of upstream bytes at fetch time)",
        f"# generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ')}",
        "",
    ]

    for entry in modules:
        mid = entry["id"]
        url = entry["upstream"]
        print(f"fetch {mid}: {url}")
        raw = fetch(url)
        digest = hashlib.sha256(raw).hexdigest()
        dest_name = vendor_filename(mid, url)
        dest = vendors_dir / dest_name
        dest.write_bytes(raw)
        print(f"  saved {dest.relative_to(ROOT)} ({len(raw)} bytes, sha256={digest[:12]}…)")
        sha_lines.append(f"{digest}  {dest_name}  {url}")
        text = raw.decode("utf-8", errors="replace")
        sources.append((mid, text))

    (vendors_dir / "SHA256SUMS").write_text("\n".join(sha_lines) + "\n", encoding="utf-8")
    (vendors_dir / "README.md").write_text(
        "\n".join(
            [
                "# Modules/vendors — 上游原样副本",
                "",
                "每个文件是对应上游 raw **下载时刻** 的字节副本，不做任何改写。",
                "合集 `adblock-verbatim.module` 由这些文件拼接而成（仅去重 + MITM 合并）。",
                "",
                "校验：见同目录 `SHA256SUMS`。",
                "",
                "本地补丁（NB / 微信 / heat）**不**进入此目录；需要时单独加模块。",
                "",
            ]
        ),
        encoding="utf-8",
    )

    merged = build_verbatim(
        sources,
        primary_name=str(merge_cfg.get("primary_name") or "去广告合集（原样）"),
        primary_desc=str(merge_cfg.get("primary_desc") or "上游原样拼接"),
        header_lines=list(merge_cfg.get("header_lines") or []),
        merge_sections=tuple(merge_cfg.get("merge_sections") or MERGE_SECTIONS_DEFAULT),
    )
    out_name = str(merge_cfg.get("output") or "adblock-verbatim.module")
    out_path = MODULES / out_name
    out_path.write_text(merged, encoding="utf-8")
    print(f"wrote {out_path.relative_to(ROOT)} ({len(merged)} chars, {len(sources)} sources)")


if __name__ == "__main__":
    main()
