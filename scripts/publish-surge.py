#!/usr/bin/env python3
"""Publish Surge-only snapshot from sync workspace → origin/surge branch.

Keeps Egern main clean: Surge.conf + Rules + Surge-only modules live on surge.
Shared Scripts / most Modules still referenced from main raw URLs.

Hand-tuned Surge fixes (heat6+ 防烫 / ByteDance-Heat) must not be downgraded when
sync/surge/ factory snapshot is stale. Protected paths keep the higher heat marker
from the existing surge branch.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKTREE = Path(os.environ.get("PUBLISH_SURGE_WORKTREE", "/tmp/egern-surge-publish"))
SURGE_SRC = ROOT / "surge"
BRANCH = "surge"

# Paths relative to repo root on the published surge branch
PUBLISH_FILES = [
    "Surge.conf",
    "README.md",
    "Icons.md",
]

PUBLISH_MODULE_FILES = [
    "Modules/adblock-collection.module",
    "Modules/patches-pipixia.sgmodule",
    "Modules/patches-unlock.sgmodule",
    "Modules/pingme.sgmodule",
    "Modules/pipixia-heat.sgmodule",
    "Modules/qdreader.sgmodule",
    "Modules/iringo-others.sgmodule",
    "Modules/iringo-maps.sgmodule",
    "Modules/unlock-collection.module",
    "Modules/oil-price.sgmodule",
    "Modules/netunlock.sgmodule",
    "Modules/tg-mitm-heat.sgmodule",
    "Modules/app-heat.sgmodule",
    "Modules/google-gemini-fix.sgmodule",
]

PUBLISH_SCRIPT_FILES = [
    "Scripts/PingMe-capture.js",
    "Scripts/PingMe-signin.js",
    "Scripts/pangolin-fake-log.js",
    "Scripts/oil-price.js",
    "Scripts/netunlock.js",
]

# Never downgrade these when surge branch has a higher heat marker.
PROTECTED_HEAT_PATHS = frozenset(
    {
        "Modules/adblock-collection.module",
        "Modules/pipixia-heat.sgmodule",
    }
)

# Keep surge-branch copy if sync factory omitted the file entirely.
PROTECTED_PRESERVE_IF_MISSING = frozenset(
    {
        "Rules/ByteDance-Heat.list",
        "Scripts/pangolin-fake-log.js",
        "Modules/oil-price.sgmodule",
        "Modules/netunlock.sgmodule",
        "Modules/tg-mitm-heat.sgmodule",
        "Modules/app-heat.sgmodule",
        "Modules/google-gemini-fix.sgmodule",
        "Rules/App-Heat.list",
        "Scripts/oil-price.js",
        "Scripts/netunlock.js",
    }
)

_HEAT_SCORE_RE = re.compile(r"heat(\d+)", re.IGNORECASE)

ANTI_RETRY_MARKERS = (
    "DOMAIN,stats.jpush.cn,DIRECT",
    "pangolin-fake-log",
    "(?!log-api\\.)(?!api-access\\.)",
    "jpush-fake-stats",
)


def run(cmd: list[str], *, cwd: Path) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def heat_score(text: str) -> int:
    scores = [int(m.group(1)) for m in _HEAT_SCORE_RE.finditer(text[:4000])]
    return max(scores) if scores else 0


def has_anti_retry(text: str) -> bool:
    return all(m in text for m in ANTI_RETRY_MARKERS)


def read_text(path: Path) -> str | None:
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def snapshot_tree(base: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not base.is_dir():
        return out
    for path in base.rglob("*"):
        if not path.is_file() or path.name == ".git":
            continue
        rel = path.relative_to(base).as_posix()
        if rel.startswith(".git/"):
            continue
        text = read_text(path)
        if text is not None:
            out[rel] = text
    return out


def copy_file(rel: str, *, src_root: Path, dest_root: Path, preserved: dict[str, str]) -> None:
    src = src_root / rel
    dest = dest_root / rel
    preserved_text = preserved.get(rel)

    if not src.is_file():
        if preserved_text is not None and rel in PROTECTED_PRESERVE_IF_MISSING:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(preserved_text, encoding="utf-8")
            print(f"preserve missing sync source {rel} (kept surge branch)")
        else:
            print(f"skip missing {src}")
        return

    src_text = read_text(src) or ""
    use_preserved = False

    if preserved_text is not None and rel in PROTECTED_HEAT_PATHS:
        src_ok = has_anti_retry(src_text)
        old_ok = has_anti_retry(preserved_text)
        src_score = heat_score(src_text)
        old_score = heat_score(preserved_text)
        # Prefer surge copy whenever sync lost anti-retry markers, or heat dropped.
        if old_ok and not src_ok:
            use_preserved = True
            print(f"preserve {rel} (sync missing anti-retry markers; kept surge)")
        elif old_score > src_score:
            use_preserved = True
            print(
                f"preserve {rel} (surge heat{old_score} > sync heat{src_score})"
            )

    dest.parent.mkdir(parents=True, exist_ok=True)
    if use_preserved and preserved_text is not None:
        dest.write_text(preserved_text, encoding="utf-8")
    else:
        shutil.copy2(src, dest)
        print(f"copy {rel}")


def copy_rules(*, src_root: Path, dest_root: Path, preserved: dict[str, str]) -> None:
    rules_src = src_root / "Rules"
    rules_dst = dest_root / "Rules"
    if rules_dst.exists():
        shutil.rmtree(rules_dst)
    if rules_src.is_dir():
        shutil.copytree(rules_src, rules_dst)
        print("copy Rules/")
    else:
        rules_dst.mkdir(parents=True, exist_ok=True)
        print("skip missing Rules/ source")

    for rel, needle in (
        ("Rules/ByteDance-Heat.list", "stats.jpush.cn"),
        ("Rules/App-Heat.list", "doudou520.online"),
    ):
        preserved_text = preserved.get(rel)
        if preserved_text is None:
            continue
        name = Path(rel).name
        dest = rules_dst / name
        src_text = read_text(rules_src / name) if rules_src.is_dir() else None
        if src_text is None:
            dest.write_text(preserved_text, encoding="utf-8")
            print(f"preserve {rel} (missing in sync Rules/)")
            continue
        if needle not in src_text and needle in preserved_text:
            dest.write_text(preserved_text, encoding="utf-8")
            print(f"preserve {rel} (sync list missing {needle})")


def validate_adblock(dest_root: Path) -> None:
    path = dest_root / "Modules/adblock-collection.module"
    text = read_text(path)
    if not text:
        raise SystemExit(f"publish surge: missing {path}")
    score = heat_score(text)
    if score < 6:
        raise SystemExit(
            f"publish surge: adblock-collection.module heat score {score} < 6; "
            "refusing to publish stale factory snapshot (would restore 狂刷 REJECT)."
        )
    missing = [s for s in ANTI_RETRY_MARKERS if s not in text]
    if missing:
        raise SystemExit(
            "publish surge: adblock missing anti-retry markers: " + ", ".join(missing)
        )
    print(f"validate adblock-collection.module heat{score} ok")


def merge_surge_conf(*, src: Path, dest: Path, preserved_text: str | None) -> None:
    if not src.is_file():
        if preserved_text:
            dest.write_text(preserved_text, encoding="utf-8")
            print("preserve Surge.conf (missing sync source)")
        return
    text = read_text(src) or ""
    for heat_line, label in (
        (
            "RULE-SET,https://raw.githubusercontent.com/oo226/egern-config/"
            "refs/heads/surge/Rules/ByteDance-Heat.list,DIRECT,extended-matching",
            "ByteDance-Heat",
        ),
        (
            "RULE-SET,https://raw.githubusercontent.com/oo226/egern-config/"
            "refs/heads/surge/Rules/App-Heat.list,DIRECT,extended-matching",
            "App-Heat",
        ),
    ):
        if heat_line in text:
            continue
        if preserved_text and heat_line in preserved_text:
            text = preserved_text
            print(f"preserve Surge.conf (kept {label} RULE-SET from surge branch)")
            break
        needle = (
            "DOMAIN-SET,https://raw.githubusercontent.com/oo226/egern-config/"
            "refs/heads/surge/Rules/Reject-Merged.domainset"
        )
        if needle in text:
            text = text.replace(needle, heat_line + "\n" + needle, 1)
            print(f"inserted {label} RULE-SET into Surge.conf")

    # Telegram 裸 IP MitM 排除必须在主配置 hostname 最前；缺了就从 surge 备份补或硬插入。
    ip_excl = "-<ip-address>:0"
    if ip_excl not in text:
        if preserved_text and ip_excl in preserved_text:
            text = preserved_text
            print("preserve Surge.conf (kept -<ip-address>:0 MitM exclude from surge)")
        else:
            text2, n = re.subn(
                r"^(hostname\s*=\s*)",
                rf"\g<1>{ip_excl}, ",
                text,
                count=1,
                flags=re.M,
            )
            if n:
                text = text2
                print("inserted -<ip-address>:0 into Surge.conf MITM hostname")
            else:
                print("warn: could not insert -<ip-address>:0 (no hostname= line)")

    dest.write_text(text, encoding="utf-8")
    print("copy Surge.conf")


def main() -> None:
    if not (SURGE_SRC / "Surge.conf").is_file():
        raise SystemExit(f"missing {SURGE_SRC / 'Surge.conf'}; run export + place conf first")
    if not (SURGE_SRC / "Rules").is_dir():
        raise SystemExit(f"missing {SURGE_SRC / 'Rules'}; run scripts/export-surge-rulesets.py")

    if WORKTREE.exists():
        shutil.rmtree(WORKTREE)

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
        run(["git", "worktree", "add", "--detach", str(WORKTREE), "HEAD"], cwd=ROOT)
        run(["git", "checkout", "--orphan", BRANCH], cwd=WORKTREE)
        subprocess.run(
            ["git", "rm", "-rf", "--ignore-unmatch", "."],
            cwd=WORKTREE,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for child in list(WORKTREE.iterdir()):
            if child.name == ".git":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()

    preserved = snapshot_tree(WORKTREE)

    if has_remote:
        for child in list(WORKTREE.iterdir()):
            if child.name == ".git":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()

    for name in PUBLISH_FILES:
        if name == "Surge.conf":
            merge_surge_conf(
                src=SURGE_SRC / name,
                dest=WORKTREE / name,
                preserved_text=preserved.get(name),
            )
            continue
        src = SURGE_SRC / name
        if not src.is_file():
            print(f"skip missing {src}")
            continue
        shutil.copy2(src, WORKTREE / name)
        print(f"copy {name}")

    for rel in PUBLISH_MODULE_FILES:
        copy_file(rel, src_root=SURGE_SRC, dest_root=WORKTREE, preserved=preserved)

    for rel in PUBLISH_SCRIPT_FILES:
        copy_file(rel, src_root=SURGE_SRC, dest_root=WORKTREE, preserved=preserved)

    copy_rules(src_root=SURGE_SRC, dest_root=WORKTREE, preserved=preserved)

    disclaimer = ROOT / "DISCLAIMER.md"
    if disclaimer.is_file():
        shutil.copy2(disclaimer, WORKTREE / "DISCLAIMER.md")

    validate_adblock(WORKTREE)

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
