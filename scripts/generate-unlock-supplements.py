#!/usr/bin/env python3
"""Auto-build Surge unlock modules from mirrored QX-style author scripts."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import GITHUB_RAW_MAIN, MODULES, SIGNIN_SCRIPTS

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

CONFIG = Path(__file__).with_name("author-repos.yaml")
SECTION_RE = re.compile(r"\[rewrite_local\]", re.I)
MITM_RE = re.compile(r"\[mitm\]", re.I)


def load_config() -> dict:
    if not yaml:
        raise SystemExit("PyYAML required")
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}


def extract_block(text: str, start_pat: re.Pattern[str]) -> list[str]:
    lines = text.splitlines()
    out: list[str] = []
    active = False
    for line in lines:
        if start_pat.search(line):
            active = True
            continue
        if active:
            if line.strip().startswith("[") and line.strip().endswith("]"):
                break
            out.append(line)
    return out


def local_script_url(repo_id: str, filename: str) -> str:
    return f"{GITHUB_RAW_MAIN}/Scripts/{repo_id}/{filename}"


def surge_entries(repo_id: str, filename: str, text: str) -> tuple[list[str], set[str]]:
    scripts: list[str] = []
    hosts: set[str] = set()
    rewrite_lines = extract_block(text, SECTION_RE)
    mitm_lines = extract_block(text, MITM_RE)
    script_url = local_script_url(repo_id, filename)
    base_name = Path(filename).stem

    for line in mitm_lines:
        line = line.strip()
        if not line or line.startswith("#") or line == "*":
            continue
        if line.lower().startswith("hostname"):
            rhs = line.split("=", 1)[-1].strip()
            for h in rhs.split(","):
                h = h.strip()
                if h and h != "*":
                    hosts.add(h)

    idx = 0
    for line in rewrite_lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if " script-response-body " in line:
            pattern, _ = line.split(" script-response-body ", 1)
            idx += 1
            scripts.append(
                f"{base_name}_{idx} = type=http-response, pattern={pattern.strip()}, "
                f"script-path={script_url}, requires-body=true, max-size=-1, timeout=60"
            )
        elif " script-request-header " in line:
            pattern, _ = line.split(" script-request-header ", 1)
            idx += 1
            scripts.append(
                f"{base_name}_{idx} = type=http-request, pattern={pattern.strip()}, "
                f"script-path={script_url}, requires-body=true, max-size=-1, timeout=60"
            )
        elif " script-request-body " in line:
            pattern, _ = line.split(" script-request-body ", 1)
            idx += 1
            scripts.append(
                f"{base_name}_{idx} = type=http-request, pattern={pattern.strip()}, "
                f"script-path={script_url}, requires-body=true, max-size=-1, timeout=60"
            )

    return scripts, hosts


def build_module(repo_id: str, title: str, script_dir: Path) -> str:
    all_scripts: list[str] = []
    all_hosts: set[str] = set()
    for path in sorted(script_dir.glob("*.js")):
        text = path.read_text(encoding="utf-8", errors="replace")
        entries, hosts = surge_entries(repo_id, path.name, text)
        if entries:
            all_scripts.append(f"# --- {path.name} ---")
            all_scripts.extend(entries)
            all_hosts.update(hosts)

    lines = [
        f"#!name={title}",
        f"#!desc=自动生成：{repo_id} 仓库全量解锁脚本（本地镜像）",
        f"#!author=oo226/egern-config",
        "",
        "[Script]",
        *all_scripts,
        "",
        "[MITM]",
        "hostname = %APPEND% " + ", ".join(sorted(all_hosts)) if all_hosts else "hostname = %APPEND%",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    data = load_config()
    for repo in data.get("repos", []):
        if not repo.get("generate_unlock"):
            continue
        repo_id = repo["id"]
        script_dir = SIGNIN_SCRIPTS / repo["dest_scripts"]
        if not script_dir.is_dir():
            print(f"skip {repo_id}: missing {script_dir}")
            continue
        title = {"weigiegie": "WeiGiegie解锁合集", "liul0ng": "liul0ng解锁合集"}.get(
            repo_id, f"{repo_id} unlock"
        )
        out = MODULES / f"{repo_id}-unlock.sgmodule"
        content = build_module(repo_id, title, script_dir)
        out.write_text(content, encoding="utf-8")
        print(f"wrote {out.name} ({len(content.splitlines())} lines)")


if __name__ == "__main__":
    main()
