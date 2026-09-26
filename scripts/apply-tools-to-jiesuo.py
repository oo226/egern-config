#!/usr/bin/env python3
"""一次性：工具模块进仓库 + 解锁合集；eulac/追风进 fenliu。不跑全量 build-yuanban。"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from routing_list_utils import parse_surge_list, write_egern_sets  # noqa: E402

spec = importlib.util.spec_from_file_location("by", ROOT / "scripts" / "build-yuanban.py")
by = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(by)

RAW = by.RAW
QITA = by.QITA
ZUOZHE = by.ZUOZHE
HEJI = by.HEJI
BRANCH = by.BRANCH


def rewrite_yaml_script_urls(text: str, author: str, cache: dict[str, str]) -> str:
    """Egern yaml: script_url: https://...js → 本仓。"""

    def _sub(m: re.Match[str]) -> str:
        prefix, url = m.group(1), m.group(2)
        return prefix + by.mirror_js(url, author, cache)

    return re.sub(
        r"(script_url:\s*)(https?://[^\s\"']+\.(?:js|mjs)(?:\?[^\s\"']*)?)",
        _sub,
        text,
        flags=re.I,
    )


def save_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"  wrote {path.relative_to(ROOT)}")


def mirror_tools(cache: dict[str, str]) -> None:
    qlocal = QITA / "local"
    qlocal.mkdir(parents=True, exist_ok=True)
    local_m = by.ensure_author("local")["mokuai"]

    # Sub-Store Egern 原版 → qita（Profile 用）；脚本指 iewha 已镜像 js
    ss = by.fetch(
        "https://raw.githubusercontent.com/sub-store-org/Sub-Store/refs/heads/master/config/Egern.yaml"
    ).decode("utf-8", errors="replace")
    ss = rewrite_yaml_script_urls(ss, "iewha", cache)
    # 已有 sub-store js 时 mirror_js 会复用；再强制换成 iewha 路径若占位失败
    for old, new in (
        (
            "https://github.com/sub-store-org/Sub-Store/releases/latest/download/sub-store-1.min.js",
            f"{RAW}/Yuanban/zuozhe/iewha/js/sub-store-1.min.js",
        ),
        (
            "https://github.com/sub-store-org/Sub-Store/releases/latest/download/sub-store-0.min.js",
            f"{RAW}/Yuanban/zuozhe/iewha/js/sub-store-0.min.js",
        ),
        (
            "https://github.com/sub-store-org/Sub-Store/releases/latest/download/cron-sync-artifacts.min.js",
            f"{RAW}/Yuanban/zuozhe/iewha/js/cron-sync-artifacts.min.js",
        ),
    ):
        ss = ss.replace(old, new)
    save_text(qlocal / "sub-store.egern.yaml", ss)

    # Script Hub Egern β
    sh = by.fetch(
        "https://raw.githubusercontent.com/Script-Hub-Org/Script-Hub/refs/heads/main/modules/script-hub.beta.egern.yaml"
    ).decode("utf-8", errors="replace")
    sh = rewrite_yaml_script_urls(sh, "scripthub", cache)
    save_text(qlocal / "script-hub.egern.yaml", sh)

    # BoxJs：同步到 local/mokuai（进 jiesuo）
    box = (QITA / "local" / "boxjs.sgmodule").read_text(encoding="utf-8", errors="replace")
    box = by.rewrite_js_urls(box, "local", cache)
    save_text(local_m / "boxjs.sgmodule", box)
    save_text(qlocal / "boxjs.sgmodule", box)

    # iRingo WeatherKit / Maps 原版 — JS 按产品+版本命名，避免 request.bundle.js 撞名
    import re as _re

    def _iringo(label: str, mod_url: str, fname: str, product: str) -> None:
        raw = by.fetch(mod_url).decode("utf-8", errors="replace")
        url_map: dict[str, str] = {}
        for u in sorted(set(_re.findall(r"https?://github\.com/NSRingo/[^\s,\"']+\.js", raw))):
            parts = u.rstrip("/").split("/")
            ver = parts[-2] if len(parts) >= 2 else "x"
            base = parts[-1]
            dest_name = f"{product}-{ver}-{base}"
            dest = by.ZUOZHE / "nsringo" / "js" / dest_name
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.is_file():
                dest.write_bytes(by.fetch(u))
                print(f"  js/nsringo/{dest_name}")
            local = f"{RAW}/Yuanban/zuozhe/nsringo/js/{dest_name}"
            url_map[u] = local
            cache[u] = local
        for u, local in url_map.items():
            raw = raw.replace(u, local)
        save_text(local_m / fname, raw)
        save_text(qlocal / fname, raw)
        print(f"  iringo {label} ok")

    _iringo(
        "weather",
        "https://github.com/NSRingo/WeatherKit/releases/latest/download/iRingo.WeatherKit.sgmodule",
        "iringo-weather.sgmodule",
        "WeatherKit",
    )
    _iringo(
        "maps",
        "https://github.com/NSRingo/GeoServices/releases/latest/download/iRingo.Maps.sgmodule",
        "iringo-maps.sgmodule",
        "GeoServices",
    )

    # AntiRevoke → sgmodule 形态进 local
    ar = by.fetch(
        "https://raw.githubusercontent.com/salem-2007/apple-cert-block/main/AntiRevoke.plugin"
    ).decode("utf-8", errors="replace")
    # plugin 头改成 sgmodule 友好
    if not ar.lstrip().startswith("#!name"):
        ar = "#!name=AntiRevoke（苹果证书）\n#!desc=屏蔽 Apple P12/OCSP 证书验证\n\n" + ar
    save_text(local_m / "antirevoke.sgmodule", ar)
    save_text(qlocal / "antirevoke.sgmodule", ar)

    # 保留 location/others 单件（已在 qita/local，不进合集）
    print("tools mirrored")


