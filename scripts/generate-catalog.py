#!/usr/bin/env python3
"""Build site/catalog.json and site/disclaimer.html — main-branch module hub."""

from __future__ import annotations

import html
import json
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
from external_script_utils import extract_script_urls, is_local_url, should_skip_mirror
from paths import GITHUB_RAW_MAIN, GITHUB_RAW_MAIN_BOXJS, MODULES, ROOT, ROUTING, SIGNIN_SCRIPTS, WIDGETS

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

PUBLISH_MANIFEST = ROOT / "publish" / "manifest.yaml"
CATALOG_META = Path(__file__).with_name("catalog-meta.yaml")
SITE_DIR = ROOT / "site"
CATALOG_OUT = SITE_DIR / "catalog.json"
DISCLAIMER_OUT = SITE_DIR / "disclaimer.html"
DISCLAIMER_MD = ROOT / "DISCLAIMER.md"
WIDGET_MANIFEST = WIDGETS / "IBL3ND" / "manifest.yaml"
SCRIPTS_MANIFEST = Path(__file__).with_name("manifest.yaml")
BOXJS_PATH = MODULES / "egern.boxjs.json"
EGERN_YAML = ROOT / "Egern.yaml"

GITHUB_PAGES = "https://oo226.github.io/egern-config"
UPSTREAM_CHECK_LIMIT = 80

IRINGO_HINTS = {
    "iringo-mitm": "与地图 / 天气 / 定位模块配套；启用 iRingo 时建议同时开启。",
    "iringo-maps": "⚠️ 请先添加并启用「 iRingo MITM 域名」模块，否则无法解密 Apple 地图 API。",
    "iringo-weather": "⚠️ 请先添加并启用「 iRingo MITM 域名」模块，否则 weatherkit 无法解密。",
    "iringo-location": "⚠️ 请先添加并启用「 iRingo MITM 域名」模块，否则定位增强不生效。",
    "iringo-others": "TestFlight / TV / News 等；若涉及 Apple API，请同时开 MITM 模块。",
}


def load_yaml(path: Path) -> dict:
    if not yaml:
        raise SystemExit("PyYAML required: pip install pyyaml")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def raw_url(rel: str, *, boxjs: bool = False) -> str:
    base = GITHUB_RAW_MAIN_BOXJS if boxjs else GITHUB_RAW_MAIN
    return f"{base}/{rel.lstrip('/')}"


def module_add_url(url: str) -> str:
    return f"egern:///modules/new?url={quote(url, safe='')}"


def parse_surge_header(text: str) -> dict[str, str]:
    meta: dict[str, str] = {}
    for line in text.splitlines()[:40]:
        m = re.match(r"^#!(\w+)\s*=\s*(.+)$", line.strip())
        if m:
            meta[m.group(1).lower()] = m.group(2).strip()
    return meta


def parse_egern_yaml_module(path: Path) -> dict[str, str]:
    data = load_yaml(path)
    return {
        "name": str(data.get("name") or path.stem),
        "desc": str(data.get("description") or ""),
        "icon": str(data.get("icon") or ""),
        "homepage": str(data.get("homepage") or ""),
    }


def load_egern_module_defaults() -> dict[str, bool]:
    """Map Modules/filename -> enabled from Egern.yaml."""
    if not EGERN_YAML.is_file():
        return {}
    data = load_yaml(EGERN_YAML)
    out: dict[str, bool] = {}
    for mod in data.get("modules") or []:
        url = str(mod.get("url") or "")
        enabled = bool(mod.get("enabled", False))
        if "/Modules/" in url:
            name = url.rsplit("/Modules/", 1)[-1].split("?")[0]
            out[name] = enabled
    return out


def usage_tier(default_enabled: bool | None, kind: str, category: str) -> str:
    if default_enabled is True:
        return "daily"
    if default_enabled is False:
        return "optional"
    if kind == "config":
        return "daily"
    if category == "scripts":
        return "optional"
    if kind == "boxjs" and category == "boxjs":
        return "optional"
    return "neutral"


