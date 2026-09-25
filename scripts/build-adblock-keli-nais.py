#!/usr/bin/env python3
"""Build self-hosted adblock collection: QingRex 1:1 first, then fmz200 gaps, then splash.

Pipeline (as requested):
  1) Mirror QingRex/LoonKissSurge 「××去广告」modules byte-for-byte → Modules/vendors/qingrex/
  2) Mirror every external script-path → Scripts/vendors/...
  3) Rewrite script URLs to this repo; merge → Modules/adblock-collection.module
  4) Diff fmz200 blockAds; append rules not already present (exclude unlock/crack noise)
  5) Same for 开屏: mirror 墨鱼 StartUpAds (+ FakeiOS), append gaps

No heat/NB patches. Collection content = upstream pieces with URL remaps only.
"""

from __future__ import annotations

import hashlib
import json
import re
import ssl
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
MODULES = ROOT / "Modules"
SCRIPTS = ROOT / "Scripts"
VENDORS_Q = MODULES / "vendors" / "qingrex"
VENDORS_F = MODULES / "vendors" / "fmz200"
VENDORS_S = MODULES / "vendors" / "splash"
SCRIPTS_V = SCRIPTS / "vendors"
OUT = MODULES / "adblock-collection.module"
SHA_DIR = MODULES / "vendors"

GITHUB_RAW = "https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main"
CTX = ssl.create_default_context()
UA = {"User-Agent": "egern-config-keli-nais/1.0"}

QINGREX_API = "https://api.github.com/repos/QingRex/LoonKissSurge/git/trees/main?recursive=1"
QINGREX_RAW = "https://raw.githubusercontent.com/QingRex/LoonKissSurge/main/"
FMZ_BLOCKADS = "https://raw.githubusercontent.com/fmz200/wool_scripts/main/Surge/module/blockAds.module"

SPLASH_PRIMARY = [
    ("moyu-StartUpAds.conf", "https://ddgksf2013.top/rewrite/StartUpAds.conf"),
    (
        "moyu-FakeiOSAds.conf",
        "https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/AdBlock/FakeiOSAds.conf",
    ),
]

# Unlock / VIP crack must stay in unlock-collection, not adblock gaps.
GAP_LINE_EXCLUDES = (
    "spotify.crack",
    "spotify.crack.dev",
    "spotifymodule.crack",
    "domain-suffix,wxs.qq.com,reject",  # 误伤微信正文图；精准三域名另管
    r"mp\.weixin\.qq\.com\/mp\/getappmsgad advertisement fmz200",
)

SCRIPT_URL_RE = re.compile(
    r"(https?://[^\s,\"']+\.(?:js|mjs)(?:\?[^\s,\"']*)?)",
    re.IGNORECASE,
)


def encode_url(url: str) -> str:
    """Percent-encode non-ASCII path/query so urllib does not raise UnicodeEncodeError."""
    parsed = urlparse(url)
    path = quote(unquote(parsed.path), safe="/:@!$&'()*+,;=-._~")
    query = quote(unquote(parsed.query), safe="=&%:@!$&'()*+,;=-._~") if parsed.query else ""
    return parsed._replace(path=path, query=query).geturl()


def fetch(url: str, *, timeout: int = 90) -> bytes:
    url = encode_url(url)
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=timeout) as resp:
            data = resp.read()
    except Exception:
        mirror = "https://ghproxy.net/" + url
        req = urllib.request.Request(mirror, headers=UA)
        with urllib.request.urlopen(req, context=CTX, timeout=timeout) as resp:
            data = resp.read()
    if data.lstrip()[:20].lower().startswith((b"<!doctype", b"<html")):
        raise ValueError(f"HTML returned for {url}")
    return data


def fetch_text(url: str) -> str:
    return fetch(url).decode("utf-8", errors="replace")


def safe_name(path: str) -> str:
    return path.split("/")[-1]


