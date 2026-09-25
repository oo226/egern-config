#!/usr/bin/env python3
"""Formal adblock tree: Adblock/{js,modules} — 可莉 1:1 → 合集 → 奶思差集 → 墨鱼开屏.

Layout (this branch only; does not touch sync 日更):
  Adblock/
    js/                         # all self-hosted scripts
    modules/
      qingrex/                  # 可莉 per-app 原样
      fmz200/                   # 奶思 blockAds 原样 + gaps
      moyu/                     # 墨鱼开屏原样 + Surge 转换
    adblock-collection.module   # 大合集
    UPSTREAM.md                 # 合并了什么、来自哪

Pipeline:
  1) QingRex Surge/*去广告.sgmodule → modules/qingrex/ (byte-identical)
  2) Mirror script-path → js/<host>/... ; rewrite URLs to this branch
  3) Merge 可莉 → base collection
  4) fmz200 blockAds gaps (exclude unlock/crack noise)
  5) 墨鱼 StartUpAds + FakeiOSAds gaps (开屏与去广告同一合集)
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import ssl
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
ADBLOCK = ROOT / "Adblock"
JS = ADBLOCK / "js"
MOD = ADBLOCK / "modules"
MOD_Q = MOD / "qingrex"
MOD_F = MOD / "fmz200"
MOD_M = MOD / "moyu"
OUT = ADBLOCK / "adblock-collection.module"
REPORT = ADBLOCK / "UPSTREAM.md"
SHA_FILE = ADBLOCK / "SHA256SUMS"

BRANCH = (
    os.environ.get("ADBLOCK_BRANCH")
    or os.environ.get("GITHUB_REF_NAME")
    or "cursor/adblock-formal-f611"
)
GITHUB_RAW = f"https://raw.githubusercontent.com/oo226/egern-config/refs/heads/{BRANCH}"

CTX = ssl.create_default_context()
UA = {"User-Agent": "egern-config-adblock-formal/1.0"}

QINGREX_API = "https://api.github.com/repos/QingRex/LoonKissSurge/git/trees/main?recursive=1"
QINGREX_RAW = "https://raw.githubusercontent.com/QingRex/LoonKissSurge/main/"
FMZ_BLOCKADS = "https://raw.githubusercontent.com/fmz200/wool_scripts/main/Surge/module/blockAds.module"
SPLASH_PRIMARY = [
    ("StartUpAds.conf", "https://ddgksf2013.top/rewrite/StartUpAds.conf"),
    (
        "FakeiOSAds.conf",
        "https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/AdBlock/FakeiOSAds.conf",
    ),
]

GAP_LINE_EXCLUDES = (
    "spotify.crack",
    "spotify.crack.dev",
    "spotifymodule.crack",
    "domain-suffix,wxs.qq.com,reject",
    r"mp\.weixin\.qq\.com\/mp\/getappmsgad advertisement fmz200",
)

SCRIPT_URL_RE = re.compile(
    r"(https?://[^\s,\"']+\.(?:js|mjs)(?:\?[^\s,\"']*)?)",
    re.IGNORECASE,
)

# stats for UPSTREAM.md
STATS: dict = {
    "qingrex_ok": [],
    "qingrex_fail": [],
    "scripts_ok": [],
    "scripts_fail": [],
    "fmz_gaps": {},
    "splash_gaps": {},
}


def encode_url(url: str) -> str:
    p = urlparse(url)
    path = quote(unquote(p.path), safe="/:@!$&'()*+,;=-._~")
    query = quote(unquote(p.query), safe="=&%:@!$&'()*+,;=-._~") if p.query else ""
    return p._replace(path=path, query=query).geturl()


def fetch(url: str, *, timeout: int = 90) -> bytes:
    url = encode_url(url)
    headers = dict(UA)
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token and "api.github.com" in url:
        headers["Authorization"] = f"Bearer {token}"
        headers["Accept"] = "application/vnd.github+json"
    req = urllib.request.Request(url, headers=headers)
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


def script_local_path(url: str) -> Path:
    u = urlparse(url)
    host = u.netloc.replace(":", "_")
    path = unquote(u.path).lstrip("/")
    if not path or path.endswith("/"):
        path = path + "index.js"
    if u.query:
        qh = hashlib.sha1(u.query.encode()).hexdigest()[:8]
        p = Path(path)
        path = str(p.with_name(p.stem + f"_{qh}" + p.suffix))
    return JS / host / path


def mirror_script(url: str, cache: dict[str, str]) -> str:
    if url in cache:
        return cache[url]
    low = url.lower()
    if any(x in low for x in ("spotify.crack", "crack.dev.js")):
        cache[url] = url
        return url
    dest = script_local_path(url)
    if not dest.is_file():
        print(f"  js ← {url}")
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(fetch(url))
            STATS["scripts_ok"].append(url)
        except Exception as exc:
            print(f"  ! js skip {url}: {exc}")
            STATS["scripts_fail"].append(f"{url} ({exc})")
            cache[url] = url
            return url
    else:
        if url not in STATS["scripts_ok"]:
            STATS["scripts_ok"].append(url)
    rel = dest.relative_to(ROOT).as_posix()
    local = f"{GITHUB_RAW}/{rel}"
    cache[url] = local
    return local


def rewrite_scripts(text: str, cache: dict[str, str]) -> str:
    return SCRIPT_URL_RE.sub(lambda m: mirror_script(m.group(1), cache), text)


def list_qingrex() -> list[str]:
    tree = json.loads(fetch(QINGREX_API).decode())["tree"]
    out = []
    for t in tree:
        if t.get("type") != "blob":
            continue
        p = t["path"]
        if not p.endswith(".sgmodule"):
            continue
        if p.startswith("Surge/Beta/"):
            continue
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


def is_excluded_gap(line: str) -> bool:
    s = line.lower()
    return any(n.lower() in s for n in GAP_LINE_EXCLUDES)


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
    parsed = [(sid, parse_module(text)[1]) for sid, text in sources]
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
        "#!author=oo226/egern-config (可莉原样 + 奶思差集 + 墨鱼开屏)",
        f"# built_at={datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ')}",
        f"# branch={BRANCH}",
        *notes,
        "",
    ]
    for section in order:
        blocks = [(sid, sec[section]) for sid, sec in parsed if sec.get(section)]
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
    _, sec = parse_module(text)
    keys: set[str] = set()
    for name, lines in sec.items():
        if name == "MITM":
            for h in split_mitm(lines):
                keys.add("mitm:" + h.lower())
            continue
        for line in lines:
            k = script_key(line) if name == "Script" else rule_key(line)
            if k:
                keys.add(f"{name}:{k}")
    return keys


def gap_lines(src_text: str, have: set[str]) -> dict[str, list[str]]:
    _, sec = parse_module(src_text)
    gaps: dict[str, list[str]] = {}
    for name, lines in sec.items():
        if name == "MITM":
            missing = [h for h in split_mitm(lines) if ("mitm:" + h.lower()) not in have]
            if missing:
                buf: list[str] = []
                chunk: list[str] = []
                for h in missing:
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
            if not active(line) or is_excluded_gap(line):
                continue
            k = script_key(line) if name == "Script" else rule_key(line)
            if not k or f"{name}:{k}" in have:
                continue
            kept.append(line)
        if kept:
            gaps[name] = kept
    return gaps


def qx_to_surge(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {"Rule": [], "URL Rewrite": [], "Script": [], "MITM": []}
    lines = text.splitlines()
    has_sections = any(ln.strip().startswith("[") and ln.strip().endswith("]") for ln in lines)
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
            rhs = s.split("=", 1)[1].strip() if "=" in s else (s.split(None, 1)[1].strip() if " " in s else "")
            if rhs:
                sections["MITM"].append("hostname = %APPEND% " + rhs)
            continue
        if low.startswith("host-suffix") or low.startswith("host-keyword") or low.startswith("host,"):
            parts = [p.strip() for p in s.split(",")]
            if len(parts) >= 2:
                kind = "DOMAIN-SUFFIX" if low.startswith("host-suffix") else (
                    "DOMAIN-KEYWORD" if low.startswith("host-keyword") else "DOMAIN"
                )
                action = (parts[2] if len(parts) > 2 else "reject").upper()
                if action.startswith("REJECT"):
                    action = "REJECT"
                sections["Rule"].append(f"{kind},{parts[1]},{action}")
            continue
        if not (in_rewrite or in_mitm or not has_sections):
            continue
        if in_mitm:
            sections["MITM"].append("hostname = %APPEND% " + s)
            continue
        if " url reject" in s or s.endswith(" reject") or " url reject-" in s:
            if " url " in s:
                pat, rest = s.split(" url ", 1)
                kind = rest.strip().split()[0]
                if kind in {"reject", "reject-200", "reject-img", "reject-dict", "reject-array"}:
                    sections["URL Rewrite"].append(f"{pat.strip()} - {kind}")
                else:
                    sections["URL Rewrite"].append(f"{pat.strip()} - reject-200")
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


def write_report() -> None:
    q_ok = STATS["qingrex_ok"]
    lines = [
        "# 去广告合集 — 上游合并说明",
        "",
        f"构建时间（UTC）：{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
        f"分支：`{BRANCH}`",
        "",
        "## 目录结构",
        "",
        "```",
        "Adblock/",
        "  js/                 # 自托管脚本（按上游 host 分子目录）",
        "  modules/",
        "    qingrex/          # 可莉原样单模块",
        "    fmz200/           # 奶思 blockAds 原样 + 差集模块",
        "    moyu/             # 墨鱼开屏原样 + Surge 转换",
        "  adblock-collection.module",
        "  UPSTREAM.md         # 本文件",
        "  SHA256SUMS",
        "```",
        "",
        "## 合并顺序",
        "",
        "1. **可莉（QingRex/LoonKissSurge）** — 根目录 `Surge/*去广告.sgmodule` 原样拼合（不含 Beta）",
        "2. **奶思（fmz200/wool_scripts blockAds）** — 相对可莉合集的差集",
        "3. **墨鱼开屏（ddgksf2013 StartUpAds + FakeiOSAds）** — 相对上一步的差集；开屏与去广告同一大合集",
        "",
        "未做：分流、解锁（下一批）。无 heat/NB 补丁；仅把可镜像的 script URL 改指本仓 `Adblock/js/`。",
        "",
        "## 1) 可莉 QingRex",
        "",
        f"- 上游：https://github.com/QingRex/LoonKissSurge",
        f"- 成功镜像模块：**{len(q_ok)}** → `Adblock/modules/qingrex/`",
    ]
    if STATS["qingrex_fail"]:
        lines.append(f"- 失败：{len(STATS['qingrex_fail'])}")
        for x in STATS["qingrex_fail"][:20]:
            lines.append(f"  - {x}")
    lines += [
        "",
        "角色：**大合集底座**（全部规则/改写/脚本/MITM 先并进来）。",
        "",
        "## 2) 奶思 fmz200 blockAds",
        "",
        "- 上游：https://github.com/fmz200/wool_scripts `Surge/module/blockAds.module`",
        "- 原样：`Adblock/modules/fmz200/blockAds.module`",
        "- 差集：`Adblock/modules/fmz200/blockAds-gaps.module`",
        f"- 差集行数：`{STATS['fmz_gaps']}`",
        "- 已剔除：Spotify Crack 等解锁噪声（解锁另做）",
        "",
        "角色：**补可莉没有的规则/改写/脚本/MITM**。",
        "",
        "## 3) 墨鱼开屏",
        "",
        "- StartUpAds：https://ddgksf2013.top/rewrite/StartUpAds.conf → `modules/moyu/`",
        "- FakeiOSAds：https://github.com/ddgksf2013/Rewrite `AdBlock/FakeiOSAds.conf`",
        f"- 并入合集的差集：`{STATS['splash_gaps']}`",
        "",
        "角色：**开屏规则并进同一去广告大合集**（不另开模块订阅）。",
        "",
        "## 脚本自托管",
        "",
        f"- 成功：{len(STATS['scripts_ok'])} → `Adblock/js/<host>/...`",
        f"- 失败（保留上游 URL）：{len(STATS['scripts_fail'])}",
    ]
    if STATS["scripts_fail"]:
        lines.append("")
        lines.append("失败样例（多为 kelee.one Cloudflare 403）：")
        for x in STATS["scripts_fail"][:30]:
            lines.append(f"- `{x}`")
    lines += [
        "",
        "## 订阅（本分支）",
        "",
        "```",
        f"{GITHUB_RAW}/Adblock/adblock-collection.module",
        "```",
        "",
        "重建：`python3 scripts/build-adblock-formal.py`",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {REPORT}")


def main() -> None:
    script_cache: dict[str, str] = {}
    sha_lines = [
        f"# Adblock checksums @ {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ')}",
        "",
    ]

    for d in (JS, MOD_Q, MOD_F, MOD_M):
        d.mkdir(parents=True, exist_ok=True)

    # ── 1) 可莉 ──
    paths = list_qingrex()
    print(f"QingRex 去广告 modules: {len(paths)}")
    q_sources: list[tuple[str, str]] = []
    for rel in paths:
        url = QINGREX_RAW + quote(rel, safe="/")
        name = rel.split("/")[-1]
        print(f"module {name}")
        try:
            raw = fetch(url)
        except Exception as exc:
            print(f"  ! fail {rel}: {exc}")
            STATS["qingrex_fail"].append(f"{rel}: {exc}")
            continue
        dest = MOD_Q / name
        dest.write_bytes(raw)
        sha_lines.append(f"{hashlib.sha256(raw).hexdigest()}  modules/qingrex/{name}")
        text = rewrite_scripts(raw.decode("utf-8", errors="replace"), script_cache)
        q_sources.append((f"qingrex/{name}", text))
        STATS["qingrex_ok"].append(name)

    if not q_sources:
        print("FATAL: no QingRex modules", file=sys.stderr)
        sys.exit(1)

    base = merge_modules(
        q_sources,
        title="去广告合集",
        desc="可莉原样 + 奶思差集 + 墨鱼开屏",
        notes=[
            "# 1/3 QingRex 可莉原样拼合",
            f"# qingrex_modules={len(q_sources)}",
        ],
    )
    have = collect_keys(base)
    print(f"after 可莉 keys={len(have)}")

    # ── 2) 奶思差集 ──
    print("fetch fmz200 blockAds")
    fmz_raw = fetch(FMZ_BLOCKADS)
    (MOD_F / "blockAds.module").write_bytes(fmz_raw)
    sha_lines.append(f"{hashlib.sha256(fmz_raw).hexdigest()}  modules/fmz200/blockAds.module")
    fmz_text = rewrite_scripts(fmz_raw.decode("utf-8", errors="replace"), script_cache)
    gaps = gap_lines(fmz_text, have)
    STATS["fmz_gaps"] = {k: len(v) for k, v in gaps.items()}
    print("fmz gaps:", STATS["fmz_gaps"])

    gap_mod = ""
    all_sources = list(q_sources)
    if any(gaps.values()):
        gl = ["#!name=fmz200-gaps", "#!desc=奶思差集", ""]
        for sec, lines in gaps.items():
            if not lines:
                continue
            gl.append(f"[{sec}]")
            gl.append("# >>> fmz200-blockAds gaps")
            gl.extend(lines)
            gl.append("")
        gap_mod = "\n".join(gl)
        (MOD_F / "blockAds-gaps.module").write_text(gap_mod, encoding="utf-8")
        all_sources.append(("fmz200-gaps", gap_mod))
        have = collect_keys(merge_modules(all_sources, title="t", desc="t", notes=[]))

    # ── 3) 墨鱼开屏（与去广告同一合集）──
    splash_mods: list[tuple[str, str]] = []
    for fname, url in SPLASH_PRIMARY:
        print(f"splash {fname}")
        try:
            raw = fetch(url)
        except Exception as exc:
            print(f"  ! {fname}: {exc}")
            continue
        (MOD_M / fname).write_bytes(raw)
        sha_lines.append(f"{hashlib.sha256(raw).hexdigest()}  modules/moyu/{fname}")
        text = rewrite_scripts(raw.decode("utf-8", errors="replace"), script_cache)
        secs = qx_to_surge(text)
        mod = sections_to_module(secs, name=f"moyu-{fname}", desc="墨鱼开屏")
        (MOD_M / (fname + ".surge.module")).write_text(mod, encoding="utf-8")
        sg = gap_lines(mod, have)
        if any(sg.values()):
            STATS["splash_gaps"][fname] = {k: len(v) for k, v in sg.items() if v}
            bl = ["#!name=splash-gaps", ""]
            for sec, lines in sg.items():
                if not lines:
                    continue
                bl.append(f"[{sec}]")
                bl.append(f"# >>> moyu/{fname} gaps")
                bl.extend(lines)
                bl.append("")
            piece = "\n".join(bl)
            splash_mods.append((f"moyu/{fname}", piece))
            have |= collect_keys(piece)
            print(f"  gaps: {STATS['splash_gaps'][fname]}")
        else:
            print(f"  no gaps")

    all_sources.extend(splash_mods)
    final = merge_modules(
        all_sources,
        title="去广告合集",
        desc="可莉原样 + 奶思差集 + 墨鱼开屏",
        notes=[
            "# PIPELINE: 可莉1:1 → 奶思差集 → 墨鱼开屏差集（同一合集）",
            f"# qingrex_modules={len(q_sources)}",
            f"# fmz200_gap_lines={STATS['fmz_gaps']}",
            f"# splash_gap_files={list(STATS['splash_gaps'])}",
            "# tree: Adblock/{js,modules/{qingrex,fmz200,moyu}}",
            "# 无分流/解锁；无 heat/NB 补丁",
        ],
    )
    OUT.write_text(final, encoding="utf-8")
    print(f"wrote {OUT} ({len(final)} chars)")

    SHA_FILE.write_text("\n".join(sha_lines) + "\n", encoding="utf-8")
    (ADBLOCK / "README.md").write_text(
        "\n".join(
            [
                "# Adblock — 去广告（本分支正式树）",
                "",
                "| 路径 | 内容 |",
                "|------|------|",
                "| `js/` | 自托管脚本 |",
                "| `modules/qingrex/` | 可莉单模块原样 |",
                "| `modules/fmz200/` | 奶思原样 + 差集 |",
                "| `modules/moyu/` | 墨鱼开屏原样 |",
                "| `adblock-collection.module` | 大合集（可莉→奶思差集→开屏） |",
                "| `UPSTREAM.md` | 上游合并明细 |",
                "",
                "订阅：",
                "",
                "```",
                f"{GITHUB_RAW}/Adblock/adblock-collection.module",
                "```",
                "",
                "重建：`python3 scripts/build-adblock-formal.py`",
                "",
                "与 `sync` 日更无关；分流 / 解锁下一批再做。",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (MOD_Q / "README.md").write_text(
        "# modules/qingrex\n\n来源 QingRex/LoonKissSurge `Surge/*去广告.sgmodule`，字节原样。\n",
        encoding="utf-8",
    )
    (MOD_F / "README.md").write_text(
        "# modules/fmz200\n\n`blockAds.module` 原样；`blockAds-gaps.module` 为相对可莉的差集。\n",
        encoding="utf-8",
    )
    (MOD_M / "README.md").write_text(
        "# modules/moyu\n\n墨鱼去开屏 StartUpAds / FakeiOSAds 原样 + `.surge.module` 转换件。\n",
        encoding="utf-8",
    )
    (JS / "README.md").write_text(
        "# js\n\n合集引用的脚本镜像，按上游域名分子目录。构建时 URL 改指本分支 raw。\n",
        encoding="utf-8",
    )

    write_report()
    print(
        f"done qingrex={len(q_sources)} js_ok={len(STATS['scripts_ok'])} "
        f"js_fail={len(STATS['scripts_fail'])} fmz={STATS['fmz_gaps']} splash={STATS['splash_gaps']}"
    )


if __name__ == "__main__":
    main()
