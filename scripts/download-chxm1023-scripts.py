#!/usr/bin/env python3
"""Mirror chxm1023/ddm1023 Rewrite + Advertising scripts into Scripts/chxm1023/."""

from __future__ import annotations

import json
import re
import ssl
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import CHXM1023_AD_SCRIPTS, CHXM1023_SCRIPTS, GITHUB_RAW_MAIN

CTX = ssl.create_default_context()
MIRROR = "https://ghproxy.net/"

MODULE_URLS = (
    "https://raw.githubusercontent.com/chxm1023/Script_X/main/Collections.sgmodule",
    "https://raw.githubusercontent.com/chxm1023/Advertising/Shadowrocket/AppAd.sgmodule",
)

REPO_APIS = {
    "Rewrite": "https://api.github.com/repos/chxm1023/Rewrite/git/trees/main?recursive=1",
    "Advertising": "https://api.github.com/repos/chxm1023/Advertising/git/trees/main?recursive=1",
}


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


def is_valid_script(data: bytes) -> bool:
    if len(data) < 16:
        return False
    head = data[:512].lstrip()
    return not (head.startswith(b"<!DOCTYPE") or head.startswith(b"<html"))


def list_repo_js(repo: str) -> list[tuple[str, str]]:
    payload = json.loads(fetch_bytes(REPO_APIS[repo]))
    items: list[tuple[str, str]] = []
    for entry in payload.get("tree", []):
        path = entry.get("path", "")
        if path.endswith(".js"):
            items.append((path, f"https://raw.githubusercontent.com/chxm1023/{repo}/main/{path}"))
    return items


def script_paths_from_modules() -> set[str]:
    urls: set[str] = set()
    pattern = re.compile(
        r"script-path=(https://raw\.githubusercontent\.com/chxm1023/[^\s,]+)"
    )
    supplement = Path(__file__).resolve().parent.parent / "Modules/chxm1023-ad-supplement.sgmodule"
    module_sources = list(MODULE_URLS)
    if supplement.exists():
        module_sources.append(f"file://{supplement}")
    for source in module_sources:
        try:
            if source.startswith("file://"):
                text = Path(source[7:]).read_text(encoding="utf-8")
            else:
                text = fetch_bytes(source).decode("utf-8", errors="replace")
        except Exception as exc:
            print(f"WARN module fetch {source}: {exc}")
            continue
        for match in pattern.finditer(text):
            urls.add(match.group(1).rstrip())
    return urls


def local_path_for_chxm_url(url: str) -> Path | None:
    prefix_rewrite = "https://raw.githubusercontent.com/chxm1023/Rewrite/main/"
    prefix_ad = "https://raw.githubusercontent.com/chxm1023/Advertising/main/"
    if url.startswith(prefix_rewrite):
        return CHXM1023_SCRIPTS / url[len(prefix_rewrite) :]
    if url.startswith(prefix_ad):
        return CHXM1023_AD_SCRIPTS / url[len(prefix_ad) :]
    return None


def mirror_file(url: str, dest: Path) -> str:
    try:
        data = fetch_bytes(url)
        if not is_valid_script(data):
            raise ValueError("invalid script payload")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return "ok"
    except Exception as exc:
        if dest.exists():
            return f"keep ({exc})"
        return f"fail ({exc})"


def main() -> None:
    CHXM1023_SCRIPTS.mkdir(parents=True, exist_ok=True)
    CHXM1023_AD_SCRIPTS.mkdir(parents=True, exist_ok=True)

    targets: dict[str, Path] = {}

    for repo in ("Rewrite", "Advertising"):
        for rel, url in list_repo_js(repo):
            dest = (
                CHXM1023_SCRIPTS / rel
                if repo == "Rewrite"
                else CHXM1023_AD_SCRIPTS / rel
            )
            targets[url] = dest

    for url in script_paths_from_modules():
        dest = local_path_for_chxm_url(url)
        if dest:
            targets[url] = dest

    ok = keep = fail = 0
    for url in sorted(targets):
        dest = targets[url]
        result = mirror_file(url, dest)
        if result == "ok":
            ok += 1
        elif result.startswith("keep"):
            keep += 1
            print(f"KEEP {dest.relative_to(CHXM1023_SCRIPTS.parent)} {result}")
        else:
            fail += 1
            print(f"FAIL {dest.relative_to(CHXM1023_SCRIPTS.parent)} {result}")

    print(f"chxm1023 mirror summary ok={ok} kept={keep} fail={fail}")
    print(f"mirror base: {GITHUB_RAW_MAIN}/Scripts/chxm1023/")


if __name__ == "__main__":
    main()
