#!/usr/bin/env python3
"""Yuanban/ — 拼音目录：作者原样 + 单件备份 + 合集 + 签到文件夹。

目录（全部在 Yuanban 下）::

  Yuanban/
    zuozhe/<作者拼音>/{fenliu,mokuai,js}/   # 原作者照搬
    qiandao/  qita/  danxiang/
    heji/
      quguanggao / qukaiping / jiesuo / zhuacan / shibajia(18+) / fenliu/

合集规则：
  - 不改作者规则正文；script-path 改指本仓自托管 js（不留外站）
  - Fan.a.tail 分段；去广告置顶：广告平台拦截器 → 可莉广告过滤器
  - 18+ 单独 heji/shibajia.module，不进日常解锁合集
  - 签到 / 其他脚本不做 heji
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
# kelee.one Cloudflare：QX/普通 UA 常 403，Surge UA 可下
KELEE_UA = {"User-Agent": "Surge iOS/3200"}

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
)

# 怎么肥事 ZenmoFeiShi — 直白中文名（一眼知道干啥）
ZENMO_JS_NAMES = {
    "CalShot.js": "CalShot打卡.js",
    "hongze.js": "洪泽论坛签到.js",
    "mixc_signin.js": "一点万象签到.js",
    "Nodeseek_NsCheckin.js": "NodeSeek签到.js",
    "PingMe.js": "PingMe签到.js",
    "WeTalk.js": "WeTalk签到.js",
    "QQMusic.js": "QQ音乐绿钻签到.js",
    "LKXDYF.js": "老百姓大药房签到.js",
    "SLY.js": "随乐游签到.js",
    "LaiChong.js": "来充签到.js",
    "SoulSing.js": "Soul唱歌签到.js",
    "iios_checkin.js": "iios签到.js",
    "bili_view_ad.js": "B站去广告.js",
    "hlwxx_remove_ads.js": "黑料不打烊去广告.js",
    "MeiTuanNoAd.js": "美团去广告.js",
    "TilingSales_getNav.js": "瓜子影视导航净化.js",
    "youtube.response.js": "油管去广告.js",
    "yt-zh-sub.js": "油管简体字幕.js",
    "yt-sub-clean.js": "油管字幕清理.js",
    "BPZJ.js": "表盘专辑解锁.js",
    "MTB.js": "磨题帮解锁.js",
    "mgtv_vip.js": "芒果TV解锁.js",
    "migu_vip.js": "咪咕视频解锁.js",
    "XMLYVIP.js": "喜马拉雅VIP解锁.js",
    "gyrfalcon_unlock.js": "Gyrfalcon解锁.js",
    "xzimu-unlock.js": "X字幕解锁.js",
    "TaskHotBiliVideo.js": "B站热播任务.js",
}
ZENMO_SNIPPET_NAMES = {
    "bili_view_ad_rewrite.snippet": "B站去广告.conf",
    "WB.snippet": "微博净化.conf",
    "Soul.snippet": "Soul净化.conf",
    "Keep.snippet": "Keep净化.conf",
    "Smzdm.snippet": "什么值得买净化.conf",
    "HP.snippet": "虎扑净化.conf",
    "KuAn.snippet": "酷安净化.conf",
    "TB.snippet": "贴吧净化.conf",
    "TH.snippet": "途虎养车净化.conf",
    "SF.snippet": "顺丰净化.conf",
    "Pinduoduo.snippet": "拼多多净化.conf",
    "Didichuxing.snippet": "滴滴出行净化.conf",
    "T3.snippet": "T3出行净化.conf",
    "Cwkj.snippet": "畅玩空间净化.conf",
    "hlwxx_remove_ads.snippet": "黑料不打烊去广告.conf",
    "TilingSales_ad_remove.snippet": "瓜子影视去广告.conf",
    "WxPureDominion.snippet": "微信净化.conf",
    "Youtube.snippet": "油管去广告.conf",
    "Yt-zh.snippet": "油管简体字幕.conf",
    "mgtv_vip.snippet": "芒果TV解锁.conf",
    "migu_vip_share.snippet": "咪咕视频解锁.conf",
    "xzimu-unlock.snippet": "X字幕解锁.conf",
    "xTerm256.snippet": "xTerm256解锁.conf",
}
ZENMO_AD_CONFS = (
    "B站去广告.conf", "微博净化.conf", "Soul净化.conf", "Keep净化.conf",
    "什么值得买净化.conf", "虎扑净化.conf", "酷安净化.conf", "贴吧净化.conf",
    "途虎养车净化.conf", "顺丰净化.conf", "拼多多净化.conf", "滴滴出行净化.conf",
    "T3出行净化.conf", "畅玩空间净化.conf", "黑料不打烊去广告.conf",
    "瓜子影视去广告.conf", "微信净化.conf", "油管去广告.conf",
)
ZENMO_UNLOCK_CONFS = (
    "芒果TV解锁.conf", "咪咕视频解锁.conf", "X字幕解锁.conf",
    "xTerm256解锁.conf", "油管简体字幕.conf",
)
ZENMO_UNLOCK_JS = (
    "表盘专辑解锁.js", "磨题帮解锁.js", "芒果TV解锁.js", "咪咕视频解锁.js",
    "喜马拉雅VIP解锁.js", "Gyrfalcon解锁.js", "X字幕解锁.js", "美团去广告.js",
)
ZENMO_QIANDAO_JS = (
    "CalShot打卡.js", "洪泽论坛签到.js", "一点万象签到.js", "NodeSeek签到.js",
    "PingMe签到.js", "WeTalk签到.js", "QQ音乐绿钻签到.js", "老百姓大药房签到.js",
    "随乐游签到.js", "来充签到.js", "Soul唱歌签到.js", "iios签到.js",
)

# 分流公开名：作者-用途（一眼能懂）
AUTHOR_CN = {
    "repcz": "Repcz",
    "moli": "莫离",
    "sukka": "Sukka",
    "loyalsoldier": "Loyalsoldier",
    "vpsdance": "VPSDance",
    "blackmatrix7": "BMJ",
    "keli": "可莉",
    "naisi": "奶思",
    "moyu": "墨鱼",
    "dunai": "毒奶",
    "zenmofeishi": "怎么肥事",
    "nobyda": "NobyDa",
    "local": "本仓",
    "iewha": "iEwha",
    "chxm": "chxm",
    "weigiegie": "WeiGiegie",
    "liulong": "liul0ng",
    "yu9191": "Yu9191",
    "yuheng": "Yuheng",
    "miranquil": "miranquil",
    "laoshu": "老书",
    "eulac": "eulac",
    "nsringo": "NSRingo",
    "scripthub": "ScriptHub",
}

# jnlaoshu/MySelf Egern 精选模块（Rule+Map Local 为主，脚本指 Maasea/墨鱼等）
LAOSHU_EGERN_MODULES = (
    "VideoAdBlock.yaml",
    "MusicAdBlock.yaml",
    "YouTube.yaml",
    "EcommerceAdBlock.yaml",
    "MapAdBlock.yaml",
    "TravelAdBlock.yaml",
    "Audi_AdBlock.yaml",
    "JDPrice.yaml",
    "Xueqiu.yaml",
)
LAOSHU_RAW = "https://raw.githubusercontent.com/jnlaoshu/MySelf/main/Egern/Module/"
FENLIU_CN = {
    "ChinaDomain": "国内域名", "ChinaIP": "国内IP", "ChinaASN": "国内ASN",
    "ChinaMax": "国内域名Max", "Direct": "直连", "Lan": "局域网",
    "Reject": "广告拒绝", "reject": "广告拒绝", "reject_extra": "广告拒绝补充",
    "reject.txt": "广告拒绝", "Anti-Ad": "广告拦截",
    "Proxy": "代理", "ProxyGFW": "GFW代理", "proxy": "代理", "gfw": "GFW列表",
    "direct": "直连大名单", "AI": "AI", "ai": "AI", "OpenAI": "OpenAI",
    "Claude": "Claude", "Gemini": "Gemini", "Google": "Google", "google": "Google",
    "Telegram": "Telegram", "telegram": "Telegram", "telegram_ip": "Telegram-IP",
    "telegramcidr": "Telegram-CIDR", "Twitter": "Twitter", "TikTok": "TikTok",
    "YouTube": "YouTube", "Netflix": "Netflix", "Disney": "Disney",
    "Spotify": "Spotify", "Emby": "Emby", "Github": "GitHub", "GitHub": "GitHub",
    "Microsoft": "Microsoft", "microsoft": "Microsoft", "AppleCN": "苹果中国",
    "AppleServers": "苹果服务", "Apple": "苹果", "apple": "苹果",
    "apple_cn": "苹果中国", "apple_services": "苹果服务", "icloud": "iCloud",
    "WeChat": "微信", "Bilibili": "哔哩哔哩", "Game": "游戏",
    "Steam": "Steam", "PayPal": "PayPal", "GlobalMedia": "全球流媒体",
    "AdvertisingLite": "广告精简", "Cloudflare": "Cloudflare",
    "cdn": "CDN", "download": "下载", "stream": "流媒体",
    "china_ip": "国内IP", "cncidr": "国内CIDR", "private": "私有网络",
    "tld-not-cn": "非中国TLD", "greatfire": "GreatFire", "all": "AI合集",
    "ResourceSite": "视频资源站", "PanVod": "网盘点播", "Zhuifeng": "追风",
}

# kelee.one 常 403：换已知 GitHub 镜像（内容自托管后不再依赖）
KELEE_FALLBACKS = {
    "VVebo_repair.js": (
        "https://raw.githubusercontent.com/suiyuran/stash/main/scripts/"
        "fix-vvebo-user-timeline.js"
    ),
    "TikTok_redirect.js": (
        "https://raw.githubusercontent.com/VirgilClyne/GetSomeFries/main/js/TikTok.request.js"
    ),
}

# sync 工具模块 → qita/local（定位/其他仍单件；天气/地图另拉 NSRingo 原版进解锁合集）
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

# 工具/分流补充（进仓库；天气地图+BoxJs+AntiRevoke 进 jiesuo）
TOOL_EGERN_MODULES = (
    (
        "sub-store.egern.yaml",
        "https://raw.githubusercontent.com/sub-store-org/Sub-Store/refs/heads/master/config/Egern.yaml",
    ),
    (
        "script-hub.egern.yaml",
        "https://raw.githubusercontent.com/Script-Hub-Org/Script-Hub/refs/heads/main/modules/script-hub.beta.egern.yaml",
    ),
)
EULAC_FENLIU = (
    (
        "ResourceSite",
        "视频资源站",
        "https://raw.githubusercontent.com/eulac-dev/Proxy/refs/heads/main/Loon/Rules/ResourceSite.lsr",
    ),
    (
        "PanVod",
        "网盘点播",
        "https://raw.githubusercontent.com/eulac-dev/Proxy/refs/heads/main/Loon/Rules/PanVod.lsr",
    ),
)

# 只改写脚本引用，勿动 reject/URL-Rewrite 里出现的广告 .js 链接
# 扩展名必须先匹配更长的 mjs/json，再匹配 js，否则 .json 会被截成 .js + 残留 on
SCRIPT_PATH_RE = re.compile(
    r"(script-path\s*=\s*)(https?://[^\s,\"']+\.(?:mjs|json|js)(?:\?[^\s,\"']*)?)",
    re.IGNORECASE,
)
QX_SCRIPT_URL_RE = re.compile(
    r"(url\s+script-[\w-]+\s+)(https?://[^\s,\"']+\.(?:mjs|json|js)(?:\?[^\s,\"']*)?)",
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
    # GitHub API/raw：普通 UA；ddgksf2013.top 仍用 QX UA；kelee 用 Surge UA
    if "kelee.one" in url:
        headers = dict(KELEE_UA)
    elif "api.github.com" in url or "raw.githubusercontent.com" in url:
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

    attempts: list[dict[str, str]] = [headers]
    # kelee：若 Surge UA 失败再试 QX（少数路径策略不同）
    if "kelee.one" in url:
        attempts.append(dict(UA))
    attempts.append({"User-Agent": "egern-yuanban/1.0"})

    data: bytes | None = None
    last_exc: Exception | None = None
    for hdr in attempts:
        h = dict(hdr)
        if "api.github.com" in url and "Accept" not in h:
            h["Accept"] = "application/vnd.github+json"
        try:
            data = _read(urllib.request.Request(url, headers=h))
            break
        except Exception as exc:
            last_exc = exc
            # 401：去掉 Authorization 再试（公共仓库）
            h.pop("Authorization", None)
            try:
                data = _read(urllib.request.Request(url, headers=h))
                break
            except Exception as exc2:
                last_exc = exc2
                continue
    if data is None:
        try:
            proxy_headers = {"User-Agent": "egern-yuanban/1.0"}
            data = _read(
                urllib.request.Request("https://ghproxy.net/" + url, headers=proxy_headers)
            )
        except Exception as exc:
            raise last_exc or exc
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


def _readable_js_name(url: str) -> str:
    """扁平、直白的脚本文件名（不要 raw.githubusercontent.com/... 长路径）。"""
    u = urlparse(url)
    path = unquote(u.path).rstrip("/")
    base = Path(path).name or "script.js"
    if base.lower() in {"raw", "index.js", "script.js", "main.js"} and Path(path).parent.name:
        base = Path(path).parent.name + ".js"
    base = ZENMO_JS_NAMES.get(base, base)
    # kelee: .../VVebo/VVebo_repair.js → VVebo时间线修复.js
    if "kelee.one" in (u.netloc or "") or "/Resource/JavaScript/" in path or "/Resource/Script/" in path:
        parts = [p for p in path.split("/") if p]
        if len(parts) >= 2:
            app, fname = parts[-2], parts[-1]
            stem = Path(fname).stem
            base = f"{app}-{stem}.js"
    if u.query:
        qh = hashlib.sha1(u.query.encode()).hexdigest()[:6]
        p = Path(base)
        base = f"{p.stem}_{qh}{p.suffix}"
    base = re.sub(r"[^\w.\u4e00-\u9fff\-]+", "-", base)
    if not base.lower().endswith((".js", ".mjs", ".json")):
        base += ".js"
    return base


def _js_fetch_candidates(url: str) -> list[str]:
    """自托管拉取候选：原链 → 作者仓/已知替身 → sync 镜像 → 本仓 Scripts。

    可莉模块正文来自 QingRex/LoonKissSurge；script-path 多指向 kelee.one CDN
    （不在 GitHub 仓内）。禁止把 sync 当唯一来源。
    """
    url = _normalize_js_url(url)
    out: list[str] = [url]
    path = unquote(urlparse(url).path)
    base = Path(path).name

    # oo226 本仓已是终态镜像时不再绕
    if "raw.githubusercontent.com/oo226/" in url or "github.com/oo226/" in url:
        return out

    # perzikkop（可莉小程序镜像站，常 404）→ kelee WexinMiniPrograms
    if "raw.perzikkop.com" in url:
        m = re.search(r"/Scripts/(?:MiniPrograms/)?(.+)$", path)
        if m:
            rel = m.group(1)
            stem = Path(rel).stem
            out.append(f"https://kelee.one/Resource/Script/WexinMiniPrograms/{stem}/{base}")
            out.append(f"https://kelee.one/Resource/JavaScript/{stem}/{base}")
            out.append(f"https://kelee.one/Resource/JavaScript/{stem}/{stem}_remove_ads.js")

    # 已知作者仓替身（jnlaoshu 等同款：Maasea / app2smile / ddgksf2013 / mieqq）
    KELEE_AUTHOR_ALTS: dict[str, list[str]] = {
        "YouTube_Subtitles_request.js": [
            "https://raw.githubusercontent.com/Maasea/sgmodule/master/Script/Youtube/youtube.request.js",
        ],
        "YouTube_Subtitles_response.js": [
            "https://raw.githubusercontent.com/Maasea/sgmodule/master/Script/Youtube/youtube.response.js",
        ],
        "YouTube_Composite_Subtitles_response.js": [
            "https://raw.githubusercontent.com/Maasea/sgmodule/master/Script/Youtube/youtube.response.js",
        ],
        "YouTube_Subtitles_Translate_response.js": [
            "https://raw.githubusercontent.com/Maasea/sgmodule/master/Script/Youtube/youtube.response.js",
        ],
        "Bilibili_proto_kokoryh.js": [
            "https://raw.githubusercontent.com/app2smile/rules/master/js/bilibili-proto.js",
        ],
        "bilibili.protobuf.js": [
            "https://raw.githubusercontent.com/app2smile/rules/master/js/bilibili-proto.js",
        ],
        "bilibili.helper.beta.js": [
            "https://raw.githubusercontent.com/Maasea/sgmodule/master/Script/Bilibili/bilibili.helper.js",
        ],
        "bilibili.helper.v2.beta.js": [
            "https://raw.githubusercontent.com/Maasea/sgmodule/master/Script/Bilibili/bilibili.helper.v2.js",
        ],
        "bilibili.airborne.js": [
            "https://raw.githubusercontent.com/kokoryh/Sparkle/master/dist/bilibili.json.js",
        ],
        "UnblockURLinWeChat.js": [
            "https://raw.githubusercontent.com/ddgksf2013/Scripts/master/weixin110.js",
        ],
        "replace-body.js": [
            "https://raw.githubusercontent.com/mieqq/mieqq/master/replace-body.js",
        ],
        "Tieba_remove_ads.js": [
            "https://raw.githubusercontent.com/app2smile/rules/master/js/tieba-json.js",
        ],
        "tieba-json.js": [
            "https://raw.githubusercontent.com/app2smile/rules/master/js/tieba-json.js",
        ],
        "NeteaseCloudMusic_remove_ads.js": [
            "https://kelee.one/Resource/JavaScript/NeteaseCloudMusic/NeteaseCloudMusic_remove_ads.js",
            "https://raw.githubusercontent.com/app2smile/rules/master/js/netease.js",
        ],
        "Auto_join_TF.js": [
            "https://raw.githubusercontent.com/NobyDa/Script/master/TestFlight/TestFlightAccount.js",
        ],
        "TF_keys.js": [
            "https://raw.githubusercontent.com/NobyDa/Script/master/TestFlight/TestFlightAccount.js",
        ],
    }
    if base in KELEE_AUTHOR_ALTS:
        out.extend(KELEE_AUTHOR_ALTS[base])

    # 通用：github raw → 本仓 sync _external（仅作备份，不优先）
    m = re.match(
        r"https?://raw\.githubusercontent\.com/([^/]+)/([^/]+)/([^/]+)/(.*)",
        url,
        re.I,
    )
    if m:
        owner, repo, ref, gpath = m.groups()
        for branch in ("sync", "main", BRANCH):
            out.append(
                f"https://raw.githubusercontent.com/oo226/egern-config/refs/heads/"
                f"{branch}/Scripts/_external/github-raw/{owner}/{repo}/{ref}/{gpath}"
            )
            out.append(
                f"https://raw.githubusercontent.com/oo226/egern-config/refs/heads/"
                f"{branch}/Scripts/{owner}/{Path(gpath).name}"
            )

    # Zenmo / 已知作者 → sync Scripts/<id>/（备份）
    for prefix, dest in (
        ("ZenmoFeiShi/Qx", "zenmofeishi"),
        ("fmz200/wool_scripts", "fmz200"),
        ("chavyleung/scripts", "chavyleung"),
        ("NobyDa/Script", "NobyDa"),
        ("WeiGiegie/666", "weigiegie"),
        ("liul0ng/quanx", "liul0ng"),
        ("Yuheng0101/X", "yuheng"),
        ("Yu9191/", "yu9191"),
    ):
        if prefix.lower() in url.lower() and base:
            for branch in ("sync", "main"):
                out.append(
                    f"https://raw.githubusercontent.com/oo226/egern-config/refs/heads/"
                    f"{branch}/Scripts/{dest}/{base}"
                )

    if base in KELEE_FALLBACKS:
        out.append(KELEE_FALLBACKS[base])
    for k, alt in KELEE_FALLBACKS.items():
        if k in url:
            out.append(alt)

    gm = re.match(
        r"https?://gist\.githubusercontent\.com/([^/]+)/([^/]+)/raw/(.*)",
        url,
        re.I,
    )
    if gm:
        user, gid, rest = gm.groups()
        for branch in ("sync", "main"):
            out.append(
                f"https://raw.githubusercontent.com/oo226/egern-config/refs/heads/"
                f"{branch}/Scripts/_external/gist/{user}/{gid}/raw/{rest}"
            )
    return list(dict.fromkeys(out))  # dedupe keep order


def _find_existing_js(basename: str) -> Path | None:
    """已在 Yuanban/zuozhe/*/js 或 sync 拉取目录中的同名脚本。"""
    if not basename:
        return None
    for p in ZUOZHE.glob(f"*/js/{basename}"):
        if p.is_file() and p.stat().st_size > 0:
            return p
    for p in ZUOZHE.glob(f"*/js/**/{basename}"):
        if p.is_file() and p.stat().st_size > 0:
            return p
    return None


