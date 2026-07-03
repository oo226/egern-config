#!/usr/bin/env python3
"""Download module collections listed in Modules/manifest.yaml."""

from __future__ import annotations

import ssl
import urllib.request
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "Modules" / "manifest.yaml"
MODULES_DIR = ROOT / "Modules"
CTX = ssl.create_default_context()
MIRROR = "https://ghproxy.net/"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "egern-config-sync/1.0"})
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=120) as resp:
            data = resp.read()
    except Exception:
        mirror_url = MIRROR + url if not url.startswith(MIRROR) else url
        req = urllib.request.Request(mirror_url, headers={"User-Agent": "egern-config-sync/1.0"})
        with urllib.request.urlopen(req, context=CTX, timeout=120) as resp:
            data = resp.read()
    if data.lstrip().startswith(b"<!DOCTYPE") or data.lstrip().startswith(b"<html"):
        raise ValueError("upstream returned HTML instead of module content")
    return data


def load_manifest() -> dict:
    text = MANIFEST.read_text(encoding="utf-8")
    if yaml:
        return yaml.safe_load(text) or {}
    raise SystemExit("PyYAML required: pip install pyyaml")


def main() -> None:
    data = load_manifest()
    MODULES_DIR.mkdir(parents=True, exist_ok=True)

    ok = fail = 0
    for item in data.get("modules", []):
        out = MODULES_DIR / item["file"]
        try:
            out.write_bytes(fetch(item["upstream"]))
            print(f"OK module {item['file']}")
            ok += 1
        except Exception as exc:
            print(f"FAIL module {item['file']}: {exc}")
            fail += 1

    print(f"summary ok={ok} fail={fail}")
    if fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
