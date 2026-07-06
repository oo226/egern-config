#!/usr/bin/env python3
"""Merge mirrored author sgmodules into deduplicated collection supplements."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from boxjs_player import strip_boxjs_module_arguments
from paths import MODULES, UPSTREAM_CACHE

_merge_spec = importlib.util.spec_from_file_location(
    "merge_adblock_modules", Path(__file__).with_name("merge-adblock-modules.py")
)
_merge = importlib.util.module_from_spec(_merge_spec)
assert _merge_spec.loader is not None
_merge_spec.loader.exec_module(_merge)
build_merged_module = _merge.build_merged_module
mirror_script_paths = _merge.mirror_script_paths

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

CONFIG = Path(__file__).with_name("author-repos.yaml")

UNLOCK_KEYWORDS = (
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
)

FMZ200_SKIP_ADBLOCK = frozenset(
    {
        "blockAds.module",
        "cookies.module",
    }
)

FMZ200_COOKIE = frozenset(
    {
        "cookies.module",
    }
)

COOKIE_KEYWORDS = (
    "cookie",
    "cookies",
    "get_cookie",
    "getcookie",
    "抓参",
    "抓ck",
)

SIGNIN_KEYWORDS = (
    "签到",
    "Sub-Store",
    "联通余量",
    "WPS每日",
    "书香门第",
)

SIGNIN_SKIP_FILES = frozenset(
    {
        "Official/⭐️ Sub-Store.official.sgmodule",
        "Official/联通余量.official.sgmodule",
        "Official/Follow每日签到.official.sgmodule",
        "Official/哔哩漫画签到.official.sgmodule",
        "Official/哔哩漫画抢券.official.sgmodule",
        "Official/巴哈姆特签到.official.sgmodule",
        "Official/快看漫画签到.official.sgmodule",
        "Official/携程旅行签到.official.sgmodule",
        "Official/爱奇艺会员签到.official.sgmodule",
        "Official/百度贴吧签到.official.sgmodule",
    }
)

FMZ200_UNLOCK = frozenset(
    {
        "blockHTTPDNS.module",
    }
)

# NSRingo/iRingo: standalone Modules/iringo-*.sgmodule — exclude from QingRex merge
QINGREX_SKIP_FILES = frozenset(
    {
        "Official/🍟 Apple 定位修改.official.sgmodule",
        "Official/🍟 Apple 天气增强.official.sgmodule",
        "Official/🍟 Apple 地图优化.official.sgmodule",
        "Official/🍟 Apple TestFlight.official.sgmodule",
        "Official/🍟 Apple TV 增强.official.sgmodule",
        "Official/🍟 Apple News 解锁.official.sgmodule",
        "Official/新手友好の去广告集合.official.sgmodule",
        "Official/小程序和应用懒人去广告合集.official.sgmodule",
    }
)

# Skip modules whose scripts point at dead or blocked hosts (kelee.one 403/404, perzikkop down)
QINGREX_SKIP_CONTENT_MARKERS = (
    "kelee.one",
    "perzikkop.com",
    "Maasea/sgmodule/master/Script/Bilibili/dist/bilibili.helper",
    "kokoryh/Sparkle/refs/heads/master/dist/bilibili.airborne.js",
)


def load_config() -> dict:
    if not yaml:
        raise SystemExit("PyYAML required")
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}


def module_kind(filename: str) -> str:
    name = filename.lower()
    if filename in SIGNIN_SKIP_FILES or any(k in filename for k in SIGNIN_KEYWORDS):
        return "signin"
    if any(k.lower() in name for k in UNLOCK_KEYWORDS):
        return "unlock"
    if filename in FMZ200_COOKIE or any(k in name for k in COOKIE_KEYWORDS):
        return "cookie"
    return "adblock"


def module_kind_from_header(filename: str, text: str) -> str:
    """Classify by filename and module header (#!name / #!desc / #!category)."""
    kind = module_kind(filename)
    if kind != "adblock":
        return kind
    header = text.split("[", 1)[0].lower()
    unlock_markers = (
        "解锁",
        "vip",
        "会员",
        "18+",
        "破解",
        "订阅",
        "subscription",
        "premium",
    )
    if any(m in header for m in unlock_markers):
        return "unlock"
    return kind


def read_modules(
    directory: Path,
    *,
    skip: frozenset[str] | None = None,
    skip_content_markers: tuple[str, ...] = (),
) -> list[tuple[str, str]]:
    if not directory.is_dir():
        return []
    items: list[tuple[str, str]] = []
    for path in sorted(directory.rglob("*.sgmodule")):
        rel = path.relative_to(directory).as_posix()
        if skip and rel in skip:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if skip_content_markers and any(m in text for m in skip_content_markers):
            continue
        items.append((rel, text))
    for path in sorted(directory.rglob("*.module")):
        rel = path.relative_to(directory).as_posix()
        if skip and rel in skip:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if skip_content_markers and any(m in text for m in skip_content_markers):
            continue
        items.append((rel, text))
    return items


def merge_modules(
    title: str,
    desc: str,
    modules: list[tuple[str, str]],
    *,
    primary_name: str | None = None,
    exclude_cron_scripts: bool = False,
) -> str:
    if not modules:
        return ""
    if primary_name:
        primary_text = next(text for name, text in modules if name == primary_name)
        supplements = [(name, text) for name, text in modules if name != primary_name]
    else:
        primary_text = modules[0][1]
        supplements = [(name, text) for name, text in modules[1:]]
    merged = build_merged_module(
        primary_text,
        supplements,
        header_lines=[
            "# AUTO-GENERATED by scripts/generate-author-collection-supplements.py",
            f"# {desc}",
            "# Do not edit manually.",
            "",
        ],
        primary_desc=desc,
        exclude_cron_scripts=exclude_cron_scripts,
    )
    merged = mirror_script_paths(merged)
    return strip_boxjs_module_arguments(merged)


def write_if_content(path: Path, content: str) -> None:
    if not content.strip():
        print(f"skip {path.name}: no modules")
        return
    path.write_text(content, encoding="utf-8")
    print(f"wrote {path.name} ({len(content.splitlines())} lines)")


def generate_qingrex() -> None:
    directory = UPSTREAM_CACHE / "qingrex"
    modules = read_modules(
        directory,
        skip=QINGREX_SKIP_FILES,
        skip_content_markers=QINGREX_SKIP_CONTENT_MARKERS,
    )
    if not modules:
        print("skip qingrex: no mirrored modules")
        return

    adblock = [(n, t) for n, t in modules if module_kind(n) == "adblock"]
    unlock = [(n, t) for n, t in modules if module_kind(n) == "unlock"]

    adblock_text = merge_modules(
        "可莉去广告合集",
        "可莉/QingRex 全仓库去广告模块合并去重（本地镜像）",
        adblock,
        exclude_cron_scripts=True,
    )
    write_if_content(MODULES / "qingrex-adblock.sgmodule", adblock_text)

    unlock_text = merge_modules(
        "可莉解锁合集",
        "可莉/QingRex 全仓库解锁/增强模块合并去重（本地镜像）",
        unlock,
    )
    write_if_content(MODULES / "qingrex-unlock.sgmodule", unlock_text)


def generate_yu9191_rewrite() -> None:
    directory = UPSTREAM_CACHE / "yu9191-rewrite"
    modules = read_modules(directory)
    if not modules:
        print("skip yu9191-rewrite: no mirrored modules")
        return

    unlock = [
        (n, t)
        for n, t in modules
        if module_kind_from_header(n, t) == "unlock"
    ]
    unlock_text = merge_modules(
        "Yu9191 Rewrite 解锁合集",
        "Yu9191/Rewrite 仓库 sgmodule 解锁合并去重（幻宇星球等，脚本已镜像）",
        unlock,
    )
    write_if_content(MODULES / "yu9191-rewrite-unlock.sgmodule", unlock_text)


def generate_fmz200() -> None:
    directory = UPSTREAM_CACHE / "fmz200"
    modules = read_modules(directory)
    if not modules:
        print("skip fmz200: no mirrored modules")
        return

    unlock = [(n, t) for n, t in modules if n in FMZ200_UNLOCK or module_kind(n) == "unlock"]
    cookie = [(n, t) for n, t in modules if module_kind(n) == "cookie" and n not in FMZ200_COOKIE]
    adblock = [
        (n, t)
        for n, t in modules
        if module_kind(n) == "adblock"
        and n not in FMZ200_UNLOCK
        and n not in FMZ200_SKIP_ADBLOCK
        and n not in FMZ200_COOKIE
    ]

    adblock_text = merge_modules(
        "奶思补充合集",
        "奶思 fmz200 全仓库单 App 模块合并去重（blockAds / cookies 之外的补充）",
        adblock,
    )
    write_if_content(MODULES / "fmz200-extra.sgmodule", adblock_text)

    cookie_text = merge_modules(
        "奶思抓参补充",
        "奶思 fmz200 抓参/Cookie 模块补充（cookies.module 之外的合并去重）",
        cookie,
    )
    write_if_content(MODULES / "fmz200-cookie-extra.sgmodule", cookie_text)

    unlock_text = merge_modules(
        "奶思解锁补充",
        "奶思 fmz200 解锁/HTTPDNS 相关模块（本地镜像）",
        unlock,
    )
    write_if_content(MODULES / "fmz200-unlock-extra.sgmodule", unlock_text)


def main() -> None:
    data = load_config()
    for repo in data.get("repos", []):
        if repo.get("generate_unlock_modules"):
            if repo["id"] == "yu9191-rewrite":
                generate_yu9191_rewrite()
            continue
        if not repo.get("generate_collections") and repo["id"] != "fmz200":
            continue
        if repo["id"] == "qingrex":
            generate_qingrex()
        if repo["id"] == "fmz200":
            generate_fmz200()


if __name__ == "__main__":
    main()