def mirror_js(url: str, author: str, cache: dict[str, str]) -> str:
    """镜像到 zuozhe/<author>/js/<直白名>.js；**永远**返回本仓 URL（不留上游）。"""
    url = _normalize_js_url(url)
    if url in cache:
        return cache[url]
    low = url.lower()
    if "spotify.crack" in low or "/spotify-crack" in low:
        # Crack 不收录：指向本仓占位，避免合集挂上游
        ensure_author(author)
        dest = ZUOZHE / author / "js" / "跳过-SpotifyCrack.js"
        if not dest.is_file():
            dest.write_text(
                "// intentionally skipped: Spotify Crack\n"
                "console.log('spotify crack skipped');\n",
                encoding="utf-8",
            )
        local = f"{RAW}/{dest.relative_to(ROOT).as_posix()}"
        cache[url] = local
        return local

    ensure_author(author)
    name = _readable_js_name(url)
    dest = ZUOZHE / author / "js" / name
    # 已有同名：复用（WeatherKit/Maps 请用产品-版本前缀命名，见 apply-tools）
    if dest.is_file():
        STATS["js_ok"] += 1
        local = f"{RAW}/{dest.relative_to(ROOT).as_posix()}"
        cache[url] = local
        return local

    data: bytes | None = None
    used = ""
    for cand in _js_fetch_candidates(url):
        try:
            data = fetch(cand)
            used = cand
            break
        except Exception:
            continue
    if data is None:
        hit = _find_existing_js(Path(unquote(urlparse(url).path)).name)
        if hit is not None:
            data = hit.read_bytes()
            used = str(hit)

    if data is None:
        STATS["js_fail"].append(url)
        print(f"  ! js miss (仍自托管占位) {url}")
        data = (
            f"// MISSING mirror of:\n// {url}\n"
            "// 已自托管占位：不依赖上游；待补文件后重建\n"
            "throw new Error('script not mirrored: " + name + "');\n"
        ).encode()
        used = "placeholder"
    else:
        STATS["js_ok"] += 1
        print(f"  js/{author}/{name} ← {used if used != url else 'ok'}")

    save_bytes(dest, data, author=author, kind="js")
    local = f"{RAW}/{dest.relative_to(ROOT).as_posix()}"
    cache[url] = local
    return local