def script_local_path(url: str) -> Path:
    """Map remote script URL → Scripts/vendors/<host>/<path...>"""
    u = urlparse(url)
    host = u.netloc.replace(":", "_")
    path = unquote(u.path).lstrip("/")
    if not path or path.endswith("/"):
        path = path + "index.js"
    if u.query:
        qh = hashlib.sha1(u.query.encode()).hexdigest()[:8]
        p = Path(path)
        path = str(p.with_name(p.stem + f"_{qh}" + p.suffix))
    return SCRIPTS_V / host / path


def mirror_script(url: str, cache: dict[str, str]) -> str:
    if url in cache:
        return cache[url]
    # Never self-host unlock/crack scripts into adblock vendors
    low = url.lower()
    if any(x in low for x in ("spotify.crack", "crack.dev.js")):
        cache[url] = url
        return url
    dest = script_local_path(url)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.is_file():
        print(f"  mirror script {url}")
        try:
            dest.write_bytes(fetch(url))
        except Exception as exc:
            print(f"  ! skip script {url}: {exc}")
            cache[url] = url
            return url
    rel = dest.relative_to(ROOT).as_posix()
    local = f"{GITHUB_RAW}/{rel}"
    cache[url] = local
    return local


def rewrite_scripts_in_text(text: str, cache: dict[str, str]) -> str:
    def repl(m: re.Match[str]) -> str:
        return mirror_script(m.group(1), cache)

    return SCRIPT_URL_RE.sub(repl, text)


def list_qingrex_modules() -> list[str]:
    raw = fetch(QINGREX_API)
    tree = json.loads(raw.decode())["tree"]
    out: list[str] = []
    for t in tree:
        if t.get("type") != "blob":
            continue
        p = t["path"]
        if not p.endswith(".sgmodule"):
            continue
        if p.startswith("Surge/Beta/"):
            continue
        # per-app root only (avoid Official mega aggregates double-counting)
        if p.startswith("Surge/") and p.count("/") == 1 and "去广告" in p:
            out.append(p)
    return sorted(out)


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


def active(line: str) -> bool:
    s = line.strip()
    return bool(s) and not s.startswith("#") and not s.startswith("#!")


def is_excluded_gap_line(line: str) -> bool:
    s = line.lower()
    for needle in GAP_LINE_EXCLUDES:
        if needle.lower() in s:
            return True
    return False


def rule_key(line: str) -> str | None:
    s = line.strip()
    if not active(line):
        return None
    if " - " in s:
        return s.rsplit(" - ", 1)[0].strip().strip("\"'")
    return s


def script_key(line: str) -> str | None:
    s = line.strip()
    if not active(line):
        return None
    name_m = re.match(r"^([^=]+?)\s*=", s)
    type_m = re.search(r"type\s*=\s*([^,\s]+)", s, re.I)
    pattern_m = re.search(r"pattern\s*=\s*(\"[^\"]+\"|'[^']+'|[^,]+)", s, re.I)
    parts = []
    if name_m:
        parts.append(name_m.group(1).strip().lower())
    if type_m:
        parts.append(type_m.group(1).strip().lower())
    if pattern_m:
        parts.append(pattern_m.group(1).strip().strip("\"'"))
    return "|".join(parts) if parts else s


def dedupe(lines: list[str], *, section: str) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    key_fn = script_key if section == "Script" else rule_key
    for line in lines:
        k = key_fn(line)
        if k is None:
            out.append(line)
            continue
        if k in seen:
            continue
        seen.add(k)
        out.append(line)
    return out


def split_mitm(lines: list[str]) -> list[str]:
    hosts: list[str] = []
    for line in lines:
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if "hostname" in s.lower() and "=" in s:
            rhs = s.split("=", 1)[1].strip()
            rhs = re.sub(r"^%APPEND%\s*", "", rhs, flags=re.I)
            for part in rhs.split(","):
                h = part.strip()
                if h:
                    hosts.append(h)
        else:
            for part in s.split(","):
                h = part.strip()
                if h and not h.startswith("#"):
                    hosts.append(h)
    seen: set[str] = set()
    ordered: list[str] = []
    for h in hosts:
        k = h.lower()
        if k in seen:
            continue
        seen.add(k)
        ordered.append(h)
    return ordered


