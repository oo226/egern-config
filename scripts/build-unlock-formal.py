#!/usr/bin/env python3
"""Formal Unlock tree: Unlock/{js,modules} — 可莉解锁底座 → 多源差集。

Layout (本分支；不动 sync 日更):
  Unlock/
    js/
    modules/
      qingrex/
      fmz200/
      iewha/
      chxm1023/
      miranquil/
      weigiegie/
      liul0ng/
      yu9191/
      local/          # spotify Eevee、patches 等
    unlock-collection.module
    UPSTREAM.md
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
UNLOCK = ROOT / "Unlock"
JS = UNLOCK / "js"
MOD = UNLOCK / "modules"
OUT = UNLOCK / "unlock-collection.module"
REPORT = UNLOCK / "UPSTREAM.md"
SHA_FILE = UNLOCK / "SHA256SUMS"

BRANCH = (
    os.environ.get("ADBLOCK_BRANCH")
    or os.environ.get("GITHUB_REF_NAME")
    or "cursor/adblock-formal-f611"
)
GITHUB_RAW = f"https://raw.githubusercontent.com/oo226/egern-config/refs/heads/{BRANCH}"

CTX = ssl.create_default_context()
UA = {"User-Agent": "egern-config-unlock-formal/1.0"}

QINGREX_API = "https://api.github.com/repos/QingRex/LoonKissSurge/git/trees/main?recursive=1"
QINGREX_RAW = "https://raw.githubusercontent.com/QingRex/LoonKissSurge/main/"

UNLOCK_NAME_KW = (
    "解锁",
    "HTTPDNS",
    "httpdns",
    "外链",
    "Spotify",
    "TikTok",
    "Fileball",
    "DNS防泄露",
    "Google搜索重定向",
    "Google重定向",
    "网盘挂载",
    "快捷搜索",
    "拦截HTTPDNS",
    "歌词增强",
    "歌词翻译",
    "TestFlight",
    "TF",
    "去水印",
    "翻译",
    "比价",
    "广告过滤器",
    "广告平台",
    "1.1.1.1",
    "IPA",
    "VVebo",
)

SIGNIN_KW = ("签到", "每日签到", "signin", "checkin")

# Remote modules to mirror (after 可莉)
REMOTE_MODULES: list[tuple[str, str, str]] = [
    # folder, filename, url
    (
        "iewha",
        "Unlock.sgmodule",
        "https://raw.githubusercontent.com/iEwha/Profiles/master/Surge/Unlock.sgmodule",
    ),
    (
        "iewha",
        "Script.sgmodule",
        "https://raw.githubusercontent.com/iEwha/Profiles/master/Surge/Script.sgmodule",
    ),
    (
        "chxm1023",
        "Collections.sgmodule",
        "https://raw.githubusercontent.com/chxm1023/Script_X/main/Collections.sgmodule",
    ),
    (
        "miranquil",
        "qq-c-pc-page.sgmodule",
        "https://raw.githubusercontent.com/miranquil/surge-scripts/main/tencent/c-pc-page/module.sgmodule",
    ),
]

# Local repo modules to copy into Unlock/modules/local/
LOCAL_MODULES = (
    "spotify-unlock.sgmodule",
    "patches-unlock.sgmodule",
    "patches-alicloud.sgmodule",
    "yu9191-rewrite-unlock.sgmodule",
    "yu9191-ShortcutStudio.sgmodule",
    "weigiegie-unlock.sgmodule",
    "liul0ng-unlock.sgmodule",
    "fmz200-unlock-extra.sgmodule",
)

GAP_LINE_EXCLUDES = (
    "spotify.crack",
    "spotify.crack.dev",
    "dualsubs.spotify",
    "dualsubsspotify",
    "domain,configuration.apple.com,reject",
    "domain-suffix,wxs.qq.com,reject",
    "domain,wximg.wxs.qq.com,reject",
    "domain,wxsmw.wxs.qq.com,reject",
    "domain,wxa.wxs.qq.com,reject",
)

MITM_EXCLUDES = (
    "*.telegram.org",
    "*.telegram-cdn.org",
    "*.t.me",
    "*.whatsapp.com",
    "*.whatsapp.net",
    "*.wa.me",
)

SCRIPT_URL_RE = re.compile(
    r"(https?://[^\s,\"']+\.(?:js|mjs)(?:\?[^\s,\"']*)?)",
    re.IGNORECASE,
)

STATS: dict = {
    "qingrex": [],
    "qingrex_fail": [],
    "remote_ok": [],
    "remote_fail": [],
    "local_ok": [],
    "scripts_ok": [],
    "scripts_fail": [],
    "gaps": {},
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
        req = urllib.request.Request("https://ghproxy.net/" + url, headers=UA)
        with urllib.request.urlopen(req, context=CTX, timeout=timeout) as resp:
            data = resp.read()
    if data.lstrip()[:20].lower().startswith((b"<!doctype", b"<html")):
        raise ValueError(f"HTML for {url}")
    return data


def script_local_path(url: str) -> Path:
    u = urlparse(url)
    host = u.netloc.replace(":", "_")
    path = unquote(u.path).lstrip("/") or "index.js"
    if u.query:
        qh = hashlib.sha1(u.query.encode()).hexdigest()[:8]
        p = Path(path)
        path = str(p.with_name(p.stem + f"_{qh}" + p.suffix))
    return JS / host / path


def mirror_script(url: str, cache: dict[str, str]) -> str:
    if url in cache:
        return cache[url]
    low = url.lower()
    if any(x in low for x in ("spotify.crack", "dualsubs.spotify")):
        cache[url] = url
        return url
    # already pointing at this branch Unlock/js or Adblock/js
    if "oo226/egern-config" in url and ("/Unlock/js/" in url or "/Adblock/js/" in url):
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
            print(f"  ! js skip: {exc}")
            STATS["scripts_fail"].append(f"{url} ({exc})")
            cache[url] = url
            return url
    else:
        STATS["scripts_ok"].append(url)
    rel = dest.relative_to(ROOT).as_posix()
    local = f"{GITHUB_RAW}/{rel}"
    cache[url] = local
    return local


def rewrite_scripts(text: str, cache: dict[str, str]) -> str:
    return SCRIPT_URL_RE.sub(lambda m: mirror_script(m.group(1), cache), text)


def is_unlock_name(filename: str) -> bool:
    if any(k in filename for k in SIGNIN_KW):
        return False
    return any(k.lower() in filename.lower() for k in UNLOCK_NAME_KW)


def list_qingrex_unlock() -> list[str]:
    tree = json.loads(fetch(QINGREX_API).decode())["tree"]
    out = []
    for t in tree:
        if t.get("type") != "blob":
            continue
        p = t["path"]
        if not p.endswith(".sgmodule"):
            continue
        if not p.startswith("Surge/") or p.startswith("Surge/Beta/") or p.count("/") != 1:
            continue
        if "去广告" in p:
            continue
        name = p.split("/")[-1]
        if is_unlock_name(name):
            out.append(p)
    return sorted(out)


def parse_module(text: str) -> dict[str, list[str]]:
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
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1]
            sections.setdefault(current, [])
            continue
        if current is not None:
            sections[current].append(line)
    return sections


def active(line: str) -> bool:
    s = line.strip()
    return bool(s) and not s.startswith("#") and not s.startswith("#!")


def excluded(line: str) -> bool:
    s = line.lower()
    return any(n in s for n in GAP_LINE_EXCLUDES)


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
        if excluded(line) and active(line):
            continue
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
            rhs = re.sub(r"^%APPEND%\s*", "", s.split("=", 1)[1].strip(), flags=re.I)
            hosts.extend(h.strip() for h in rhs.split(",") if h.strip())
        else:
            hosts.extend(h.strip() for h in s.split(",") if h.strip() and not h.strip().startswith("#"))
    excl = {h.lower() for h in MITM_EXCLUDES}
    seen: set[str] = set()
    ordered: list[str] = []
    for h in hosts:
        k = h.lower()
        if k in excl or k in seen:
            continue
        # prefix match for 149.154.* style
        if any(k.startswith(e.rstrip("*").lower()) for e in MITM_EXCLUDES if e.endswith("*")):
            continue
        seen.add(k)
        ordered.append(h)
    return ordered


def merge_modules(sources: list[tuple[str, str]], *, title: str, desc: str, notes: list[str]) -> str:
    parsed = [(sid, parse_module(text)) for sid, text in sources]
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
    out = [
        f"#!name={title}",
        f"#!desc={desc}",
        "#!category=解锁",
        "#!author=oo226/egern-config (可莉解锁 + 多源差集)",
        f"# built_at={datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ')}",
        f"# branch={BRANCH}",
        *notes,
        "",
    ]
    drop_general = {
        "skip-proxy",
        "always-real-ip",
        "hide-vpn-icon",
        "use-local-host-item-for-proxy",
        "encrypted-dns-follow-outbound-mode",
    }
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
            uniq = []
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
            if section == "General":
                kept = []
                for line in lines:
                    key = line.split("=", 1)[0].strip().lower() if "=" in line else ""
                    if key in drop_general:
                        continue
                    kept.append(line)
                lines = kept
            merged.extend(lines)
            if lines and lines[-1].strip():
                merged.append("")
        out.extend(dedupe(merged, section=section))
        if out[-1].strip():
            out.append("")
    return "\n".join(out).rstrip() + "\n"


def collect_keys(text: str) -> set[str]:
    sec = parse_module(text)
    keys: set[str] = set()
    for name, lines in sec.items():
        if name == "MITM":
            for h in split_mitm(lines):
                keys.add("mitm:" + h.lower())
            continue
        for line in lines:
            if excluded(line):
                continue
            k = script_key(line) if name == "Script" else rule_key(line)
            if k:
                keys.add(f"{name}:{k}")
    return keys


def gap_lines(src_text: str, have: set[str]) -> dict[str, list[str]]:
    sec = parse_module(src_text)
    gaps: dict[str, list[str]] = {}
    for name, lines in sec.items():
        if name == "MITM":
            missing = [h for h in split_mitm(lines) if ("mitm:" + h.lower()) not in have]
            if missing:
                buf, chunk = [], []
                for h in missing:
                    chunk.append(h)
                    if len(chunk) >= 50:
                        buf.append("hostname = %APPEND% " + ", ".join(chunk))
                        chunk = []
                if chunk:
                    buf.append("hostname = %APPEND% " + ", ".join(chunk))
                gaps[name] = buf
            continue
        if name == "General":
            continue
        kept = []
        for line in lines:
            if not active(line) or excluded(line):
                continue
            k = script_key(line) if name == "Script" else rule_key(line)
            if not k or f"{name}:{k}" in have:
                continue
            kept.append(line)
        if kept:
            gaps[name] = kept
    return gaps


def gaps_to_module(sid: str, gaps: dict[str, list[str]]) -> str:
    lines = [f"#!name={sid}-gaps", ""]
    for sec, ls in gaps.items():
        if not ls:
            continue
        lines.append(f"[{sec}]")
        lines.append(f"# >>> {sid} gaps")
        lines.extend(ls)
        lines.append("")
    return "\n".join(lines)


def write_report(qingrex_n: int) -> None:
    lines = [
        "# 解锁合集 — 上游合并说明",
        "",
        f"构建时间（UTC）：{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
        f"分支：`{BRANCH}`",
        "",
        "## 目录",
        "",
        "```",
        "Unlock/",
        "  js/",
        "  modules/{qingrex,fmz200,iewha,chxm1023,miranquil,weigiegie,liul0ng,yu9191,local}/",
        "  unlock-collection.module",
        "  UPSTREAM.md",
        "```",
        "",
        "## 合并顺序",
        "",
        "1. **可莉** QingRex 解锁相关单模块原样拼合（底座）",
        "2. **差集依次**：iEwha → chxm1023 Collections → miranquil → 本地 fmz200/weigiegie/liul0ng/yu9191 → Spotify Eevee → patches",
        "",
        "已剔除：Spotify Crack / DualSubs Spotify、微信 CDN 整域 REJECT、configuration.apple.com REJECT；MITM 不含 TG/WhatsApp。",
        "",
        f"## 1) 可莉 — {qingrex_n} 模块",
        "",
        "- 上游：https://github.com/QingRex/LoonKissSurge",
        "- 目录：`Unlock/modules/qingrex/`",
    ]
    for n in STATS["qingrex"]:
        lines.append(f"- `{n}`")
    lines += [
        "",
        "## 2) 远程差集源",
        "",
    ]
    for x in STATS["remote_ok"]:
        lines.append(f"- OK `{x}`")
    for x in STATS["remote_fail"]:
        lines.append(f"- FAIL `{x}`")
    lines += [
        "",
        "## 3) 本地模块副本",
        "",
    ]
    for x in STATS["local_ok"]:
        lines.append(f"- `{x}`")
    lines += [
        "",
        f"## 差集行数",
        "",
        f"`{STATS['gaps']}`",
        "",
        f"## 脚本",
        "",
        f"- 镜像成功：{len(STATS['scripts_ok'])}",
        f"- 失败：{len(STATS['scripts_fail'])}",
        "",
        "## 订阅",
        "",
        "```",
        f"{GITHUB_RAW}/Unlock/unlock-collection.module",
        "```",
        "",
        "重建：`python3 scripts/build-unlock-formal.py`",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    cache: dict[str, str] = {}
    sha_lines = [f"# Unlock checksums @ {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ')}", ""]
    for d in (JS, MOD):
        d.mkdir(parents=True, exist_ok=True)

    # 1) QingRex unlock modules
    paths = list_qingrex_unlock()
    print(f"QingRex unlock-ish modules: {len(paths)}")
    q_sources: list[tuple[str, str]] = []
    (MOD / "qingrex").mkdir(parents=True, exist_ok=True)
    for rel in paths:
        name = rel.split("/")[-1]
        print(f"qingrex {name}")
        try:
            raw = fetch(QINGREX_RAW + quote(rel, safe="/"))
        except Exception as exc:
            STATS["qingrex_fail"].append(f"{rel}: {exc}")
            continue
        (MOD / "qingrex" / name).write_bytes(raw)
        sha_lines.append(f"{hashlib.sha256(raw).hexdigest()}  modules/qingrex/{name}")
        text = rewrite_scripts(raw.decode("utf-8", errors="replace"), cache)
        q_sources.append((f"qingrex/{name}", text))
        STATS["qingrex"].append(name)

    if not q_sources:
        print("FATAL: no qingrex unlock modules", file=sys.stderr)
        sys.exit(1)

    all_sources = list(q_sources)
    have = collect_keys(merge_modules(all_sources, title="t", desc="t", notes=[]))
    print(f"after 可莉 keys={len(have)}")

    # 2) Remote modules as gaps
    for folder, fname, url in REMOTE_MODULES:
        dest_dir = MOD / folder
        dest_dir.mkdir(parents=True, exist_ok=True)
        print(f"remote {folder}/{fname}")
        try:
            raw = fetch(url)
        except Exception as exc:
            STATS["remote_fail"].append(f"{folder}/{fname}: {exc}")
            print(f"  ! {exc}")
            continue
        (dest_dir / fname).write_bytes(raw)
        sha_lines.append(f"{hashlib.sha256(raw).hexdigest()}  modules/{folder}/{fname}")
        text = rewrite_scripts(raw.decode("utf-8", errors="replace"), cache)
        gaps = gap_lines(text, have)
        STATS["remote_ok"].append(f"{folder}/{fname}")
        if any(gaps.values()):
            STATS["gaps"][f"{folder}/{fname}"] = {k: len(v) for k, v in gaps.items()}
            piece = gaps_to_module(f"{folder}/{fname}", gaps)
            (dest_dir / (fname + ".gaps.module")).write_text(piece, encoding="utf-8")
            all_sources.append((f"{folder}/{fname}-gaps", piece))
            have |= collect_keys(piece)
            print(f"  gaps {STATS['gaps'][f'{folder}/{fname}']}")
        else:
            print("  no gaps")

    # 3) Local modules
    local_dir = MOD / "local"
    local_dir.mkdir(parents=True, exist_ok=True)
    for name in LOCAL_MODULES:
        src = ROOT / "Modules" / name
        if not src.is_file():
            print(f"  skip missing local {name}")
            continue
        raw = src.read_bytes()
        (local_dir / name).write_bytes(raw)
        sha_lines.append(f"{hashlib.sha256(raw).hexdigest()}  modules/local/{name}")
        text = rewrite_scripts(raw.decode("utf-8", errors="replace"), cache)
        # remap Scripts/ paths already on main → keep as-is if exist; also rewrite any remaining remotes
        gaps = gap_lines(text, have)
        STATS["local_ok"].append(name)
        if any(gaps.values()):
            STATS["gaps"][f"local/{name}"] = {k: len(v) for k, v in gaps.items()}
            piece = gaps_to_module(f"local/{name}", gaps)
            (local_dir / (name + ".gaps.module")).write_text(piece, encoding="utf-8")
            all_sources.append((f"local/{name}-gaps", piece))
            have |= collect_keys(piece)
            print(f"local {name} gaps {STATS['gaps'][f'local/{name}']}")
        else:
            print(f"local {name}: no gaps")

    final = merge_modules(
        all_sources,
        title="解锁合集",
        desc="可莉解锁原样 + 多源差集（Spotify Eevee / 屏蔽更新等）",
        notes=[
            "# PIPELINE: 可莉解锁 → iEwha/chxm/miranquil/本地差集",
            f"# qingrex_modules={len(q_sources)}",
            f"# gap_sources={list(STATS['gaps'])}",
            "# tree: Unlock/{js,modules/...}",
            "# 无去广告/分流；sync 日更不动",
        ],
    )
    OUT.write_text(final, encoding="utf-8")
    SHA_FILE.write_text("\n".join(sha_lines) + "\n", encoding="utf-8")
    (UNLOCK / "README.md").write_text(
        "\n".join(
            [
                "# Unlock — 解锁（本分支正式树）",
                "",
                "| 路径 | 内容 |",
                "|------|------|",
                "| `js/` | 自托管脚本 |",
                "| `modules/qingrex/` | 可莉解锁相关原样 |",
                "| `modules/*/` | 其它上游原样 + gaps |",
                "| `unlock-collection.module` | 大合集 |",
                "| `UPSTREAM.md` | 合并明细 |",
                "",
                "```",
                f"{GITHUB_RAW}/Unlock/unlock-collection.module",
                "```",
                "",
                "重建：`python3 scripts/build-unlock-formal.py`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_report(len(q_sources))
    print(f"wrote {OUT} ({len(final)} chars) gaps={STATS['gaps']}")


if __name__ == "__main__":
    main()