def rewrite_js_urls(text: str, author: str, cache: dict[str, str]) -> str:
    """仅重写 script-path / QX script-*；结果必须是本仓 URL。"""

    def _sub(m: re.Match[str]) -> str:
        url = m.group(2)
        # 已是本仓 raw，勿再镜像（否则会把 nsringo/js 拷进 local/js）
        if "raw.githubusercontent.com/oo226/egern-config" in url:
            return m.group(1) + url
        return m.group(1) + mirror_js(url, author, cache)

    text = SCRIPT_PATH_RE.sub(_sub, text)
    text = QX_SCRIPT_URL_RE.sub(_sub, text)
    return text


def fenliu_public_name(author: str, filename: str) -> str:
    """heji/danxiang 用的直白分流名：莫离-国内域名.list"""
    stem = Path(filename).stem
    ext = Path(filename).suffix
    cn = FENLIU_CN.get(filename) or FENLIU_CN.get(stem) or stem
    label = AUTHOR_CN.get(author, author)
    return f"{label}-{cn}{ext}"


# 18+ 识别（文件名 / merged-from 注释 / 脚本名）
ADULT_RE = re.compile(
    r"haijiao|huangdou|huangguo|insav|javhd|porntube|\blsp\b|pear|qiyoushe|skbz|tlsm|"
    r"xjh51|\bxv\b|1808|6lpu5|hanxiucao|mjgs|luolita|含羞|18pcs|18top|qiyou|"
    r"javbus|javday|hlbdy|4ksj|成人|18\+|罗莉|91fenglou|7semao|huanxiu|huanyu|qishe|"
    r"91porn|madou|xchina|黑料",
    re.I,
)

