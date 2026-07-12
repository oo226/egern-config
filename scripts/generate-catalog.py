#!/usr/bin/env python3
"""Build site/catalog.json — main-branch module hub index."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import GITHUB_RAW_MAIN, GITHUB_RAW_MAIN_BOXJS, MODULES, ROOT, ROUTING, SIGNIN_SCRIPTS, WIDGETS

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

PUBLISH_MANIFEST = ROOT / "publish" / "manifest.yaml"
CATALOG_META = Path(__file__).with_name("catalog-meta.yaml")
SITE_DIR = ROOT / "site"
CATALOG_OUT = SITE_DIR / "catalog.json"
WIDGET_MANIFEST = WIDGETS / "IBL3ND" / "manifest.yaml"
SCRIPTS_MANIFEST = Path(__file__).with_name("manifest.yaml")
BOXJS_PATH = MODULES / "egern.boxjs.json"
EGERN_YAML = ROOT / "Egern.yaml"

GITHUB_PAGES = "https://oo226.github.io/egern-config"


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


def module_item(filename: str, meta_cfg: dict) -> dict:
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
    return {
        "id": path.stem,
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
        "default_enabled": override.get("default_enabled"),
        "requires": override.get("requires") or [],
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
                "tags": ["Egern", "订阅"],
            }
        )
    return items


def routing_items(meta_cfg: dict) -> list[dict]:
    routing_meta = meta_cfg.get("routing") or {}
    items: list[dict] = []
    paths = sorted(ROUTING.rglob("*.yaml"))
    for path in paths:
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
                "tags": ["分流", "rule_set"],
            }
        )
    return items


def boxjs_items(meta_cfg: dict) -> list[dict]:
    items: list[dict] = []
    boxjs_meta = meta_cfg.get("boxjs") or {}
    publish = load_yaml(PUBLISH_MANIFEST)
    module_files = (
        (publish.get("directories") or [{}])[1].get("include_only") or []
        if len(publish.get("directories") or []) > 1
        else []
    )
    if "egern.boxjs.json" not in module_files or not BOXJS_PATH.is_file():
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
            "tags": ["BoxJS", "配置"],
        }
    )

    data = json.loads(BOXJS_PATH.read_text(encoding="utf-8"))
    for app in data.get("apps") or []:
        app_id = app.get("id") or app.get("name")
        if not app_id:
            continue
        icons = app.get("icons") or []
        icon = icons[0] if icons else ""
        items.append(
            {
                "id": f"boxjs-{app_id}",
                "kind": "boxjs-app",
                "category": "boxjs",
                "group": "应用",
                "name": app.get("name") or app_id,
                "desc": " ".join(app.get("descs") or app.get("desc") or [])[:200]
                if isinstance(app.get("descs"), list)
                else str(app.get("desc") or "")[:200],
                "icon": icon,
                "path": f"Modules/egern.boxjs.json#{app_id}",
                "url": sub_url,
                "add_url": f"http://boxjs.com/#/app/{app_id}",
                "tags": ["BoxJS"],
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
        path = SIGNIN_SCRIPTS / filename
        if not path.is_file():
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
                "tags": ["脚本", "签到" if "签到" in str(note) or cron else "工具"],
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
                "tags": ["小组件", "Widget"],
            }
        )
    return items


def external_module_items(meta_cfg: dict) -> list[dict]:
    items: list[dict] = []
    for entry in meta_cfg.get("external_modules") or []:
        url = entry["url"]
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
                "default_enabled": entry.get("default_enabled"),
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


def build_catalog() -> dict:
    meta_cfg = load_yaml(CATALOG_META) if CATALOG_META.is_file() else {}
    items: list[dict] = []
    items.extend(config_items(meta_cfg))
    for filename in published_module_files():
        item = module_item(filename, meta_cfg)
        if item:
            items.append(item)
    items.extend(external_module_items(meta_cfg))
    items.extend(routing_items(meta_cfg))
    items.extend(boxjs_items(meta_cfg))
    items.extend(script_items())
    items.extend(widget_items())

    categories = [
        {"id": "config", "name": "主配置", "icon": "⚙️"},
        {"id": "modules", "name": "模块", "icon": "🧩"},
        {"id": "routing", "name": "分流规则", "icon": "🔀"},
        {"id": "boxjs", "name": "BoxJS", "icon": "📦"},
        {"id": "scripts", "name": "签到脚本", "icon": "📅"},
        {"id": "widgets", "name": "小组件", "icon": "📱"},
    ]
    counts = {c["id"]: sum(1 for i in items if i.get("category") == c["id"]) for c in categories}

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "branch": "main",
        "repo": "oo226/egern-config",
        "raw_base": GITHUB_RAW_MAIN,
        "pages_url": GITHUB_PAGES,
        "categories": [{**c, "count": counts[c["id"]]} for c in categories],
        "items": items,
        "total": len(items),
    }


def main() -> None:
    catalog = build_catalog()
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    CATALOG_OUT.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {CATALOG_OUT.relative_to(ROOT)}: {catalog['total']} items")


if __name__ == "__main__":
    main()
