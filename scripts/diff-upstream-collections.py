#!/usr/bin/env python3
"""Compare watched upstream mega-collections vs our mirrors; pull missing scripts.

Writes site/collection-diff.json and mirrors any new script-path into Scripts/_external/,
then rewrites collection modules to point at this repo.
"""

from __future__ import annotations

import json
import ssl
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from external_script_utils import (
    REWRITE_MAP,
    dest_absolute_path,
    extract_script_urls,
    is_local_url,
    load_rewrite_map,
    local_raw_url,
    dest_relative_path,
    should_skip_mirror,
)
from paths import MANIFEST, MODULES, ROOT, UNLOCK_MANIFEST, COOKIE_MANIFEST

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

# Reuse mirror helpers
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "mirror_external_scripts", Path(__file__).with_name("mirror-external-scripts.py")
)
_mirror = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mirror)

CTX = ssl.create_default_context()
UA = {"User-Agent": "egern-config-sync/1.0"}
OUT = ROOT / "site" / "collection-diff.json"
UPSTREAM_SOURCES = Path(__file__).with_name("upstream-sources.yaml")


def load_yaml(path: Path) -> dict:
    if not yaml:
        raise SystemExit("PyYAML required")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=120) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception:
        mirror = "https://ghproxy.net/" + url
        req = urllib.request.Request(mirror, headers=UA)
        with urllib.request.urlopen(req, context=CTX, timeout=120) as resp:
            return resp.read().decode("utf-8", errors="replace")


def collection_seeds() -> list[dict]:
    """Upstream mega modules we already watch / merge from."""
    seeds: list[dict] = []
    for path, label in (
        (MANIFEST, "adblock"),
        (UNLOCK_MANIFEST, "unlock"),
        (COOKIE_MANIFEST, "cookie"),
    ):
        if not path.is_file():
            continue
        data = load_yaml(path)
        for item in data.get("modules") or []:
            url = item.get("upstream")
            if not url:
                continue
            seeds.append(
                {
                    "id": item.get("name") or url,
                    "url": url,
                    "group": label,
                    "note": item.get("note") or "",
                }
            )
    # optional extras in upstream-sources.yaml
    if UPSTREAM_SOURCES.is_file():
        cfg = load_yaml(UPSTREAM_SOURCES)
        for item in cfg.get("collection_watch") or []:
            if item.get("url"):
                seeds.append(
                    {
                        "id": item.get("id") or item["url"],
                        "url": item["url"],
                        "group": item.get("group") or "extra",
                        "note": item.get("note") or "",
                    }
                )
    # dedupe by url
    by_url: dict[str, dict] = {}
    for s in seeds:
        by_url[s["url"]] = s
    return list(by_url.values())


def known_stub_rewrites() -> dict[str, str]:
    """Dead upstream script URLs already remapped in merge manifests / defaults."""
    fixes: dict[str, str] = {}
    merge_path = Path(__file__).with_name("merge-adblock-modules.py")
    if merge_path.is_file():
        try:
            spec = importlib.util.spec_from_file_location("merge_adblock_modules", merge_path)
            mod = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(mod)
            fixes.update({str(k): str(v) for k, v in (getattr(mod, "DEFAULT_SCRIPT_URL_FIXES", {}) or {}).items()})
        except Exception as exc:
            print(f"warn: could not load DEFAULT_SCRIPT_URL_FIXES: {exc}")
    for path in (MANIFEST, UNLOCK_MANIFEST, COOKIE_MANIFEST):
        if not path.is_file():
            continue
        data = load_yaml(path)
        merge = data.get("merge") or {}
        for old, new in (merge.get("script_url_fixes") or {}).items():
            fixes[str(old)] = str(new)
    return fixes


def main() -> None:
    seeds = collection_seeds()
    existing_map = load_rewrite_map()
    stub_fixes = known_stub_rewrites()
    # Prefer explicit stub/local fixes over attempting a dead upstream download
    for old, new in stub_fixes.items():
        existing_map.setdefault(old, new)

    report = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "collections_checked": [],
        "missing_before": [],
        "mirrored_now": [],
        "still_missing": [],
        "stubbed": [],
        "foreign_in_our_collections": [],
    }

    all_upstream_urls: set[str] = set()
    for seed in seeds:
        entry = {"id": seed["id"], "url": seed["url"], "group": seed["group"], "ok": False, "scripts": 0}
        try:
            text = fetch_text(seed["url"])
            urls = extract_script_urls(text)
            entry["ok"] = True
            entry["scripts"] = len(urls)
            all_upstream_urls |= urls
            print(f"OK collection {seed['id']} scripts={len(urls)}")
        except Exception as exc:
            entry["error"] = str(exc)
            print(f"FAIL collection {seed['id']}: {exc}")
        report["collections_checked"].append(entry)

    # Also scan our merged collections for leftover foreign links
    our_foreign: set[str] = set()
    for name in (
        "adblock-collection.module",
        "unlock-collection.module",
        "cookie-collection.module",
        "skip-proxy-collection.module",
    ):
        path = MODULES / name
        if path.is_file():
            our_foreign |= extract_script_urls(path.read_text(encoding="utf-8", errors="replace"))

    missing: list[str] = []
    for url in sorted(all_upstream_urls | our_foreign):
        if is_local_url(url) or should_skip_mirror(url):
            continue
        if url in stub_fixes:
            report["stubbed"].append({"url": url, "local": stub_fixes[url]})
            continue
        if url in existing_map:
            # Already rewritten (local raw or stub); no need to re-download
            continue
        dest = dest_absolute_path(url)
        if dest.is_file() and dest.stat().st_size > 0:
            continue
        missing.append(url)

    report["missing_before"] = missing
    print(f"missing scripts to mirror: {len(missing)}")
    print(f"stubbed dead upstream scripts: {len(report['stubbed'])}")

    rewrites = dict(existing_map)
    for url in missing:
        status, local_url = _mirror.mirror_url(url)
        if status.startswith("fail") and not dest_absolute_path(url).is_file():
            report["still_missing"].append({"url": url, "error": status})
            print(f"FAIL mirror {url} {status}")
            continue
        rewrites[url] = local_url
        report["mirrored_now"].append({"url": url, "local": local_url, "status": status})
        print(f"MIRRORED {url} -> {local_url} ({status})")

    # Always include our_foreign for rewrite application
    for url in our_foreign:
        if is_local_url(url) or should_skip_mirror(url):
            continue
        if url not in rewrites and dest_absolute_path(url).is_file():
            rewrites[url] = local_raw_url(dest_relative_path(url))

    _mirror.write_rewrite_map(rewrites)
    _mirror.apply_collections(rewrites)

    # re-scan foreign leftovers (extract_script_urls already excludes local)
    left: list[str] = []
    for name in (
        "adblock-collection.module",
        "unlock-collection.module",
        "cookie-collection.module",
        "skip-proxy-collection.module",
    ):
        path = MODULES / name
        if not path.is_file():
            continue
        for url in sorted(extract_script_urls(path.read_text(encoding="utf-8", errors="replace"))):
            left.append(url)
    report["foreign_in_our_collections"] = left
    print(f"foreign script-path left in our collections: {len(left)}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
