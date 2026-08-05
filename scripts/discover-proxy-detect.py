#!/usr/bin/env python3
"""Discover upstream modules/rewrites related to proxy-app detection.

Writes:
  site/upstream-proxy-detect.json  — catalog-ready list (upstream raw URLs)
  Modules/proxy-detect-extra.sgmodule — merged General/Rule snippets for unlock merge
  site/upstreams.json — snapshot of scripts/upstream-sources.yaml sources

Users subscribe via upstream URLs; we only index + optionally merge.
"""

from __future__ import annotations

import json
import re
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import MODULES, ROOT, UPSTREAM_CACHE

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

CTX = ssl.create_default_context()
UA = {"User-Agent": "egern-config-sync/1.0"}
CONFIG = Path(__file__).with_name("upstream-sources.yaml")
OUT_INDEX = ROOT / "site" / "upstream-proxy-detect.json"
OUT_SOURCES = ROOT / "site" / "upstreams.json"
OUT_MODULE = MODULES / "proxy-detect-extra.sgmodule"

MODULE_SUFFIXES = (".sgmodule", ".module", ".conf")
RULE_SUFFIXES = (".yaml", ".yml", ".list", ".txt", ".conf")

# 文件名强相关才整收；内容命中需 General 里真有 skip-proxy/always-real-ip，且用途像「代理检测」
PATH_STRONG = re.compile(
    r"skip[-_]?proxy|always[-_]?real[-_]?ip|代理检测|跳过代理|Skip[-_]?Proxy|防代理检测",
    re.IGNORECASE,
)
GENERAL_LINE = re.compile(
    r"^\s*(skip-proxy|always-real-ip)\s*=",
    re.IGNORECASE,
)
PURPOSE = re.compile(
    r"代理检测|跳过代理|skip\s*proxy|real-?ip|绕过.*检测|防.*检测",
    re.IGNORECASE,
)
FALSE_POSITIVE_NAME = re.compile(
    r"testflight|iringo|去广告|adblock|广告|签到|cookie|boxjs",
    re.IGNORECASE,
)


def load_cfg() -> dict:
    if not yaml:
        raise SystemExit("PyYAML required: pip install pyyaml")
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}


def fetch(url: str, timeout: int = 90) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, context=CTX, timeout=timeout) as resp:
        return resp.read()


def fetch_text(url: str) -> str:
    return fetch(url).decode("utf-8", errors="replace")


def keyword_re(keywords: list[str]) -> re.Pattern[str]:
    parts = [re.escape(k) for k in keywords if k]
    return re.compile("|".join(parts), re.IGNORECASE)


def github_raw(github: str, branch: str, path: str) -> str:
    return f"https://raw.githubusercontent.com/{github}/{branch}/{quote(path, safe='/')}"


def list_repo_tree(github: str, branch: str) -> list[str]:
    url = f"https://api.github.com/repos/{github}/git/trees/{quote(branch, safe='')}?recursive=1"
    try:
        data = json.loads(fetch(url).decode("utf-8"))
    except Exception as exc:
        print(f"WARN tree {github}@{branch}: {exc}")
        return []
    if data.get("truncated"):
        print(f"WARN tree truncated: {github}")
    out: list[str] = []
    for item in data.get("tree") or []:
        if item.get("type") == "blob" and item.get("path"):
            out.append(item["path"])
    return out


def looks_relevant(path: str, keywords: re.Pattern[str], text_head: str = "") -> bool:
    del keywords  # seeds/watch use PATH_STRONG + PURPOSE; config keywords kept for docs
    name = path.rsplit("/", 1)[-1]
    if FALSE_POSITIVE_NAME.search(name) and not PATH_STRONG.search(name):
        return False
    if PATH_STRONG.search(path) or PATH_STRONG.search(name):
        return True
    if not text_head:
        return False
    header = text_head.split("[", 1)[0]
    has_general_knob = any(GENERAL_LINE.search(line) for line in text_head.splitlines())
    if not has_general_knob:
        return False
    # General 有 knob，且标题/描述明确是代理检测类（避免「通用模块」误伤）
    if PURPOSE.search(header) or PURPOSE.search(name):
        return True
    return False


def parse_surge_header(text: str) -> dict[str, str]:
    meta: dict[str, str] = {}
    for line in text.splitlines()[:40]:
        if line.startswith("#!") and "=" in line:
            key, _, val = line[2:].partition("=")
            meta[key.strip().lower()] = val.strip()
        elif line.startswith("["):
            break
    return meta


