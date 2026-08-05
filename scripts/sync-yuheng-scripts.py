#!/usr/bin/env python3
"""Mirror Yuheng0101/X Tasks scripts + Surge modules into this repo (anti-delete).

- Scripts/yuheng/Tasks/**/*.js  (skip src/ build trees; keep dist/ + leaf tasks)
- Modules/yuheng/*.sgmodule     (profiles with script-path rewritten to local mirrors)
- Also refresh Scripts/qdreader.js shortcut used by cookie-collection
"""

from __future__ import annotations

import json
import re
import shutil
import ssl
import sys
import urllib.request
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import GITHUB_RAW_MAIN, MODULES, SIGNIN_SCRIPTS

REPO = "Yuheng0101/X"
BRANCH = "main"
OUTPUT_SCRIPTS = SIGNIN_SCRIPTS / "yuheng"
OUTPUT_MODULES = MODULES / "yuheng"
CTX = ssl.create_default_context()
MIRROR = "https://ghproxy.net/"
UA = {"User-Agent": "egern-config-sync/1.0"}

SKIP_DIR_PARTS = {
    "node_modules",
    "src",
    ".git",
}
SKIP_NAME_SUFFIXES = (
    ".config.js",
    "rollup.config.js",
    "rollup.default.config.js",
    "rollup.dev.config.js",
    "biome.json",
    "package.json",
    "package-lock.json",
    "local-links.json",
)

UPSTREAM_SCRIPT_PREFIXES = (
    f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/",
    f"https://raw.githubusercontent.com/{REPO}/refs/heads/{BRANCH}/",
)


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=120) as resp:
            return resp.read()
    except Exception:
        mirror_url = MIRROR + url
        req = urllib.request.Request(mirror_url, headers=UA)
        with urllib.request.urlopen(req, context=CTX, timeout=120) as resp:
            return resp.read()


def list_tree() -> list[str]:
    url = f"https://api.github.com/repos/{REPO}/git/trees/{BRANCH}?recursive=1"
    data = json.loads(fetch(url).decode("utf-8"))
    if data.get("truncated"):
        print("WARN: yuheng tree truncated")
    return [t["path"] for t in data.get("tree") or [] if t.get("type") == "blob" and t.get("path")]


def keep_script(path: str) -> bool:
    if not path.startswith("Tasks/"):
        return False
    if not path.endswith(".js"):
        return False
    parts = path.split("/")
    if any(p in SKIP_DIR_PARTS for p in parts):
        return False
    name = parts[-1]
    if name.endswith(SKIP_NAME_SUFFIXES) or name in SKIP_NAME_SUFFIXES:
        return False
    if name.endswith(".config.js"):
        return False
    return True


def keep_module(path: str) -> bool:
    return path.startswith("Tasks/") and path.endswith(".sgmodule")


def is_valid_script(data: bytes) -> bool:
    if len(data) < 16:
        return False
    head = data[:512].lstrip()
    return not (head.startswith(b"<!DOCTYPE") or head.startswith(b"<html"))


def rewrite_module_text(text: str) -> str:
    for old in UPSTREAM_SCRIPT_PREFIXES:
        text = text.replace(old, f"{GITHUB_RAW_MAIN}/Scripts/yuheng/")
    # keep #!arguments intact for Egern template UI
    if "#!author=" not in text.split("[", 1)[0]:
        text = text.replace(
            "#!desc=",
            "#!author=Yuheng0101[https://github.com/Yuheng0101]\n#!homepage=https://github.com/Yuheng0101/X\n#!desc=",
            1,
        )
    note = "# mirrored from Yuheng0101/X — script-path → 本仓 Scripts/yuheng/（防删库）；模版参数保留\n"
    if not text.lstrip().startswith("# mirrored"):
        text = note + text
    return text


def module_out_name(rel: str) -> str:
    # Tasks/QDReader/profiles/qdreader.surge.sgmodule -> qdreader.sgmodule (compat)
    # Tasks/meitu/meitu.sgmodule -> meitu.sgmodule
    name = Path(rel).name
    name = re.sub(r"\.surge\.sgmodule$", ".sgmodule", name)
    return name


def main() -> None:
    paths = list_tree()
    scripts = [p for p in paths if keep_script(p)]
    modules = [p for p in paths if keep_module(p)]
    OUTPUT_SCRIPTS.mkdir(parents=True, exist_ok=True)
    OUTPUT_MODULES.mkdir(parents=True, exist_ok=True)

    ok = fail = skip = 0
    for rel in sorted(scripts):
        url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{quote(rel, safe='/')}"
        out = OUTPUT_SCRIPTS / rel
        try:
            data = fetch(url)
            if not is_valid_script(data):
                raise ValueError("invalid script payload")
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(data)
            print(f"OK script {rel} ({len(data)} bytes)")
            ok += 1
        except Exception as exc:
            if out.is_file() and out.stat().st_size > 0:
                print(f"KEEP script {rel}: {exc}")
                skip += 1
            else:
                print(f"FAIL script {rel}: {exc}")
                fail += 1

    # shortcut copy for cookie-collection / legacy catalog
    src_qd = OUTPUT_SCRIPTS / "Tasks/QDReader/qdreader.js"
    dst_qd = SIGNIN_SCRIPTS / "qdreader.js"
    if src_qd.is_file():
        shutil.copy2(src_qd, dst_qd)
        print(f"OK shortcut Scripts/qdreader.js <- {src_qd.relative_to(SIGNIN_SCRIPTS)}")

    mod_ok = mod_fail = 0
    published_names: list[str] = []
    for rel in sorted(modules):
        url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{quote(rel, safe='/')}"
        out_name = module_out_name(rel)
        # 起点模块固定在 Modules/qdreader.sgmodule（保留模版参数，稳定 URL）
        if out_name == "qdreader.sgmodule":
            print("skip Modules/yuheng/qdreader.sgmodule (use Modules/qdreader.sgmodule)")
            stale = OUTPUT_MODULES / out_name
            if stale.exists():
                stale.unlink()
            continue
        out = OUTPUT_MODULES / out_name
        try:
            text = fetch(url).decode("utf-8", errors="replace")
            text = rewrite_module_text(text)
            out.write_text(text, encoding="utf-8")
            published_names.append(out_name)
            print(f"OK module {rel} -> Modules/yuheng/{out_name}")
            mod_ok += 1
        except Exception as exc:
            print(f"FAIL module {rel}: {exc}")
            mod_fail += 1

    # also mirror boxjs.json
    try:
        box = fetch(
            f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/Tasks/boxjs.json"
        )
        (OUTPUT_SCRIPTS / "Tasks" / "boxjs.json").parent.mkdir(parents=True, exist_ok=True)
        (OUTPUT_SCRIPTS / "Tasks" / "boxjs.json").write_bytes(box)
        print(f"OK Tasks/boxjs.json ({len(box)} bytes)")
    except Exception as exc:
        print(f"FAIL boxjs.json: {exc}")

    print(
        f"summary scripts ok={ok} kept={skip} fail={fail} "
        f"modules ok={mod_ok} fail={mod_fail} names={published_names}"
    )


if __name__ == "__main__":
    main()
