#!/usr/bin/env python3
"""Mirror GeoIP/ASN databases into Assets/ for offline use."""

from __future__ import annotations

import ssl
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ROOT

CTX = ssl.create_default_context()
MIRROR = "https://ghproxy.net/"

ASSETS = ROOT / "Assets" / "geoip"

SOURCES = {
    "Country-without-asn.mmdb": (
        "https://raw.githubusercontent.com/Loyalsoldier/geoip/release/Country-without-asn.mmdb"
    ),
    "GeoLite2-ASN.mmdb": (
        "https://raw.githubusercontent.com/Loyalsoldier/geoip/release/GeoLite2-ASN.mmdb"
    ),
}


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "egern-config-sync/1.0"})
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=180) as resp:
            return resp.read()
    except Exception:
        mirror_url = MIRROR + url
        req = urllib.request.Request(mirror_url, headers={"User-Agent": "egern-config-sync/1.0"})
        with urllib.request.urlopen(req, context=CTX, timeout=180) as resp:
            return resp.read()


def mirror_file(name: str, url: str) -> str:
    dest = ASSETS / name
    try:
        data = fetch_bytes(url)
        if len(data) < 1024:
            raise ValueError("payload too small")
        ASSETS.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return "ok"
    except Exception as exc:
        if dest.is_file() and dest.stat().st_size > 1024:
            return f"keep ({exc})"
        return f"fail ({exc})"


def main() -> None:
    ok = keep = fail = 0
    for name, url in SOURCES.items():
        status = mirror_file(name, url)
        if status == "ok":
            ok += 1
        elif status.startswith("keep"):
            keep += 1
        else:
            fail += 1
        print(f"{status}: {name}")
    print(f"geoip summary ok={ok} keep={keep} fail={fail}")
    if fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