# Yuheng Tasks 直白名（含 18+ 签到/推送，单件在 zuozhe；合集见 shibajia 说明）
YUHENG_JS_NAMES = {
    "javbus.js": "巴士论坛签到.js",
    "javday.js": "JAVDay每日推荐.js",
    "hlbdy.js": "黑料不打烊.js",
    "1024.js": "1024技术推送.js",
    "4ksj.js": "4K世界签到.js",
    "52pojie.js": "吾爱破解签到.js",
    "60s.js": "60秒读懂世界.js",
    "AutoJoinTF.js": "自动加入TestFlight.js",
    "douban.js": "豆瓣.js",
    "moyu.js": "墨鱼签到.js",
    "ql.js": "青龙.js",
    "top.js": "TOP.js",
    "zippo.js": "Zippo签到.js",
    "qdreader.js": "起点读书.js",
    "bdyy.js": "笔趣阁阅读.js",
    "95598.js": "国家电网95598.js",
    "cloud139.js": "移动云盘139.js",
    "capture.js": "移动云盘抓参.js",
    "meitu.js": "美图秀秀.js",
    "step.js": "小米运动步数.js",
    "eshop.js": "Eshop.js",
}


def _chunk_is_adult(chunk: str) -> bool:
    first = chunk.splitlines()[0] if chunk.strip() else ""
    js_names = " ".join(re.findall(r"[\w.-]+\.js", chunk)[:12])
    return bool(ADULT_RE.search(first) or ADULT_RE.search(js_names))


def _split_section_lines(lines: list[str]) -> tuple[list[str], list[str]]:
    """按 # >>> merged / # --- file.js --- 把 section 行拆成 (sfw, adult)。"""
    text = "\n".join(lines)
    if "# >>> merged from " in text:
        chunks = re.split(r"(?=^# >>> merged from )", text, flags=re.M)
    elif re.search(r"^# --- .+\.js ---", text, re.M):
        chunks = re.split(r"(?=^# --- .+\.js ---)", text, flags=re.M)
    else:
        blob = text.strip()
        if not blob:
            return [], []
        if _chunk_is_adult(blob):
            return [], lines[:]
        return lines[:], []

    sfw: list[str] = []
    adult: list[str] = []
    for i, ch in enumerate(chunks):
        if not ch.strip():
            continue
        # 首段若无 marker，按内容归类（可能是无注释的前导规则）
        is_marker = ch.lstrip().startswith("# >>>") or bool(
            re.match(r"^# --- .+\.js ---", ch.lstrip())
        )
        if i == 0 and not is_marker:
            (adult if _chunk_is_adult(ch) else sfw).extend(ch.splitlines())
            continue
        (adult if _chunk_is_adult(ch) else sfw).extend(ch.splitlines())
    return sfw, adult


def _filter_mitm_hostnames(hostname_line: str) -> tuple[str, str]:
    """把 hostname = %APPEND% a, b, c 拆成 (日常, 18+)。识别不出时两边都保留。"""
    m = re.match(r"^(\s*hostname\s*=\s*%APPEND%\s*)(.+)$", hostname_line, re.I)
    if not m:
        return hostname_line, hostname_line
    prefix, rest = m.group(1), m.group(2)
    hosts = [h.strip() for h in rest.split(",") if h.strip()]
    sfw_h = [h for h in hosts if not ADULT_RE.search(h)]
    adult_h = [h for h in hosts if ADULT_RE.search(h)]
    # 拆不出成人主机时：日常保留全量，成人也保留全量（避免漏 MITM）
    if not adult_h:
        return hostname_line, hostname_line
    sfw_line = prefix + ", ".join(sfw_h) if sfw_h else ""
    adult_line = prefix + ", ".join(adult_h)
    return sfw_line, adult_line


def split_module_adult(text: str) -> tuple[str, str]:
    """按分段注释拆成 (日常/SFW正文, 18+正文)，保留 section 结构。"""
    head_lines: list[str] = []
    body_start = 0
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("[") and line.endswith("]"):
            body_start = i
            break
        head_lines.append(line)
    else:
        if ADULT_RE.search(text[:800]):
            return ("", text if text.endswith("\n") else text + "\n")
        return (text if text.endswith("\n") else text + "\n", "")

    # 无分段标记且整体非 18+ 分类 → 整份日常
    head_blob = "\n".join(head_lines)
    has_markers = ("# >>> merged from " in text) or bool(
        re.search(r"^# --- .+\.js ---", text, re.M)
    )
    if not has_markers:
        if ADULT_RE.search(head_blob):
            return ("", text if text.endswith("\n") else text + "\n")
        return (text if text.endswith("\n") else text + "\n", "")

    sections = parse_sections(text)
    sfw_sec: dict[str, list[str]] = {}
    adult_sec: dict[str, list[str]] = {}

    for sec, sec_lines in sections.items():
        if sec.upper() == "MITM":
            sfw_m: list[str] = []
            adult_m: list[str] = []
            for line in sec_lines:
                if re.match(r"^\s*hostname\s*=", line, re.I):
                    s_line, a_line = _filter_mitm_hostnames(line)
                    if s_line:
                        sfw_m.append(s_line)
                    if a_line:
                        adult_m.append(a_line)
                else:
                    sfw_m.append(line)
                    adult_m.append(line)
            if sfw_m:
                sfw_sec[sec] = sfw_m
            if adult_m:
                adult_sec[sec] = adult_m
            continue

        s_lines, a_lines = _split_section_lines(sec_lines)
        if s_lines:
            sfw_sec[sec] = s_lines
        if a_lines:
            adult_sec[sec] = a_lines

    def _emit(name: str, desc: str, category: str | None, secmap: dict[str, list[str]]) -> str:
        if not secmap:
            return ""
        # 至少要有规则行（不只是空 MITM）
        has_rule = any(
            any(l.strip() and not l.strip().startswith("#") for l in ls)
            for k, ls in secmap.items()
            if k.upper() != "MITM"
        )
        if not has_rule and "MITM" in {k.upper() for k in secmap}:
            # 仅 MITM 无脚本 → 不算独立合集
            return ""
        if not has_rule and not secmap:
            return ""
        out = [f"#!name={name}", f"#!desc={desc}"]
        if category:
            out.append(f"#!category={category}")
        out.append("")
        # 保持常见顺序
        order = ["Script", "Rule", "URL Rewrite", "MITM", "Map Local", "General"]
        seen = set()
        for key in order:
            for sec, ls in secmap.items():
                if sec.lower() == key.lower() and sec not in seen:
                    out.append(f"[{sec}]")
                    out.extend(ls)
                    out.append("")
                    seen.add(sec)
        for sec, ls in secmap.items():
            if sec not in seen:
                out.append(f"[{sec}]")
                out.extend(ls)
                out.append("")
        return "\n".join(out).rstrip() + "\n"

    sfw = _emit("解锁日常", "已剥离18+（见 heji/shibajia）", None, sfw_sec)
    adult = _emit("18+解锁", "成人向，与日常解锁分开订阅", "18+", adult_sec)
    return sfw, adult


