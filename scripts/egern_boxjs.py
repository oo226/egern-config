"""Build a unified BoxJS subscription for scripts mirrored in egern-config."""

from __future__ import annotations

import copy
import json
import re
import urllib.request
from pathlib import Path
from urllib.parse import unquote

from paths import GITHUB_RAW_MAIN, GITHUB_RAW_MAIN_BOXJS, MIRRORED_SCRIPT_REWRITES, MODULES, ROOT, SIGNIN_SCRIPTS

EGERN_BOXJS_SUBSCRIPTION = f"{GITHUB_RAW_MAIN_BOXJS}/Modules/egern.boxjs.json"
OUTPUT_PATH = MODULES / "egern.boxjs.json"

UPSTREAM_SUBSCRIPTIONS: tuple[tuple[str, str], ...] = (
    (
        "chavy",
        "https://raw.githubusercontent.com/chavyleung/scripts/master/box/chavy.boxjs.json",
    ),
    (
        "lowking",
        "https://raw.githubusercontent.com/lowking/Scripts/master/lowking.boxjs.json",
    ),
    (
        "fmz200",
        "https://raw.githubusercontent.com/fmz200/wool_scripts/main/boxjs/fmz200_boxjs.json",
    ),
    (
        "yu9191_pear",
        "https://raw.githubusercontent.com/Yu9191/Rewrite/refs/heads/main/pear.boxjs.json",
    ),
    (
        "yu9191_scheme",
        "https://raw.githubusercontent.com/Yu9191/Rewrite/refs/heads/main/boxjs.json",
    ),
    (
        "fokit",
        "https://raw.githubusercontent.com/FoKit/Scripts/main/boxjs/fokit.boxjs.json",
    ),
    (
        "toulanboy",
        "https://raw.githubusercontent.com/toulanboy/scripts/master/toulanboy.boxjs.json",
    ),
)

_EXTRA_SCRIPT_REWRITES: tuple[tuple[str, str], ...] = (
    (
        "https://github.com/fmz200/wool_scripts/raw/main/Scripts/",
        f"{GITHUB_RAW_MAIN}/Scripts/fmz200/",
    ),
    (
        "https://raw.githubusercontent.com/fmz200/wool_scripts/raw/main/Scripts/",
        f"{GITHUB_RAW_MAIN}/Scripts/fmz200/",
    ),
    (
        "https://github.com/lowking/Scripts/raw/master/",
        f"{GITHUB_RAW_MAIN}/Scripts/_external/github-raw/lowking/Scripts/master/",
    ),
    (
        "https://raw.githubusercontent.com/lowking/Scripts/raw/master/",
        f"{GITHUB_RAW_MAIN}/Scripts/_external/github-raw/lowking/Scripts/master/",
    ),
    (
        "https://github.com/lowking/Scripts/blob/master/",
        f"{GITHUB_RAW_MAIN}/Scripts/_external/github-raw/lowking/Scripts/master/",
    ),
    (
        "https://raw.githubusercontent.com/toulanboy/scripts/master/",
        f"{GITHUB_RAW_MAIN}/Scripts/_external/github-raw/toulanboy/scripts/master/",
    ),
    (
        "https://github.com/toulanboy/scripts/raw/master/",
        f"{GITHUB_RAW_MAIN}/Scripts/_external/github-raw/toulanboy/scripts/master/",
    ),
    (
        "https://raw.githubusercontent.com/FoKit/Scripts/main/",
        f"{GITHUB_RAW_MAIN}/Scripts/_external/github-raw/FoKit/Scripts/main/",
    ),
    (
        "https://raw.githubusercontent.com/ClydeTime/BiliBili/main/",
        f"{GITHUB_RAW_MAIN}/Scripts/_external/github-raw/ClydeTime/BiliBili/main/",
    ),
)

_SCRIPT_REWRITES = MIRRORED_SCRIPT_REWRITES + _EXTRA_SCRIPT_REWRITES

# chavyleung sign-in apps shipped at Scripts/ root (not under _external).
CHAVY_ROOT_SCRIPT_OVERRIDES: dict[str, str] = {
    "BAIDU": "Scripts/tieba.js",
    "10000": "Scripts/dianxin10000.js",
    "sfexpress": "Scripts/sfexpress.js",
    "ximalaya": "Scripts/ximalaya.js",
}

