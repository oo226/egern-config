#!/usr/bin/env python3
"""Yuanban/ — 拼音目录：作者原样 + 单件备份 + 四分合集 + 签到文件夹。

目录（全部在 Yuanban 下）::

  Yuanban/
    zuozhe/<作者拼音>/{fenliu,mokuai,js}/   # 原作者照搬，字节不改
    zuozhe/keli/official/                   # QingRex Surge/Official（非签到）
    danxiang/{fenliu,mokuai,js}/            # 单件汇总备份（文件名带作者前缀）
    qiandao/                                # 签到：只放单件，不做合集
      keli/  official/  local/  js/
    qita/                                   # 其他脚本/工具：只放单件，不做合集
      official/  local/  ibl3nd/             # IBL3ND 小组件（单件）
    heji/
      quguanggao.module   # 去广告
      qukaiping.module    # 去开屏
      jiesuo.module       # 解锁增强
      zhuacan.module      # 抓参
      fenliu/             # 分流规则集（单件，非巨型 module）
      UPSTREAM.md

合集规则：
  - 不改作者规则正文；仅 script-path URL 改指本仓自托管 js
  - Fan.a.tail 风格：按 App/模块分段注释写清楚
  - 去广告合集最上方强制：广告平台拦截器 → 可莉广告过滤器（基础、最先生效）
  - 签到 / 其他脚本不做 heji，只进 qiandao/、qita/
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import ssl
import subprocess
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
QIANDAO = YUAN / "qiandao"
QITA = YUAN / "qita"


def _detect_branch() -> str:
    """Prefer current git branch so stale ADBLOCK_BRANCH env cannot poison URLs."""
    override = os.environ.get("ADBLOCK_BRANCH_FORCE")
    if override:
        return override
    try:
        git_b = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if git_b and git_b != "HEAD":
            return git_b
    except Exception:
        pass
    return (
        os.environ.get("ADBLOCK_BRANCH")
        or os.environ.get("GITHUB_REF_NAME")
        or "guize"
    )


BRANCH = _detect_branch()
RAW = f"https://raw.githubusercontent.com/oo226/egern-config/refs/heads/{BRANCH}"
# guize 根目录不保留 Modules/；本仓补丁从 sync 日更拉取
SYNC_RAW = "https://raw.githubusercontent.com/oo226/egern-config/refs/heads/sync"

CTX = ssl.create_default_context()
# Quantumult X UA：墨鱼 ddgksf2013.top 对普通爬虫常回 HTML 首页
UA = {"User-Agent": "Quantumult%20X/1.4.0 (egern-yuanban)"}

QINGREX_API = "https://api.github.com/repos/QingRex/LoonKissSurge/git/trees/main?recursive=1"
QINGREX_RAW = "https://raw.githubusercontent.com/QingRex/LoonKissSurge/main/"
MOYU_REWRITE = "https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/AdBlock/"
MOYU_FUNCTION = "https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/Function/"
MOYU_FOROWNUSE = "https://raw.githubusercontent.com/ddgksf2013/dev/master/ForOwnUse.conf"

# 毒奶 limbopro/Adblock4limbo（网页广告用户脚本）
DUNAI_SGMODULE = (
    "https://raw.githubusercontent.com/limbopro/Adblock4limbo/main/Adblock4limbo.sgmodule"
)

# blackmatrix7 通用广告（规则 + 脚本）
BMJ_ADVERTISING = (
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/"
    "rewrite/Surge/Advertising/Advertising.sgmodule"
)
BMJ_ADVERTISING_SCRIPT = (
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/"
    "rewrite/Surge/AdvertisingScript/AdvertisingScript.sgmodule"
)

IBL3ND_API = "https://api.github.com/repos/IBL3ND/module/git/trees/main?recursive=1"
IBL3ND_RAW = "https://raw.githubusercontent.com/IBL3ND/module/main/"

MOLI_API = "https://api.github.com/repos/Moli-X/Resources/git/trees/main?recursive=1"
MOLI_RAW = "https://raw.githubusercontent.com/Moli-X/Resources/main/"
MOLI_JD_COOKIE = MOLI_RAW + "Surge/Module/JD_Cookie.sgmodule"

NOBYDA_GETCOOKIE = (
    "https://raw.githubusercontent.com/NobyDa/Script/master/Surge/Module/GetCookie.sgmodule"
)

LOYALSOLDIER_RAW = "https://raw.githubusercontent.com/Loyalsoldier/surge-rules/release/"
LOYALSOLDIER_FENLIU = (
    "direct.txt", "proxy.txt", "gfw.txt", "reject.txt", "cncidr.txt",
    "google.txt", "apple.txt", "icloud.txt", "private.txt",
    "telegramcidr.txt", "tld-not-cn.txt", "greatfire.txt",
)

SUKKA_LIST = "https://ruleset.skk.moe/"
SUKKA_FENLIU = (
    ("domainset/reject.conf", "reject.conf"),
    ("domainset/reject_extra.conf", "reject_extra.conf"),
    ("non_ip/ai.conf", "ai.conf"),
    ("non_ip/cdn.conf", "cdn.conf"),
    ("non_ip/download.conf", "download.conf"),
    ("non_ip/stream.conf", "stream.conf"),
    ("non_ip/telegram.conf", "telegram.conf"),
    ("non_ip/apple_services.conf", "apple_services.conf"),
    ("non_ip/apple_cn.conf", "apple_cn.conf"),
    ("non_ip/microsoft.conf", "microsoft.conf"),
    ("ip/china_ip.conf", "china_ip.conf"),
    ("ip/telegram.conf", "telegram_ip.conf"),
)

# blackmatrix7 细分补洞（Repcz/莫离没有或偏薄的）
BMJ_RULE = "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Surge/"
BMJ_FENLIU = (
    "ChinaMax", "OpenAI", "Claude", "Gemini", "Steam", "PayPal",
    "GlobalMedia", "AdvertisingLite", "Cloudflare", "GitHub",
)

# 墨鱼 Function（进 jiesuo）：微信110 / TF / Emby 等
MOYU_FUNCTION_CONFS = (
    ("UnblockURLinWeChat.conf", "微信110外链解锁"),
    ("ForceInstallTF.conf", "Mac M 系列解除 iOS TF 下载限制"),
    ("TFDownload.conf", "国区 TF 下载补丁"),
    ("EmbyPlugin.conf", "Emby 外置播放器"),
    ("UposRedirect.conf", "B站 Upos 重定向"),
    ("Bilibili_CC.conf", "B站繁体 CC 转简体"),
)

# 墨鱼通用去广告（进 quguanggao）；开屏 StartUpAds/FakeiOSAds 另见 qukaiping
# WeChat.conf 上游已划掉仍保留原件；FakeiOSAds 只进开屏合集
MOYU_ADBLOCK_CONFS = (
    "Applet.conf",
    "WeiboAds.conf",
    "YoutubeAds.conf",
    "Ximalaya.conf",
    "KeepAds.conf",
    "AmapAds.conf",
    "NeteaseAds.conf",
    "CainiaoAds.conf",
    "BingSimplify.conf",
    "SmzdmAds.conf",
    "CaiYunAds.conf",
    "TieBaAds.conf",
    "RedditAds.conf",
    "NeteaseMailAds.conf",
    "GoofishAds.conf",
    "QiShuiMusicAds.conf",
    "XiaoYuZhouAds.conf",
    "CheLaiLeAds.conf",
    "MoJiWeatherAds.conf",
    "TaoPiaoPiaoAds.conf",
    "ChinaUnicomAds.conf",
    "BiliBiliComicsAds.conf",
    "WeChat.conf",
)
MOYU_ADBLOCK_LABEL = {
    "Applet.conf": "微信小程序去广告",
    "WeiboAds.conf": "微博/轻享版去广告",
    "YoutubeAds.conf": "油管去广告",
    "Ximalaya.conf": "喜马拉雅去广告",
    "KeepAds.conf": "Keep超级净化",
    "AmapAds.conf": "高德地图去广告",
    "NeteaseAds.conf": "网易云去广告",
    "CainiaoAds.conf": "菜鸟裹裹去广告",
    "BingSimplify.conf": "Bing首页简化",
    "SmzdmAds.conf": "什么值得买去广告",
    "CaiYunAds.conf": "彩云天气净化",
    "TieBaAds.conf": "贴吧去广告",
    "RedditAds.conf": "Reddit去广告",
    "NeteaseMailAds.conf": "网易邮箱大师净化",
    "GoofishAds.conf": "闲鱼净化",
    "QiShuiMusicAds.conf": "汽水音乐净化",
    "XiaoYuZhouAds.conf": "小宇宙FM去广告",
    "CheLaiLeAds.conf": "车来了净化",
    "MoJiWeatherAds.conf": "墨迹天气去广告",
    "TaoPiaoPiaoAds.conf": "淘票票净化",
    "ChinaUnicomAds.conf": "中国联通去广告",
    "BiliBiliComicsAds.conf": "哔哩漫画去广告",
    "WeChat.conf": "公众号图文去广告(旧)",
    "NBProAds.conf": "NBPro净化",
}

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
# 可莉上游近重复：合集只留较新/较完整的一份（单件仍在 zuozhe/keli/mokuai）
KELI_UNLOCK_DEDUP_SKIP = frozenset({
    "Google重定向.sgmodule",          # 留 Google搜索重定向
    "拦截HTTPDNS.sgmodule",           # 留 HTTPDNS拦截器（更新）
    "Spotify歌词翻译.sgmodule",       # 留 Spotify歌词增强（正文几乎相同）
})
SIGNIN_KW = ("签到", "每日签到", "抢券")
# Official 里跟签到文件夹放一起的非「签到」字样模块
QIANDAO_OFFICIAL_EXTRA = frozenset({
    "联通余量.official.sgmodule",
})

# Official 文件名含这些 → 仍是去广告，不进 qita（原料留 keli/official）
OFFICIAL_AD_KW = ("去广告", "广告联盟", "BiliADBlock", "ADBlock")

# sync 签到脚本（无独立 sgmodule 的，进 qiandao/js/）
QIANDAO_SYNC_JS = (
    "Scripts/Nodeseek_NsCheckin.js",
    "Scripts/iios_checkin.js",
    "Scripts/mixc_signin.js",
    "Scripts/PingMe-signin.js",
    "Scripts/PingMe-capture.js",
    "Scripts/fmz200/PingMe/PingMeSignin.js",
    "Scripts/fmz200/ccbLife/ccbLife_signin.js",
    "Scripts/fmz200/chery/cheryAppSignin.js",
    "Scripts/fmz200/dalanshu/dalanshu_checkin.js",
    "Scripts/fmz200/macat/macat_signin.js",
    "Scripts/fmz200/weibo/weibo_signin.js",
    "Scripts/fmz200/weibo/weibotalk_signin.js",
    "Scripts/fmz200/weibo/weibotalk.cookie.js",
    "Scripts/fmz200/xxyx/xxyx_signin.js",
    "Scripts/fmz200/douyu/yubaSign.js",
    "Scripts/zenmofeishi/Nodeseek_NsCheckin.js",
    "Scripts/zenmofeishi/iios_checkin.js",
    "Scripts/zenmofeishi/mixc_signin.js",
)

# sync 工具模块 → qita/local
QITA_SYNC_MODULES = (
    "boxjs.sgmodule",
    "proxy-detect-extra.sgmodule",
    "skip-proxy-collection.module",
    "iringo-location.sgmodule",
    "iringo-maps.sgmodule",
    "iringo-weather.sgmodule",
    "iringo-others.sgmodule",
    "fmz200-extra.sgmodule",
)

# 只改写脚本引用，勿动 reject/URL-Rewrite 里出现的广告 .js 链接
SCRIPT_PATH_RE = re.compile(
    r"(script-path\s*=\s*)(https?://[^\s,\"']+\.(?:js|mjs)(?:\?[^\s,\"']*)?)",
    re.IGNORECASE,
)
QX_SCRIPT_URL_RE = re.compile(
    r"(url\s+script-[\w-]+\s+)(https?://[^\s,\"']+\.(?:js|mjs)(?:\?[^\s,\"']*)?)",
    re.IGNORECASE,
)

STATS: dict = {
    "zuozhe": {},
    "heji": {},
    "qiandao": {},
    "qita": {},
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
    # GitHub API/raw：普通 UA；ddgksf2013.top 仍用 QX UA
    if "api.github.com" in url or "raw.githubusercontent.com" in url:
        headers["User-Agent"] = "egern-yuanban/1.0"
    if "api.github.com" in url:
        headers["Accept"] = "application/vnd.github+json"
        # 坏掉的 GITHUB_TOKEN 会导致 401；仅显式 FORCE 时带 token
        token = os.environ.get("ADBLOCK_GH_TOKEN") or ""
        if token:
            headers["Authorization"] = f"Bearer {token}"

    def _read(req: urllib.request.Request) -> bytes:
        with urllib.request.urlopen(req, context=CTX, timeout=timeout) as resp:
            return resp.read()

    req = urllib.request.Request(url, headers=headers)
    try:
        data = _read(req)
    except Exception:
        # 401：去掉 Authorization 再试（公共仓库）
        headers.pop("Authorization", None)
        try:
            data = _read(urllib.request.Request(url, headers=headers))
        except Exception:
            proxy_headers = {"User-Agent": headers.get("User-Agent", "egern-yuanban/1.0")}
            data = _read(
                urllib.request.Request("https://ghproxy.net/" + url, headers=proxy_headers)
            )
    if data.lstrip()[:20].lower().startswith((b"<!doctype", b"<html")):
        raise ValueError(f"HTML {url}")
    return data


def is_signin_name(name: str) -> bool:
    """判断是否应进 qiandao/（签到单件，不做合集）。"""
    base = Path(name).name
    if base in QIANDAO_OFFICIAL_EXTRA:
        return True
    return any(k in base for k in SIGNIN_KW)


def is_official_ad_name(name: str) -> bool:
    """Official 去广告类：留 keli/official，不进 qita。"""
    base = Path(name).name
    return any(k in base for k in OFFICIAL_AD_KW)


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


def qiandao_dir(bucket: str) -> Path:
    d = QIANDAO / bucket
    d.mkdir(parents=True, exist_ok=True)
    STATS["qiandao"].setdefault(bucket, 0)
    return d


def save_qiandao(bucket: str, filename: str, data: bytes) -> Path:
    dest = qiandao_dir(bucket) / filename
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    STATS["qiandao"][bucket] = STATS["qiandao"].get(bucket, 0) + 1
    return dest


def qita_dir(bucket: str) -> Path:
    d = QITA / bucket
    d.mkdir(parents=True, exist_ok=True)
    STATS["qita"].setdefault(bucket, 0)
    return d


def save_qita(bucket: str, filename: str, data: bytes) -> Path:
    dest = qita_dir(bucket) / filename
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    STATS["qita"][bucket] = STATS["qita"].get(bucket, 0) + 1
    return dest


def save_bytes(dest: Path, data: bytes, *, author: str, kind: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    STATS["zuozhe"][author][kind] = STATS["zuozhe"][author].get(kind, 0) + 1


def _normalize_js_url(url: str) -> str:
    """github.com/.../raw/... → raw.githubusercontent.com（避免 HTML 中间页）。"""
    m = re.match(
        r"^https?://github\.com/([^/]+)/([^/]+)/raw/([^/]+)/(.*)$",
        url,
        re.I,
    )
    if m:
        owner, repo, ref, path = m.groups()
        return f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}"
    m = re.match(
        r"^https?://github\.com/([^/]+)/([^/]+)/refs/heads/([^/]+)/(.*)$",
        url,
        re.I,
    )
    if m:
        owner, repo, ref, path = m.groups()
        return f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}"
    return url


def mirror_js(url: str, author: str, cache: dict[str, str]) -> str:
    """Download script into zuozhe/<author>/js/... ; return self-host URL for heji rewrite."""
    url = _normalize_js_url(url)
    if url in cache:
        return cache[url]
    # 解锁合集用 Eevee；Crack 不进自托管（spotify.crack 路径）
    low = url.lower()
    if "spotify.crack" in low or "/spotify-crack" in low:
        cache[url] = url
        return url
    ensure_author(author)
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
    """仅重写 script-path / QX script-* 的脚本 URL；reject 里的 .js 保持原文。"""

    def _sub(m: re.Match[str]) -> str:
        return m.group(1) + mirror_js(m.group(2), author, cache)

    text = SCRIPT_PATH_RE.sub(_sub, text)
    text = QX_SCRIPT_URL_RE.sub(_sub, text)
    return text


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


def qx_conf_to_surge_body(text: str, *, script_prefix: str = "moyu") -> str:
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
                # host, x, reject|direct
                action = parts[2].upper() if len(parts) >= 3 else "REJECT"
                if action in {"REJECT", "DIRECT"}:
                    rules.append(f"{kind},{parts[1]},{action}")
                else:
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
                    f"{script_prefix}-{script_i} = type={surge_type},pattern={pat},"
                    f"script-path={surl},requires-body={req_body},timeout=60"
                )
            continue
        # QX response-body 替换：Surge 无等价，保留注释便于对照
        if " url response-body " in s:
            rewrites.append(f"# QX-response-body (未转): {s}")
            continue
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

_QINGREX_TREE_CACHE: list[dict] | None = None


def _qingrex_tree() -> list[dict]:
    global _QINGREX_TREE_CACHE
    if _QINGREX_TREE_CACHE is None:
        _QINGREX_TREE_CACHE = json.loads(fetch(QINGREX_API).decode())["tree"]
    return _QINGREX_TREE_CACHE


def mirror_keli(cache: dict[str, str]) -> dict[str, Path]:
    """可莉：全部 Surge 根 sgmodule 原样 → mokuai；签到另拷 qiandao/keli。"""
    paths = ensure_author("keli")
    tree = _qingrex_tree()
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
        rewrite_js_urls(raw.decode("utf-8", errors="replace"), "keli", cache)
        if is_signin_name(name):
            save_qiandao("keli", name, raw)
            print(f"  mokuai+qiandao {name}")
        else:
            print(f"  mokuai {name}")
    (paths["mokuai"] / "README.md").write_text(
        "可莉 QingRex/LoonKissSurge — Surge 根目录模块原样（含广告平台拦截器 / 可莉广告过滤器）。\n"
        "签到类另见 Yuanban/qiandao/keli/（单件，无合集）。\n",
        encoding="utf-8",
    )
    return paths


def mirror_keli_official(cache: dict[str, str]) -> None:
    """QingRex Surge/Official：非签到 → zuozhe/keli/official；签到 → qiandao/official。"""
    paths = ensure_author("keli")
    official_dir = paths["mokuai"].parent / "official"
    official_dir.mkdir(parents=True, exist_ok=True)
    tree = _qingrex_tree()
    mods = sorted(
        t["path"]
        for t in tree
        if t.get("type") == "blob"
        and t["path"].startswith("Surge/Official/")
        and t["path"].endswith(".sgmodule")
    )
    print(f"keli official modules: {len(mods)}")
    n_off = n_qd = 0
    for rel in mods:
        name = rel.split("/")[-1]
        try:
            raw = fetch(QINGREX_RAW + quote(rel, safe="/"))
        except Exception as exc:
            print(f"  ! official {name}: {exc}")
            continue
        rewrite_js_urls(raw.decode("utf-8", errors="replace"), "keli", cache)
        if is_signin_name(name):
            save_qiandao("official", name, raw)
            n_qd += 1
            print(f"  qiandao/official {name}")
        else:
            dest = official_dir / name
            dest.write_bytes(raw)
            n_off += 1
            STATS["zuozhe"]["keli"]["mokuai"] = STATS["zuozhe"]["keli"].get("mokuai", 0) + 1
            print(f"  keli/official {name}")
    (official_dir / "README.md").write_text(
        "可莉 QingRex Surge/Official 非签到模块原样。签到/抢券/联通余量见 Yuanban/qiandao/official/。\n",
        encoding="utf-8",
    )
    print(f"  official kept={n_off} qiandao={n_qd}")


def build_qiandao_local(cache: dict[str, str]) -> None:
    """本仓/sync 签到相关单件 → qiandao/local + js（不做合集）。"""
    ensure_author("local")
    items = [
        ("pingme.sgmodule", f"{SYNC_RAW}/Modules/pingme.sgmodule"),
        ("qdreader.sgmodule", f"{SYNC_RAW}/Modules/qdreader.sgmodule"),
    ]
    for fname, url in items:
        try:
            raw = fetch(url)
        except Exception as exc:
            print(f"  ! qiandao/local {fname}: {exc}")
            continue
        save_qiandao("local", fname, raw)
        rewrite_js_urls(raw.decode("utf-8", errors="replace"), "local", cache)
        print(f"  qiandao/local {fname}")

    # 无独立模块的签到/抓参脚本：原样放 qiandao/js/
    for rel in QIANDAO_SYNC_JS:
        url = f"{SYNC_RAW}/{quote(rel, safe='/')}"
        fname = rel.replace("Scripts/", "").replace("/", "__")
        try:
            raw = fetch(url)
        except Exception as exc:
            print(f"  ! qiandao/js {fname}: {exc}")
            continue
        save_qiandao("js", fname, raw)
        print(f"  qiandao/js/{fname}")

    (QIANDAO / "README.md").write_text(
        "\n".join(
            [
                "# 签到（单件，无合集）",
                "",
                "签到模块差异大、依赖 Cookie/BoxJs，**不做 heji 合集**，按来源分文件夹自取。",
                "",
                "上游能做成 Surge 模块的就这些；更多是 **Task/JS**（BoxJs 或手动），放在 `js/`。",
                "",
                "- `keli/` — 可莉 Surge 根目录签到（WPS / 书香门第）",
                "- `official/` — QingRex Official 签到 / 抢券 / 联通余量",
                "- `local/` — 本仓 sync：PingMe、起点签到模块",
                "- `js/` — sync 签到脚本（fmz200 / 怎么肥事 / Nodeseek…，无独立 module）",
                "",
                "抓参合集见 `heji/zhuacan.module`（抓完关掉）。工具类见 `Yuanban/qita/`。",
                "",
            ]
        ),
        encoding="utf-8",
    )


def mirror_ibl3nd(cache: dict[str, str]) -> None:
    """IBL3ND/module 小组件 + sgmodule → qita/ibl3nd（单件，不做合集）。"""
    skip_suffix = {".yaml", ".lpx", ".txt", ".md"}
    skip_names = {"README.md", "weather.TXT", "surge-loon-to-egern.yaml", "Telegram.yaml"}
    try:
        tree = json.loads(fetch(IBL3ND_API).decode())["tree"]
    except Exception as exc:
        print(f"  ! ibl3nd tree: {exc}")
        return
    n = 0
    for t in tree:
        if t.get("type") != "blob":
            continue
        rel = t["path"]
        name = Path(rel).name
        if name in skip_names or Path(name).suffix.lower() in skip_suffix:
            continue
        suf = Path(name).suffix.lower()
        if suf not in {".js", ".jsx", ".sgmodule"} and not name.endswith(".JS"):
            continue
        try:
            raw = fetch(IBL3ND_RAW + quote(rel, safe="/"))
        except Exception as exc:
            print(f"  ! ibl3nd {name}: {exc}")
            continue
        save_qita("ibl3nd", name, raw)
        if suf == ".sgmodule" or name.endswith(".sgmodule"):
            rewrite_js_urls(raw.decode("utf-8", errors="replace"), "local", cache)
        n += 1
        print(f"  qita/ibl3nd/{name}")
    # sync 插件中心跳转（Egern）
    try:
        hub = fetch(f"{SYNC_RAW}/Modules/ibl3nd-plugin-hub.yaml")
        save_qita("ibl3nd", "ibl3nd-plugin-hub.yaml", hub)
        print("  qita/ibl3nd/ibl3nd-plugin-hub.yaml ← sync")
        n += 1
    except Exception as exc:
        print(f"  ! ibl3nd-plugin-hub: {exc}")
    (QITA / "ibl3nd" / "README.md").write_text(
        "IBL3ND/module 小组件与 Surge 模块原样（单件自取，不做合集）。\n"
        "插件中心跳转：`ibl3nd-plugin-hub.yaml`（sync 镜像）。\n"
        f"上游：https://github.com/IBL3ND/module\n共约 {n} 个文件。\n",
        encoding="utf-8",
    )


def build_qita(cache: dict[str, str]) -> None:
    """其他脚本/工具单件 → qita/（不做合集）。"""
    # Official 非广告、非签到 → qita/official
    official_dir = ZUOZHE / "keli" / "official"
    if official_dir.is_dir():
        for path in sorted(official_dir.glob("*.sgmodule")):
            if is_signin_name(path.name) or is_official_ad_name(path.name):
                continue
            raw = path.read_bytes()
            save_qita("official", path.name, raw)
            rewrite_js_urls(raw.decode("utf-8", errors="replace"), "keli", cache)
            print(f"  qita/official {path.name}")

    # sync 工具模块
    for fname in QITA_SYNC_MODULES:
        url = f"{SYNC_RAW}/Modules/{quote(fname, safe='/')}"
        try:
            raw = fetch(url)
        except Exception as exc:
            print(f"  ! qita/local {fname}: {exc}")
            continue
        save_qita("local", fname, raw)
        rewrite_js_urls(raw.decode("utf-8", errors="replace"), "local", cache)
        print(f"  qita/local {fname}")

    # boxjs json 可选
    for fname in ("egern.boxjs.json",):
        url = f"{SYNC_RAW}/Modules/{quote(fname, safe='/')}"
        try:
            raw = fetch(url)
            save_qita("local", fname, raw)
            print(f"  qita/local {fname}")
        except Exception as exc:
            print(f"  ! qita/local {fname}: {exc}")

    print("=== qita/ibl3nd（小组件）===")
    mirror_ibl3nd(cache)

    (QITA / "README.md").write_text(
        "\n".join(
            [
                "# 其他脚本 / 工具（单件，无合集）",
                "",
                "BoxJs、Sub-Store、面板、定位/天气增强、测速、小组件等——**不做 heji**，按需自取。",
                "",
                "- `official/` — QingRex Official 工具/增强（已排除去广告与签到）",
                "- `local/` — 本仓 sync：BoxJs、IRingo、proxy-detect、skip-proxy、fmz200-extra 等",
                "- `ibl3nd/` — IBL3ND 小组件 + Surge 模块 + plugin-hub",
                "",
                "去广告/开屏/解锁/抓参合集仍在 `heji/`；签到在 `qiandao/`。",
                "",
            ]
        ),
        encoding="utf-8",
    )


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
        if not author_dir.is_dir() or author_dir.name == "README.md":
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
        official = author_dir / "official"
        if official.is_dir():
            for f in official.iterdir():
                if f.is_file() and f.name != "README.md":
                    dest = DAN / "mokuai" / f"{author}__official__{f.name}"
                    shutil.copy2(f, dest)
        js_dir = author_dir / "js"
        if js_dir.is_dir():
            for f in js_dir.rglob("*"):
                if f.is_file() and f.name != "README.md":
                    rel = f.relative_to(js_dir).as_posix().replace("/", "__")
                    dest = DAN / "js" / f"{author}__{rel}"
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, dest)
    # qiandao / qita 单件也备份
    for root, prefix, kind_default in (
        (QIANDAO, "qiandao", "mokuai"),
        (QITA, "qita", "mokuai"),
    ):
        if not root.is_dir():
            continue
        for bucket in sorted(root.iterdir()):
            if not bucket.is_dir():
                continue
            kind = "js" if bucket.name == "js" else kind_default
            for f in bucket.rglob("*"):
                if f.is_file() and f.name != "README.md":
                    rel = f.relative_to(bucket).as_posix().replace("/", "__")
                    dest = DAN / kind / f"{prefix}_{bucket.name}__{rel}"
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, dest)
    (DAN / "README.md").write_text(
        "单件备份：从 zuozhe / qiandao / qita 汇总，文件名带前缀。原样，不改内容。\n",
        encoding="utf-8",
    )


# ── heji builders ───────────────────────────────────────────────

def _moyu_conf_to_bag(
    path: Path, label: str, cache: dict[str, str]
) -> tuple[str, dict[str, list[str]]] | None:
    if not path.is_file():
        return None
    raw = path.read_text(encoding="utf-8", errors="replace")
    rewrite_js_urls(raw, "moyu", cache)
    surge_body = qx_conf_to_surge_body(raw, script_prefix="moyu-" + path.stem[:12])
    surge_body = rewrite_js_urls(surge_body, "moyu", cache)
    return (label, parse_sections(surge_body))


def heji_quguanggao(cache: dict[str, str]) -> None:
    """去广告：基础置顶 → 可莉 → 墨鱼 AdBlock/NBPro → 毒奶 → BMJ → 奶思。"""
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

    # 3) 墨鱼 AdBlock（含 NBPro）— QX→Surge 仅格式
    moyu_m = ZUOZHE / "moyu" / "mokuai"
    for fname in MOYU_ADBLOCK_CONFS:
        bag = _moyu_conf_to_bag(
            moyu_m / fname,
            f"墨鱼 · {MOYU_ADBLOCK_LABEL.get(fname, fname)}",
            cache,
        )
        if bag:
            bags.append(bag)
    bag = _moyu_conf_to_bag(
        moyu_m / "NBProAds.conf",
        f"墨鱼 · {MOYU_ADBLOCK_LABEL['NBProAds.conf']}",
        cache,
    )
    if bag:
        bags.append(bag)
    # Egern 补全：telnet Map Local + 自托管脚本（sync custom-apps）
    egern_nb = moyu_m / "NBPro-egern.sgmodule"
    if egern_nb.is_file():
        raw = egern_nb.read_text(encoding="utf-8", errors="replace")
        rewritten = rewrite_js_urls(raw, "moyu", cache)
        bags.append(("墨鱼 · NBPro Egern补全（telnet+脚本）", parse_sections(rewritten)))

    # 4) 毒奶 Adblock4limbo
    dunai = ZUOZHE / "dunai" / "mokuai" / "Adblock4limbo.sgmodule"
    if dunai.is_file():
        raw = dunai.read_text(encoding="utf-8", errors="replace")
        rewritten = rewrite_js_urls(raw, "dunai", cache)
        title, _ = strip_module_header(raw)
        bags.append((f"毒奶 · {title or 'Adblock4limbo'}", parse_sections(rewritten)))

    # 5) blackmatrix7 Advertising(+Script)
    bmj_m = ZUOZHE / "blackmatrix7" / "mokuai"
    for fname, label in (
        ("Advertising.sgmodule", "blackmatrix7 · Advertising"),
        ("AdvertisingScript.sgmodule", "blackmatrix7 · AdvertisingScript"),
    ):
        path = bmj_m / fname
        if not path.is_file():
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        rewritten = rewrite_js_urls(raw, "blackmatrix7", cache)
        bags.append((label, parse_sections(rewritten)))

    # 6) 奶思 blockAds 整模块（不拆不改）
    naisi = ZUOZHE / "naisi" / "mokuai" / "blockAds.module"
    if naisi.is_file():
        raw = naisi.read_text(encoding="utf-8", errors="replace")
        rewritten = rewrite_js_urls(raw, "naisi", cache)
        bags.append(("奶思 · blockAds 整模块", parse_sections(rewritten)))

    text = merge_section_bags(
        bags,
        name="去广告合集",
        desc="可莉基础置顶 + 可莉逐App + 墨鱼AdBlock/NBPro + 毒奶 + BMJ + 奶思（原文，URL自托管）",
        notes=[
            "# 合集类型: 去广告",
            "# 置顶基础: 1)广告平台拦截器 2)可莉广告过滤器 —— 须最先生效",
            "# 然后: 可莉各 App「××去广告」原样分段",
            "# 然后: 墨鱼 ddgksf2013 AdBlock（微博/闲鱼/网易云/NBPro…）+ Egern NBPro 补全",
            "# 然后: 毒奶 limbopro/Adblock4limbo（网页广告）",
            "# 然后: blackmatrix7 Advertising + AdvertisingScript",
            "# 然后: 奶思 blockAds.module 整块",
            "# 不含开屏（见 heji/qukaiping.module：StartUpAds / FakeiOSAds）",
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
        surge_body = qx_conf_to_surge_body(raw, script_prefix="moyu-kp")
        surge_body = rewrite_js_urls(surge_body, "moyu", cache)
        bags.append((label, parse_sections(surge_body)))

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
    if is_signin_name(name):
        return False
    if name in KELI_UNLOCK_DEDUP_SKIP:
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

    # 墨鱼：微信110 + ForOwnUse VIP + Function
    moyu_m = ZUOZHE / "moyu" / "mokuai"
    for fname, label in (
        ("UnblockURLinWeChat.conf", "墨鱼 · 微信110外链解锁"),
        ("ForOwnUse.conf", "墨鱼 · 专属VIP合集 ForOwnUse"),
    ):
        bag = _moyu_conf_to_bag(moyu_m / fname, label, cache)
        if bag:
            bags.append(bag)
    for fname, label in MOYU_FUNCTION_CONFS:
        if fname == "UnblockURLinWeChat.conf":
            continue  # 已上
        bag = _moyu_conf_to_bag(moyu_m / fname, f"墨鱼 · {label}", cache)
        if bag:
            bags.append(bag)

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
        desc="可莉解锁 + 墨鱼微信110/VIP/Function + iEwha/chxm/…（作者原文，URL自托管）",
        notes=[
            "# 合集类型: 解锁增强",
            "# 分段注释标明每个作者/模块用途",
            "# 墨鱼: UnblockURLinWeChat(微信110) + ForOwnUse(专属VIP) + Function(TF/Emby/…)",
            "# Spotify 用 Eevee（spotify-unlock），不含 Crack",
            "# 已跳过可莉近重复: Google重定向 / 拦截HTTPDNS / Spotify歌词翻译（单件仍在 zuozhe）",
        ],
    )
    (HEJI / "jiesuo.module").write_text(text, encoding="utf-8")
    STATS["heji"]["jiesuo"] = len(bags)
    print(f"heji jiesuo bags={len(bags)}")


def heji_fenliu() -> None:
    """分流：复制 zuozhe 规则集到 heji/fenliu，并写订阅清单（不做巨型 .module）。"""
    out = HEJI / "fenliu"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    for author_dir in sorted(ZUOZHE.iterdir()):
        fen = author_dir / "fenliu"
        if not fen.is_dir():
            continue
        for f in fen.iterdir():
            if f.is_file() and f.name != "README.md":
                dest = out / f"{author_dir.name}__{f.name}"
                shutil.copy2(f, dest)
                n += 1
    lines = [
        "# 分流规则集（单件）",
        "",
        "不合并成一个 module（用途不同，按策略组自选）。原料在 `zuozhe/*/fenliu/`。",
        "",
        "## 上游怎么选",
        "",
        "| 前缀 | 上游 | 适合 |",
        "|------|------|------|",
        "| `repcz__` | Repcz/Tool Egern | **骨架**：国内/代理/流媒体，Egern 原生 yaml |",
        "| `moli__` | 莫离 Moli-X Ruleset | **分类多**：Ads/CDN/Claude/Steam/PayPal… |",
        "| `sukka__` | Sukka ruleset.skk.moe | reject/AI/CDN/流媒体/Apple |",
        "| `loyalsoldier__` | Loyalsoldier surge-rules | **大名单底**：direct/proxy/gfw/reject |",
        "| `vpsdance__` | VPSDance | AI 专项最全 |",
        "| `blackmatrix7__` | blackmatrix7 | 细分补洞：ChinaMax/Steam/GlobalMedia… |",
        "",
        "广告类 Reject 与去广告合集会叠，别无脑全开。",
        "",
        "## 订阅示例",
        "",
        "```",
    ]
    for f in sorted(out.iterdir()):
        if f.is_file() and f.name != "README.md":
            lines.append(f"{RAW}/Yuanban/heji/fenliu/{f.name}")
    lines += ["```", "", f"共 {n} 个文件。", ""]
    (out / "README.md").write_text("\n".join(lines), encoding="utf-8")
    STATS["heji"]["fenliu"] = n
    print(f"heji fenliu files={n}")


def heji_zhuacan(cache: dict[str, str]) -> None:
    bags: list[tuple[str, dict[str, list[str]]]] = []
    # cookie-collection = sync 合并版（已含奶思+起点）；合集不再叠原版以免双倍 MITM
    # 奶思/起点原件仍在 zuozhe 单件备份
    items = [
        ("local", "cookie-collection.module", "本仓 · Cookie合集（奶思+起点+自托管）"),
        ("nobyda", "GetCookie.sgmodule", "NobyDa · 签到Cookie（爱奇艺/贴吧/B漫/快看/携程）"),
        ("moli", "JD_Cookie.sgmodule", "莫离 · 京东Cookie"),
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
        desc="签到 Cookie/Token 抓取：奶思合集 + NobyDa + 莫离京东 + 起点（按需开，抓完关掉）",
        notes=[
            "# 合集类型: 抓参",
            "# 默认建议关闭；抓完关掉省电 / 少 MITM",
            "# 主源: sync cookie-collection（奶思 cookies + 起点 + 脚本自托管）",
            "# 补充: 奶思原版 / NobyDa GetCookie / 莫离京东 JD_Cookie / Yuheng 起点",
        ],
    )
    (HEJI / "zhuacan.module").write_text(text, encoding="utf-8")
    STATS["heji"]["zhuacan"] = len(bags)
    print(f"heji zhuacan bags={len(bags)}")


def mirror_moli_ruleset() -> int:
    """莫离 Moli-X/Resources Ruleset/*.list → zuozhe/moli/fenliu。"""
    paths = ensure_author("moli")
    try:
        tree = json.loads(fetch(MOLI_API).decode())["tree"]
    except Exception as exc:
        print(f"  ! moli tree: {exc}")
        return 0
    n = 0
    for t in tree:
        if t.get("type") != "blob":
            continue
        rel = t["path"]
        if not (rel.startswith("Ruleset/") and rel.endswith(".list")):
            continue
        name = Path(rel).name
        try:
            raw = fetch(MOLI_RAW + quote(rel, safe="/"))
        except Exception as exc:
            print(f"  ! moli/{name}: {exc}")
            continue
        save_bytes(paths["fenliu"] / name, raw, author="moli", kind="fenliu")
        n += 1
        print(f"  moli/fenliu/{name}")
    (paths["fenliu"] / "README.md").write_text(
        "莫离 Moli-X/Resources Ruleset（Surge/QX 通用 .list 原样）。\n"
        "上游：https://github.com/Moli-X/Resources\n",
        encoding="utf-8",
    )
    return n


def mirror_sync_module(author: str, filename: str, cache: dict[str, str]) -> Path | None:
    """从 sync 分支 Modules/ 拉取本仓补丁（guize 根目录不保留 Modules）。"""
    url = f"{SYNC_RAW}/Modules/{quote(filename, safe='/')}"
    return mirror_url_module(author, url, filename, cache)


def write_docs() -> None:
    (YUAN / "README.md").write_text(
        "\n".join(
            [
                "# Yuanban — 原版资源根（拼音目录）",
                "",
                "全部去广告 / 开屏 / 解锁 / 抓参 / 签到 / 其他脚本 / 分流都在这一个文件夹下。",
                "",
                "## 结构",
                "",
                "```",
                "Yuanban/",
                "  zuozhe/                 # 按作者",
                "    keli/                 # 可莉",
                "      fenliu/  mokuai/  js/  official/",
                "    naisi/  moyu/  …",
                "  qiandao/                # 签到单件（无合集）",
                "    keli/  official/  local/  js/",
                "  qita/                   # 其他脚本/工具（无合集）",
                "    official/  local/  ibl3nd/",
                "  danxiang/               # 单件备份",
                "  heji/                   # 合集（四分）+ 分流清单",
                "    quguanggao / qukaiping / jiesuo / zhuacan / fenliu/",
                "```",
                "",
                "## 原则",
                "",
                "- `zuozhe` / `danxiang` / `qiandao` / `qita`：**原作者照搬**，文件字节不改",
                "- `heji`：只拼装 + Fan.a.tail 分段；**规则正文不改**；script URL 改指本仓",
                "- 去广告置顶：`广告平台拦截器` → `可莉广告过滤器`",
                "- **签到 / 其他脚本 / IBL3ND 小组件不做合集**",
                "",
                "## 订阅（合集）",
                "",
                "```",
                f"{RAW}/Yuanban/heji/quguanggao.module",
                f"{RAW}/Yuanban/heji/qukaiping.module",
                f"{RAW}/Yuanban/heji/jiesuo.module",
                f"{RAW}/Yuanban/heji/zhuacan.module",
                "```",
                "",
                "签到：`Yuanban/qiandao/`　其他/小组件：`Yuanban/qita/`　分流：`heji/fenliu/README.md`",
                "",
                "重建：`python3 scripts/build-yuanban.py`",
                "",
                "与 sync 日更并行，不覆盖。",
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
        lines.append(
            f"- **{author}**: mokuai={st.get('mokuai',0)} js={st.get('js',0)} fenliu={st.get('fenliu',0)}"
        )
    lines += [
        "",
        "## qiandao 签到单件（无合集）",
        "",
        f"`{STATS.get('qiandao', {})}`",
        "",
        "## qita 其他脚本（无合集）",
        "",
        f"`{STATS.get('qita', {})}`",
        "",
        "## heji 分段袋数 / 分流文件数",
        "",
        f"`{STATS['heji']}`",
        "",
        f"脚本镜像成功约 {STATS['js_ok']}，失败 {len(STATS['js_fail'])}（多为 kelee.one 403，合集保留上游 URL）",
        "",
        "## 解锁近重复（合集已跳过，单件仍保留）",
        "",
        "- 跳过 `Google重定向` → 用 `Google搜索重定向`",
        "- 跳过 `拦截HTTPDNS` → 用 `HTTPDNS拦截器`",
        "- 跳过 `Spotify歌词翻译` → 用 `Spotify歌词增强`",
        "",
        "## 去广告置顶",
        "",
        "1. `zuozhe/keli/mokuai/广告平台拦截器.sgmodule`",
        "2. `zuozhe/keli/mokuai/可莉广告过滤器.sgmodule`",
        "3. 可莉各 App `*去广告.sgmodule`",
        "4. 墨鱼 AdBlock + NBPro",
        "5. 毒奶 `Adblock4limbo.sgmodule`",
        "6. blackmatrix7 Advertising(+Script)",
        "7. 奶思 `blockAds.module` 整块",
        "",
        "## 解锁补充（墨鱼）",
        "",
        "- 微信110：`UnblockURLinWeChat.conf` + `weixin110.js`",
        "- 专属VIP：`ForOwnUse.conf`（ddgksf2013/dev）",
        "- Function：TF / Emby / Upos / Bilibili_CC",
        "",
        "## 小组件",
        "",
        "- `Yuanban/qita/ibl3nd/` — IBL3ND/module 原样（单件）",
        "",
        "## 分流上游",
        "",
        "- Repcz（Egern 骨架）+ 莫离 Ruleset + Sukka + Loyalsoldier 大名单 + VPSDance AI + BMJ 细分",
        "- 清单见 `heji/fenliu/README.md`",
        "",
        "## 抓参",
        "",
        "- `heji/zhuacan`：sync Cookie合集 + 奶思原版 + NobyDa GetCookie + 莫离京东 + 起点",
        "",
    ]
    if STATS["js_fail"]:
        lines += ["## js 镜像失败（节选）", ""]
        for item in STATS["js_fail"][:30]:
            lines.append(f"- `{item}`")
        lines.append("")
    (HEJI / "UPSTREAM.md").write_text("\n".join(lines), encoding="utf-8")
    (ZUOZHE / "README.md").write_text(
        "作者拼音目录。每人下有 fenliu / mokuai / js；可莉另有 official/。内容与上游字节一致。\n\n"
        "拼音：keli可莉 naisi奶思 moyu墨鱼 dunai毒奶 moli莫离 nobyda blackmatrix7 "
        "loyalsoldier iewha chxm weigiegie liulong yu9191 repcz sukka vpsdance "
        "yuheng local miranquil\n",
        encoding="utf-8",
    )


def main() -> None:
    if YUAN.exists():
        shutil.rmtree(YUAN)
    for d in (ZUOZHE, DAN / "fenliu", DAN / "mokuai", DAN / "js", HEJI, QIANDAO, QITA):
        d.mkdir(parents=True, exist_ok=True)

    cache: dict[str, str] = {}

    print("=== zuozhe/keli ===")
    mirror_keli(cache)

    print("=== zuozhe/keli/official + qiandao/official ===")
    mirror_keli_official(cache)

    print("=== qiandao/local + js ===")
    build_qiandao_local(cache)

    print("=== qita（其他脚本/工具）===")
    build_qita(cache)

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
    mirror_sync_module("naisi", "fmz200-unlock-extra.sgmodule", cache)

    print("=== zuozhe/moyu（开屏 + AdBlock + NBPro + Function + VIP）===")
    paths = ensure_author("moyu")
    moyu_items: list[tuple[str, str]] = [
        ("StartUpAds.conf", "https://ddgksf2013.top/rewrite/StartUpAds.conf"),
        ("FakeiOSAds.conf", MOYU_REWRITE + "FakeiOSAds.conf"),
        ("NBProAds.conf", "https://ddgksf2013.top/rewrite/NBProAds.conf"),
        ("ForOwnUse.conf", MOYU_FOROWNUSE),
    ]
    for fname in MOYU_ADBLOCK_CONFS:
        moyu_items.append((fname, MOYU_REWRITE + fname))
    for fname, _label in MOYU_FUNCTION_CONFS:
        moyu_items.append((fname, MOYU_FUNCTION + fname))
    for fname, url in moyu_items:
        try:
            raw = fetch(url)
            save_bytes(paths["mokuai"] / fname, raw, author="moyu", kind="mokuai")
            rewrite_js_urls(raw.decode("utf-8", errors="replace"), "moyu", cache)
            print(f"  moyu/mokuai/{fname}")
        except Exception as exc:
            print(f"  ! moyu {fname}: {exc}")
    # NBPro 脚本：优先墨鱼站点，失败则 sync 镜像
    for js_url in (
        "https://ddgksf2013.top/scripts/nbpro.ads.js",
        f"{SYNC_RAW}/Scripts/ddgksf2013/nbpro.ads.js",
    ):
        try:
            mirror_js(js_url, "moyu", cache)
            break
        except Exception as exc:
            print(f"  ! moyu nbpro.ads.js via {js_url}: {exc}")
    # 微信110 脚本（Function/UnblockURLinWeChat 引用）
    mirror_js(
        "https://raw.githubusercontent.com/ddgksf2013/Scripts/master/weixin110.js",
        "moyu",
        cache,
    )
    # Egern 侧已调过的 NBPro 补全（含 telnet Map Local）
    mirror_sync_module("moyu", "custom-apps.sgmodule", cache)
    custom = paths["mokuai"] / "custom-apps.sgmodule"
    if custom.is_file():
        dest = paths["mokuai"] / "NBPro-egern.sgmodule"
        dest.write_bytes(custom.read_bytes())
        custom.unlink(missing_ok=True)
        print("  moyu/mokuai/NBPro-egern.sgmodule ← sync custom-apps")
    (paths["mokuai"] / "README.md").write_text(
        "墨鱼 ddgksf2013：\n"
        "- 开屏 StartUpAds / FakeiOSAds → heji/qukaiping\n"
        "- AdBlock/*.conf + NBProAds + NBPro-egern → heji/quguanggao\n"
        "- Function（微信110 / TF / Emby…）+ ForOwnUse（专属VIP）→ heji/jiesuo\n",
        encoding="utf-8",
    )

    print("=== zuozhe/dunai（毒奶 Adblock4limbo）===")
    mirror_url_module("dunai", DUNAI_SGMODULE, "Adblock4limbo.sgmodule", cache)
    (ZUOZHE / "dunai" / "mokuai" / "README.md").write_text(
        "毒奶 limbopro/Adblock4limbo — 网页广告用户脚本（Surge sgmodule 原样）。\n"
        "进 heji/quguanggao。上游：https://github.com/limbopro/Adblock4limbo\n",
        encoding="utf-8",
    )

    print("=== zuozhe/blackmatrix7（Advertising）===")
    mirror_url_module("blackmatrix7", BMJ_ADVERTISING, "Advertising.sgmodule", cache)
    mirror_url_module(
        "blackmatrix7", BMJ_ADVERTISING_SCRIPT, "AdvertisingScript.sgmodule", cache
    )
    (ZUOZHE / "blackmatrix7" / "mokuai" / "README.md").write_text(
        "blackmatrix7 Advertising + AdvertisingScript（Surge 原样）。\n"
        "进 heji/quguanggao。\n",
        encoding="utf-8",
    )

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

    print("=== zuozhe sync Modules copies ===")
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
        mirror_sync_module(author, src_name, cache)

    print("=== zuozhe cookie / 抓参模块 ===")
    mirror_sync_module("local", "cookie-collection.module", cache)
    mirror_url_module("nobyda", NOBYDA_GETCOOKIE, "GetCookie.sgmodule", cache)
    mirror_url_module("moli", MOLI_JD_COOKIE, "JD_Cookie.sgmodule", cache)
    (ZUOZHE / "nobyda" / "mokuai" / "README.md").write_text(
        "NobyDa GetCookie — 爱奇艺/B漫/贴吧/快看/携程签到 Cookie。\n",
        encoding="utf-8",
    )

    print("=== zuozhe fenliu（多上游）===")
    # 1) Repcz Egern 原生骨架
    repcz = "https://raw.githubusercontent.com/Repcz/Tool/X/Egern/Rules"
    for name in (
        "Reject", "Direct", "WeChat", "Bilibili", "AppleCN",
        "ChinaDomain", "ChinaIP", "ChinaASN", "Lan",
        "AI", "Telegram", "Twitter", "TikTok", "YouTube",
        "Netflix", "Disney", "Spotify", "Emby", "Google",
        "Github", "Microsoft", "AppleServers", "Game", "ProxyGFW", "Proxy",
    ):
        mirror_url_fenliu("repcz", f"{repcz}/{name}.yaml", f"{name}.yaml")

    # 2) 莫离 Ruleset 全量（60 类）
    print("  --- moli Ruleset ---")
    mirror_moli_ruleset()

    # 3) Sukka 扩充
    for rel, fname in SUKKA_FENLIU:
        mirror_url_fenliu("sukka", SUKKA_LIST + "List/" + rel, fname)

    # 4) Loyalsoldier 大名单
    for fname in LOYALSOLDIER_FENLIU:
        mirror_url_fenliu("loyalsoldier", LOYALSOLDIER_RAW + fname, fname)

    # 5) VPSDance AI
    mirror_url_fenliu(
        "vpsdance",
        "https://cdn.jsdelivr.net/gh/VPSDance/ai-proxy-rules@main/rules/egern/all.yaml",
        "all.yaml",
    )

    # 6) blackmatrix7 细分补洞
    for name in BMJ_FENLIU:
        mirror_url_fenliu(
            "blackmatrix7",
            f"{BMJ_RULE}{name}/{name}.list",
            f"{name}.list",
        )
    (ZUOZHE / "loyalsoldier" / "fenliu" / "README.md").write_text(
        "Loyalsoldier/surge-rules release DOMAIN-SET（大名单底）。\n",
        encoding="utf-8",
    )
    (ZUOZHE / "sukka" / "fenliu" / "README.md").write_text(
        "Sukka ruleset.skk.moe — reject/AI/CDN/流媒体/Apple/…\n",
        encoding="utf-8",
    )
    (ZUOZHE / "blackmatrix7" / "fenliu" / "README.md").write_text(
        "blackmatrix7 细分补洞（ChinaMax/AI/Steam/GlobalMedia…）。\n"
        "广告 Advertising 模块另见 mokuai/。\n",
        encoding="utf-8",
    )

    print("=== danxiang ===")
    build_danxiang()

    print("=== heji ===")
    heji_quguanggao(cache)
    heji_qukaiping(cache)
    heji_jiesuo(cache)
    heji_zhuacan(cache)
    heji_fenliu()

    write_docs()
    for p in sorted(YUAN.rglob("*"), reverse=True):
        if p.is_dir() and not any(p.iterdir()):
            try:
                p.rmdir()
            except OSError:
                pass
    print(
        "done heji=", STATS["heji"],
        "qiandao=", STATS["qiandao"],
        "qita=", STATS["qita"],
        "js_ok=", STATS["js_ok"],
        "js_fail=", len(STATS["js_fail"]),
    )


if __name__ == "__main__":
    main()