def merge_modules(sources: list[tuple[str, str]], *, title: str, desc: str, notes: list[str]) -> str:
    parsed: list[tuple[str, dict[str, list[str]]]] = []
    for sid, text in sources:
        _, sec = parse_module(text)
        parsed.append((sid, sec))

    order = [
        "General",
        "Rule",
        "URL Rewrite",
        "Header Rewrite",
        "Body Rewrite",
        "Map Local",
        "Script",
        "MITM",
    ]
    for _, sec in parsed:
        for name in sec:
            if name not in order:
                order.append(name)

    out: list[str] = [
        f"#!name={title}",
        f"#!desc={desc}",
        "#!category=去广告",
        "#!author=oo226/egern-config (可莉原样 + 奶思差集 + 开屏)",
        f"# built_at={datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ')}",
        *notes,
        "",
    ]
    for section in order:
        blocks: list[tuple[str, list[str]]] = []
        for sid, sec in parsed:
            lines = sec.get(section)
            if lines:
                blocks.append((sid, lines))
        if not blocks:
            continue
        out.append(f"[{section}]")
        if section == "MITM":
            hosts: list[str] = []
            for _, lines in blocks:
                hosts.extend(split_mitm(lines))
            seen: set[str] = set()
            uniq: list[str] = []
            for h in hosts:
                k = h.lower()
                if k in seen:
                    continue
                seen.add(k)
                uniq.append(h)
            chunk: list[str] = []
            for h in uniq:
                chunk.append(h)
                if len(chunk) >= 50:
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
        out.extend(dedupe(merged, section=section))
        if out[-1].strip():
            out.append("")
    return "\n".join(out).rstrip() + "\n"


def collect_keys(text: str) -> set[str]:
    """Fingerprint active rules for gap detection."""
    _, sec = parse_module(text)
    keys: set[str] = set()
    for name, lines in sec.items():
        if name == "MITM":
            for h in split_mitm(lines):
                keys.add("mitm:" + h.lower())
            continue
        for line in lines:
            if name == "Script":
                k = script_key(line)
            else:
                k = rule_key(line)
            if k:
                keys.add(f"{name}:{k}")
    return keys


def gap_lines_from_source(src_text: str, have: set[str]) -> dict[str, list[str]]:
    """Return section→lines from src that are not covered by have keys."""
    _, sec = parse_module(src_text)
    gaps: dict[str, list[str]] = {}
    for name, lines in sec.items():
        if name == "MITM":
            missing_hosts = []
            for h in split_mitm(lines):
                if ("mitm:" + h.lower()) not in have:
                    missing_hosts.append(h)
            if missing_hosts:
                chunk: list[str] = []
                buf: list[str] = []
                for h in missing_hosts:
                    chunk.append(h)
                    if len(chunk) >= 50:
                        buf.append("hostname = %APPEND% " + ", ".join(chunk))
                        chunk = []
                if chunk:
                    buf.append("hostname = %APPEND% " + ", ".join(chunk))
                gaps[name] = buf
            continue
        kept: list[str] = []
        for line in lines:
            if not active(line):
                continue
            if is_excluded_gap_line(line):
                continue
            k = script_key(line) if name == "Script" else rule_key(line)
            if not k:
                continue
            if f"{name}:{k}" in have:
                continue
            kept.append(line)
        if kept:
            gaps[name] = kept
    return gaps


