"""Repository path constants for sync / merge scripts."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ROUTING = ROOT / "分流"
ROUTING_UPSTREAM = ROUTING / "_upstream"
ROUTING_FOREIGN = ROUTING / "国外"
MODULES = ROOT / "模块"
SIGNIN_SCRIPTS = ROOT / "脚本"
TOOLS = ROOT / "scripts"

CHINA_DIRECT = ROUTING / "国内直连.yaml"
REJECT_MERGED = ROUTING / "去广告.yaml"
LAN = ROUTING / "局域网.yaml"
ADBLOCK_MODULE = MODULES / "去广告净化合集.module"
CUSTOM_APPS = MODULES / "custom-apps.sgmodule"
MANIFEST = MODULES / "manifest.yaml"
UPSTREAM_CACHE = MODULES / "_upstream"

GITHUB_RAW_MAIN = (
    "https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main"
)
