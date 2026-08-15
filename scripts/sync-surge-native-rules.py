#!/usr/bin/env python3
"""Build Surge-native RULE-SET trees under surge/Rules/ (Rabbit-Spec style).

Egern Routing/*.yaml stays on the Egern path. This script does NOT read Egern YAML.
Optional thin overlays are copied from surge/egern-Rules/ when present (Tailscale,
Zhuifeng, App policy lists, etc.).

Upstream: https://github.com/Rabbit-Spec/Surge (Rules/)
"""

from __future__ import annotations

import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ROOT

CTX = ssl.create_default_context()
MIRROR = "https://ghproxy.net/"

SURGE = ROOT / "surge"
RULES = SURGE / "Rules"
EGERN_EXPORT = SURGE / "egern-Rules"

RABBIT_RAW = "https://raw.githubusercontent.com/Rabbit-Spec/Surge/Master/Rules"

# Core lists mirrored 1:1 from Rabbit-Spec (lazy-config style).
RABBIT_LISTS = (
    "AIGC.list",
    "Apple.list",
    "BiliBili.list",
    "China.list",
    "ChinaASN.list",
    "ChinaCIDR.list",
    "ChinaMedia.list",
    "Disney.list",
    "Game.list",
    "GlobalMedia.list",
    "Google.list",
    "Microsoft.list",
    "Netflix.list",
    "Proxy.list",
    "Spotify.list",
    "Telegram.list",
    "TelegramASN.list",
    "TikTok.list",
    "YouTube.list",
    "Facebook.list",
    "Instagram.list",
    "Meta.list",
)

# Thin overlays kept from our Egern export (policy extras Rabbit does not cover).
LOCAL_FROM_EGERN = (
    ("Tailscale-Direct.list", "Local/Tailscale-Direct.list"),
    ("Bootstrap-Direct.list", "Local/Bootstrap-Direct.list"),
    ("Unbreak.list", "Local/Unbreak.list"),
    ("Direct-Priority.list", "Local/Direct-Priority.list"),
    ("Lan.list", "Local/Lan.list"),
    ("Zhuifeng.list", "Local/Zhuifeng.list"),
    ("Foreign/Github.list", "Local/Github.list"),
    ("Foreign/Emby.list", "Local/Emby.list"),
    ("Foreign/App/Douyin.list", "Local/App/Douyin.list"),
    ("Foreign/App/RedBook.list", "Local/App/RedBook.list"),
    ("Foreign/App/KuaiShou.list", "Local/App/KuaiShou.list"),
    ("Foreign/App/Soul.list", "Local/App/Soul.list"),
    ("Foreign/App/Weibo.list", "Local/App/Weibo.list"),
    ("Foreign/App/Line.list", "Local/App/Line.list"),
)


def fetch(url: str) -> str:
    last: Exception | None = None
    for candidate in (url, MIRROR + url):
        try:
            req = urllib.request.Request(candidate, headers={"User-Agent": "egern-config-surge-native"})
            with urllib.request.urlopen(req, context=CTX, timeout=60) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001
            last = exc
    assert last is not None
    raise last


def write_list(path: Path, body: str, *, header: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = body if body.endswith("\n") else body + "\n"
    if not text.lstrip().startswith("#"):
        text = header + text
    path.write_text(text, encoding="utf-8")


def sync_rabbit() -> None:
    header = (
        "# Surge-native RULE-SET — mirrored from Rabbit-Spec/Surge\n"
        "# https://github.com/Rabbit-Spec/Surge\n"
        "# synced by scripts/sync-surge-native-rules.py — do not hand-merge Egern YAML here\n"
    )
    RULES.mkdir(parents=True, exist_ok=True)
    for name in RABBIT_LISTS:
        url = f"{RABBIT_RAW}/{name}"
        try:
            body = fetch(url)
        except Exception as exc:  # noqa: BLE001
            print(f"KEEP? fail {name}: {exc}")
            dest = RULES / name
            if dest.is_file():
                print(f"  keep existing {dest.relative_to(SURGE)}")
                continue
            raise
        dest = RULES / name
        write_list(dest, body, header=header)
        lines = sum(1 for l in body.splitlines() if l.strip() and not l.strip().startswith("#"))
        print(f"OK rabbit {name} ({lines} lines)")


def sync_local_overlays() -> None:
    if not EGERN_EXPORT.is_dir():
        print(f"skip local overlays: missing {EGERN_EXPORT}")
        return
    for src_rel, dst_rel in LOCAL_FROM_EGERN:
        src = EGERN_EXPORT / src_rel
        if not src.is_file():
            print(f"skip missing overlay {src_rel}")
            continue
        body = src.read_text(encoding="utf-8", errors="replace")
        dest = RULES / dst_rel
        header = (
            "# Surge Local overlay (from egern-Rules export; thin policy extras)\n"
            f"# source: egern-Rules/{src_rel}\n"
        )
        # Strip old export banners; keep rules
        lines = []
        for line in body.splitlines():
            if line.startswith("# Format:") or line.startswith("# Source:") or line.startswith("# AUTO"):
                continue
            lines.append(line)
        write_list(dest, "\n".join(lines) + "\n", header=header)
        print(f"OK local {dst_rel}")


def write_readme() -> None:
    readme = RULES / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# Surge-native Rules",
                "",
                "与 **Egern `Routing/*.yaml` 分开维护**。",
                "",
                "| 目录/文件 | 来源 |",
                "| --- | --- |",
                "| `*.list`（根下） | [Rabbit-Spec/Surge](https://github.com/Rabbit-Spec/Surge) 镜像 |",
                "| `Local/` | 本仓薄补丁（追风/Tailscale/App 策略等），从 `surge/egern-Rules` 抽取 |",
                "| `surge/egern-Rules/` | Egern YAML 导出（对照用，**不进默认 Surge.conf**） |",
                "",
                "更新：`python3 scripts/sync-surge-native-rules.py`",
                "",
            ]
        ),
        encoding="utf-8",
    )


def prune_egern_leftovers() -> None:
    """Remove old Egern mega dumps from Rules/ so publish stays lean."""
    leftovers = [
        "China-Direct.list",
        "China-Direct.domainset",
        "China-Direct.ip.list",
        "Reject-Merged.list",
        "Reject-Merged.domainset",
        "Reject-Merged.ip.list",
        "Privacy-Reject.list",
        "Privacy-Reject.domainset",
        "Foreign",
        "Bootstrap-Direct.list",
        "Bootstrap-Direct.domainset",
        "Unbreak.list",
        "Unbreak.domainset",
        "Direct-Priority.list",
        "Direct-Priority.domainset",
        "Direct-Priority.ip.list",
        "Lan.list",
        "Lan.domainset",
        "Lan.ip.list",
        "Tailscale-Direct.list",
        "Tailscale-Direct.domainset",
        "Tailscale-Direct.ip.list",
        "Zhuifeng.list",
        "Zhuifeng.domainset",
    ]
    import shutil

    for name in leftovers:
        path = RULES / name
        if path.is_dir():
            shutil.rmtree(path)
            print(f"removed dir {name}")
        elif path.is_file():
            path.unlink()
            print(f"removed {name}")


def main() -> None:
    sync_rabbit()
    sync_local_overlays()
    prune_egern_leftovers()
    write_readme()
    print(f"done → {RULES}")


if __name__ == "__main__":
    main()
