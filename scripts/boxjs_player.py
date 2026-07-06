"""Helpers for Yu9191 player scripts that read BoxJS instead of module arguments."""

from __future__ import annotations

import json
import re
from pathlib import Path

from paths import GITHUB_RAW_MAIN, GITHUB_RAW_MAIN_BOXJS, MODULES

YU9191_BOXJS_SUBSCRIPTION = f"{GITHUB_RAW_MAIN_BOXJS}/Modules/yu9191-player.boxjs.json"
YU9191_BOXJS_UPSTREAM = (
    "https://raw.githubusercontent.com/Yu9191/Rewrite/refs/heads/main/pear.boxjs.json"
)

# Script path fragments whose module `argument=` overrides BoxJS settings.
BOXJS_PLAYER_SCRIPT_MARKERS = (
    "/qiyoushe/dist/qiyoushequ.js",
    "/qiyoushe/qiyoushequ.js",
    "/rewrite/pear.js",
    "/insav-tv/dist/insav.js",
    "/rewrite/insav.tv.js",
    "/porntube/dist/porntube.js",
    "/xjh51/dist/xjh51.js",
)

_ARGUMENT_RE = re.compile(r",\s*argument=[^\n]*", re.IGNORECASE)
_HEADER_ARGUMENT_RE = re.compile(r"^#!arguments(?:-desc)?=.*\n", re.MULTILINE)

_SCRIPT_URL_REWRITES = (
    ("https://raw.githubusercontent.com/Yu9191/Rewrite/refs/heads/main/", f"{GITHUB_RAW_MAIN}/Scripts/yu9191/rewrite/"),
    ("https://raw.githubusercontent.com/Yu9191/Rewrite/main/", f"{GITHUB_RAW_MAIN}/Scripts/yu9191/rewrite/"),
)


def script_line_uses_boxjs_player(line: str) -> bool:
    if "script-path=" not in line:
        return False
    return any(marker in line for marker in BOXJS_PLAYER_SCRIPT_MARKERS)


def strip_boxjs_module_arguments(text: str) -> str:
    """Remove module argument overrides so BoxJS persistent keys take effect."""
    lines: list[str] = []
    for line in text.splitlines():
        if script_line_uses_boxjs_player(line):
            line = _ARGUMENT_RE.sub("", line.rstrip())
        lines.append(line)
    out = "\n".join(lines)
    if text.endswith("\n"):
        out += "\n"
    out = _HEADER_ARGUMENT_RE.sub("", out)
    return out


def rewrite_boxjs_script_urls(payload: dict) -> dict:
    """Point subscription app script URLs at this repo's mirrored scripts."""
    apps = payload.get("apps")
    if not isinstance(apps, list):
        return payload
    for app in apps:
        if not isinstance(app, dict):
            continue
        script = app.get("script")
        if isinstance(script, str):
            for old, new in _SCRIPT_URL_REWRITES:
                if script.startswith(old):
                    app["script"] = new + script[len(old) :]
                    break
    return payload


def sync_yu9191_boxjs_subscription(
    *,
    upstream_url: str = YU9191_BOXJS_UPSTREAM,
    output: Path | None = None,
) -> Path:
    import urllib.request

    output = output or (MODULES / "yu9191-player.boxjs.json")
    with urllib.request.urlopen(upstream_url, timeout=60) as resp:
        raw = resp.read().decode("utf-8-sig")
    payload = json.loads(raw)
    payload = rewrite_boxjs_script_urls(payload)
    payload["repo"] = "https://github.com/oo226/egern-config"
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    output.write_text(text, encoding="utf-8")
    return output
