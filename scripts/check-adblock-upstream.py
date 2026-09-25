#!/usr/bin/env python3
"""Check whether 可莉 / 奶思 / 开屏 upstream fingerprints changed.

Exit codes:
  0 — no change (or --write updated the local fingerprint file)
  1 — usage / network error
  2 — upstream changed (print JSON summary to stdout)

Used by .github/workflows/adblock-keli-nais.yml on this feature branch only.
Does not touch sync 日更.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import ssl
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
FINGERPRINT = ROOT / "Modules" / "vendors" / "upstream-fingerprint.json"
CTX = ssl.create_default_context()
UA = {"User-Agent": "egern-config-adblock-check/1.0"}

QINGREX_API = "https://api.github.com/repos/QingRex/LoonKissSurge/git/trees/main?recursive=1"
QINGREX_COMMITS = "https://api.github.com/repos/QingRex/LoonKissSurge/commits/main"
FMZ_BLOCKADS = "https://raw.githubusercontent.com/fmz200/wool_scripts/main/Surge/module/blockAds.module"
SPLASH = [
    ("moyu-StartUpAds", "https://ddgksf2013.top/rewrite/StartUpAds.conf"),
    (
        "moyu-FakeiOSAds",
        "https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/AdBlock/FakeiOSAds.conf",
    ),
]


def fetch(url: str, *, timeout: int = 90) -> bytes:
    # percent-encode non-ascii path
    from urllib.parse import urlparse, unquote

    p = urlparse(url)
    path = quote(unquote(p.path), safe="/:@!$&'()*+,;=-._~")
    url = p._replace(path=path).geturl()
    headers = dict(UA)
    token = __import__("os").environ.get("GITHUB_TOKEN") or __import__("os").environ.get("GH_TOKEN")
    if token and "api.github.com" in url:
        headers["Authorization"] = f"Bearer {token}"
        headers["Accept"] = "application/vnd.github+json"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=timeout) as resp:
            return resp.read()
    except Exception:
        mirror = "https://ghproxy.net/" + url
        req = urllib.request.Request(mirror, headers=UA)
        with urllib.request.urlopen(req, context=CTX, timeout=timeout) as resp:
            return resp.read()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def collect() -> dict:
    # QingRex: tree SHA of root Surge/*去广告.sgmodule blobs
    tree = json.loads(fetch(QINGREX_API).decode())
    q_paths = []
    for t in tree.get("tree", []):
        if t.get("type") != "blob":
            continue
        p = t["path"]
        if (
            p.startswith("Surge/")
            and p.count("/") == 1
            and p.endswith(".sgmodule")
            and "去广告" in p
            and not p.startswith("Surge/Beta/")
        ):
            q_paths.append((p, t.get("sha", "")))
    q_paths.sort()
    q_blob = "\n".join(f"{sha}  {path}" for path, sha in q_paths).encode()
    try:
        commits = json.loads(fetch(QINGREX_COMMITS).decode())
        q_commit = commits[0]["sha"] if isinstance(commits, list) and commits else ""
    except Exception:
        q_commit = ""

    fmz = fetch(FMZ_BLOCKADS)
    splash = {}
    for name, url in SPLASH:
        try:
            splash[name] = sha256(fetch(url))
        except Exception as exc:
            splash[name] = f"ERROR:{exc}"

    return {
        "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "qingrex": {
            "commit": q_commit,
            "adblock_module_count": len(q_paths),
            "tree_fingerprint": sha256(q_blob),
        },
        "fmz200_blockAds": {"sha256": sha256(fmz), "bytes": len(fmz)},
        "splash": splash,
    }


def load_local() -> dict | None:
    if not FINGERPRINT.is_file():
        return None
    return json.loads(FINGERPRINT.read_text(encoding="utf-8"))


def core(fp: dict) -> dict:
    """Comparable subset (ignore checked_at)."""
    return {
        "qingrex": fp.get("qingrex"),
        "fmz200_blockAds": fp.get("fmz200_blockAds"),
        "splash": fp.get("splash"),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--write",
        action="store_true",
        help="Write remote fingerprint to Modules/vendors/upstream-fingerprint.json",
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="Always print remote fingerprint JSON",
    )
    args = ap.parse_args()

    try:
        remote = collect()
    except Exception as exc:
        print(f"check failed: {exc}", file=sys.stderr)
        sys.exit(1)

    local = load_local()
    changed = local is None or core(local) != core(remote)

    if args.write:
        FINGERPRINT.parent.mkdir(parents=True, exist_ok=True)
        FINGERPRINT.write_text(json.dumps(remote, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {FINGERPRINT.relative_to(ROOT)}")

    if args.json or changed:
        print(json.dumps({"changed": changed, "remote": remote, "local": local}, ensure_ascii=False, indent=2))

    if changed and not args.write:
        sys.exit(2)
    if changed and args.write:
        # after write, caller still needs to know it changed
        sys.exit(2)
    print("upstream unchanged")
    sys.exit(0)


if __name__ == "__main__":
    main()
