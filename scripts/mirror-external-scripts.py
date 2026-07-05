#!/usr/bin/env python3
"""Mirror every third-party script-path URL referenced by modules into Scripts/_external/."""

from __future__ import annotations

import ssl
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from external_script_utils import (
    REWRITE_MAP,
    collect_module_source_paths,
    collect_script_urls_from_paths,
    dest_absolute_path,
    dest_relative_path,
    extract_script_urls,
    is_local_url,
    local_raw_url,
    normalize_url,
    should_skip_mirror,
)
from paths import MODULES, ROOT

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

CTX = ssl.create_default_context()
MIRROR = "https://ghproxy.net/"


def is_valid_payload(data: bytes) -> bool:
    if not data:
        return False
    head = data[:512].lstrip()
    if head.startswith(b"<!DOCTYPE") or head.startswith(b"<html") or head.startswith(b"<HTML"):
        return False
    if b"404: Not Found" in data[:200] or b"404: Not Found" in data[-200:]:
        return False
    return True


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


def mirror_url(url: str) -> tuple[str, str]:
    """Return (status, local_raw_url). status is ok|keep|fail."""
    url = normalize_url(url)
    dest = dest_absolute_path(url)
    rel = dest_relative_path(url)
    local_url = local_raw_url(rel)

    try:
        data = fetch_bytes(url)
        if not is_valid_payload(data):
            raise ValueError("invalid payload")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return "ok", local_url
    except Exception as exc:
        if dest.is_file() and dest.stat().st_size > 0:
            return f"keep ({exc})", local_url
        return f"fail ({exc})", local_url


def discover_urls(extra_files: list[Path] | None = None) -> set[str]:
    paths = collect_module_source_paths(ROOT)
    if extra_files:
        paths.extend(extra_files)
    paths = sorted(set(paths))
    urls = collect_script_urls_from_paths(paths)
    for path in (MODULES / "adblock-collection.module", MODULES / "unlock-collection.module"):
        if path.is_file():
            urls.update(extract_script_urls(path.read_text(encoding="utf-8", errors="replace")))
    return urls


def write_rewrite_map(rewrites: dict[str, str]) -> None:
    if not yaml:
        raise SystemExit("PyYAML required")
    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rewrites": dict(sorted(rewrites.items())),
    }
    REWRITE_MAP.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def apply_collections(rewrites: dict[str, str]) -> None:
    from external_script_utils import apply_external_rewrites

    targets = [
        MODULES / "adblock-collection.module",
        MODULES / "unlock-collection.module",
        MODULES / "boxjs.sgmodule",
    ]
    targets.extend(MODULES.glob("iringo-*.sgmodule"))
    targets.extend(
        p
        for p in MODULES.glob("*.sgmodule")
        if p.name
        not in {
            "custom-apps.sgmodule",
            "chxm1023-ad-supplement.sgmodule",
            "patches-alicloud.sgmodule",
            "patches-unlock.sgmodule",
        }
        and not p.name.startswith("qingrex-")
        and not p.name.startswith("fmz200-")
        and not p.name.startswith("weigiegie-")
        and not p.name.startswith("liul0ng-")
    )

    seen: set[Path] = set()
    for path in targets:
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        original = path.read_text(encoding="utf-8")
        updated = apply_external_rewrites(original, rewrites)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            print(f"rewrote {path.name}")


def main() -> None:
    extra: list[Path] = []
    for arg in sys.argv[1:]:
        path = Path(arg)
        if path.is_file():
            extra.append(path)

    urls = sorted(discover_urls(extra))
    rewrites: dict[str, str] = {}
    ok = keep = fail = 0

    print(f"discovered {len(urls)} external script-path URLs")
    for url in urls:
        if is_local_url(url) or should_skip_mirror(url):
            continue
        status, local_url = mirror_url(url)
        if status.startswith("fail") and not dest_absolute_path(url).is_file():
            fail += 1
            print(f"FAIL {url} {status}")
            continue
        rewrites[url] = local_url
        if status == "ok":
            ok += 1
            print(f"OK {dest_relative_path(url)}")
        elif status.startswith("keep"):
            keep += 1
            print(f"KEEP {dest_relative_path(url)} {status}")
        else:
            fail += 1
            print(f"FAIL {url} {status}")

    write_rewrite_map(rewrites)
    apply_collections(rewrites)
    print(
        f"mirror summary ok={ok} keep={keep} fail={fail} "
        f"map={REWRITE_MAP.name} ({len(rewrites)} entries)"
    )
    if fail:
        print("warning: some scripts could not be mirrored; retained map entries point at local paths only when files exist")


if __name__ == "__main__":
    main()