def qx_conf_to_surge_sections(text: str) -> dict[str, list[str]]:
    """QuantumultX rewrite conf → Surge-like section bags.

    墨鱼 StartUpAds 是无 [rewrite_local] 的扁平 conf：行内 `url reject-200` /
    `url script-response-body`，末尾一行 `hostname = ...`。
    """
    sections: dict[str, list[str]] = {
        "Rule": [],
        "URL Rewrite": [],
        "Script": [],
        "MITM": [],
    }
    lines = text.splitlines()
    has_sections = any(
        ln.strip().startswith("[") and ln.strip().endswith("]") for ln in lines
    )
    in_rewrite = not has_sections
    in_mitm = False
    script_i = 0

    for line in lines:
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            name = s[1:-1].lower()
            in_rewrite = name in {"rewrite_local", "rewrite", "url rewrite"}
            in_mitm = name == "mitm"
            continue
        if not s or s.startswith("#") or s.startswith(";") or s.startswith("//"):
            continue

        low = s.lower()
        if low.startswith("hostname"):
            if "=" in s:
                rhs = s.split("=", 1)[1].strip()
            else:
                rhs = s.split(None, 1)[1].strip() if " " in s else ""
            if rhs:
                sections["MITM"].append("hostname = %APPEND% " + rhs)
            continue

        if low.startswith("host-suffix"):
            parts = [p.strip() for p in s.split(",")]
            if len(parts) >= 2:
                action = (parts[2] if len(parts) > 2 else "reject").upper()
                if action.startswith("REJECT"):
                    action = "REJECT"
                sections["Rule"].append(f"DOMAIN-SUFFIX,{parts[1]},{action}")
            continue
        if low.startswith("host-keyword"):
            parts = [p.strip() for p in s.split(",")]
            if len(parts) >= 2:
                action = (parts[2] if len(parts) > 2 else "reject").upper()
                if action.startswith("REJECT"):
                    action = "REJECT"
                sections["Rule"].append(f"DOMAIN-KEYWORD,{parts[1]},{action}")
            continue
        if low.startswith("host,"):
            parts = [p.strip() for p in s.split(",")]
            if len(parts) >= 2:
                action = (parts[2] if len(parts) > 2 else "reject").upper()
                if action.startswith("REJECT"):
                    action = "REJECT"
                sections["Rule"].append(f"DOMAIN,{parts[1]},{action}")
            continue

        if not (in_rewrite or in_mitm or not has_sections):
            continue
        if in_mitm:
            sections["MITM"].append("hostname = %APPEND% " + s)
            continue

        # QX: pattern url reject / reject-200 / reject-dict / ...
        if " url reject" in s or s.endswith(" reject") or " url reject-" in s:
            if " url " in s:
                pat, rest = s.split(" url ", 1)
                pat = pat.strip()
                rest = rest.strip()
                if rest.startswith("reject-"):
                    kind = rest.split()[0]  # reject-200 / reject-dict / ...
                    # Surge URL Rewrite supports reject / reject-200 / reject-img / reject-dict
                    if kind in {"reject", "reject-200", "reject-img", "reject-dict", "reject-array"}:
                        sections["URL Rewrite"].append(f"{pat} - {kind}")
                    else:
                        sections["URL Rewrite"].append(f"{pat} - reject-200")
                else:
                    sections["URL Rewrite"].append(f"{pat} - reject")
            continue

        if " script-" in s or " url script-" in s:
            m = re.match(r"^(\S+)\s+url\s+(script-[\w-]+)\s+(\S+)", s)
            if m:
                pat, stype, surl = m.group(1), m.group(2), m.group(3)
                surge_type = "http-response" if "response" in stype else "http-request"
                req_body = "true" if ("body" in stype or "analyze" in stype) else "false"
                script_i += 1
                sections["Script"].append(
                    f"moyu-splash-{script_i} = type={surge_type},pattern={pat},"
                    f"script-path={surl},requires-body={req_body},timeout=60"
                )
            continue

        if " url " in s:
            # other QX rewrite forms — keep as comment for audit
            sections["URL Rewrite"].append("# qx: " + s)

    return sections


def sections_to_module(sections: dict[str, list[str]], *, name: str, desc: str) -> str:
    out = [f"#!name={name}", f"#!desc={desc}", ""]
    for sec, lines in sections.items():
        if not lines:
            continue
        out.append(f"[{sec}]")
        out.extend(lines)
        out.append("")
    return "\n".join(out)


def write_aliases(final: str) -> None:
    # finalize-egern-adblock.py re-publishes aliases after divert/jsDelivr rewrite;
    # write them here so a local rebuild without finalize still has working URLs.
    for alias in (
        "adblock-egern.module",
        "adblock-egern-v0815b.module",
        "adblock-egern-v0815c.module",
    ):
        (MODULES / alias).write_text(final, encoding="utf-8")
        print(f"alias {alias}")