SCRIPT_PATH_ALIASES: dict[str, str] = {
    "Scripts/yu9191/rewrite/insav.js": "Scripts/yu9191/rewrite/insav-tv/dist/insav.js",
}

# fmz200 / other apps with script=null — reserved for future explicit bindings.

_PLAYER_SELECT_ITEMS = [
    {"key": "lenna", "label": "Lenna 视频库"},
    {"key": "SenPlayer", "label": "SenPlayer (播放)"},
    {"key": "SenPlayer-dl", "label": "SenPlayer (下载+命名.mp4)"},
    {"key": "Infuse", "label": "Infuse 播放器"},
    {"key": "Fileball", "label": "Fileball 文件管理"},
    {"key": "VidHub", "label": "VidHub 影库"},
    {"key": "IINA", "label": "IINA 播放器"},
    {"key": "NPlayer", "label": "nPlayer"},
    {"key": "VLC", "label": "VLC 播放器"},
    {"key": "KMPlayer", "label": "KMPlayer"},
    {"key": "Alook", "label": "Alook 浏览器"},
    {"key": "Safari", "label": "Safari 浏览器"},
    {"key": "custom", "label": "🛠 自定义播放器"},
]

_LOG_LEVEL_ITEMS = [
    {"key": "off", "label": "off (静默)"},
    {"key": "error", "label": "error"},
    {"key": "warn", "label": "warn"},
    {"key": "info", "label": "info (默认)"},
    {"key": "debug", "label": "debug"},
    {"key": "all", "label": "all"},
]


EGERN_AUTHOR = "egern-config"


def _local_url(relative: str) -> str:
    return f"{GITHUB_RAW_MAIN_BOXJS}/{relative.lstrip('/')}"


def rewrite_script_url(url: str) -> str:
    url = unquote(url.strip()).split("?")[0]
    if "github.com/" in url and "/blob/" in url:
        url = url.replace("https://github.com/", "https://raw.githubusercontent.com/").replace(
            "/blob/", "/"
        )
    for old, new in _SCRIPT_REWRITES:
        if url.startswith(old):
            return new + url[len(old) :]
    return url


def _collect_referenced_scripts() -> set[str]:
    refs: set[str] = set()
    pattern = re.compile(r"script-path=([^\s,]+)")
    for path in MODULES.glob("*.module"):
        for match in pattern.finditer(path.read_text(encoding="utf-8", errors="replace")):
            url = match.group(1).strip()
            if "egern-config" in url:
                refs.add(url.split("egern-config/refs/heads/main/")[-1])
    # Scripts shipped in this repo that commonly use BoxJS (even if module disabled).
    scope_dirs = (
        SIGNIN_SCRIPTS / "fmz200",
        SIGNIN_SCRIPTS / "yu9191",
        SIGNIN_SCRIPTS / "zenmofeishi",
        SIGNIN_SCRIPTS / "chxm1023",
        SIGNIN_SCRIPTS / "weigiegie",
        SIGNIN_SCRIPTS / "weibo",
        SIGNIN_SCRIPTS / "tencent-sports",
        SIGNIN_SCRIPTS / "liul0ng",
        SIGNIN_SCRIPTS / "xiaohongshu",
    )
    for directory in scope_dirs:
        if directory.is_dir():
            for path in directory.rglob("*.js"):
                refs.add(path.relative_to(ROOT).as_posix())
    for path in SIGNIN_SCRIPTS.glob("*.js"):
        refs.add(path.relative_to(ROOT).as_posix())
    return refs


def _resolve_script_alias(rel: str) -> str:
    return SCRIPT_PATH_ALIASES.get(rel, rel)


def _collect_local_scripts() -> set[str]:
    rel: set[str] = set()
    for path in SIGNIN_SCRIPTS.rglob("*.js"):
        rel.add(path.relative_to(ROOT).as_posix())
    return rel


def _script_index() -> tuple[set[str], set[str], dict[str, str]]:
    referenced = _collect_referenced_scripts()
    local = _collect_local_scripts()
    basename_to_rel: dict[str, str] = {}
    for rel in local:
        basename_to_rel.setdefault(rel.rsplit("/", 1)[-1], rel)
    return referenced, local, basename_to_rel


def _fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=90) as resp:
        return json.loads(resp.read().decode("utf-8-sig"))