def mirror_fenliu_extras() -> None:
    eulac = by.ensure_author("eulac")["fenliu"]
    local_f = by.ensure_author("local")["fenliu"]

    for name, url, title in (
        (
            "ResourceSite",
            "https://raw.githubusercontent.com/eulac-dev/Proxy/refs/heads/main/Loon/Rules/ResourceSite.lsr",
            "视频资源站",
        ),
        (
            "PanVod",
            "https://raw.githubusercontent.com/eulac-dev/Proxy/refs/heads/main/Loon/Rules/PanVod.lsr",
            "网盘点播",
        ),
    ):
        raw = by.fetch(url).decode("utf-8", errors="replace")
        (eulac / f"{name}.lsr").write_text(raw, encoding="utf-8")
        sets = parse_surge_list(raw)
        write_egern_sets(
            eulac / f"{name}.yaml",
            sets,
            header_lines=[
                f"# 规则名称: {title}（{name}）",
                "# 上游: eulac-dev/Proxy Loon/Rules",
                f"# 镜像: Yuanban/zuozhe/eulac/fenliu/{name}.yaml",
            ],
            no_resolve=True,
        )
        # heji 直白名
        heji_name = f"eulac-{title}.yaml"
        write_egern_sets(
            HEJI / "fenliu" / heji_name,
            sets,
            header_lines=[
                f"# 规则名称: {title}（{name}）",
                "# 上游: eulac-dev/Proxy",
            ],
            no_resolve=True,
        )
        print(f"  fenliu {heji_name}")

    zf = """# 类型: 分流规则 — 追风挂机（途游小程序游戏辅助）
# 仅这两条域名走专用 HTTP 代理，其余流量不受影响。

domain_suffix_set:
  - sq-hlsg.tytuyoo.com
  - open-hlsg.tytuyoo.com
"""
    save_text(local_f / "Zhuifeng.yaml", zf)
    save_text(HEJI / "fenliu" / "本仓-追风.yaml", zf)


def rebuild_jiesuo(cache: dict[str, str]) -> None:
    """在现有 heji_jiesuo 逻辑上追加工具袋。"""
    # 先跑原逻辑
    by.heji_jiesuo(cache)

    # 再读出来，追加工具段后重写（避免改 heji_jiesuo 签名时漏袋）
    # 更干净：直接再 merge 一次带 extras
    bags: list[tuple[str, dict[str, list[str]]]] = []
    # 复用 heji_jiesuo 内部太重；改为：读现有 jiesuo 不够。直接 call 改过的 heji。
    # 这里改为 patch extras into build then call again — 见 build-yuanban 更新。
    print("jiesuo rebuilt via by.heji_jiesuo")


def main() -> None:
    print(f"branch={BRANCH} RAW={RAW}")
    cache: dict[str, str] = {}
    print("=== mirror tools ===")
    mirror_tools(cache)
    print("=== fenliu eulac + 追风 ===")
    mirror_fenliu_extras()
    print("=== rebuild jiesuo ===")
    by.heji_jiesuo(cache)
    by.assert_self_hosted()
    print("done js_ok=", by.STATS["js_ok"], "js_fail=", len(by.STATS["js_fail"]))
    if by.STATS["js_fail"]:
        for u in by.STATS["js_fail"][:15]:
            print("  miss", u[:100])


if __name__ == "__main__":
    main()