def boxjs_group(app_id: str, name: str) -> str:
    aid = (app_id or "").lower()
    nm = (name or "").lower()
    if aid.startswith("iringo") or "iringo" in nm:
        return "iRingo"
    if any(k in aid + nm for k in ("sign", "checkin", "签到", "cookie", "capture", "抓参")):
        return "签到 / 抓参"
    if any(k in aid + nm for k in ("player", "播放", "pear", "video", "insav", "porntube")):
        return "播放器"
    if "cookie" in aid or "cookie" in nm:
        return "Cookie"
    if any(k in aid + nm for k in ("yuheng", "酷我", "豆瓣", "茅台")):
        return "Yuheng"
    if "微信" in name or "wechat" in aid:
        return "工具"
    return "其他"


def build_scripting_yaml(entry: dict, url: str) -> str:
    name = entry.get("name") or Path(entry.get("file", "script")).stem
    cron = entry.get("cron") or "0 8 * * *"
    script_type = entry.get("type") or "schedule"
    lines = ["# 粘贴到 Egern.yaml 的 scriptings 段", "scriptings:"]
    if script_type == "http_request" and entry.get("match"):
        lines.extend(
            [
                f"  - name: {name}",
                "    type: http_request",
                f"    match: {entry['match']}",
                f"    script: {url}",
                "    enabled: true",
            ]
        )
    else:
        if not entry.get("cron"):
            lines.append(f"  # {name} — 请自行填写 cron 或改用 BoxJS 配置")
        lines.extend(
            [
                f"  - name: {name}",
                "    type: schedule",
                f"    cron: \"{cron}\"",
                f"    script: {url}",
                "    enabled: true",
            ]
        )
    return "\n".join(lines) + "\n"


def module_item(filename: str, meta_cfg: dict, egern_defaults: dict[str, bool]) -> dict:
    path = MODULES / filename
    if not path.is_file():
        return {}
    override = (meta_cfg.get("modules") or {}).get(filename) or {}
    suffix = path.suffix.lower()
    if suffix in {".module", ".sgmodule"}:
        header = parse_surge_header(path.read_text(encoding="utf-8", errors="replace"))
        name = header.get("name") or override.get("name") or filename
        desc = header.get("desc", "").replace("\\n", " ")
        icon = header.get("icon") or override.get("icon", "")
        homepage = header.get("homepage") or override.get("homepage", "")
        tags = [t.strip() for t in header.get("tag", "").split(",") if t.strip()]
    else:
        parsed = parse_egern_yaml_module(path)
        name = parsed["name"]
        desc = parsed["desc"]
        icon = parsed["icon"]
        homepage = parsed.get("homepage", "")
        tags = list(override.get("tags") or [])

    tags = list(dict.fromkeys([*(override.get("tags") or []), *tags]))
    url = raw_url(f"Modules/{filename}")
    default_enabled = egern_defaults.get(filename, override.get("default_enabled"))
    item_id = path.stem
    return {
        "id": item_id,
        "kind": "module",
        "category": "modules",
        "group": override.get("group", "其他"),
        "name": name,
        "desc": desc,
        "icon": icon,
        "homepage": homepage,
        "path": f"Modules/{filename}",
        "url": url,
        "add_url": module_add_url(url),
        "default_enabled": default_enabled,
        "usage_tier": usage_tier(default_enabled, "module", "modules"),
        "requires": override.get("requires") or [],
        "hint": IRINGO_HINTS.get(item_id) or override.get("hint", ""),
        "tags": tags,
    }


def config_items(meta_cfg: dict) -> list[dict]:
    items: list[dict] = []
    for entry in meta_cfg.get("config") or []:
        path = entry["path"]
        url = raw_url(path)
        items.append(
            {
                "id": entry["id"],
                "kind": "config",
                "category": "config",
                "group": "主配置",
                "name": entry["name"],
                "desc": entry.get("desc", ""),
                "icon": entry.get("icon", ""),
                "path": path,
                "url": url,
                "add_url": url,
                "usage_tier": "daily",
                "tags": ["Egern", "订阅", "默认开启"],
            }
        )
    return items