def _player_settings(prefix: str, *, jump: bool = True) -> list[dict]:
    settings: list[dict] = [
        {
            "id": f"{prefix}_player_select",
            "name": "播放器选择",
            "val": "lenna",
            "type": "selects",
            "items": _PLAYER_SELECT_ITEMS,
            "desc": "选择播放器（或使用自定义）",
        },
        {
            "id": f"{prefix}_custom_scheme",
            "name": "自定义 Scheme",
            "val": "",
            "type": "text",
            "desc": "例如: nplayer-http:// 或 myplayer://x-callback-url/play?url= 记得点旁边的保存按钮",
            "show": {f"{prefix}_player_select": "custom"},
        },
        {
            "id": f"{prefix}_url_encode",
            "name": "URL 编码",
            "val": "auto",
            "type": "selects",
            "items": [
                {"key": "auto", "label": "自动（推荐）"},
                {"key": "yes", "label": "强制编码"},
                {"key": "no", "label": "不编码"},
            ],
            "desc": "是否对播放地址进行 URL 编码（大部分 x-callback-url 需要编码）",
        },
        {
            "id": f"{prefix}_log_level",
            "name": "日志级别",
            "val": "info",
            "type": "selects",
            "items": _LOG_LEVEL_ITEMS,
            "desc": "脚本日志输出级别（影响代理工具的日志面板）",
        },
    ]
    if jump:
        settings.insert(
            3,
            {
                "id": f"{prefix}_player_jump",
                "name": "播放器跳转",
                "val": "yes",
                "type": "selects",
                "items": [
                    {"key": "yes", "label": "通知并跳转外部播放器"},
                    {"key": "no", "label": "不通知、不跳转"},
                ],
                "desc": "关闭后仅修改接口响应，不发送播放器跳转通知",
            },
        )
    return settings


def local_only_apps() -> list[dict]:
    return [
        {
            "id": "iios_checkin",
            "name": "iios 签到",
            "keys": [
                "iios_login_accounts",
                "iios_login_email",
                "iios_login_password",
                "iios_client_id",
            ],
            "settings": [
                {
                    "id": "iios_login_accounts",
                    "name": "多账号 JSON",
                    "val": "[]",
                    "type": "textarea",
                    "desc": '例: [{"email":"a@b.com","password":"***","client_id":"..."}]',
                },
                {
                    "id": "iios_login_email",
                    "name": "单账号邮箱",
                    "val": "",
                    "type": "text",
                },
                {
                    "id": "iios_login_password",
                    "name": "单账号密码",
                    "val": "",
                    "type": "text",
                },
                {
                    "id": "iios_client_id",
                    "name": "client_id",
                    "val": "",
                    "type": "text",
                },
            ],
            "author": "egern-config",
            "repo": "https://github.com/oo226/egern-config",
            "script": _local_url("Scripts/iios_checkin.js"),
        },
        {
            "id": "mixc_signin",
            "name": "一点万象签到",
            "keys": ["mixc_signin_params"],
            "settings": [
                {
                    "id": "mixc_signin_params",
                    "name": "抓参数据 JSON",
                    "val": "",
                    "type": "textarea",
                    "desc": "先开 MITM 抓参，保存后用于签到",
                }
            ],
            "author": "egern-config",
            "repo": "https://github.com/oo226/egern-config",
            "script": _local_url("Scripts/mixc_signin.js"),
        },
        {
            "id": "pingme_capture",
            "name": "PingMe 抓参",
            "keys": ["pingme_capture_v3"],
            "settings": [
                {
                    "id": "pingme_capture_v3",
                    "name": "抓参缓存",
                    "val": "",
                    "type": "textarea",
                    "desc": "一般由抓参脚本自动写入，也可手动粘贴",
                }
            ],
            "author": "egern-config",
            "repo": "https://github.com/oo226/egern-config",
            "script": _local_url("Scripts/PingMe-capture.js"),
        },
        {
            "id": "soulsing_capture",
            "name": "Soul 唱歌抓参",
            "keys": ["soul_sign_url", "soul_sign_headers"],
            "settings": [
                {"id": "soul_sign_url", "name": "签到 URL", "val": "", "type": "text"},
                {
                    "id": "soul_sign_headers",
                    "name": "请求头 JSON",
                    "val": "",
                    "type": "textarea",
                },
            ],
            "author": "egern-config",
            "repo": "https://github.com/oo226/egern-config",
            "script": _local_url("Scripts/SoulSing.js"),
        },
        {
            "id": "laichong_capture",
            "name": "来充抓参",
            "keys": ["LaichongAuthList"],
            "settings": [
                {
                    "id": "LaichongAuthList",
                    "name": "账号列表 JSON",
                    "val": "[]",
                    "type": "textarea",
                }
            ],
            "author": "egern-config",
            "repo": "https://github.com/oo226/egern-config",
            "script": _local_url("Scripts/LaiChong.js"),
        },
        {
            "id": "nodeseek_capture",
            "name": "NodeSeek 抓参",
            "keys": ["NS_NodeseekHeaders"],
            "settings": [
                {
                    "id": "NS_NodeseekHeaders",
                    "name": "请求头 JSON",
                    "val": "",
                    "type": "textarea",
                }
            ],
            "author": "egern-config",
            "repo": "https://github.com/oo226/egern-config",
            "script": _local_url("Scripts/Nodeseek_NsCheckin.js"),
        },
        {
            "id": "xjh51_player",
            "name": "xjh51 播放器设置",
            "keys": [
                "xjh51_player_select",
                "xjh51_custom_scheme",
                "xjh51_url_encode",
                "xjh51_player_jump",
                "xjh51_log_level",
            ],
            "settings": _player_settings("xjh51"),
            "author": "egern-config",
            "repo": "https://github.com/oo226/egern-config",
            "script": _local_url("Scripts/yu9191/rewrite/xjh51/dist/xjh51.js"),
        },
        {
            "id": "ql_sync",
            "name": "青龙同步 BoxJS",
            "keys": ["#ql_sync_keys", "ql_sync_notify"],
            "desc": "在 BoxJS「我的 → 数据」中编辑 #ql_sync_keys（逗号分隔键名）与 ql_sync_notify。",
            "author": "egern-config",
            "repo": "https://github.com/oo226/egern-config",
            "script": _local_url("Scripts/fmz200/qinglong/ql_sync.js"),
        },
        {
            "id": "yanxuan_signin",
            "name": "网易严选签到",
            "keys": ["chavy_cookie_yanxuan", "chavy_token_yanxuan"],
            "settings": [
                {
                    "id": "chavy_cookie_yanxuan",
                    "name": "Cookie",
                    "val": "",
                    "type": "textarea",
                },
                {
                    "id": "chavy_token_yanxuan",
                    "name": "Token",
                    "val": "",
                    "type": "textarea",
                },
            ],
            "author": "egern-config",
            "repo": "https://github.com/oo226/egern-config",
            "script": _local_url("Scripts/yanxuan.js"),
        },
    ]


