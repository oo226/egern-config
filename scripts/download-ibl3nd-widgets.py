#!/usr/bin/env python3
"""Mirror IBL3ND/module widget scripts into Widgets/IBL3ND/ (one file per widget)."""

from __future__ import annotations

import json
import ssl
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import GITHUB_RAW_MAIN, ROOT

CTX = ssl.create_default_context()
MIRROR = "https://ghproxy.net/"
REPO = "IBL3ND/module"
BRANCH = "main"
OUTPUT_DIR = ROOT / "Widgets" / "IBL3ND"
MANIFEST = OUTPUT_DIR / "manifest.yaml"

# Mirror all standalone script assets; skip sgmodule/yaml/lpx/readme.
SKIP_SUFFIXES = {".sgmodule", ".yaml", ".lpx", ".txt", ".md"}
SKIP_NAMES = {"surge-loon-to-egern.yaml", "README.md", "weather.TXT"}


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "egern-config-sync/1.0"})
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=120) as resp:
            return resp.read()
    except Exception:
        mirror_url = MIRROR + url if not url.startswith(MIRROR) else url
        req = urllib.request.Request(mirror_url, headers={"User-Agent": "egern-config-sync/1.0"})
        with urllib.request.urlopen(req, context=CTX, timeout=120) as resp:
            return resp.read()


def raw_url(path: str) -> str:
    return f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{path}"


def list_repo_files() -> list[str]:
    api = f"https://api.github.com/repos/{REPO}/git/trees/{BRANCH}?recursive=1"
    payload = json.loads(fetch_bytes(api))
    files: list[str] = []
    for item in payload.get("tree", []):
        if item.get("type") != "blob":
            continue
        path = item["path"]
        if path in SKIP_NAMES:
            continue
        suffix = Path(path).suffix.lower()
        if suffix in SKIP_SUFFIXES:
            continue
        if suffix in {".js", ".jsx"} or path.endswith(".JS"):
            files.append(path)
    return sorted(files)


def mirror_file(rel_path: str) -> str:
    dest = OUTPUT_DIR / Path(rel_path).name
    url = raw_url(rel_path)
    try:
        data = fetch_bytes(url)
        if not data or data[:200].lstrip().startswith(b"<!DOCTYPE"):
            raise ValueError("invalid payload")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return "ok"
    except Exception as exc:
        if dest.is_file() and dest.stat().st_size > 0:
            return f"keep ({exc})"
        return f"fail ({exc})"


def write_manifest(files: list[str]) -> None:
    try:
        import yaml
    except ImportError:
        raise SystemExit("PyYAML required")

    widgets = []
    for rel in files:
        name = Path(rel).name
        widgets.append(
            {
                "name": name,
                "upstream": raw_url(rel),
                "local_url": f"{GITHUB_RAW_MAIN}/Widgets/IBL3ND/{name}",
                "file": f"Widgets/IBL3ND/{name}",
            }
        )
    payload = {
        "source": f"https://github.com/{REPO}",
        "note": "Each widget is a separate script — add individually in Egern, not as a merged module.",
        "widgets": widgets,
    }
    MANIFEST.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def main() -> None:
    files = list_repo_files()
    ok = keep = fail = 0
    mirrored: list[str] = []
    print(f"found {len(files)} widget scripts in {REPO}")
    for rel in files:
        status = mirror_file(rel)
        if status == "ok":
            ok += 1
            mirrored.append(rel)
            print(f"OK {Path(rel).name}")
        elif status.startswith("keep"):
            keep += 1
            mirrored.append(rel)
            print(f"KEEP {Path(rel).name} {status}")
        else:
            fail += 1
            print(f"FAIL {rel} {status}")
    write_manifest(mirrored)
    print(f"ibl3nd summary ok={ok} keep={keep} fail={fail} manifest={MANIFEST.name}")


if __name__ == "__main__":
    main()
