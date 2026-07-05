"""Repository path constants for sync / merge scripts."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ROUTING = ROOT / "Routing"
ROUTING_UPSTREAM = ROUTING / "_upstream"
ROUTING_FOREIGN = ROUTING / "Foreign"
MODULES = ROOT / "Modules"
SIGNIN_SCRIPTS = ROOT / "Scripts"
CHXM1023_SCRIPTS = SIGNIN_SCRIPTS / "chxm1023"
CHXM1023_AD_SCRIPTS = CHXM1023_SCRIPTS / "advertising"
TOOLS = ROOT / "scripts"

CHINA_DIRECT = ROUTING / "China-Direct.yaml"
REJECT_MERGED = ROUTING / "Reject-Merged.yaml"
LAN = ROUTING / "Lan.yaml"
ADBLOCK_MODULE = MODULES / "adblock-collection.module"
UNLOCK_MODULE = MODULES / "unlock-collection.module"
CUSTOM_APPS = MODULES / "custom-apps.sgmodule"
PATCHES_UNLOCK = MODULES / "patches-unlock.sgmodule"
PATCHES_ALICLOUD = MODULES / "patches-alicloud.sgmodule"
PATCHES_MINIGAME = MODULES / "patches-minigame-unlock.sgmodule"
YU9191_SCRIPTS = SIGNIN_SCRIPTS / "yu9191"
MANIFEST = MODULES / "manifest.yaml"
UNLOCK_MANIFEST = MODULES / "unlock-manifest.yaml"
UPSTREAM_CACHE = MODULES / "_upstream"

GITHUB_RAW_MAIN = (
    "https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main"
)
CHXM1023_SCRIPT_REWRITES = (
    (
        "https://raw.githubusercontent.com/chxm1023/Rewrite/main/",
        f"{GITHUB_RAW_MAIN}/Scripts/chxm1023/",
    ),
    (
        "https://raw.githubusercontent.com/chxm1023/Advertising/main/",
        f"{GITHUB_RAW_MAIN}/Scripts/chxm1023/advertising/",
    ),
)

# Other mirrored third-party script URLs rewritten during module merge.
EXTRA_SCRIPT_REWRITES = (
    (
        "https://raw.githubusercontent.com/Yu9191/shortcutstudio-rewrite/refs/heads/baby/dist/",
        f"{GITHUB_RAW_MAIN}/Scripts/yu9191/",
    ),
    (
        "https://raw.githubusercontent.com/WeiGiegie/666/main/mlkp.js",
        f"{GITHUB_RAW_MAIN}/Scripts/mlkp.js",
    ),
    (
        "https://raw.githubusercontent.com/liul0ng/quanx/refs/heads/main/wuhen.js",
        f"{GITHUB_RAW_MAIN}/Scripts/wuhen.js",
    ),
    (
        "https://raw.githubusercontent.com/fmz200/wool_scripts/main/Scripts/X/X_ads.js",
        f"{GITHUB_RAW_MAIN}/Scripts/fmz200/X_ads.js",
    ),
    (
        "https://raw.githubusercontent.com/Hey-sayiwanna/TencentSports-Surge/main/",
        f"{GITHUB_RAW_MAIN}/Scripts/tencent-sports/",
    ),
)

MIRRORED_SCRIPT_REWRITES = CHXM1023_SCRIPT_REWRITES + EXTRA_SCRIPT_REWRITES