def write_split_unlock(author: str, src_name: str, cache: dict[str, str]) -> None:
    """从完整解锁模块写出「日常」与「18+」两份。"""
    src = ZUOZHE / author / "mokuai" / src_name
    if not src.is_file():
        return
    raw = src.read_text(encoding="utf-8", errors="replace")
    sfw, adult = split_module_adult(raw)
    base = src.stem.replace("-unlock", "").replace("_unlock", "")
    if sfw:
        p = ZUOZHE / author / "mokuai" / f"{base}-unlock-日常.sgmodule"
        # 再跑一遍 URL 自托管
        sfw = rewrite_js_urls(sfw, author, cache)
        p.write_text(sfw, encoding="utf-8")
        print(f"  {author}/mokuai/{p.name}")
    if adult:
        p = ZUOZHE / author / "mokuai" / f"{base}-unlock-18加.sgmodule"
        adult = rewrite_js_urls(adult, author, cache)
        p.write_text(adult, encoding="utf-8")
        print(f"  {author}/mokuai/{p.name}")


def _git_show_sync(rel: str) -> bytes:
    """本地 origin/sync 读文件（比逐个 HTTP 快）。"""
    return subprocess.check_output(
        ["git", "show", f"origin/sync:{rel}"],
        cwd=ROOT,
        stderr=subprocess.DEVNULL,
    )


