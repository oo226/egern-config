#!/usr/bin/env python3
"""Mirror full author repositories into Scripts/<id>/ and Modules/_upstream/<id>/."""

from __future__ import annotations

import json
import re
import ssl
import sys
import urllib.request
from pathlib import Path, PurePosixPath
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import GITHUB_RAW_MAIN, MODULES, SIGNIN_SCRIPTS, UPSTREAM_CACHE

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

CONFIG = Path(__file__).with_name("author-repos.yaml")
CTX = ssl.create_default_context()
MIRROR = "https://ghproxy.net/"


def load_config() -> dict:
    if not yaml:
        raise SystemExit("PyYAML required")
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}


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


def is_valid_payload(data: bytes) -> bool:
    if len(data) < 8:
        return False
    head = data[:512].lstrip()
    return not (head.startswith(b"<!DOCTYPE") or head.startswith(b"<html"))


def list_tree(github: str, branch: str) -> list[dict]:
    api = f"https://api.github.com/repos/{github}/git/trees/{branch}?recursive=1"
    payload = json.loads(fetch_bytes(api))
    if "tree" not in payload:
        raise RuntimeError(f"tree fetch failed for {github}@{branch}: {payload}")
    return payload["tree"]


def raw_url(github: str, branch: str, path: str) -> str:
    encoded = "/".join(quote(part, safe="") for part in path.split("/"))
    return f"https://raw.githubusercontent.com/{github}/{branch}/{encoded}"


def match_any(path: str, patterns: list[str]) -> bool:
    return any(re.fullmatch(p, path) for p in patterns)


def dest_script_path(repo: dict, upstream_path: str) -> Path:
    rel = upstream_path
    for prefix in repo.get("strip_script_prefixes") or []:
        if rel.startswith(prefix):
            rel = rel[len(prefix) :]
            break
    return SIGNIN_SCRIPTS / repo["dest_scripts"] / rel


def dest_module_path(repo: dict, upstream_path: str) -> Path:
    rel = upstream_path
    for prefix in repo.get("strip_module_prefixes") or []:
        if rel.startswith(prefix):
            rel = rel[len(prefix) :]
            break
    if repo.get("flat_module_names"):
        rel = PurePosixPath(upstream_path).name
    return UPSTREAM_CACHE / repo["id"] / PurePosixPath(rel)


def mirror_file(url: str, dest: Path) -> str:
    try:
        data = fetch_bytes(url)
        if not is_valid_payload(data):
            raise ValueError("invalid payload")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return "ok"
    except Exception as exc:
        if dest.exists():
            return f"keep ({exc})"
        return f"fail ({exc})"


def mirror_repo(repo: dict) -> tuple[int, int, int]:
    github = repo["github"]
    branch = repo["branch"]
    script_patterns = repo.get("include_scripts") or []
    module_patterns = repo.get("include_modules") or []

    ok = keep = fail = 0
    for entry in list_tree(github, branch):
        path = entry.get("path", "")
        if entry.get("type") != "blob":
            continue

        dest: Path | None = None
        if script_patterns and match_any(path, script_patterns):
            dest = dest_script_path(repo, path)
        elif module_patterns and match_any(path, module_patterns):
            dest = dest_module_path(repo, path)
        if dest is None:
            continue

        result = mirror_file(raw_url(github, branch, path), dest)
        if result == "ok":
            ok += 1
        elif result.startswith("keep"):
            keep += 1
            print(f"KEEP {dest} {result}")
        else:
            fail += 1
            print(f"FAIL {dest} {result}")

    print(f"repo {repo['id']}: ok={ok} kept={keep} fail={fail}")
    return ok, keep, fail


def main() -> None:
    data = load_config()
    total_ok = total_keep = total_fail = 0
    for repo in data.get("repos", []):
        ok, keep, fail = mirror_repo(repo)
        total_ok += ok
        total_keep += keep
        total_fail += fail
    print(
        f"author-repos summary ok={total_ok} kept={total_keep} fail={total_fail} "
        f"base={GITHUB_RAW_MAIN}/Scripts/"
    )


if __name__ == "__main__":
    main()
