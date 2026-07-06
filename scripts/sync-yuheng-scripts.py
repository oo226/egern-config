#!/usr/bin/env python3
"""Mirror Yuheng0101/X BoxJS task scripts into Scripts/yuheng/."""

from __future__ import annotations

import json
import re
import ssl
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import SIGNIN_SCRIPTS

BOXJS_URL = (
    "https://raw.githubusercontent.com/Yuheng0101/X/refs/heads/main/Tasks/boxjs.json"
)
OUTPUT_ROOT = SIGNIN_SCRIPTS / "yuheng"
CTX = ssl.create_default_context()
MIRROR = "https://ghproxy.net/"
SKIP_SCRIPT_HOSTS = ("192.168.", "127.0.0.1", "localhost")


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "egern-config-sync/1.0"})
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=120) as resp:
            return resp.read()
    except Exception:
        mirror_url = MIRROR + url
        req = urllib.request.Request(mirror_url, headers={"User-Agent": "egern-config-sync/1.0"})
        with urllib.request.urlopen(req, context=CTX, timeout=120) as resp:
            return resp.read()


def is_valid_script(data: bytes) -> bool:
    if len(data) < 16:
        return False
    head = data[:512].lstrip()
    return not (head.startswith(b"<!DOCTYPE") or head.startswith(b"<html"))


def upstream_rel(url: str) -> str | None:
    url = url.strip().split("?")[0]
    if not url or any(host in url for host in SKIP_SCRIPT_HOSTS):
        return None
    if "Yuheng0101/X" not in url:
        return None
    for marker in ("/main/", "/refs/heads/main/"):
        if marker in url:
            return url.split(marker, 1)[1]
    return None


def collect_script_urls(boxjs: dict) -> dict[str, str]:
    urls: dict[str, str] = {}
    for app in boxjs.get("apps", []):
        if not isinstance(app, dict):
            continue
        script = app.get("script")
        if not isinstance(script, str) or not script.strip():
            continue
        rel = upstream_rel(script)
        if rel:
            urls[rel] = script.strip().split("?")[0]
    return urls


def main() -> None:
    payload = json.loads(fetch(BOXJS_URL).decode("utf-8-sig"))
    urls = collect_script_urls(payload)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    ok = fail = skip = 0
    for rel, url in sorted(urls.items()):
        out = OUTPUT_ROOT / rel
        try:
            data = fetch(url)
            if not is_valid_script(data):
                raise ValueError("invalid script payload")
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(data)
            print(f"OK yuheng/{rel} ({len(data)} bytes)")
            ok += 1
        except Exception as exc:
            if out.is_file() and out.stat().st_size > 0:
                print(f"KEEP yuheng/{rel}: {exc}")
                skip += 1
            else:
                print(f"FAIL yuheng/{rel}: {exc}")
                fail += 1

    print(f"summary ok={ok} kept={skip} fail={fail} urls={len(urls)}")


if __name__ == "__main__":
    main()
