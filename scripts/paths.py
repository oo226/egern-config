"""Repository path constants for sync / merge scripts."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ROUTING = ROOT / "Routing"
ROUTING_UPSTREAM = ROUTING / "_upstream"
ROUTING_FOREIGN = ROUTING / "Foreign"
MODULES = ROOT / "Modules"
SIGNIN_SCRIPTS = ROOT / "Scripts"
TOOLS = ROOT / "scripts"

CHINA_DIRECT = ROUTING / "China-Direct.yaml"
REJECT_MERGED = ROUTING / "Reject-Merged.yaml"
LAN = ROUTING / "Lan.yaml"
ADBLOCK_MODULE = MODULES / "adblock-collection.module"
UNLOCK_MODULE = MODULES / "unlock-collection.module"
CUSTOM_APPS = MODULES / "custom-apps.sgmodule"
PATCHES_UNLOCK = MODULES / "patches-unlock.sgmodule"
MANIFEST = MODULES / "manifest.yaml"
UNLOCK_MANIFEST = MODULES / "unlock-manifest.yaml"
UPSTREAM_CACHE = MODULES / "_upstream"

GITHUB_RAW_MAIN = (
    "https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main"
)