def mirror_sync_scripts_tree(
    author: str,
    sync_prefix: str,
    name_map: dict[str, str] | None = None,
    *,
    also_json: bool = False,
) -> int:
    """git ls-tree origin/sync 下列出的 Scripts 树 → zuozhe/<author>/js（直白名）。"""
    name_map = name_map or {}
    try:
        out = subprocess.check_output(
            ["git", "ls-tree", "-r", "--name-only", "origin/sync", sync_prefix],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception as exc:
        print(f"  ! ls-tree {sync_prefix}: {exc}")
        return 0
    paths = ensure_author(author)
    n = 0
    for rel in out.splitlines():
        rel = rel.strip()
        if not (rel.endswith(".js") or (also_json and rel.endswith(".json"))):
            continue
        fname = Path(rel).name
        clear = name_map.get(fname) or name_map.get(rel) or fname
        try:
            data = _git_show_sync(rel)
        except Exception as exc:
            print(f"  ! {author}/js {fname}: {exc}")
            continue
        dest = paths["js"] / clear
        if dest.exists() and dest.stat().st_size == len(data):
            n += 1
            continue
        if dest.exists():
            dest = paths["js"] / f"{Path(rel).parent.name}-{clear}"
        save_bytes(dest, data, author=author, kind="js")
        n += 1
        print(f"  {author}/js/{dest.name}")
    return n


def mirror_sync_modules_tree(author: str, sync_prefix: str) -> int:
    """Modules/<author>/ 下 sgmodule → zuozhe/<author>/mokuai。"""
    try:
        out = subprocess.check_output(
            ["git", "ls-tree", "-r", "--name-only", "origin/sync", sync_prefix],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception as exc:
        print(f"  ! ls-tree {sync_prefix}: {exc}")
        return 0
    paths = ensure_author(author)
    n = 0
    for rel in out.splitlines():
        rel = rel.strip()
        if not rel.endswith((".sgmodule", ".module", ".conf")):
            continue
        fname = Path(rel).name
        try:
            data = _git_show_sync(rel)
        except Exception as exc:
            print(f"  ! {author}/mokuai {fname}: {exc}")
            continue
        dest = paths["mokuai"] / fname
        save_bytes(dest, data, author=author, kind="mokuai")
        n += 1
        print(f"  {author}/mokuai/{fname}")
    return n


def mirror_github_scripts(
    author: str,
    repo: str,
    prefix: str,
    name_map: dict[str, str] | None = None,
    *,
    also_json: bool = False,
    branch: str = "main",
) -> int:
    """从作者 GitHub 仓拉 Scripts（优先于 sync 日更备份）。"""
    name_map = name_map or {}
    api = (
        f"https://api.github.com/repos/{repo}/git/trees/{quote(branch)}?recursive=1"
    )
    try:
        tree = json.loads(fetch(api).decode())["tree"]
    except Exception as exc:
        print(f"  ! github tree {repo}: {exc}")
        return 0
    paths = ensure_author(author)
    raw_base = f"https://raw.githubusercontent.com/{repo}/{branch}/"
    n = 0
    for t in tree:
        if t.get("type") != "blob":
            continue
        rel = t["path"]
        if not rel.startswith(prefix.rstrip("/") + "/") and rel != prefix.rstrip("/"):
            if not rel.startswith(prefix):
                continue
        fname = Path(rel).name
        if rel.endswith(".js"):
            pass
        elif also_json and fname == "boxjs.json":
            pass
        else:
            continue
        parts = rel.split("/")
        if "node_modules" in parts or ".git" in parts or "src" in parts:
            continue
        if fname.endswith(
            (".config.js", "rollup.config.js", "rollup.default.config.js",
             "rollup.dev.config.js", "package.json", "package-lock.json")
        ):
            continue
        clear = name_map.get(fname) or name_map.get(rel) or fname
        try:
            data = fetch(raw_base + quote(rel, safe="/"))
        except Exception as exc:
            print(f"  ! {author}/js {fname}: {exc}")
            continue
        dest = paths["js"] / clear
        if dest.exists() and dest.stat().st_size == len(data):
            n += 1
            continue
        if dest.exists():
            dest = paths["js"] / f"{Path(rel).parent.name}-{clear}"
        save_bytes(dest, data, author=author, kind="js")
        n += 1
        print(f"  {author}/js/{dest.name} ← {repo}")
    return n


def mirror_laoshu(cache: dict[str, str]) -> None:
    """jnlaoshu/MySelf Egern/Module — 精选去广告 yaml（作者仓直拉）。"""
    paths = ensure_author("laoshu")
    for fname in LAOSHU_EGERN_MODULES:
        url = LAOSHU_RAW + quote(fname, safe="/")
        try:
            raw = fetch(url)
        except Exception as exc:
            print(f"  ! laoshu {fname}: {exc}")
            continue
        dest = paths["mokuai"] / fname
        save_bytes(dest, raw, author="laoshu", kind="mokuai")
        rewrite_js_urls(raw.decode("utf-8", errors="replace"), "laoshu", cache)
        print(f"  laoshu/mokuai/{fname}")
    (paths["mokuai"] / "README.md").write_text(
        "老书 jnlaoshu/MySelf Egern/Module（作者仓直拉）。\n"
        "风格：Rule + Map Local 为主，脚本多用 Maasea/墨鱼/app2smile；\n"
        "部分仍引用 kelee.one（构建时自托管，Surge UA 拉取）。\n"
        "进 heji/quguanggao。\n"
        "上游：https://github.com/jnlaoshu/MySelf/tree/main/Egern/Module\n",
        encoding="utf-8",
    )


def assert_self_hosted() -> None:
    """合集里不得残留外站 script-path（完全自依赖）。"""
    bad: list[str] = []
    for path in HEJI.glob("*.module"):
        text = path.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"script-path\s*=\s*(\S+)", text, re.I):
            u = m.group(1).strip().strip('"').strip("'")
            if not u.startswith("http"):
                continue
            if "raw.githubusercontent.com/oo226/egern-config" not in u:
                bad.append(f"{path.name}: {u[:120]}")
    if bad:
        print(f"WARN self-host leaks: {len(bad)}")
        for line in bad[:20]:
            print(" ", line)
        STATS["self_host_leaks"] = len(bad)
    else:
        print("self-host OK: heji script-path 全部指向本仓")
        STATS["self_host_leaks"] = 0


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
                "- `zenmofeishi/` — 怎么肥事签到（PingMe/一点万象/NodeSeek…，中文文件名）",
                "- `js/` — 其他 sync 签到脚本（fmz200 等）",
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
                "工具单件。**BoxJs / iRingo 天气·地图原版 / AntiRevoke** 已并进 `heji/jiesuo`；",
                "Sub-Store / Script Hub 为 Egern 原生 yaml，Profile 单独启用；定位/其他仍单件。",
                "",
                "- `official/` — QingRex Official 工具/增强（已排除去广告与签到）",
                "- `local/` — BoxJs、Sub-Store/ScriptHub（Egern yaml）、IRingo、AntiRevoke、测速等",
                "- `ibl3nd/` — IBL3ND 小组件 + Surge 模块 + plugin-hub（插件跳转）",
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
    """单件备份：文件名用「作者中文-原名」，一眼能懂。"""
    for kind in ("fenliu", "mokuai", "js"):
        (DAN / kind).mkdir(parents=True, exist_ok=True)
    for author_dir in sorted(ZUOZHE.iterdir()):
        if not author_dir.is_dir() or author_dir.name == "README.md":
            continue
        author = author_dir.name
        label = AUTHOR_CN.get(author, author)
        for kind in ("fenliu", "mokuai"):
            src_dir = author_dir / kind
            if not src_dir.is_dir():
                continue
            for f in src_dir.iterdir():
                if f.is_file() and f.name != "README.md":
                    if kind == "fenliu":
                        dest = DAN / kind / fenliu_public_name(author, f.name)
                    else:
                        dest = DAN / kind / f"{label}-{f.name}"
                    shutil.copy2(f, dest)
        official = author_dir / "official"
        if official.is_dir():
            for f in official.iterdir():
                if f.is_file() and f.name != "README.md":
                    dest = DAN / "mokuai" / f"{label}-Official-{f.name}"
                    shutil.copy2(f, dest)
        js_dir = author_dir / "js"
        if js_dir.is_dir():
            for f in js_dir.rglob("*"):
                if f.is_file() and f.name != "README.md":
                    dest = DAN / "js" / f"{label}-{f.name}"
                    # 重名加父目录
                    if dest.exists():
                        dest = DAN / "js" / f"{label}-{f.parent.name}-{f.name}"
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, dest)
    for root, prefix, kind_default in (
        (QIANDAO, "签到", "mokuai"),
        (QITA, "其他", "mokuai"),
    ):
        if not root.is_dir():
            continue
        for bucket in sorted(root.iterdir()):
            if not bucket.is_dir():
                continue
            kind = "js" if bucket.name == "js" else kind_default
            for f in bucket.rglob("*"):
                if f.is_file() and f.name != "README.md":
                    dest = DAN / kind / f"{prefix}-{bucket.name}-{f.name}"
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, dest)
    (DAN / "README.md").write_text(
        "单件备份：文件名「作者-用途」。内容与 zuozhe/qiandao/qita 一致。\n",
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

    # 4b) 老书 jnlaoshu Egern 精选（Video/Music/YouTube…）
    laoshu_m = ZUOZHE / "laoshu" / "mokuai"
    for fname in LAOSHU_EGERN_MODULES:
        path = laoshu_m / fname
        if not path.is_file():
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        rewritten = rewrite_js_urls(raw, "laoshu", cache)
        title, _ = strip_module_header(raw)
        bags.append((f"老书 · {title or path.stem}", parse_sections(rewritten)))

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

    # 7) 怎么肥事净化
    zm = ZUOZHE / "zenmofeishi" / "mokuai"
    for fname in ZENMO_AD_CONFS:
        path = zm / fname
        if not path.is_file():
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        rewrite_js_urls(raw, "zenmofeishi", cache)
        surge = qx_conf_to_surge_body(raw, script_prefix="zenmo-" + path.stem[:10])
        surge = rewrite_js_urls(surge, "zenmofeishi", cache)
        bags.append((f"怎么肥事 · {path.stem}", parse_sections(surge)))

    text = merge_section_bags(
        bags,
        name="去广告合集",
        desc="可莉+墨鱼+毒奶+老书+BMJ+奶思+怎么肥事（原文，脚本全自托管）",
        notes=[
            "# 合集类型: 去广告",
            "# 置顶基础: 1)广告平台拦截器 2)可莉广告过滤器 —— 须最先生效",
            "# 然后: 可莉各 App「××去广告」原样分段",
            "# 然后: 墨鱼 AdBlock/NBPro + 毒奶 + 老书(jnlaoshu) + BMJ + 奶思 + 怎么肥事净化",
            "# 脚本 URL 全部指向本仓 Yuanban/zuozhe/*/js（不依赖上游在线）",
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

    # 怎么肥事解锁（有 rewrite conf 的进合集；纯 js 见 zuozhe/zenmofeishi/js）
    zm = ZUOZHE / "zenmofeishi" / "mokuai"
    for fname in ZENMO_UNLOCK_CONFS:
        path = zm / fname
        if not path.is_file():
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        rewrite_js_urls(raw, "zenmofeishi", cache)
        surge = qx_conf_to_surge_body(raw, script_prefix="zenmo-js-" + path.stem[:8])
        surge = rewrite_js_urls(surge, "zenmofeishi", cache)
        bags.append((f"怎么肥事 · {path.stem}", parse_sections(surge)))

    extras = [
        ("iewha", "Unlock.sgmodule", "iEwha · Unlock"),
        ("iewha", "Script.sgmodule", "iEwha · Script"),
        ("chxm", "Collections.sgmodule", "chxm1023 · Collections 解锁"),
        ("miranquil", "qq-c-pc-page.sgmodule", "miranquil · QQ解锁"),
        ("local", "spotify-unlock.sgmodule", "本仓 · Spotify Eevee VIP"),
        ("local", "patches-unlock.sgmodule", "本仓 · 屏蔽更新/P12 等"),
        ("local", "antirevoke.sgmodule", "Salem · AntiRevoke 苹果证书"),
        ("local", "patches-alicloud.sgmodule", "本仓 · 阿里云盘倍速"),
        ("local", "boxjs.sgmodule", "Chavy · BoxJs"),
        ("local", "script-hub.sgmodule", "Script Hub · 重写/规则转换"),
        ("local", "plugin-hub.sgmodule", "IBL3ND · 插件跳转 Egern"),
        ("local", "tg-redirect.sgmodule", "Telegram · 外链跳转飞机"),
        ("local", "iringo-weather.sgmodule", "NSRingo · WeatherKit 原版"),
        ("local", "iringo-maps.sgmodule", "NSRingo · Maps 原版"),
        # 日常解锁：已剥离 18+（完整/18+ 见 heji/shibajia）
        ("weigiegie", "weigiegie-unlock-日常.sgmodule", "WeiGiegie · 解锁日常"),
        ("liulong", "liul0ng-unlock.sgmodule", "liul0ng · 解锁合集"),
        ("yu9191", "yu9191-rewrite-unlock-日常.sgmodule", "Yu9191 · Rewrite 日常解锁"),
        ("yu9191", "yu9191-ShortcutStudio.sgmodule", "Yu9191 · ShortcutStudio"),
        # 奶思 unlock-extra 含 Spotify Crack，解锁合集不用；原件仍在 zuozhe/naisi 备份
        # Sub-Store 脚本已在 iEwha · Script；Script Hub 见上
        # iRingo 定位/其他：qita/local 单件，不进合集
    ]
    for author, fname, label in extras:
        path = ZUOZHE / author / "mokuai" / fname
        if not path.is_file():
            # 回退：尚未拆分时用完整版（避免空袋）
            if fname.endswith("-日常.sgmodule"):
                alt = fname.replace("-日常.sgmodule", ".sgmodule")
                path = ZUOZHE / author / "mokuai" / alt
            if not path.is_file():
                continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        rewritten = rewrite_js_urls(raw, author, cache)
        bags.append((label, parse_sections(rewritten)))

    text = merge_section_bags(
        bags,
        name="解锁增强合集",
        desc="可莉解锁 + 墨鱼微信110/VIP/Function + iEwha/chxm/…（不含18+，见 shibajia）",
        notes=[
            "# 合集类型: 解锁增强（日常/SFW）",
            "# 18+ 成人向请订阅 heji/shibajia.module",
            "# 分段注释标明每个作者/模块用途",
            "# 墨鱼: UnblockURLinWeChat(微信110) + ForOwnUse(专属VIP) + Function(TF/Emby/…)",
            "# Spotify 用 Eevee（spotify-unlock），不含 Crack",
            "# Yu9191/WeiGiegie 已剥离 18+ 分段",
            "# 工具: Sub-Store + Script Hub + BoxJs + 插件跳转 + TG外链 + iRingo 天气/地图 + AntiRevoke + 屏蔽更新/P12",
            "# iRingo 定位/其他仍单件（qita/local），不进本合集",
            "# 已跳过可莉近重复: Google重定向 / 拦截HTTPDNS / Spotify歌词翻译（单件仍在 zuozhe）",
        ],
    )
    (HEJI / "jiesuo.module").write_text(text, encoding="utf-8")
    STATS["heji"]["jiesuo"] = len(bags)
    print(f"heji jiesuo bags={len(bags)}")


def heji_shibajia(cache: dict[str, str]) -> None:
    """18+ 单独合集：Yu9191 Rewrite 成人段 + WeiGiegie 成人段。"""
    bags: list[tuple[str, dict[str, list[str]]]] = []
    extras = [
        ("yu9191", "yu9191-rewrite-unlock-18加.sgmodule", "Yu9191 · 18+ Rewrite 解锁"),
        ("weigiegie", "weigiegie-unlock-18加.sgmodule", "WeiGiegie · 18+ 解锁"),
    ]
    for author, fname, label in extras:
        path = ZUOZHE / author / "mokuai" / fname
        if not path.is_file():
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        rewritten = rewrite_js_urls(raw, author, cache)
        bags.append((label, parse_sections(rewritten)))

    if not bags:
        print("heji shibajia SKIP (no adult splits)")
        return

    text = merge_section_bags(
        bags,
        name="18+解锁合集",
        desc="成人向 Rewrite/解锁，与日常 jiesuo 分开订阅（Yu9191 为主，WeiGiegie 少量）",
        notes=[
            "# 合集类型: 18+",
            "# 主要来源: Yu9191/Rewrite（haijiao/javhd/porntube/黄豆…）",
            "# 另含: WeiGiegie 18pcs/18top/91fenglou/含羞/mjgs/奇游 等",
            "# Yuheng 巴士/JAVDay/黑料/1024/4K世界 为签到推送脚本，见 zuozhe/yuheng/js（不做 rewrite 合集）",
            "# 日常解锁请用 heji/jiesuo.module",
        ],
    )
    (HEJI / "shibajia.module").write_text(text, encoding="utf-8")
    STATS["heji"]["shibajia"] = len(bags)
    print(f"heji shibajia bags={len(bags)}")


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
                dest = out / fenliu_public_name(author_dir.name, f.name)
                shutil.copy2(f, dest)
                n += 1
    lines = [
        "# 分流规则集（单件）",
        "",
        "文件名：`作者-用途.扩展名`（一眼能懂）。原料在 `zuozhe/*/fenliu/`。",
        "",
        "## 怎么选",
        "",
        "| 文件名前缀 | 适合 |",
        "|------------|------|",
        "| `Repcz-` | **骨架**：国内/代理/流媒体（Egern 原生） |",
        "| `莫离-` | 分类多：Ads/CDN/Claude/Steam… |",
        "| `Sukka-` | reject/AI/CDN/流媒体/Apple |",
        "| `Loyalsoldier-` | **大名单底**：直连/代理/GFW/广告拒绝 |",
        "| `VPSDance-` | AI 专项最全 |",
        "| `BMJ-` | 细分补洞：国内Max/Steam/流媒体… |",
        "",
        "广告拒绝类与去广告合集会叠，别重复全开。全部文件已自托管，不依赖上游在线。",
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


def mirror_zenmofeishi(cache: dict[str, str]) -> None:
    """怎么肥事 ZenmoFeiShi/Qx：js + snippet→conf，中文直白名；签到进 qiandao。"""
    paths = ensure_author("zenmofeishi")
    # 1) 上游 tree
    try:
        tree = json.loads(
            fetch(
                "https://api.github.com/repos/ZenmoFeiShi/Qx/git/trees/main?recursive=1"
            ).decode()
        )["tree"]
    except Exception as exc:
        print(f"  ! zenmo tree: {exc}")
        tree = []
    upstream_files = {
        t["path"]: t
        for t in tree
        if t.get("type") == "blob" and not t["path"].endswith("README.md")
    }
    # 2) sync 可能多出的旧脚本
    sync_extra = (
        "LaiChong.js", "SoulSing.js", "iios_checkin.js", "XMLYVIP.js",
    )
    raw_base = "https://raw.githubusercontent.com/ZenmoFeiShi/Qx/main/"

    for fname, clear in ZENMO_JS_NAMES.items():
        url = raw_base + fname
        if fname in sync_extra and fname not in upstream_files:
            url = f"{SYNC_RAW}/Scripts/zenmofeishi/{fname}"
        elif fname not in upstream_files and fname not in sync_extra:
            # 仍尝试 sync
            url = f"{SYNC_RAW}/Scripts/zenmofeishi/{fname}"
        try:
            data = fetch(url)
        except Exception:
            try:
                data = fetch(f"{SYNC_RAW}/Scripts/zenmofeishi/{fname}")
            except Exception as exc:
                print(f"  ! zenmo js {fname}: {exc}")
                continue
        dest = paths["js"] / clear
        save_bytes(dest, data, author="zenmofeishi", kind="js")
        print(f"  zenmofeishi/js/{clear}")
        if clear in ZENMO_QIANDAO_JS:
            save_qiandao("zenmofeishi", clear, data)

    for fname, clear in ZENMO_SNIPPET_NAMES.items():
        if fname not in upstream_files:
            continue
        try:
            raw = fetch(raw_base + fname).decode("utf-8", errors="replace")
        except Exception as exc:
            print(f"  ! zenmo snippet {fname}: {exc}")
            continue
        # 原样存 conf + 抽脚本自托管
        rewrite_js_urls(raw, "zenmofeishi", cache)
        dest = paths["mokuai"] / clear
        save_bytes(dest, raw.encode("utf-8"), author="zenmofeishi", kind="mokuai")
        print(f"  zenmofeishi/mokuai/{clear}")

    (paths["mokuai"] / "README.md").write_text(
        "怎么肥事 ZenmoFeiShi/Qx — 净化/解锁重写（中文文件名）。\n"
        "签到脚本见 `js/` 与 `Yuanban/qiandao/zenmofeishi/`。\n"
        "上游：https://github.com/ZenmoFeiShi/Qx（已全量自托管，不依赖在线）。\n",
        encoding="utf-8",
    )
    (QIANDAO / "zenmofeishi" / "README.md").write_text(
        "怎么肥事签到脚本（单件，无合集）。抓参+签到二合一的，开 MITM 抓一次再跑定时。\n",
        encoding="utf-8",
    )


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
                "  heji/                   # 合集 + 分流清单",
                "    quguanggao / qukaiping / jiesuo / shibajia(18+) / zhuacan / fenliu/",
                "```",
                "",
                "## 原则",
                "",
                "- `zuozhe` / `danxiang` / `qiandao` / `qita`：**原作者照搬**，文件字节不改",
                "- `heji`：只拼装 + Fan.a.tail 分段；**规则正文不改**；script URL 改指本仓",
                "- 去广告置顶：`广告平台拦截器` → `可莉广告过滤器`",
                "- **18+ 单独 `shibajia`，不进日常 `jiesuo`**",
                "- **签到 / 其他脚本 / IBL3ND 小组件不做合集**",
                "",
                "## 订阅（合集）",
                "",
                "```",
                f"{RAW}/Yuanban/heji/quguanggao.module",
                f"{RAW}/Yuanban/heji/qukaiping.module",
                f"{RAW}/Yuanban/heji/jiesuo.module",
                f"{RAW}/Yuanban/heji/shibajia.module",
                f"{RAW}/Yuanban/heji/zhuacan.module",
                "```",
                "",
                "签到：`Yuanban/qiandao/`　其他/小组件：`Yuanban/qita/`　分流：`heji/fenliu/README.md`",
                "",
                "可莉：模块←QingRex 作者仓；js←kelee.one（Surge UA，不是 sync）。",
                "Yu9191：作者仓若删则用 sync 防删；Yuheng←Yuheng0101/X；老书←jnlaoshu/MySelf。",
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
        f"脚本镜像成功约 {STATS['js_ok']}，占位/失败 {len(STATS['js_fail'])}（仍写本仓占位，不留外站）",
        f"合集外站泄漏: {STATS.get('self_host_leaks', '?')}",
        "",
        "## 自依赖",
        "",
        "- 所有 `script-path` 指向 `raw.githubusercontent.com/oo226/egern-config/.../Yuanban/`",
        "- 上游删库不影响：规则与脚本都在本仓",
        "- 文件名：`作者-用途` / 中文直白名（怎么肥事、分流 heji 等）",
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
        "## 18+",
        "",
        "- `heji/shibajia`：Yu9191 Rewrite 成人段 + WeiGiegie 少量（18pcs/含羞/mjgs…）",
        "- 日常解锁 `jiesuo` 已剥离上述分段",
        "- Yuheng 巴士/JAVDay/黑料/1024/4K世界：签到推送脚本在 `zuozhe/yuheng/js`",
        "",
        "## 可莉来源说明（不是 sync 日更）",
        "",
        "- **模块**：`QingRex/LoonKissSurge` 作者仓直拉 → `zuozhe/keli/mokuai`",
        "- **脚本 CDN**：`kelee.one`（不在 GitHub 仓内）；需 **Surge UA**，QX UA 会 403",
        "- 规则/Map Local **不依赖** js，可莉主体（域名拦截）一直有效",
        "- js 拉不到时才写占位；已用 Surge UA + Maasea/app2smile/墨鱼替身补齐绝大多数",
        "",
        "## 老书 jnlaoshu",
        "",
        "- `zuozhe/laoshu` ← https://github.com/jnlaoshu/MySelf/tree/main/Egern/Module",
        "- Video/Music/YouTube 等进 `heji/quguanggao`（Rule+Map Local 为主）",
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
        "拼音：keli可莉 naisi奶思 moyu墨鱼 dunai毒奶 moli莫离 zenmofeishi怎么肥事 "
        "nobyda blackmatrix7 loyalsoldier iewha chxm weigiegie liulong yu9191 "
        "repcz sukka vpsdance yuheng laoshu local miranquil\n"
        "原则：优先作者仓直拉；sync 仅备份；文件名直白；合集 script-path 全自托管。\n",
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

    print("=== zuozhe/zenmofeishi（怎么肥事）===")
    mirror_zenmofeishi(cache)

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

    print("=== zuozhe/yu9191 + yuheng（作者仓优先，删库则 sync 防删备份）===")
    # Yu9191/Rewrite 目前 GitHub 404（已删/私有）→ sync Scripts/yu9191 是防删镜像
    n_yu = mirror_github_scripts("yu9191", "Yu9191/Rewrite", "", also_json=False)
    if n_yu == 0:
        n_yu = mirror_sync_scripts_tree("yu9191", "Scripts/yu9191")
        print(f"  yu9191: 作者仓不可用，用 sync 防删镜像 js={n_yu}")
    # Yuheng0101/X 仍在 → 作者仓直拉
    n_yh = mirror_github_scripts(
        "yuheng", "Yuheng0101/X", "Tasks", YUHENG_JS_NAMES, also_json=True
    )
    if n_yh == 0:
        n_yh = mirror_sync_scripts_tree(
            "yuheng", "Scripts/yuheng", YUHENG_JS_NAMES, also_json=True
        )
        print(f"  yuheng fallback sync js={n_yh}")
    n_yhm = 0
    try:
        yh_api = "https://api.github.com/repos/Yuheng0101/X/git/trees/main?recursive=1"
        yh_tree = json.loads(fetch(yh_api).decode())["tree"]
        paths_yh = ensure_author("yuheng")
        for t in yh_tree:
            if t.get("type") != "blob":
                continue
            rel = t["path"]
            if not rel.endswith(".sgmodule"):
                continue
            # Tasks/.../profiles/*.sgmodule 或 Scripts/*/*.sgmodule
            if not (rel.startswith("Tasks/") or rel.startswith("Scripts/")):
                continue
            fname = Path(rel).name
            # 避免 Scripts/*/surge.sgmodule 与 Tasks 重名互相覆盖
            if fname in {"surge.sgmodule", "scripable.sgmodule"}:
                fname = f"{Path(rel).parent.name}-{fname}"
            try:
                data = fetch(
                    f"https://raw.githubusercontent.com/Yuheng0101/X/main/{quote(rel, safe='/')}"
                )
            except Exception:
                continue
            save_bytes(paths_yh["mokuai"] / fname, data, author="yuheng", kind="mokuai")
            n_yhm += 1
            print(f"  yuheng/mokuai/{fname} ← Yuheng0101/X")
    except Exception as exc:
        print(f"  ! yuheng author modules: {exc}")
    if n_yhm == 0:
        n_yhm = mirror_sync_modules_tree("yuheng", "Modules/yuheng")
    print(f"  yu9191 js={n_yu}  yuheng js={n_yh} mokuai+={n_yhm}")
    (ZUOZHE / "yu9191" / "mokuai" / "README.md").write_text(
        "Yu9191：优先 Yu9191/Rewrite 作者仓；若 404 则用 sync 防删镜像（Scripts/yu9191）。\n"
        "- `yu9191-rewrite-unlock.sgmodule` 完整版（含 18+）\n"
        "- `yu9191-rewrite-unlock-日常.sgmodule` → heji/jiesuo\n"
        "- `yu9191-rewrite-unlock-18加.sgmodule` → heji/shibajia\n",
        encoding="utf-8",
    )
    (ZUOZHE / "yuheng" / "mokuai" / "README.md").write_text(
        "Yuheng0101/X（作者仓直拉）。\n"
        "- mokuai：Tasks/Scripts 下 sgmodule + 起点抓参\n"
        "- js：Tasks（巴士/JAVDay/黑料/1024/4K世界…中文直白名）\n"
        "上游：https://github.com/Yuheng0101/X\n",
        encoding="utf-8",
    )

    print("=== zuozhe/laoshu（jnlaoshu Egern 精选）===")
    mirror_laoshu(cache)

    print("=== 拆分 18+（Yu9191 / WeiGiegie）===")
    write_split_unlock("yu9191", "yu9191-rewrite-unlock.sgmodule", cache)
    write_split_unlock("weigiegie", "weigiegie-unlock.sgmodule", cache)

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
    heji_shibajia(cache)
    heji_zhuacan(cache)
    heji_fenliu()

    write_docs()
    assert_self_hosted()
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
        "self_host_leaks=", STATS.get("self_host_leaks"),
    )


if __name__ == "__main__":
    main()
