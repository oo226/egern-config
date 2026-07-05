#!/usr/bin/env python3
"""Download upstream routing rules into 分流/_upstream/ and 分流/国外/."""

from __future__ import annotations

import os
import ssl
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from paths import ROUTING_FOREIGN, ROUTING_UPSTREAM

MERGE_SOURCES = [
    "Reject", "Direct", "WeChat", "Bilibili", "AppleCN", "ChinaIP", "ChinaASN", "ChinaDomain",
]
FOREIGN_RULES = [
    "Lan", "AI", "Telegram", "Twitter", "TikTok",
    "YouTube", "Netflix", "Disney", "Spotify", "Emby",
    "Google", "Github", "Microsoft", "AppleServers",
    "Game", "ProxyGFW", "Proxy",
]
SKK_DIR = ROUTING_UPSTREAM / "skk"
os.makedirs(SKK_DIR, exist_ok=True)
os.makedirs(ROUTING_FOREIGN, exist_ok=True)
CTX = ssl.create_default_context()

MIRRORS = [
    "https://raw.githubusercontent.com/Repcz/Tool/X/Egern/Rules/{name}.yaml",
    "https://ghproxy.net/https://raw.githubusercontent.com/Repcz/Tool/X/Egern/Rules/{name}.yaml",
]


def fetch(url: str, out: str) -> int:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=CTX, timeout=90) as resp:
        data = resp.read()
    with open(out, "wb") as f:
        f.write(data)
    return len(data)


def download_yaml(name: str, out_dir: str) -> bool:
    out = os.path.join(out_dir, f"{name}.yaml")
    for tpl in MIRRORS:
        url = tpl.format(name=name)
        try:
            size = fetch(url, out)
            print(f"OK {name}.yaml ({size} bytes)")
            return True
        except Exception:
            continue
    print(f"FAIL {name}.yaml")
    return False


def main() -> None:
    ok = fail = 0
    for name in MERGE_SOURCES:
        if download_yaml(name, str(ROUTING_UPSTREAM)):
            ok += 1
        else:
            fail += 1

    # Lan goes to 分流/局域网.yaml directly as upstream mirror
    if download_yaml("Lan", str(ROUTING_UPSTREAM.parent)):
        # move Lan to correct name 局域网.yaml - workflow handles this
        lan_src = ROUTING_UPSTREAM.parent / "Lan.yaml"
        lan_dst = ROUTING_UPSTREAM.parent / "局域网.yaml"
        if lan_src.exists():
            lan_src.replace(lan_dst)
        ok += 1
    else:
        fail += 1

    for name in FOREIGN_RULES:
        if name == "Lan":
            continue
        if download_yaml(name, str(ROUTING_FOREIGN)):
            ok += 1
        else:
            fail += 1

    skk_urls = [
        "https://ruleset.skk.moe/List/domainset/reject.conf",
        "https://ghproxy.net/https://ruleset.skk.moe/List/domainset/reject.conf",
    ]
    for url in skk_urls:
        try:
            size = fetch(url, str(SKK_DIR / "reject.conf"))
            print(f"OK skk/reject.conf ({size} bytes)")
            break
        except Exception as exc:
            print(f"skk fail {url}: {exc}")

    print(f"summary ok={ok} fail={fail}")


if __name__ == "__main__":
    main()
