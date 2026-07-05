#!/usr/bin/env python3
"""Download supplemental routing lists (Rabbit-Spec, app lists, Unbreak)."""

from __future__ import annotations

import ssl
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ROUTING_FOREIGN, ROUTING_UPSTREAM

CTX = ssl.create_default_context()
MIRROR = "https://ghproxy.net/"

RABBIT_BASE = "https://raw.githubusercontent.com/Rabbit-Spec/Surge/Master/Rules"
MATRIX_UNBREAK = (
    "https://raw.githubusercontent.com/Centralmatrix3/Matrix-io/master/Egern/Ruleset/Unbreak.yaml"
)

APP_LISTS = {
    "WeChat": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/WeChat/WeChat.list",
    "Weibo": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/Weibo/Weibo.list",
    "Bilibili": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/BiliBili/BiliBili.list",
    "TikTok": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/TikTok/TikTok.list",
    "Douyin": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/Loon/rule/Douyin.list",
    "RedBook": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/Loon/rule/RedBook.list",
    "KuaiShou": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/Loon/rule/KuaiShou.list",
    "Soul": "https://raw.githubusercontent.com/fmz200/wool_scripts/main/Loon/rule/Soul.list",
    "Line": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/Line/Line.list",
    "TestFlight": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/TestFlight/TestFlight.list",
}


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "egern-config-sync/1.0"})
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=120) as resp:
            return resp.read()
    except Exception:
        mirror_url = MIRROR + url
        req = urllib.request.Request(mirror_url, headers={"User-Agent": "egern-config-sync/1.0"})
        with urllib.request.urlopen(req, context=CTX, timeout=120) as resp:
            return resp.read()


def mirror_file(url: str, dest: Path) -> str:
    try:
        data = fetch_bytes(url)
        if not data or data[:200].lstrip().startswith(b"<!DOCTYPE"):
            raise ValueError("invalid payload")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return "ok"
    except Exception as exc:
        if dest.is_file() and dest.stat().st_size > 0:
            return f"keep ({exc})"
        return f"fail ({exc})"


def main() -> None:
    rabbit_dir = ROUTING_UPSTREAM / "rabbit"
    app_dir = ROUTING_UPSTREAM / "app-lists"
    ok = keep = fail = 0

    for name in ("China.list", "ChinaCIDR.list"):
        dest = rabbit_dir / name
        status = mirror_file(f"{RABBIT_BASE}/{name}", dest)
        _tally(status, name, ok, keep, fail)

    dest = ROUTING_UPSTREAM / "matrix" / "Unbreak.yaml"
    status = mirror_file(MATRIX_UNBREAK, dest)
    print(f"{status}: matrix/Unbreak.yaml")

    for name, url in APP_LISTS.items():
        dest = app_dir / f"{name}.list"
        status = mirror_file(url, dest)
        if status == "ok":
            ok += 1
            print(f"OK app-lists/{name}.list")
        elif status.startswith("keep"):
            keep += 1
            print(f"KEEP app-lists/{name}.list {status}")
        else:
            fail += 1
            print(f"FAIL app-lists/{name}.list {status}")

    print(f"routing supplements summary ok={ok} keep={keep} fail={fail}")


def _tally(status: str, name: str, ok: int, keep: int, fail: int) -> None:
    if status == "ok":
        print(f"OK rabbit/{name}")
    elif status.startswith("keep"):
        print(f"KEEP rabbit/{name} {status}")
    else:
        print(f"FAIL rabbit/{name} {status}")


if __name__ == "__main__":
    main()