def routing_items(meta_cfg: dict) -> list[dict]:
    routing_meta = meta_cfg.get("routing") or {}
    items: list[dict] = []
    for path in sorted(ROUTING.rglob("*.yaml")):
        if "_upstream" in path.parts:
            continue
        rel = path.relative_to(ROOT).as_posix()
        info = routing_meta.get(rel) or {}
        name = info.get("name") or path.stem
        desc = info.get("desc", "")
        if not desc:
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[:8]:
                if line.startswith("# ") and "AUTO-GENERATED" not in line:
                    desc = line[2:].strip()
                    break
        sub = "foreign" if "Foreign" in rel else "domestic"
        url = raw_url(rel)
        items.append(
            {
                "id": rel.replace("/", "-").replace(".yaml", ""),
                "kind": "rule",
                "category": "routing",
                "group": "国外分流" if sub == "foreign" else "国内/通用",
                "name": name,
                "desc": desc,
                "icon": "",
                "path": rel,
                "url": url,
                "add_url": url,
                "usage_tier": "neutral",
                "tags": ["分流", "rule_set"],
            }
        )
    return items


def boxjs_items(meta_cfg: dict) -> list[dict]:
    items: list[dict] = []
    boxjs_meta = meta_cfg.get("boxjs") or {}
    if not published_includes("egern.boxjs.json") or not BOXJS_PATH.is_file():
        return items

    sub_meta = boxjs_meta.get("egern.boxjs.json") or {}
    sub_url = raw_url("Modules/egern.boxjs.json", boxjs=True)
    items.append(
        {
            "id": "egern-boxjs",
            "kind": "boxjs",
            "category": "boxjs",
            "group": "订阅",
            "name": sub_meta.get("name", "统一 BoxJS 订阅"),
            "desc": sub_meta.get("desc", ""),
            "icon": sub_meta.get("icon", ""),
            "path": "Modules/egern.boxjs.json",
            "url": sub_url,
            "add_url": sub_url,
            "usage_tier": "daily",
            "hint": "BoxJS 应用内添加此订阅链接；后端地址用 http://boxjs.com",
            "tags": ["BoxJS", "配置", "默认开启"],
        }
    )

    data = json.loads(BOXJS_PATH.read_text(encoding="utf-8"))
    for app in data.get("apps") or []:
        app_id = app.get("id") or app.get("name")
        if not app_id:
            continue
        app_name = app.get("name") or app_id
        icons = app.get("icons") or []
        group = boxjs_group(str(app_id), str(app_name))
        items.append(
            {
                "id": f"boxjs-{app_id}",
                "kind": "boxjs-app",
                "category": "boxjs",
                "group": group,
                "name": app_name,
                "desc": " ".join(app.get("descs") or [])[:200]
                if isinstance(app.get("descs"), list)
                else str(app.get("desc") or "")[:200],
                "icon": icons[0] if icons else "",
                "path": f"Modules/egern.boxjs.json#{app_id}",
                "url": sub_url,
                "add_url": f"http://boxjs.com/#/app/{app_id}",
                "usage_tier": "optional",
                "tags": ["BoxJS", group],
            }
        )
    return items


def script_items() -> list[dict]:
    if not SCRIPTS_MANIFEST.is_file():
        return []
    data = load_yaml(SCRIPTS_MANIFEST)
    items: list[dict] = []
    for entry in data.get("scripts") or []:
        filename = entry.get("file")
        if not filename:
            continue
        if not (SIGNIN_SCRIPTS / filename).is_file():
            continue
        note = entry.get("note") or ""
        if isinstance(note, list):
            note = note[0] if note else ""
        url = raw_url(f"Scripts/{filename}", boxjs=True)
        cron = entry.get("cron", "")
        items.append(
            {
                "id": f"script-{Path(filename).stem}",
                "kind": "script",
                "category": "scripts",
                "group": "签到 / 抓参",
                "name": entry.get("name") or Path(filename).stem,
                "desc": str(note),
                "icon": "",
                "path": f"Scripts/{filename}",
                "url": url,
                "add_url": url,
                "cron": cron,
                "usage_tier": "optional",
                "scripting_yaml": build_scripting_yaml(entry, url),
                "hint": "先开 Cookie 合集抓参（如需），再粘贴下方 YAML 到 Egern scriptings 段" if "签到" in str(note) or cron else "",
                "tags": ["脚本", "签到" if "签到" in str(note) or cron else "工具", "按需开启"],
            }
        )
    return items