def _pick_script_for_keys(
    keys: list[str],
    *,
    referenced: set[str],
) -> str | None:
    if not keys:
        return None
    candidates: list[str] = []
    for rel in sorted(referenced):
        try:
            text = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if any(str(key) in text for key in keys):
            candidates.append(rel)
    if not candidates:
        return None
    cookie_hits = [p for p in candidates if ".cookie." in p or "/cookie/" in p]
    if cookie_hits:
        return _local_url(_resolve_script_alias(cookie_hits[0]))
    return _local_url(_resolve_script_alias(candidates[0]))


def _app_local_script(
    app: dict,
    *,
    source: str,
    referenced: set[str],
    local: set[str],
) -> str | None:
    app_id = str(app.get("id", ""))
    if source == "chavy" and app_id in CHAVY_ROOT_SCRIPT_OVERRIDES:
        rel = CHAVY_ROOT_SCRIPT_OVERRIDES[app_id]
        return _local_url(rel) if rel in local else None

    script = app.get("script")
    if isinstance(script, str) and script.strip():
        rewritten = rewrite_script_url(script)
        if "egern-config" in rewritten:
            rel = rewritten.split("egern-config/refs/heads/main/")[-1]
            rel = _resolve_script_alias(rel)
            if rel in local and rel in referenced:
                return _local_url(rel)
        # Upstream path must exist locally exactly (after rewrite).
        for rel in local:
            if rewritten.endswith(rel) or rel.endswith(rewritten.split("/")[-1]):
                if rel in referenced and rewritten.split("/")[-1] == rel.rsplit("/", 1)[-1]:
                    # Require matching directory segment to avoid 10010.js / follow.js collisions.
                    upstream_tail = "/".join(rewritten.split("/")[-3:])
                    local_tail = "/".join(rel.split("/")[-3:])
                    if upstream_tail == local_tail or rel in rewritten:
                        return _local_url(rel)

    keys = app.get("keys") or []
    if isinstance(keys, list) and keys:
        return _pick_script_for_keys([str(k) for k in keys], referenced=referenced)

    return None