def entry_from_seed(seed: dict) -> dict:
    return {
        "id": seed["id"],
        "name": seed.get("name") or seed["id"],
        "kind": seed.get("kind", "module"),
        "url": seed["url"],
        "homepage": seed.get("homepage", ""),
        "tags": list(seed.get("tags") or ["代理检测"]),
        "source": "seed",
        "upstream": True,
    }


def discover_from_repos(cfg: dict, keywords: re.Pattern[str]) -> list[dict]:
    items: list[dict] = []
    seen_urls: set[str] = set()
    for repo in cfg.get("watch_repos") or []:
        github = repo["github"]
        branch = repo.get("branch") or "main"
        prefix = repo.get("path_prefix") or ""
        # 大仓只认路径/文件名；小仓才扫内容
        content_scan = bool(repo.get("content_scan", False))
        paths = list_repo_tree(github, branch)
        for path in paths:
            if prefix and not path.startswith(prefix):
                continue
            lower = path.lower()
            if not lower.endswith(MODULE_SUFFIXES + RULE_SUFFIXES):
                continue
            url = github_raw(github, branch, path)
            text_head = ""
            path_hit = bool(PATH_STRONG.search(path))
            if not path_hit:
                if not content_scan or not lower.endswith(MODULE_SUFFIXES):
                    continue
                try:
                    text_head = fetch_text(url)[:4000]
                except Exception:
                    continue
                if not looks_relevant(path, keywords, text_head):
                    continue
            else:
                try:
                    text_head = fetch_text(url)[:4000]
                except Exception as exc:
                    print(f"KEEP skip fetch {url}: {exc}")
                    text_head = ""

            if url in seen_urls:
                continue
            seen_urls.add(url)
            header = parse_surge_header(text_head) if text_head else {}
            name = header.get("name") or Path(path).stem
            desc = header.get("desc", "")
            kind = "module" if lower.endswith(MODULE_SUFFIXES) else "rule"
            if Path(path).name.lower() in {"readme.md", "license"}:
                continue
            items.append(
                {
                    "id": f"proxy-detect-{github.replace('/', '-').lower()}-{Path(path).stem.lower()}".replace(
                        ".", "-"
                    )[:80],
                    "name": name,
                    "desc": desc or f"上游 {github} — 代理检测相关",
                    "kind": kind,
                    "url": url,
                    "homepage": f"https://github.com/{github}",
                    "path": path,
                    "tags": ["代理检测", "上游原链", github.split("/")[0]],
                    "source": f"watch:{github}",
                    "upstream": True,
                }
            )
            print(f"OK discover {github}:{path}")
    return items