def widget_items() -> list[dict]:
    if not WIDGET_MANIFEST.is_file():
        return []
    data = load_yaml(WIDGET_MANIFEST)
    items: list[dict] = []
    for w in data.get("widgets") or []:
        name = w.get("name") or ""
        url = w.get("local_url") or raw_url(w.get("file", ""))
        display = Path(name).stem.replace("_", " ")
        items.append(
            {
                "id": f"widget-{Path(name).stem.lower()}",
                "kind": "widget",
                "category": "widgets",
                "group": "IBL3ND",
                "name": display,
                "desc": "小组件脚本 — 仅写入 Egern widgets 段，勿加 scriptings。",
                "icon": "",
                "path": w.get("file", ""),
                "url": url,
                "add_url": url,
                "usage_tier": "optional",
                "hint": "Oil 等常用：写入 Egern.yaml → widgets，不要写进 scriptings",
                "tags": ["小组件", "Widget", "按需开启"],
            }
        )
    return items


def external_module_items(meta_cfg: dict) -> list[dict]:
    items: list[dict] = []
    for entry in meta_cfg.get("external_modules") or []:
        url = entry["url"]
        default_enabled = entry.get("default_enabled")
        items.append(
            {
                "id": entry["id"],
                "kind": "module",
                "category": "modules",
                "group": entry.get("group", "外部"),
                "name": entry["name"],
                "desc": entry.get("desc", ""),
                "icon": entry.get("icon", ""),
                "path": url,
                "url": url,
                "add_url": module_add_url(url),
                "default_enabled": default_enabled,
                "usage_tier": usage_tier(default_enabled, "module", "modules"),
                "tags": entry.get("tags") or ["外部"],
            }
        )
    return items


def published_module_files() -> list[str]:
    data = load_yaml(PUBLISH_MANIFEST)
    for spec in data.get("directories") or []:
        if spec.get("path") == "Modules":
            return [
                name
                for name in spec.get("include_only") or []
                if name not in {"README.md", "egern.boxjs.json", "yu9191-player.boxjs.json"}
                and not name.endswith(".json")
            ]
    return []


def published_includes(name: str) -> bool:
    data = load_yaml(PUBLISH_MANIFEST)
    for spec in data.get("directories") or []:
        if spec.get("path") == "Modules":
            return name in (spec.get("include_only") or [])
    return False


    return False


