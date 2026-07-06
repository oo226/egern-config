#!/usr/bin/env python3
"""Publish curated artifacts from the sync branch workspace onto main."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "publish" / "manifest.yaml"
WORKTREE = Path(os.environ.get("PUBLISH_MAIN_WORKTREE", "/tmp/egern-main-publish"))

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


def load_manifest() -> dict:
    if not yaml:
        raise SystemExit("PyYAML required: pip install pyyaml")
    return yaml.safe_load(MANIFEST.read_text(encoding="utf-8")) or {}


def run(cmd: list[str], *, cwd: Path) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def copy_file(src: Path, dst: Path) -> None:
    if not src.is_file():
        print(f"skip missing file: {src}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"copy file {src.relative_to(ROOT)}")


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print(f"copy tree {src.relative_to(ROOT)} -> {dst.relative_to(WORKTREE)}")


def publish_routing(spec: dict) -> None:
    src_root = ROOT / "Routing"
    dst_root = WORKTREE / "Routing"
    exclude = set(spec.get("exclude_dirs") or [])
    if dst_root.exists():
        shutil.rmtree(dst_root)
    dst_root.mkdir(parents=True, exist_ok=True)
    for item in sorted(src_root.iterdir()):
        if item.name in exclude:
            continue
        target = dst_root / item.name
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)
    print("copy Routing/ (excluding %s)" % ", ".join(sorted(exclude)) or "none")


def publish_modules(spec: dict) -> None:
    include_only = spec.get("include_only") or []
    dst_root = WORKTREE / "Modules"
    if dst_root.exists():
        shutil.rmtree(dst_root)
    dst_root.mkdir(parents=True, exist_ok=True)
    for name in include_only:
        copy_file(ROOT / "Modules" / name, dst_root / name)


def publish_scripts(spec: dict) -> None:
    src_root = ROOT / "Scripts"
    dst_root = WORKTREE / "Scripts"
    exclude_dirs = set(spec.get("exclude_dirs") or [])
    include_subdirs = spec.get("include_subdirs") or []
    include_root_glob = spec.get("include_root_glob") or "*.js"
    extra_files = spec.get("extra_files") or []

    if dst_root.exists():
        shutil.rmtree(dst_root)
    dst_root.mkdir(parents=True, exist_ok=True)

    for path in sorted(src_root.glob(include_root_glob)):
        if path.is_file():
            shutil.copy2(path, dst_root / path.name)

    for name in include_subdirs:
        if name in exclude_dirs:
            continue
        src = src_root / name
        if src.is_dir():
            shutil.copytree(src, dst_root / name)

    for name in extra_files:
        copy_file(src_root / name, dst_root / name)

    print(
        "copy Scripts/ root=%s subdirs=%s"
        % (include_root_glob, ", ".join(include_subdirs))
    )


def publish_assets(spec: dict) -> None:
    dst_root = WORKTREE / "Assets"
    if dst_root.exists():
        shutil.rmtree(dst_root)
    dst_root.mkdir(parents=True, exist_ok=True)
    for name in spec.get("include_subdirs") or []:
        src = ROOT / "Assets" / name
        if src.is_dir():
            shutil.copytree(src, dst_root / name)


def publish_widgets(spec: dict) -> None:
    dst_root = WORKTREE / "Widgets"
    if dst_root.exists():
        shutil.rmtree(dst_root)
    dst_root.mkdir(parents=True, exist_ok=True)
    for name in spec.get("include_subdirs") or []:
        src = ROOT / "Widgets" / name
        if src.is_dir():
            shutil.copytree(src, dst_root / name)


def publish_directory(spec: dict) -> None:
    path = spec["path"]
    if path == "Routing":
        publish_routing(spec)
    elif path == "Modules":
        publish_modules(spec)
    elif path == "Scripts":
        publish_scripts(spec)
    elif path == "Assets":
        publish_assets(spec)
    elif path == "Widgets":
        publish_widgets(spec)
    else:
        raise SystemExit(f"unsupported publish directory: {path}")


def prune_from_main(paths: list[str]) -> None:
    for rel in paths:
        target = WORKTREE / rel
        if not target.exists():
            continue
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        print(f"prune {rel}")


def setup_worktree() -> None:
    if WORKTREE.exists():
        shutil.rmtree(WORKTREE)
    run(["git", "fetch", "origin", "main"], cwd=ROOT)
    run(
        ["git", "worktree", "add", "-B", "main", str(WORKTREE), "origin/main"],
        cwd=ROOT,
    )


def commit_and_push() -> None:
    run(["git", "config", "user.name", "github-actions[bot]"], cwd=WORKTREE)
    run(
        ["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"],
        cwd=WORKTREE,
    )
    run(["git", "add", "-A"], cwd=WORKTREE)
    status = subprocess.run(
        ["git", "diff", "--staged", "--quiet"],
        cwd=WORKTREE,
    )
    if status.returncode == 0:
        print("main publish: no changes")
        return
    run(
        ["git", "commit", "-m", "chore: publish curated snapshot from sync"],
        cwd=WORKTREE,
    )
    run(["git", "push", "origin", "main"], cwd=WORKTREE)


def cleanup_worktree() -> None:
    run(["git", "worktree", "remove", "--force", str(WORKTREE)], cwd=ROOT)


def main() -> None:
    data = load_manifest()
    setup_worktree()
    try:
        prune_from_main(data.get("prune_from_main") or [])
        for rel in data.get("files") or []:
            copy_file(ROOT / rel, WORKTREE / rel)
        for spec in data.get("directories") or []:
            publish_directory(spec)
        commit_and_push()
    finally:
        cleanup_worktree()


if __name__ == "__main__":
    main()
