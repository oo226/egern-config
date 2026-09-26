#!/usr/bin/env python3
"""Yuanban/ — 拼音目录：作者原样 + 单件备份 + 四分合集。

目录（全部在 Yuanban 下）::

  Yuanban/
    zuozhe/<作者拼音>/{fenliu,mokuai,js}/   # 原作者照搬，字节不改
    danxiang/{fenliu,mokuai,js}/            # 单件汇总备份（文件名带作者前缀）
    heji/
      quguanggao.module   # 去广告
      qukaiping.module    # 去开屏
      jiesuo.module       # 解锁增强
      zhuacan.module      # 抓参
      UPSTREAM.md

合集规则：
  - 不改作者规则正文；仅 script-path URL 改指本仓自托管 js
  - Fan.a.tail 风格：按 App/模块分段注释写清楚
  - 去广告合集最上方强制：广告平台拦截器 → 可莉广告过滤器（基础、最先生效）
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import ssl
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
YUAN = ROOT / "Yuanban"
ZUOZHE = YUAN / "zuozhe"
DAN = YUAN / "danxiang"
HEJI = YUAN / "heji"

BRANCH = (
    os.environ.get("ADBLOCK_BRANCH")
    or os.environ.get("GITHUB_REF_NAME")
    or "cursor/adblock-formal-f611"
)
RAW = f"https://raw.githubusercontent.com/oo226/egern-config/refs/heads/{BRANCH}"

CTX = ssl.create_default_context()
UA = {"User-Agent": "egern-yuanban/1.0"}

QINGREX_API = "https://api.github.com/repos/QingRex/LoonKissSurge/git/trees/main?recursive=1"
QINGREX_RAW = "https://raw.githubusercontent.com/QingRex/LoonKissSurge/main/"

# 去广告基础：必须置顶（广告平台拦截器说明里写了始终排顶部）
KELI_FOUNDATION = (
    "广告平台拦截器.sgmodule",
    "可莉广告过滤器.sgmodule",
)

UNLOCK_NAME_KW = (
    "解锁", "HTTPDNS", "httpdns", "外链", "Spotify", "TikTok", "Fileball",
    "DNS防泄露", "Google搜索重定向", "Google重定向", "网盘挂载", "快捷搜索",
    "拦截HTTPDNS", "歌词增强", "歌词翻译", "TestFlight", "去水印", "翻译",
    "比价", "1.1.1.1", "IPA", "VVebo", "自动加入TF",
)
SIGNIN_KW = ("签到", "每日签到")

SCRIPT_URL_RE = re.compile(
    r"(https?://[^\s,\"']+\.(?:js|mjs)(?:\?[^\s,\"']*)?)",
    re.IGNORECASE,
)

STATS: dict = {
    "zuozhe": {},
    "heji": {},
    "js_ok": 0,
    "js_fail": [],
}


def encode_url(url: str) -> str:
    p = urlparse(url)
    path = quote(unquote(p.path), safe="/:@!$&'()*+,;=-._~")
    q = quote(unquote(p.query), safe="=&%:@!$&'()*+,;=-._~") if p.query else ""
    return p._replace(path=path, query=q).geturl()


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
        raise ValueError(f"HTML {url}")
    return data


def ensure_author(pinyin: str) -> dict[str, Path]:
    base = ZUOZHE / pinyin
    paths = {
        "fenliu": base / "fenliu",
        "mokuai": base / "mokuai",
        "js": base / "js",
    }
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)
    STATS["zuozhe"].setdefault(pinyin, {"mokuai": 0, "js": 0, "fenliu": 0})
    return paths


def save_bytes(dest: Path, data: bytes, *, author: str, kind: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    STATS["zuozhe"][author][kind] = STATS["zuozhe"][author].get(kind, 0) + 1


def mirror_js(url: str, author: str, cache: dict[str, str]) -> str:
    """Download script into zuozhe/<author>/js/... ; return self-host URL for heji rewrite."""
    if url in cache:
        return cache[url]
    # 解锁合集用 Eevee；Crack 不进自托管
    if "spotify.crack" in url.lower() or "/crack" in url.lower():
        cache[url] = url
        return url
    u = urlparse(url)
    host = u.netloc.replace(":", "_")
    path = unquote(u.path).lstrip("/") or "index.js"
    if u.query:
        qh = hashlib.sha1(u.query.encode()).hexdigest()[:8]
        p = Path(path)
        path = str(p.with_name(p.stem + f"_{qh}" + p.suffix))
    dest = ZUOZHE / author / "js" / host / path
    if not dest.is_file():
        try:
            data = fetch(url)
            save_bytes(dest, data, author=author, kind="js")
            STATS["js_ok"] += 1
            print(f"  js/{author} ← {url}")
        except Exception as exc:
            STATS["js_fail"].append(f"{url} ({exc})")
            print(f"  ! js fail {url}: {exc}")
            cache[url] = url
            return url
    else:
        STATS["js_ok"] += 1
    rel = dest.relative_to(ROOT).as_posix()
    local = f"{RAW}/{rel}"
    cache[url] = local
    return local


def rewrite_js_urls(text: str, author: str, cache: dict[str, str]) -> str:
    return SCRIPT_URL_RE.sub(lambda m: mirror_js(m.group(1), author, cache), text)


def strip_module_header(text: str) -> tuple[str, str]:
    """Return (title_from_name, body_from_first_section)."""
    lines = text.splitlines()
    title = ""
    body_start = 0
    for i, line in enumerate(lines):
        if line.startswith("#!name="):
            title = line[7:].strip()
        if line.startswith("[") and line.endswith("]"):
            body_start = i
            break
    else:
        return title, text
    return title, "\n".join(lines[body_start:])


def parse_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current = None
    started = False
    for line in text.splitlines():
        if line.startswith("[") and line.endswith("]"):
            started = True
            current = line[1:-1]
            sections.setdefault(current, [])
            continue
        if started and current is not None:
            sections[current].append(line)
    return sections


def qx_conf_to_surge_body(text: str) -> str:
    """Format-only QX conf → Surge sections (patterns unchanged)."""
    rules, rewrites, scripts, mitm = [], [], [], []
    script_i = 0
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith(";") or s.startswith("//"):
            continue
        low = s.lower()
        if low.startswith("hostname"):
            rhs = s.split("=", 1)[1].strip() if "=" in s else s.split(None, 1)[-1]
            if rhs:
                mitm.append("hostname = %APPEND% " + rhs)
            continue
        if low.startswith("host-suffix") or low.startswith("host-keyword") or low.startswith("host,"):
            parts = [p.strip() for p in s.split(",")]
            if len(parts) >= 2:
                kind = (
                    "DOMAIN-SUFFIX"
                    if low.startswith("host-suffix")
                    else ("DOMAIN-KEYWORD" if low.startswith("host-keyword") else "DOMAIN")
                )
                rules.append(f"{kind},{parts[1]},REJECT")
            continue
        if " url reject" in s or " url reject-" in s:
            pat, rest = s.split(" url ", 1)
            kind = rest.strip().split()[0]
            if kind not in {"reject", "reject-200", "reject-img", "reject-dict", "reject-array"}:
                kind = "reject-200"
            rewrites.append(f"{pat.strip()} - {kind}")
            continue
        if " url script-" in s:
            m = re.match(r"^(\S+)\s+url\s+(script-[\w-]+)\s+(\S+)", s)
            if m:
                pat, stype, surl = m.group(1), m.group(2), m.group(3)
                surge_type = "http-response" if "response" in stype else "http-request"
                req_body = "true" if ("body" in stype or "analyze" in stype) else "false"
                script_i += 1
                scripts.append(
                    f"moyu-{script_i} = type={surge_type},pattern={pat},"
                    f"script-path={surl},requires-body={req_body},timeout=60"
                )
    out = []
    if rules:
        out += ["[Rule]", *rules, ""]
    if rewrites:
        out += ["[URL Rewrite]", *rewrites, ""]
    if scripts:
        out += ["[Script]", *scripts, ""]
    if mitm:
        out += ["[MITM]", *mitm, ""]
    return "\n".join(out)


def merge_section_bags(
    bags: list[tuple[str, dict[str, list[str]]]],
    *,
    name: str,
    desc: str,
    notes: list[str],
) -> str:
    """Merge section bags; keep every author line; label with Fan.a.tail-style banners."""
    order = [
        "General", "Rule", "URL Rewrite", "Header Rewrite", "Body Rewrite",
        "Map Local", "Script", "MITM",
    ]
    for _, sec in bags:
        for k in sec:
            if k not in order:
                order.append(k)

    out = [
        f"#!name={name}",
        f"#!desc={desc}",
        f"# built_at={datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ')}",
        f"# branch={BRANCH}",
        "# 作者规则正文不改；仅 script-path 改指 Yuanban/zuozhe/*/js 自托管",
        *notes,
        "",
    ]
    for section in order:
        pieces = [(label, sec[section]) for label, sec in bags if sec.get(section)]
        if not pieces:
            continue
        out.append(f"[{section}]")
        if section == "MITM":
            hosts: list[str] = []
            for _, lines in pieces:
                for line in lines:
                    s = line.strip()
                    if not s or s.startswith("#"):
                        continue
                    if "hostname" in s.lower() and "=" in s:
                        rhs = re.sub(r"^%APPEND%\s*", "", s.split("=", 1)[1].strip(), flags=re.I)
                        hosts.extend(x.strip() for x in rhs.split(",") if x.strip())
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
                if len(chunk) >= 40:
                    out.append("hostname = %APPEND% " + ", ".join(chunk))
                    chunk = []
            if chunk:
                out.append("hostname = %APPEND% " + ", ".join(chunk))
            out.append("")
            continue

        # 基础·置顶：广告平台拦截器 → 可莉广告过滤器 → 其余
        def _piece_rank(label: str) -> tuple[int, str]:
            if "广告平台拦截器" in label and "基础·置顶" in label:
                return (0, label)
            if "可莉广告过滤器" in label and "基础·置顶" in label:
                return (1, label)
            if "基础·置顶" in label:
                return (2, label)
            return (3, label)

        pieces.sort(key=lambda x: _piece_rank(x[0]))
        for label, lines in pieces:
            out.append("")
            out.append("# " + "- " * 24)
            out.append(f"# {label}")
            out.append("# " + "- " * 24)
            # drop skip-proxy knobs from General in heji
            if section == "General":
                for line in lines:
                    key = line.split("=", 1)[0].strip().lower() if "=" in line else ""
                    if key in {
                        "skip-proxy", "always-real-ip", "hide-vpn-icon",
                        "use-local-host-item-for-proxy",
                        "encrypted-dns-follow-outbound-mode",
                    }:
                        continue
                    out.append(line)
            else:
                out.extend(lines)
        out.append("")
    return "\n".join(out).rstrip() + "\n"


# ── mirror authors ──────────────────────────────────────────────

def mirror_keli(cache: dict[str, str]) -> dict[str, Path]:
    """可莉：全部 Surge 根 sgmodule 原样 → mokuai；脚本进 js。"""
    paths = ensure_author("keli")
    tree = json.loads(fetch(QINGREX_API).decode())["tree"]
    mods = []
    for t in tree:
        if t.get("type") != "blob":
            continue
        p = t["path"]
        if not (p.startswith("Surge/") and p.count("/") == 1 and p.endswith(".sgmodule")):
            continue
        if p.startswith("Surge/Beta/"):
            continue
        mods.append(p)
    mods.sort()
    print(f"keli modules: {len(mods)}")
    for rel in mods:
        name = rel.split("/")[-1]
        try:
            raw = fetch(QINGREX_RAW + quote(rel, safe="/"))
        except Exception as exc:
            print(f"  ! {name}: {exc}")
            continue
        dest = paths["mokuai"] / name
        save_bytes(dest, raw, author="keli", kind="mokuai")
        # still harvest js for self-host (does not modify the saved original)
        rewrite_js_urls(raw.decode("utf-8", errors="replace"), "keli", cache)
        print(f"  mokuai {name}")
    (paths["mokuai"] / "README.md").write_text(
        "可莉 QingRex/LoonKissSurge — Surge 根目录模块原样（含广告平台拦截器 / 可莉广告过滤器）。\n",
        encoding="utf-8",
    )
    return paths


def mirror_url_module(author: str, url: str, filename: str, cache: dict[str, str]) -> Path | None:
    paths = ensure_author(author)
    try:
        raw = fetch(url)
    except Exception as exc:
        print(f"  ! {author}/{filename}: {exc}")
        return None
    dest = paths["mokuai"] / filename
    save_bytes(dest, raw, author=author, kind="mokuai")
    rewrite_js_urls(raw.decode("utf-8", errors="replace"), author, cache)
    print(f"  {author}/mokuai/{filename}")
    return dest


def mirror_url_fenliu(author: str, url: str, filename: str) -> Path | None:
    paths = ensure_author(author)
    try:
        raw = fetch(url)
    except Exception as exc:
        print(f"  ! fenliu {author}/{filename}: {exc}")
        return None
    dest = paths["fenliu"] / filename
    save_bytes(dest, raw, author=author, kind="fenliu")
    print(f"  {author}/fenliu/{filename}")
    return dest


def mirror_local_module(author: str, src: Path, filename: str | None = None) -> Path | None:
    if not src.is_file():
        return None
    paths = ensure_author(author)
    name = filename or src.name
    dest = paths["mokuai"] / name
    save_bytes(dest, src.read_bytes(), author=author, kind="mokuai")
    return dest


def build_danxiang() -> None:
    """Flatten copies with author prefix — 以备不时之需."""
    for kind in ("fenliu", "mokuai", "js"):
        (DAN / kind).mkdir(parents=True, exist_ok=True)
    for author_dir in sorted(ZUOZHE.iterdir()):
        if not author_dir.is_dir():
            continue
        author = author_dir.name
        for kind in ("fenliu", "mokuai"):
            src_dir = author_dir / kind
            if not src_dir.is_dir():
                continue
            for f in src_dir.iterdir():
                if f.is_file() and f.name != "README.md":
                    dest = DAN / kind / f"{author}__{f.name}"
                    shutil.copy2(f, dest)
        js_dir = author_dir / "js"
        if js_dir.is_dir():
            for f in js_dir.rglob("*"):
                if f.is_file() and f.name != "README.md":
                    rel = f.relative_to(js_dir).as_posix().replace("/", "__")
                    dest = DAN / "js" / f"{author}__{rel}"
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, dest)
    (DAN / "README.md").write_text(
        "单件备份：从 zuozhe 汇总，文件名 `作者__原名`。原样，不改内容。\n",
        encoding="utf-8",
    )


# ── heji builders ───────────────────────────────────────────────

def heji_quguanggao(cache: dict[str, str]) -> None:
    """去广告：基础二件置顶 → 可莉全部*去广告 → 奶思 blockAds 整块。"""
    keli_m = ZUOZHE / "keli" / "mokuai"
    bags: list[tuple[str, dict[str, list[str]]]] = []

    # 1) foundation first
    for fname in KELI_FOUNDATION:
        path = keli_m / fname
        if not path.is_file():
            print(f"WARN missing foundation {fname}")
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        rewritten = rewrite_js_urls(raw, "keli", cache)
        title, _ = strip_module_header(raw)
        label = f"可莉 · {title or fname} 【基础·置顶】"
        bags.append((label, parse_sections(rewritten)))

    # 2) all 去广告 per-app
    for path in sorted(keli_m.glob("*去广告.sgmodule")):
        raw = path.read_text(encoding="utf-8", errors="replace")
        rewritten = rewrite_js_urls(raw, "keli", cache)
        title, _ = strip_module_header(raw)
        app = path.name.replace("去广告.sgmodule", "")
        label = f"可莉 · {app}去广告"
        if title and title != path.stem:
            label = f"可莉 · {title}（{app}）"
        bags.append((label, parse_sections(rewritten)))

    # 3) 奶思 blockAds 整模块（不拆不改）
    naisi = ZUOZHE / "naisi" / "mokuai" / "blockAds.module"
    if naisi.is_file():
        raw = naisi.read_text(encoding="utf-8", errors="replace")
        rewritten = rewrite_js_urls(raw, "naisi", cache)
        bags.append(("奶思 · blockAds 整模块", parse_sections(rewritten)))

    text = merge_section_bags(
        bags,
        name="去广告合集",
        desc="可莉基础置顶 + 可莉逐App去广告 + 奶思blockAds（作者原文，URL自托管）",
        notes=[
            "# 合集类型: 去广告",
            "# 置顶基础: 1)广告平台拦截器 2)可莉广告过滤器 —— 须最先生效",
            "# 然后: 可莉各 App「××去广告」原样分段",
            "# 然后: 奶思 blockAds.module 整块",
            "# 不含开屏（见 heji/qukaiping.module）",
        ],
    )
    (HEJI / "quguanggao.module").write_text(text, encoding="utf-8")
    STATS["heji"]["quguanggao"] = len(bags)
    print(f"heji quguanggao bags={len(bags)} chars={len(text)}")


def heji_qukaiping(cache: dict[str, str]) -> None:
    bags: list[tuple[str, dict[str, list[str]]]] = []
    moyu_m = ZUOZHE / "moyu" / "mokuai"
    for fname, label in (
        ("StartUpAds.conf", "墨鱼 · 去开屏 StartUpAds"),
        ("FakeiOSAds.conf", "墨鱼 · FakeiOSAds"),
    ):
        path = moyu_m / fname
        if not path.is_file():
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        # harvest js from original QX urls first
        rewrite_js_urls(raw, "moyu", cache)
        surge_body = qx_conf_to_surge_body(raw)
        surge_body = rewrite_js_urls(surge_body, "moyu", cache)
        bags.append((label, parse_sections(surge_body)))

    # 可莉里带开屏语义的个别模块也可加：当前开屏主源是墨鱼
    text = merge_section_bags(
        bags,
        name="去开屏合集",
        desc="墨鱼 StartUpAds / FakeiOSAds（QX→Surge 仅格式，规则原文）",
        notes=[
            "# 合集类型: 去开屏",
            "# 主源: 墨鱼 ddgksf2013 StartUpAds.conf + FakeiOSAds.conf",
            "# 与去广告合集分开订阅，互不掺和",
        ],
    )
    (HEJI / "qukaiping.module").write_text(text, encoding="utf-8")
    STATS["heji"]["qukaiping"] = len(bags)
    print(f"heji qukaiping bags={len(bags)}")


def classify_keli_unlock(name: str) -> bool:
    if name in KELI_FOUNDATION:
        return False  # 去广告基础，不进解锁
    if "去广告" in name:
        return False
    if any(k in name for k in SIGNIN_KW):
        return False
    return any(k.lower() in name.lower() for k in UNLOCK_NAME_KW)


def heji_jiesuo(cache: dict[str, str]) -> None:
    bags: list[tuple[str, dict[str, list[str]]]] = []
    keli_m = ZUOZHE / "keli" / "mokuai"
    for path in sorted(keli_m.glob("*.sgmodule")):
        if not classify_keli_unlock(path.name):
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        rewritten = rewrite_js_urls(raw, "keli", cache)
        title, _ = strip_module_header(raw)
        bags.append((f"可莉 · {title or path.stem}", parse_sections(rewritten)))

    extras = [
        ("iewha", "Unlock.sgmodule", "iEwha · Unlock"),
        ("iewha", "Script.sgmodule", "iEwha · Script"),
        ("chxm", "Collections.sgmodule", "chxm1023 · Collections 解锁"),
        ("miranquil", "qq-c-pc-page.sgmodule", "miranquil · QQ解锁"),
        ("local", "spotify-unlock.sgmodule", "本仓 · Spotify Eevee VIP"),
        ("local", "patches-unlock.sgmodule", "本仓 · 屏蔽更新/P12 等"),
        ("local", "patches-alicloud.sgmodule", "本仓 · 阿里云盘倍速"),
        ("weigiegie", "weigiegie-unlock.sgmodule", "WeiGiegie · 解锁合集"),
        ("liulong", "liul0ng-unlock.sgmodule", "liul0ng · 解锁合集"),
        ("yu9191", "yu9191-rewrite-unlock.sgmodule", "Yu9191 · Rewrite 解锁"),
        ("yu9191", "yu9191-ShortcutStudio.sgmodule", "Yu9191 · ShortcutStudio"),
        # 奶思 unlock-extra 含 Spotify Crack，解锁合集不用；原件仍在 zuozhe/naisi 备份
    ]
    for author, fname, label in extras:
        path = ZUOZHE / author / "mokuai" / fname
        if not path.is_file():
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        rewritten = rewrite_js_urls(raw, author, cache)
        bags.append((label, parse_sections(rewritten)))

    text = merge_section_bags(
        bags,
        name="解锁增强合集",
        desc="可莉解锁相关 + iEwha/chxm/奶思/WeiGiegie/…（作者原文，URL自托管）",
        notes=[
            "# 合集类型: 解锁增强",
            "# 分段注释标明每个作者/模块用途",
            "# Spotify 用 Eevee（spotify-unlock），不含 Crack",
        ],
    )
    (HEJI / "jiesuo.module").write_text(text, encoding="utf-8")
    STATS["heji"]["jiesuo"] = len(bags)
    print(f"heji jiesuo bags={len(bags)}")


def heji_zhuacan(cache: dict[str, str]) -> None:
    bags: list[tuple[str, dict[str, list[str]]]] = []
    items = [
        ("naisi", "cookies.module", "奶思 · cookies 抓参"),
        ("yuheng", "qdreader-cookie-extra.sgmodule", "Yuheng · 起点抓参"),
    ]
    for author, fname, label in items:
        path = ZUOZHE / author / "mokuai" / fname
        if not path.is_file():
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        rewritten = rewrite_js_urls(raw, author, cache)
        bags.append((label, parse_sections(rewritten)))

    text = merge_section_bags(
        bags,
        name="抓参合集",
        desc="签到 Cookie/Token 抓取（按需开，抓完关掉）",
        notes=[
            "# 合集类型: 抓参",
            "# 默认建议关闭；抓完关掉省电",
        ],
    )
    (HEJI / "zhuacan.module").write_text(text, encoding="utf-8")
    STATS["heji"]["zhuacan"] = len(bags)
    print(f"heji zhuacan bags={len(bags)}")


def write_docs() -> None:
    (YUAN / "README.md").write_text(
        "\n".join(
            [
                "# Yuanban — 原版资源根（拼音目录）",
                "",
                "全部去广告 / 开屏 / 解锁 / 抓参 / 分流原材料与合集都在这一个文件夹下。",
                "",
                "## 结构",
                "",
                "```",
                "Yuanban/",
                "  zuozhe/                 # 按作者",
                "    keli/                 # 可莉",
                "      fenliu/  mokuai/  js/",
                "    naisi/                # 奶思",
                "    moyu/                 # 墨鱼",
                "    …",
                "  danxiang/               # 单件备份（作者__文件名）",
                "    fenliu/  mokuai/  js/",
                "  heji/                   # 合集（四分）",
                "    quguanggao.module     # 去广告",
                "    qukaiping.module      # 去开屏",
                "    jiesuo.module         # 解锁增强",
                "    zhuacan.module        # 抓参",
                "```",
                "",
                "## 原则",
                "",
                "- `zuozhe` / `danxiang`：**原作者照搬**，文件字节不改",
                "- `heji`：只拼装 + Fan.a.tail 风格分段注释；**规则正文不改**；script URL 改指本仓 `zuozhe/*/js`",
                "- 去广告合集最上方：`广告平台拦截器` → `可莉广告过滤器`（基础，最先生效）",
                "",
                "## 订阅",
                "",
                "```",
                f"{RAW}/Yuanban/heji/quguanggao.module",
                f"{RAW}/Yuanban/heji/qukaiping.module",
                f"{RAW}/Yuanban/heji/jiesuo.module",
                f"{RAW}/Yuanban/heji/zhuacan.module",
                "```",
                "",
                "重建：`python3 scripts/build-yuanban.py`",
                "",
                "与 sync 日更的 `Modules/` `Routing/` 并行，不覆盖。",
                "",
            ]
        ),
        encoding="utf-8",
    )
    lines = [
        "# 合集上游说明",
        "",
        f"构建：{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC",
        f"分支：`{BRANCH}`",
        "",
        "## zuozhe 作者统计",
        "",
    ]
    for author, st in sorted(STATS["zuozhe"].items()):
        lines.append(f"- **{author}**: mokuai={st.get('mokuai',0)} js={st.get('js',0)} fenliu={st.get('fenliu',0)}")
    lines += [
        "",
        "## heji 分段袋数",
        "",
        f"`{STATS['heji']}`",
        "",
        f"脚本镜像成功约 {STATS['js_ok']}，失败 {len(STATS['js_fail'])}（多为 kelee.one 403，合集保留上游 URL）",
        "",
        "## 去广告置顶",
        "",
        "1. `zuozhe/keli/mokuai/广告平台拦截器.sgmodule` — 所有去广告插件的基础，须排顶部",
        "2. `zuozhe/keli/mokuai/可莉广告过滤器.sgmodule`",
        "3. 可莉各 App `*去广告.sgmodule`",
        "4. 奶思 `blockAds.module` 整块",
        "",
    ]
    (HEJI / "UPSTREAM.md").write_text("\n".join(lines), encoding="utf-8")
    (ZUOZHE / "README.md").write_text(
        "作者拼音目录。每人下有 fenliu / mokuai / js。内容与上游字节一致。\n\n"
        "拼音：keli可莉 naisi奶思 moyu墨鱼 iewha chxm weigiegie liulong yu9191 "
        "repcz sukka vpsdance rabbit yuheng local miranquil\n",
        encoding="utf-8",
    )


def main() -> None:
    if YUAN.exists():
        # clean rebuild of generated trees
        shutil.rmtree(YUAN)
    for d in (ZUOZHE, DAN / "fenliu", DAN / "mokuai", DAN / "js", HEJI):
        d.mkdir(parents=True, exist_ok=True)

    cache: dict[str, str] = {}

    print("=== zuozhe/keli ===")
    mirror_keli(cache)

    print("=== zuozhe/naisi ===")
    mirror_url_module(
        "naisi",
        "https://raw.githubusercontent.com/fmz200/wool_scripts/main/Surge/module/blockAds.module",
        "blockAds.module",
        cache,
    )
    mirror_url_module(
        "naisi",
        "https://raw.githubusercontent.com/fmz200/wool_scripts/main/Surge/module/cookies.module",
        "cookies.module",
        cache,
    )
    mirror_local_module("naisi", ROOT / "Modules" / "fmz200-unlock-extra.sgmodule")

    print("=== zuozhe/moyu ===")
    for fname, url in (
        ("StartUpAds.conf", "https://ddgksf2013.top/rewrite/StartUpAds.conf"),
        (
            "FakeiOSAds.conf",
            "https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/AdBlock/FakeiOSAds.conf",
        ),
    ):
        try:
            raw = fetch(url)
            paths = ensure_author("moyu")
            save_bytes(paths["mokuai"] / fname, raw, author="moyu", kind="mokuai")
            rewrite_js_urls(raw.decode("utf-8", errors="replace"), "moyu", cache)
            print(f"  moyu/mokuai/{fname}")
        except Exception as exc:
            print(f"  ! moyu {fname}: {exc}")

    print("=== zuozhe remote unlock ===")
    for author, fname, url in (
        ("iewha", "Unlock.sgmodule", "https://raw.githubusercontent.com/iEwha/Profiles/master/Surge/Unlock.sgmodule"),
        ("iewha", "Script.sgmodule", "https://raw.githubusercontent.com/iEwha/Profiles/master/Surge/Script.sgmodule"),
        ("chxm", "Collections.sgmodule", "https://raw.githubusercontent.com/chxm1023/Script_X/main/Collections.sgmodule"),
        (
            "miranquil",
            "qq-c-pc-page.sgmodule",
            "https://raw.githubusercontent.com/miranquil/surge-scripts/main/tencent/c-pc-page/module.sgmodule",
        ),
    ):
        mirror_url_module(author, url, fname, cache)

    print("=== zuozhe local copies ===")
    for author, src_name in (
        ("local", "spotify-unlock.sgmodule"),
        ("local", "patches-unlock.sgmodule"),
        ("local", "patches-alicloud.sgmodule"),
        ("weigiegie", "weigiegie-unlock.sgmodule"),
        ("liulong", "liul0ng-unlock.sgmodule"),
        ("yu9191", "yu9191-rewrite-unlock.sgmodule"),
        ("yu9191", "yu9191-ShortcutStudio.sgmodule"),
        ("yuheng", "qdreader-cookie-extra.sgmodule"),
    ):
        mirror_local_module(author, ROOT / "Modules" / src_name, src_name)

    print("=== zuozhe fenliu ===")
    repcz = "https://raw.githubusercontent.com/Repcz/Tool/X/Egern/Rules"
    for name in (
        "Reject", "Direct", "WeChat", "Bilibili", "AppleCN",
        "ChinaDomain", "ChinaIP", "ChinaASN", "Lan",
        "AI", "Telegram", "Twitter", "TikTok", "YouTube",
        "Netflix", "Disney", "Spotify", "Emby", "Google",
        "Github", "Microsoft", "AppleServers", "Game", "ProxyGFW", "Proxy",
    ):
        mirror_url_fenliu("repcz", f"{repcz}/{name}.yaml", f"{name}.yaml")
    mirror_url_fenliu("sukka", "https://ruleset.skk.moe/List/domainset/reject.conf", "reject.conf")
    mirror_url_fenliu("sukka", "https://ruleset.skk.moe/List/non_ip/ai.conf", "ai.conf")
    mirror_url_fenliu(
        "vpsdance",
        "https://cdn.jsdelivr.net/gh/VPSDance/ai-proxy-rules@main/rules/egern/all.yaml",
        "all.yaml",
    )

    print("=== danxiang ===")
    build_danxiang()

    print("=== heji ===")
    heji_quguanggao(cache)
    heji_qukaiping(cache)
    heji_jiesuo(cache)
    heji_zhuacan(cache)

    write_docs()
    # drop empty kelee dirs
    for p in YUAN.rglob("*"):
        if p.is_dir() and not any(p.iterdir()):
            try:
                p.rmdir()
            except OSError:
                pass
    print("done", STATS["heji"], "js_ok", STATS["js_ok"], "js_fail", len(STATS["js_fail"]))


if __name__ == "__main__":
    main()
