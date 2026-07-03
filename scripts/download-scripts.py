#!/usr/bin/env python3
"""Download sign-in scripts listed in scripts/manifest.yaml."""

from __future__ import annotations

import ssl
import urllib.request
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = Path(__file__).resolve().parent / "manifest.yaml"
SCRIPTS_DIR = ROOT / "scripts"
CTX = ssl.create_default_context()

MIRROR = "https://ghproxy.net/"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "egern-config-sync/1.0"})
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=90) as resp:
            return resp.read()
    except Exception:
        mirror_url = MIRROR + url
        req = urllib.request.Request(mirror_url, headers={"User-Agent": "egern-config-sync/1.0"})
        with urllib.request.urlopen(req, context=CTX, timeout=90) as resp:
            return resp.read()


def load_manifest() -> dict:
    text = MANIFEST.read_text(encoding="utf-8")
    if yaml:
        return yaml.safe_load(text) or {}
    raise SystemExit("PyYAML required: pip install pyyaml")


def main() -> None:
    data = load_manifest()
    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    ok = fail = 0
    for item in data.get("scripts", []):
        out = SCRIPTS_DIR / item["file"]
        try:
            out.write_bytes(fetch(item["upstream"]))
            print(f"OK script {item['file']}")
            ok += 1
        except Exception as exc:
            print(f"FAIL script {item['file']}: {exc}")
            fail += 1

    print(f"summary ok={ok} fail={fail}")


if __name__ == "__main__":
    main()