def git_changelog(limit: int = 8) -> list[dict]:
    try:
        proc = subprocess.run(
            ["git", "log", f"-{limit}", "--pretty=format:%h|%s|%cs", "origin/main"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if proc.returncode != 0:
            proc = subprocess.run(
                ["git", "log", f"-{limit}", "--pretty=format:%h|%s|%cs", "main"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=15,
            )
        entries: list[dict] = []
        for line in (proc.stdout or "").splitlines():
            parts = line.split("|", 2)
            if len(parts) == 3:
                entries.append({"hash": parts[0], "subject": parts[1], "date": parts[2]})
        return entries
    except Exception as exc:
        print(f"skip changelog: {exc}")
        return []


def check_url_ok(url: str) -> bool:
    if not url.startswith("https://raw.githubusercontent.com/oo226/egern-config"):
        return True
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "egern-catalog-check/1.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            return 200 <= resp.status < 400
    except Exception:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "egern-catalog-check/1.0"})
            with urllib.request.urlopen(req, timeout=12) as resp:
                return 200 <= resp.status < 400
        except Exception:
            return False


def apply_health_checks(items: list[dict]) -> None:
    checked = 0
    for item in items:
        if item.get("kind") not in {"module", "config", "rule", "boxjs", "script", "widget"}:
            continue
        url = item.get("url") or ""
        if not url.startswith("https://raw.githubusercontent.com/oo226/egern-config"):
            continue
        item["health"] = "ok" if check_url_ok(url) else "fail"
        checked += 1
    print(f"health-checked {checked} local raw URLs")


def build_modules_yaml_bundle(item_ids: list[str], items_by_id: dict[str, dict]) -> str:
    lines = ["# 粘贴到 Egern.yaml 的 modules 段", "modules:"]
    for iid in item_ids:
        item = items_by_id.get(iid)
        if not item:
            continue
        lines.append(f"  - name: \"{item['name']}\"")
        lines.append(f"    url: {item['url']}")
        if item.get("kind") == "module" and not item["id"].endswith("-mitm"):
            lines.append("    update_interval: 86400")
        lines.append("    enabled: false")
    return "\n".join(lines) + "\n"


def check_upstream_script_urls() -> dict:
    """HEAD-check external script-path URLs in published modules."""
    urls: set[str] = set()
    for name in published_module_files():
        path = MODULES / name
        if path.is_file():
            urls.update(extract_script_urls(path.read_text(encoding="utf-8", errors="replace")))
    for name in ("adblock-collection.module", "unlock-collection.module", "cookie-collection.module"):
        path = MODULES / name
        if path.is_file():
            urls.update(extract_script_urls(path.read_text(encoding="utf-8", errors="replace")))

    external = sorted(u for u in urls if u.startswith("http") and not is_local_url(u) and not should_skip_mirror(u))
    checked = external[:UPSTREAM_CHECK_LIMIT]
    broken: list[dict] = []
    ok = 0
    for url in checked:
        if check_url_ok(url):
            ok += 1
        else:
            broken.append({"url": url})
    print(f"upstream scripts: {len(external)} unique, checked {len(checked)}, fail {len(broken)}")
    return {
        "total_unique": len(external),
        "checked": len(checked),
        "ok": ok,
        "fail": len(broken),
        "broken": broken[:15],
        "truncated": len(external) > UPSTREAM_CHECK_LIMIT,
    }


def build_featured_boxjs(meta_cfg: dict, items_by_id: dict[str, dict]) -> list[dict]:
    out: list[dict] = []
    for app_id in meta_cfg.get("featured_boxjs") or []:
        item = items_by_id.get(f"boxjs-{app_id}")
        if item:
            out.append(
                {
                    "id": app_id,
                    "name": item["name"],
                    "group": item.get("group", ""),
                    "add_url": item.get("add_url"),
                }
            )
    return out


def attach_share_urls(items: list[dict]) -> None:
    for item in items:
        item["share_url"] = f"{GITHUB_PAGES}/#id={item['id']}"


def build_quick_start(meta_cfg: dict, items_by_id: dict[str, dict]) -> list[dict]:
    out: list[dict] = []
    for iid in meta_cfg.get("quick_start") or []:
        item = items_by_id.get(iid)
        if item:
            out.append(
                {
                    "id": iid,
                    "name": item["name"],
                    "desc": item.get("desc", "")[:80],
                    "add_url": item.get("add_url"),
                    "url": item.get("url"),
                    "kind": item.get("kind"),
                    "qr_url": item.get("url") if item.get("kind") != "module" else item.get("add_url"),
                }
            )
    return out


def git_sync_digest() -> dict:
    """Summarize latest sync commit file changes."""
    try:
        proc = subprocess.run(
            ["git", "log", "-1", "--pretty=format:%h|%s|%cs", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=15,
        )
        head = proc.stdout.strip().split("|", 2) if proc.returncode == 0 else []
        diff = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=15,
        )
        files = [f for f in (diff.stdout or "").splitlines() if f.strip()]
    except Exception as exc:
        return {"summary": [], "commit": None, "error": str(exc)}

    buckets: dict[str, list[str]] = {}
    for f in files:
        top = f.split("/", 1)[0]
        buckets.setdefault(top, []).append(f)

    summary: list[str] = []
    labels = {
        "Routing": "分流规则",
        "Modules": "模块",
        "Scripts": "脚本",
        "site": "模块站",
        "Egern.yaml": "主配置",
    }
    for key, label in labels.items():
        if key in buckets:
            summary.append(f"{label} 更新 {len(buckets[key])} 个文件")
        elif any(f.startswith(key + "/") or f == key for f in files):
            summary.append(f"{label} 有变更")

    china = ROOT / "Routing" / "China-Direct.yaml"
    if china.is_file():
        for line in china.read_text(encoding="utf-8", errors="replace").splitlines()[:25]:
            if line.startswith("# Total unique entries:"):
                summary.append(f"国内直连 {line.split(':', 1)[1].strip()} 条")
                break

    if not summary and files:
        summary.append(f"共 {len(files)} 个文件变更")

    commit = None
    if len(head) == 3:
        commit = {"hash": head[0], "subject": head[1], "date": head[2]}

    return {"commit": commit, "summary": summary[:8], "files_changed": len(files)}


def build_signin_bundle(meta_cfg: dict, items_by_id: dict[str, dict]) -> dict | None:
    cfg = meta_cfg.get("signin_bundle")
    if not cfg:
        return None
    blocks: list[str] = ["# 粘贴到 Egern.yaml 的 scriptings 段", "scriptings:"]
    names: list[str] = []
    for sid in cfg.get("script_ids") or []:
        item = items_by_id.get(sid)
        if not item or not item.get("scripting_yaml"):
            continue
        names.append(item["name"])
        for line in item["scripting_yaml"].splitlines():
            if line.startswith("#") or line == "scriptings:":
                continue
            blocks.append(line)
    if len(blocks) <= 2:
        return None
    return {
        "id": "signin-bundle",
        "name": cfg.get("name", "签到脚本包"),
        "desc": cfg.get("desc", ""),
        "scripts": names,
        "scripting_yaml": "\n".join(blocks) + "\n",
    }


def build_onboarding(meta_cfg: dict, items_by_id: dict[str, dict]) -> list[dict]:
    out: list[dict] = []
    for i, step in enumerate(meta_cfg.get("onboarding") or [], start=1):
        ref = step.get("ref")
        item = items_by_id.get(ref) if ref else None
        out.append(
            {
                "step": i,
                "title": step.get("title", ""),
                "desc": step.get("desc", ""),
                "url": item.get("url") if item else "",
                "add_url": item.get("add_url") if item else "",
            }
        )
    return out


def build_bundles(meta_cfg: dict, items_by_id: dict[str, dict]) -> list[dict]:
    bundles: list[dict] = []
    for b in meta_cfg.get("bundles") or []:
        ids = b.get("item_ids") or []
        add_urls = [items_by_id[i]["add_url"] for i in ids if i in items_by_id and items_by_id[i].get("add_url")]
        bundles.append(
            {
                "id": b["id"],
                "name": b["name"],
                "desc": b.get("desc", ""),
                "item_ids": ids,
                "add_urls": add_urls,
                "modules_yaml": build_modules_yaml_bundle(ids, items_by_id),
            }
        )
    return bundles


def mark_featured(meta_cfg: dict, items: list[dict]) -> None:
    featured = set(meta_cfg.get("featured_widgets") or [])
    for item in items:
        if item["id"] in featured:
            item["featured"] = True


def build_catalog() -> dict:
    meta_cfg = load_yaml(CATALOG_META) if CATALOG_META.is_file() else {}
    egern_defaults = load_egern_module_defaults()
    items: list[dict] = []
    items.extend(config_items(meta_cfg))
    for filename in published_module_files():
        item = module_item(filename, meta_cfg, egern_defaults)
        if item:
            items.append(item)
    items.extend(external_module_items(meta_cfg))
    items.extend(routing_items(meta_cfg))
    items.extend(boxjs_items(meta_cfg))
    items.extend(script_items())
    items.extend(widget_items())
    mark_featured(meta_cfg, items)
    items_by_id = {i["id"]: i for i in items}
    attach_share_urls(items)
    apply_health_checks(items)
    upstream_health = check_upstream_script_urls()
    local_broken = [i["id"] for i in items if i.get("health") == "fail"]
    local_health = {"checked": sum(1 for i in items if i.get("health")), "fail": len(local_broken), "broken_ids": local_broken[:20]}

    categories = [
        {"id": "config", "name": "主配置", "icon": "⚙️"},
        {"id": "modules", "name": "模块", "icon": "🧩"},
        {"id": "routing", "name": "分流规则", "icon": "🔀"},
        {"id": "boxjs", "name": "BoxJS", "icon": "📦"},
        {"id": "scripts", "name": "签到脚本", "icon": "📅"},
        {"id": "widgets", "name": "小组件", "icon": "📱"},
    ]
    counts = {c["id"]: sum(1 for i in items if i.get("category") == c["id"]) for c in categories}
    daily_count = sum(1 for i in items if i.get("usage_tier") == "daily")
    optional_count = sum(1 for i in items if i.get("usage_tier") == "optional")

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "branch": "main",
        "repo": "oo226/egern-config",
        "raw_base": GITHUB_RAW_MAIN,
        "pages_url": GITHUB_PAGES,
        "presets": [
            {"id": "daily", "name": "默认开启", "icon": "✅", "usage_tier": "daily", "count": daily_count},
            {"id": "optional", "name": "按需开启", "icon": "🔧", "usage_tier": "optional", "count": optional_count},
        ],
        "quick_start": build_quick_start(meta_cfg, items_by_id),
        "featured_boxjs": build_featured_boxjs(meta_cfg, items_by_id),
        "bundles": build_bundles(meta_cfg, items_by_id),
        "signin_bundle": build_signin_bundle(meta_cfg, items_by_id),
        "onboarding": build_onboarding(meta_cfg, items_by_id),
        "sync_digest": git_sync_digest(),
        "changelog": git_changelog(),
        "local_health": local_health,
        "upstream_health": upstream_health,
        "categories": [{**c, "count": counts[c["id"]]} for c in categories],
        "items": items,
        "total": len(items),
    }


