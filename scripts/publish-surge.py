#!/usr/bin/env python3
"""Publish Surge-only snapshot from sync workspace → origin/surge branch.

Keeps Egern main clean: Surge.conf + Rules + Surge-only modules live on surge.
Shared Scripts / most Modules still referenced from main raw URLs.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKTREE = Path(os.environ.get("PUBLISH_SURGE_WORKTREE", "/tmp/egern-surge-publish"))
SURGE_SRC = ROOT / "surge"
BRANCH = "surge"

# Paths relative to surge/ on the published branch
PUBLISH_FILES = [
    "Surge.conf",
    "README.md",
    "Icons.md",
]

# Surge-only modules (full copies; not shared with main Egern modules).
PUBLISH_MODULE_FILES = [
    "Modules/adblock-collection.module",
    "Modules/patches-pipixia.sgmodule",
    "Modules/pingme.sgmodule",
    "Modules/qdreader.sgmodule",
]

# Surge-only scripts (PingMe etc.); keep off main/Egern.
PUBLISH_SCRIPT_FILES = [
    "Scripts/PingMe-capture.js",
    "Scripts/PingMe-signin.js",
]


def run(cmd: list[str], *, cwd: Path) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> None:
    if not (SURGE_SRC / "Surge.conf").is_file():
        raise SystemExit(f"missing {SURGE_SRC / 'Surge.conf'}; run export + place conf first")
    if not (SURGE_SRC / "Rules").is_dir():
        raise SystemExit(f"missing {SURGE_SRC / 'Rules'}; run scripts/export-surge-rulesets.py")

    if WORKTREE.exists():
        shutil.rmtree(WORKTREE)

    # surge branch may not exist yet on first publish
    fetch = subprocess.run(
        ["git", "fetch", "origin", BRANCH],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    has_remote = fetch.returncode == 0
    if not has_remote:
        print(f"note: origin/{BRANCH} missing ({fetch.stderr.strip() or 'no ref'}); creating")

    if has_remote:
        run(
            ["git", "worktree", "add", "-B", BRANCH, str(WORKTREE), f"origin/{BRANCH}"],
            cwd=ROOT,
        )
    else:
        run(
            ["git", "worktree", "add", "--detach", str(WORKTREE), "HEAD"],
            cwd=ROOT,
        )
        run(["git", "checkout", "--orphan", BRANCH], cwd=WORKTREE)
        # Clear orphan index inherited from HEAD
        subprocess.run(
            ["git", "rm", "-rf", "--ignore-unmatch", "."],
            cwd=WORKTREE,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # Also unstage/remove leftover tracked files from working tree
        for child in list(WORKTREE.iterdir()):
            if child.name == ".git":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()

    # Existing surge branch: wipe working tree before copy
    if has_remote:
        for child in list(WORKTREE.iterdir()):
            if child.name == ".git":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()

    for name in PUBLISH_FILES:
        src = SURGE_SRC / name
        if not src.is_file():
            print(f"skip missing {src}")
            continue
        shutil.copy2(src, WORKTREE / name)
        print(f"copy {name}")

    for rel in PUBLISH_MODULE_FILES:
        src = SURGE_SRC / rel
        if not src.is_file():
            print(f"skip missing {src}")
            continue
        dest = WORKTREE / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        print(f"copy {rel}")

    for rel in PUBLISH_SCRIPT_FILES:
        src = SURGE_SRC / rel
        if not src.is_file():
            print(f"skip missing {src}")
            continue
        dest = WORKTREE / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        print(f"copy {rel}")

    # Disclaimer from repo root
    disclaimer = ROOT / "DISCLAIMER.md"
    if disclaimer.is_file():
        shutil.copy2(disclaimer, WORKTREE / "DISCLAIMER.md")

    rules_src = SURGE_SRC / "Rules"
    rules_dst = WORKTREE / "Rules"
    shutil.copytree(rules_src, rules_dst)
    print("copy Rules/")

    run(["git", "config", "user.name", "github-actions[bot]"], cwd=WORKTREE)
    run(
        ["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"],
        cwd=WORKTREE,
    )
    run(["git", "add", "-A"], cwd=WORKTREE)
    status = subprocess.run(["git", "diff", "--staged", "--quiet"], cwd=WORKTREE)
    if status.returncode == 0:
        print("surge publish: no changes")
    else:
        run(
            ["git", "commit", "-m", "chore: publish Surge snapshot from sync"],
            cwd=WORKTREE,
        )
        run(["git", "push", "-u", "origin", BRANCH], cwd=WORKTREE)

    run(["git", "worktree", "remove", "--force", str(WORKTREE)], cwd=ROOT)


if __name__ == "__main__":
    main()
