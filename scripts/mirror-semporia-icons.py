#!/usr/bin/env python3
"""Mirror Semporia Hand-Painted icon manifest for local policy group icons."""

from __future__ import annotations

import ssl
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ASSETS

URL = "https://raw.githubusercontent.com/Semporia/Hand-Painted-icon/master/Semporia.json"
DEST = ASSETS / "icons" / "Semporia.json"
CTX = ssl.create_default_context()
MIRROR = "https://ghproxy.net/"


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "egern-config-sync/1.0"})
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=120) as resp:
            return resp.read()
    except Exception:
        req = urllib.request.Request(MIRROR + url, headers={"User-Agent": "egern-config-sync/1.0"})
        with urllib.request.urlopen(req, context=CTX, timeout=120) as resp:
            return resp.read()


def main() -> None:
    try:
        data = fetch_bytes(URL)
        if not data or data[:1] != b"{":
            raise ValueError("invalid json")
        DEST.parent.mkdir(parents=True, exist_ok=True)
        DEST.write_bytes(data)
        print(f"ok: {DEST}")
    except Exception as exc:
        if DEST.is_file():
            print(f"keep: {DEST} ({exc})")
        else:
            raise SystemExit(f"fail: {exc}") from exc


if __name__ == "__main__":
    main()