def md_to_html_body(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    in_ul = False
    in_table = False

    def close_ul() -> None:
        nonlocal in_ul
        if in_ul:
            out.append("</ul>")
            in_ul = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            close_ul()
            if in_table:
                out.append("</tbody></table>")
                in_table = False
            continue
        if stripped.startswith("# "):
            close_ul()
            out.append(f"<h2>{html.escape(stripped[2:])}</h2>")
        elif stripped.startswith("## "):
            close_ul()
            out.append(f"<h2>{html.escape(stripped[3:])}</h2>")
        elif stripped.startswith("### "):
            close_ul()
            out.append(f"<h3>{html.escape(stripped[4:])}</h3>")
        elif stripped.startswith("- "):
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            content = stripped[2:]
            content = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', content)
            content = re.sub(r"`([^`]+)`", r"<code>\1</code>", content)
            out.append(f"<li>{content}</li>")
        elif stripped.startswith("|") and "|" in stripped[1:]:
            close_ul()
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if not in_table:
                out.append("<table><thead><tr>" + "".join(f"<th>{html.escape(c)}</th>" for c in cells) + "</tr></thead><tbody>")
                in_table = True
            else:
                out.append("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in cells) + "</tr>")
        elif stripped.startswith("*") and stripped.endswith("*"):
            close_ul()
            out.append(f"<p><em>{html.escape(stripped.strip('*'))}</em></p>")
        else:
            close_ul()
            esc = html.escape(stripped)
            esc = re.sub(r"`([^`]+)`", r"<code>\1</code>", esc)
            out.append(f"<p>{esc}</p>")

    close_ul()
    if in_table:
        out.append("</tbody></table>")
    return "\n".join(out)


def generate_disclaimer_html() -> None:
    body = md_to_html_body(DISCLAIMER_MD.read_text(encoding="utf-8"))
    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>免责声明 — egern-config</title>
  <link rel="stylesheet" href="styles.css">
  <link rel="manifest" href="manifest.webmanifest">
</head>
<body>
  <header class="hero">
    <div class="hero-inner">
      <a class="back-link" href="index.html">← 返回模块中心</a>
      <h1>免责声明</h1>
      <p>个人自用镜像整理 · 上游版权归原作者</p>
    </div>
  </header>
  <main class="page-body">
    {body}
  </main>
  <footer class="page-footer">
    <p>完整 Markdown：<a href="https://github.com/oo226/egern-config/blob/main/DISCLAIMER.md">DISCLAIMER.md</a></p>
  </footer>
</body>
</html>
"""
    DISCLAIMER_OUT.write_text(page, encoding="utf-8")
    print(f"wrote {DISCLAIMER_OUT.relative_to(ROOT)}")


def main() -> None:
    catalog = build_catalog()
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    CATALOG_OUT.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {CATALOG_OUT.relative_to(ROOT)}: {catalog['total']} items")
    generate_disclaimer_html()


if __name__ == "__main__":
    main()
