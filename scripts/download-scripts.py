#!/usr/bin/env python3
"""Download sign-in scripts into 脚本/."""

from __future__ import annotations

import ssl
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import SIGNIN_SCRIPTS

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

MANIFEST = Path(__file__).resolve().parent / "manifest.yaml"
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


def is_valid_script(data: bytes) -> bool:
    if len(data) < 32:
        return False
    text = data[:512].lstrip()
    if text.startswith(b"<!DOCTYPE") or text.startswith(b"<html"):
        return False
    return True


def load_manifest() -> dict:
    text = MANIFEST.read_text(encoding="utf-8")
    if yaml:
        return yaml.safe_load(text) or {}
    raise SystemExit("PyYAML required: pip install pyyaml")


def main() -> None:
    data = load_manifest()
    SIGNIN_SCRIPTS.mkdir(parents=True, exist_ok=True)

    ok = fail = skip = 0
    for item in data.get("scripts", []):
        out = SIGNIN_SCRIPTS / item["file"]
        try:
            if item.get("mirror_from"):
                src = SIGNIN_SCRIPTS / item["mirror_from"]
                if not src.exists():
                    raise FileNotFoundError(f"mirror missing {src}")
                data_bytes = src.read_bytes()
            else:
                data_bytes = fetch(item["upstream"])
            if not is_valid_script(data_bytes):
                raise ValueError("upstream returned empty or HTML instead of script")
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(data_bytes)
            print(f"OK script {item['file']} ({len(data_bytes)} bytes)")
            ok += 1
        except Exception as exc:
            if out.exists():
                print(f"KEEP script {item['file']}: {exc} (retaining local copy)")
                skip += 1
            else:
                print(f"FAIL script {item['file']}: {exc}")
                fail += 1

    print(f"summary ok={ok} kept={skip} fail={fail}")


if __name__ == "__main__":
    main()