def main() -> None:
    script_cache: dict[str, str] = {}
    sha_lines = [
        f"# vendors checksums @ {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ')}",
        "",
    ]

    # ── 1) QingRex per-app modules ──
    VENDORS_Q.mkdir(parents=True, exist_ok=True)
    # drop stale rewritten intermediates from prior runs
    for stale in VENDORS_Q.glob("*.rewritten"):
        stale.unlink()

    paths = list_qingrex_modules()
    print(f"QingRex root 去广告 modules: {len(paths)}")
    q_sources: list[tuple[str, str]] = []
    for rel in paths:
        url = QINGREX_RAW + quote(rel, safe="/")
        name = safe_name(rel)
        print(f"fetch {name}")
        try:
            raw = fetch(url)
        except Exception as exc:
            print(f"  ! fail {rel}: {exc}")
            continue
        dest = VENDORS_Q / name
        dest.write_bytes(raw)
        digest = hashlib.sha256(raw).hexdigest()
        sha_lines.append(f"{digest}  vendors/qingrex/{name}")
        text = rewrite_scripts_in_text(raw.decode("utf-8", errors="replace"), script_cache)
        q_sources.append((f"qingrex/{name}", text))

    if not q_sources:
        print("FATAL: qingrex_modules=0 — abort (would ship full-fmz as fake 可莉)", file=sys.stderr)
        sys.exit(1)

    # ── 2) Merge QingRex → base collection text ──
    base = merge_modules(
        q_sources,
        title="去广告合集",
        desc="可莉原样拼合 + 奶思差集 + 开屏·强制更新本模块",
        notes=[
            "# PIPELINE: QingRex 1:1 → self-host scripts → merge; then fmz200 gaps; then splash gaps",
            f"# qingrex_modules={len(q_sources)}",
            "# originals: Modules/vendors/qingrex/*.sgmodule (byte-identical upstream)",
        ],
    )
    have = collect_keys(base)
    print(f"base keys={len(have)}")

    # ── 3) fmz200 blockAds gaps ──
    VENDORS_F.mkdir(parents=True, exist_ok=True)
    print("fetch fmz200 blockAds")
    fmz_raw = fetch(FMZ_BLOCKADS)
    (VENDORS_F / "blockAds.module").write_bytes(fmz_raw)
    sha_lines.append(f"{hashlib.sha256(fmz_raw).hexdigest()}  vendors/fmz200/blockAds.module")
    fmz_text = rewrite_scripts_in_text(fmz_raw.decode("utf-8", errors="replace"), script_cache)
    gaps = gap_lines_from_source(fmz_text, have)
    gap_counts = {k: len(v) for k, v in gaps.items()}
    print("fmz200 gap lines:", gap_counts)

    gap_mod = ""
    if any(gaps.values()):
        gap_mod_lines = ["#!name=fmz200-gaps", "#!desc=奶思差集", ""]
        for sec, lines in gaps.items():
            if not lines:
                continue
            gap_mod_lines.append(f"[{sec}]")
            gap_mod_lines.append("# >>> fmz200-blockAds gaps")
            gap_mod_lines.extend(lines)
            gap_mod_lines.append("")
        gap_mod = "\n".join(gap_mod_lines)
        (VENDORS_F / "blockAds-gaps.module").write_text(gap_mod, encoding="utf-8")
        base = merge_modules(
            q_sources + [("fmz200-gaps", gap_mod)],
            title="去广告合集",
            desc="可莉原样拼合 + 奶思差集 + 开屏·强制更新本模块",
            notes=[
                "# PIPELINE: QingRex 1:1 → self-host scripts → merge; then fmz200 gaps; then splash gaps",
                f"# qingrex_modules={len(q_sources)}",
                f"# fmz200_gap_lines={gap_counts}",
                "# originals: Modules/vendors/qingrex/*.sgmodule + vendors/fmz200/blockAds.module",
            ],
        )
        have = collect_keys(base)
    else:
        (VENDORS_F / "blockAds-gaps.module").write_text(
            "#!name=fmz200-gaps\n#!desc=奶思差集 (empty)\n", encoding="utf-8"
        )

    # ── 4) Splash (墨鱼去开屏) ──
    VENDORS_S.mkdir(parents=True, exist_ok=True)
    splash_mods: list[tuple[str, str]] = []
    for fname, url in SPLASH_PRIMARY:
        print(f"fetch splash {fname}")
        try:
            raw = fetch(url)
        except Exception as exc:
            print(f"  ! {fname}: {exc}")
            continue
        (VENDORS_S / fname).write_bytes(raw)
        sha_lines.append(f"{hashlib.sha256(raw).hexdigest()}  vendors/splash/{fname}")
        text = rewrite_scripts_in_text(raw.decode("utf-8", errors="replace"), script_cache)
        if fname.endswith(".conf"):
            secs = qx_conf_to_surge_sections(text)
            mod = sections_to_module(secs, name=f"splash-{fname}", desc="墨鱼开屏(自托管转换)")
        else:
            mod = text
        (VENDORS_S / (fname + ".surge.module")).write_text(mod, encoding="utf-8")
        splash_gaps = gap_lines_from_source(mod, have)
        if any(splash_gaps.values()):
            gl = ["#!name=splash-gaps", ""]
            for sec, lines in splash_gaps.items():
                if not lines:
                    continue
                gl.append(f"[{sec}]")
                gl.append(f"# >>> {fname} gaps")
                gl.extend(lines)
                gl.append("")
            splash_mods.append((f"splash/{fname}", "\n".join(gl)))
            print(f"  splash gaps from {fname}:", {k: len(v) for k, v in splash_gaps.items() if v})
            # fold into have so second splash file only adds true leftovers
            have |= collect_keys("\n".join(gl))
        else:
            print(f"  splash {fname}: no gaps (already covered)")

    all_sources = list(q_sources)
    if gap_mod:
        all_sources.append(("fmz200-gaps", gap_mod))
    all_sources.extend(splash_mods)

    final = merge_modules(
        all_sources,
        title="去广告合集",
        desc="可莉原样拼合 + 奶思差集 + 开屏·强制更新本模块",
        notes=[
            "# PIPELINE: QingRex 1:1 → self-host scripts → merge; then fmz200 gaps; then splash gaps",
            f"# qingrex_modules={len(q_sources)}",
            f"# fmz200_gap_lines={gap_counts}",
            f"# splash_gap_modules={len(splash_mods)}",
            "# 原样副本: Modules/vendors/{qingrex,fmz200,splash}/",
            "# 脚本镜像: Scripts/vendors/<host>/...",
            "# 无 heat/NB 补丁；仅 script URL 改指本仓",
        ],
    )
    OUT.write_text(final, encoding="utf-8")
    print(f"wrote {OUT} ({len(final)} chars)")
    write_aliases(final)

    (SHA_DIR / "SHA256SUMS").write_text("\n".join(sha_lines) + "\n", encoding="utf-8")
    (VENDORS_Q / "README.md").write_text(
        "\n".join(
            [
                "# vendors/qingrex — 可莉去广告原样副本",
                "",
                "来源：https://github.com/QingRex/LoonKissSurge `Surge/*去广告.sgmodule`（不含 Beta）",
                "字节与上游一致；合集构建时仅把 script URL 改指本仓 `Scripts/vendors/`。",
                "",
                "重建：`python3 scripts/build-adblock-keli-nais.py`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (VENDORS_F / "README.md").write_text(
        "\n".join(
            [
                "# vendors/fmz200 — 奶思 blockAds 原样 + 差集",
                "",
                "- `blockAds.module`：上游原样",
                "- `blockAds-gaps.module`：相对可莉合集多出来的规则（已剔除 Spotify Crack 等解锁噪声）",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (VENDORS_S / "README.md").write_text(
        "\n".join(
            [
                "# vendors/splash — 墨鱼去开屏原样 + Surge 转换",
                "",
                "- `moyu-StartUpAds.conf` / `moyu-FakeiOSAds.conf`：上游原样",
                "- `*.surge.module`：QX→Surge 转换（合集只并入相对已有规则的差集）",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print("done. mirrored scripts:", len(script_cache))
    print(f"qingrex_modules={len(q_sources)} fmz_gaps={gap_counts} splash_mods={len(splash_mods)}")


if __name__ == "__main__":
    main()