def _sanitize_app(app: dict) -> dict:
    """Drop fields / ids that break BoxJS navigation or DOM bindings."""
    app.pop("tasks", None)
    app.pop("rewrites", None)
    for key in list(app):
        if key.startswith("desc") and key not in ("desc",):
            app.pop(key, None)
    settings = app.get("settings")
    if isinstance(settings, list):
        for setting in settings:
            if not isinstance(setting, dict):
                continue
            sid = str(setting.get("id", ""))
            # `#foo` is a valid persistent key but invalid as an HTML id in BoxJS UI.
            if sid.startswith("#"):
                setting["id"] = f"boxjs_{sid.lstrip('#')}"
    return app


def _normalize_app(
    app: dict,
    *,
    source: str,
    local_script: str,
    used_ids: set[str],
) -> dict:
    out = copy.deepcopy(app)
    out["script"] = local_script
    out["repo"] = "https://github.com/oo226/egern-config"
    out["author"] = EGERN_AUTHOR

    original_id = str(out.get("id", "")).strip()
    # Drop legacy prefixed ids from earlier generator versions.
    if original_id.startswith("egern."):
        original_id = original_id.split(".")[-1]

    app_id = original_id
    if app_id in used_ids:
        app_id = f"{source}_{original_id}"
    if app_id in used_ids:
        app_id = f"egern_{source}_{original_id}".replace(".", "_")

    out["id"] = app_id
    used_ids.add(app_id)
    return _sanitize_app(out)


def _should_skip_app(app: dict) -> bool:
    name = str(app.get("name", "")).lower()
    app_id = str(app.get("id", "")).lower()
    if "demo" in name or "toolkitdemo" in app_id:
        return True
    return False


def build_egern_boxjs() -> dict:
    referenced, local, _basename_to_rel = _script_index()

    merged: dict[str, dict] = {}
    used_ids: set[str] = set()
    sources_meta: list[str] = []

    for source, url in UPSTREAM_SUBSCRIPTIONS:
        try:
            payload = _fetch_json(url)
        except Exception as exc:
            sources_meta.append(f"{source}: fetch failed ({exc})")
            continue
        apps = payload.get("apps")
        if not isinstance(apps, list):
            continue
        kept = 0
        for app in apps:
            if not isinstance(app, dict) or _should_skip_app(app):
                continue
            local_script = _app_local_script(
                app,
                source=source,
                referenced=referenced,
                local=local,
            )
            if not local_script:
                continue
            normalized = _normalize_app(
                app,
                source=source,
                local_script=local_script,
                used_ids=used_ids,
            )
            merged[normalized["id"]] = normalized
            kept += 1
        sources_meta.append(f"{source}: {kept}/{len(apps)}")

    for app in local_only_apps():
        app = _sanitize_app(copy.deepcopy(app))
        app["author"] = EGERN_AUTHOR
        app["repo"] = "https://github.com/oo226/egern-config"
        if app["id"] in used_ids:
            app["id"] = f"egern_{app['id']}"
        used_ids.add(app["id"])
        merged[app["id"]] = app

    if "InsavSettings" in merged:
        merged["InsavSettings"]["script"] = _local_url(
            "Scripts/yu9191/rewrite/insav-tv/dist/insav.js"
        )

    apps_out = sorted(merged.values(), key=lambda item: str(item.get("name", "")))
    return {
        "id": "egern-config.sub",
        "name": "Egern Config 合集",
        "author": "oo226/egern-config",
        "icon": "https://raw.githubusercontent.com/chavyleung/scripts/master/box/box.png",
        "repo": "https://github.com/oo226/egern-config",
        "desc": "本仓库脚本统一 BoxJS 订阅：播放器、签到、抓参、Cookie 相关配置。",
        "sources": sources_meta,
        "apps": apps_out,
    }


def sync_egern_boxjs(*, output: Path | None = None) -> tuple[Path, dict]:
    output = output or OUTPUT_PATH
    payload = build_egern_boxjs()
    stats = payload.pop("sources", [])
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    output.write_text(text, encoding="utf-8")
    return output, stats