def discover_from_local(keywords: re.Pattern[str]) -> list[dict]:
    """Scan Modules/_upstream mirrors; only emit entries we can map to a public upstream URL."""
    del keywords
    if not UPSTREAM_CACHE.is_dir():
        return []
    # author-repos id → github/branch for raw URL rebuild
    author_map: dict[str, tuple[str, str]] = {}
    try:
        repos_cfg = yaml.safe_load((Path(__file__).with_name("author-repos.yaml")).read_text(encoding="utf-8")) or {}
        for repo in repos_cfg.get("repos") or []:
            author_map[repo["id"]] = (repo["github"], repo.get("branch") or "main")
    except Exception:
        pass

    items: list[dict] = []
    for path in sorted(UPSTREAM_CACHE.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".sgmodule", ".module"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        rel = path.relative_to(UPSTREAM_CACHE).as_posix()
        if not looks_relevant(rel, PATH_STRONG, text[:4000]):
            continue
        author = rel.split("/", 1)[0]
        rest = rel.split("/", 1)[1] if "/" in rel else path.name
        url = ""
        homepage = ""
        if author in author_map:
            gh, branch = author_map[author]
            # mirrored path may already be stripped; best-effort
            url = github_raw(gh, branch, rest)
            homepage = f"https://github.com/{gh}"
        if not url:
            continue
        header = parse_surge_header(text)
        items.append(
            {
                "id": f"proxy-detect-local-{path.stem.lower()}"[:80],
                "name": header.get("name") or path.stem,
                "desc": header.get("desc") or f"本地镜像命中：{rel}",
                "kind": "module",
                "url": url,
                "homepage": homepage,
                "path": rel,
                "tags": ["代理检测", "上游原链", author],
                "source": f"local:{author}",
                "upstream": True,
            }
        )
    return items


def merge_general_snippets(entries: list[dict]) -> str:
    """Build a small supplement module from upstream General skip-proxy / always-real-ip lines."""
    skip: list[str] = []
    realip: list[str] = []
    rules: list[str] = []
    for entry in entries:
        url = entry.get("url") or ""
        if not url or entry.get("kind") != "module":
            continue
        try:
            text = fetch_text(url)
        except Exception as exc:
            print(f"skip merge fetch {url}: {exc}")
            continue
        section = None
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                section = stripped[1:-1].strip().lower()
                continue
            if not stripped or stripped.startswith("#"):
                continue
            if section == "general":
                low = stripped.lower()
                if low.startswith("skip-proxy"):
                    skip.append(stripped)
                elif low.startswith("always-real-ip"):
                    realip.append(stripped)
            elif section == "rule":
                rules.append(stripped)

    def uniq(lines: list[str]) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for line in lines:
            key = re.sub(r"\s+", "", line.lower())
            if key in seen:
                continue
            seen.add(key)
            out.append(line)
        return out

    skip_u, real_u, rules_u = uniq(skip), uniq(realip), uniq(rules)
    if not (skip_u or real_u or rules_u):
        return ""

    lines = [
        "#!name=代理检测补充（上游扫描）",
        "#!desc=由 discover-proxy-detect.py 从上游 skip-proxy / always-real-ip 合并；订阅请优先用上游原链",
        "#!category=代理检测",
        "",
    ]
    if skip_u or real_u:
        lines.append("[General]")
        lines.extend(skip_u)
        lines.extend(real_u)
        lines.append("")
    if rules_u:
        lines.append("[Rule]")
        lines.extend(rules_u)
        lines.append("")
    return "\n".join(lines)


def dedupe_entries(entries: list[dict]) -> list[dict]:
    by_url: dict[str, dict] = {}
    no_url: list[dict] = []
    for e in entries:
        url = (e.get("url") or "").strip()
        if not url:
            no_url.append(e)
            continue
        prev = by_url.get(url)
        if not prev or (e.get("source") == "seed"):
            by_url[url] = e
    # stable: seeds first-ish by sorting source
    out = sorted(by_url.values(), key=lambda x: (0 if x.get("source") == "seed" else 1, x.get("id", "")))
    out.extend(no_url)
    return out


def write_sources_snapshot(cfg: dict) -> None:
    payload = {
        "note": cfg.get("updated_note", ""),
        "sources": cfg.get("sources") or [],
        "proxy_detect_watch": {
            "keywords": (cfg.get("proxy_detect") or {}).get("keywords") or [],
            "seeds": (cfg.get("proxy_detect") or {}).get("seeds") or [],
            "watch_repos": (cfg.get("proxy_detect") or {}).get("watch_repos") or [],
        },
    }
    OUT_SOURCES.parent.mkdir(parents=True, exist_ok=True)
    OUT_SOURCES.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT_SOURCES.relative_to(ROOT)}")


def main() -> None:
    cfg = load_cfg()
    pd = cfg.get("proxy_detect") or {}
    keywords = keyword_re(list(pd.get("keywords") or []))

    entries: list[dict] = [entry_from_seed(s) for s in pd.get("seeds") or []]
    entries.extend(discover_from_repos(pd, keywords))
    if pd.get("scan_local_upstream", True):
        entries.extend(discover_from_local(keywords))
    entries = dedupe_entries(entries)

    # enrich seed headers
    for e in entries:
        if e.get("source") == "seed" and e.get("url"):
            try:
                header = parse_surge_header(fetch_text(e["url"])[:4000])
                if header.get("name"):
                    e["name"] = header["name"]
                if header.get("desc"):
                    e["desc"] = header["desc"]
            except Exception:
                pass

    OUT_INDEX.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_by": "scripts/discover-proxy-detect.py",
        "count": len(entries),
        "items": entries,
    }
    OUT_INDEX.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT_INDEX.relative_to(ROOT)} ({len(entries)} items)")

    merged = merge_general_snippets([e for e in entries if e.get("upstream") and e.get("url")])
    if merged:
        OUT_MODULE.write_text(merged, encoding="utf-8")
        print(f"wrote {OUT_MODULE.relative_to(ROOT)} ({len(merged.splitlines())} lines)")
    else:
        print("skip proxy-detect-extra: nothing to merge")

    write_sources_snapshot(cfg)


if __name__ == "__main__":
    main()
