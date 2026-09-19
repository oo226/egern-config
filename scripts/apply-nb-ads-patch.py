#!/usr/bin/env python3
"""Re-apply NB助手假成功 patches after daily adblock merge.

Daily merge rebuilds Modules/adblock-collection.module from upstream + supplements.
custom-apps.sgmodule is local:true (source of truth), but heat/finalize and accidental
hard REJECT can still drift. This script forces:

1. custom-apps Map Local / URL Rewrite (Network OK + empty /nb/app + IP bypass)
2. Egern.yaml map_locals (same semantics; no hard REJECT on control channel)
3. Strip DST-PORT/url_regex hard REJECT for nbtool8 in Surge.conf / modules
4. Patch Egern + Surge 去广告合集 Map Local
5. Reject-Hot must NOT reject nbtool8 control URLs (SDK domains only)

Wire after apply-surge-heat-patch.py, before finalize-egern-adblock.py.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CUSTOM_APPS = ROOT / "Modules" / "custom-apps.sgmodule"
EGERN_YAML = ROOT / "Egern.yaml"
REJECT_HOT = ROOT / "Routing" / "Reject-Hot.yaml"
SURGE_CONF = ROOT / "surge" / "Surge.conf"
ADBLOCK_FILES = (
    ROOT / "Modules" / "adblock-collection.module",
    ROOT / "surge" / "Modules" / "adblock-collection.module",
)

URL_REWRITE_BLOCK = r"""# NB全能助手 / NB Pro — 官方域名开屏与广告接口（须匹配 :端口，否则 9527/nb/app 漏网）
^https?:\/\/(api\.|www\.|app\.)?nbtool8\.com(:\d+)?\/.*(splash|startup|launch|open[Ss]creen|welcome|banner|popup|promo|advert|/ad/|/ads/) - reject-dict
^https?:\/\/[^:/]*nbtool8\.com(:\d+)?\/.*(splash|startup|launch|banner|popup|advert|/ad/|/ads/) - reject-dict
# 控制口假成功：telnet=Network OK；app=空正文；含硬编码 IP 绕过
^https?:\/\/[^:/]*nbtool8\.com(:\d+)?\/nb\/telnet data-type=text data="Network OK" status-code=200 header="Content-Type:text/plain"
^https?:\/\/124\.222\.32\.246(:\d+)?\/nb\/telnet data-type=text data="Network OK" status-code=200 header="Content-Type:text/plain"
^https?:\/\/[^:/]*nbtool8\.com(:\d+)?\/nb\/app data-type=text data="" status-code=200 header="Content-Type:text/plain"
^https?:\/\/124\.222\.32\.246(:\d+)?\/nb\/app data-type=text data="" status-code=200 header="Content-Type:text/plain"
^https?:\/\/[^:/]*nbtool8\.com:\d+\/nb\/(?!telnet) data-type=text data="" status-code=200 header="Content-Type:text/plain"
^http:\/\/[^:/]*nbtool8\.com:\d+\/ data-type=text data="" status-code=200 header="Content-Type:text/plain"
^http:\/\/124\.222\.32\.246(:\d+)?\/ data-type=text data="" status-code=200 header="Content-Type:text/plain"
"""

MAP_LOCAL_BLOCK = r"""# NB助手：假成功去开屏（勿硬 REJECT；含 IP 绕过 124.222.32.246）
^https?:\/\/[^:/]*nbtool8\.com(:\d+)?\/nb\/telnet data-type=text data="Network OK" status-code=200 header="Content-Type:text/plain"
^https?:\/\/124\.222\.32\.246(:\d+)?\/nb\/telnet data-type=text data="Network OK" status-code=200 header="Content-Type:text/plain"
^https?:\/\/[^:/]*nbtool8\.com(:\d+)?\/nb\/app data-type=text data="" status-code=200 header="Content-Type:text/plain"
^https?:\/\/124\.222\.32\.246(:\d+)?\/nb\/app data-type=text data="" status-code=200 header="Content-Type:text/plain"
^http:\/\/[^:/]*nbtool8\.com:\d+\/ data-type=text data="" status-code=200 header="Content-Type:text/plain"
^http:\/\/124\.222\.32\.246(:\d+)?\/ data-type=text data="" status-code=200 header="Content-Type:text/plain"
"""

EGERN_MAP_LOCALS = r"""# NB助手：假成功去开屏（硬 REJECT 会无网络；域名拦了会改走 IP 80）
# 微信公众号：getappmsgad / jsmonitor 等（须 MITM mp.weixin.qq.com；勿整域拒 wxs.qq.com）
map_locals:
  # 心跳：真实接口返回纯文本 Network OK
  - match: '^https?://[^/]*nbtool8\.com(?::\d+)?/nb/telnet'
    status_code: 200
    headers:
      Content-Type: text/plain
    body: "Network OK"
  - match: '^https?://124\.222\.32\.246(?::\d+)?/nb/telnet'
    status_code: 200
    headers:
      Content-Type: text/plain
    body: "Network OK"
  # 广告配置：空正文，避免下发开屏任务
  - match: '^https?://[^/]*nbtool8\.com(?::\d+)?/nb/app'
    status_code: 200
    headers:
      Content-Type: text/plain
    body: ""
  - match: '^https?://124\.222\.32\.246(?::\d+)?/nb/app'
    status_code: 200
    headers:
      Content-Type: text/plain
    body: ""
  - match: '^https?://124\.222\.32\.246(?::\d+)?/'
    status_code: 200
    headers:
      Content-Type: text/plain
    body: ""
  # 微信公众号底栏广告
  - match: '^https://mp\.weixin\.qq\.com/mp/getappmsgad'
    status_code: 200
    headers:
      Content-Type: application/json
    body: '{"advertisement_num":0,"advertisement_info":[]}'
  - match: '^https://mp\.weixin\.qq\.com/mp/(cps_product_info|jsmonitor|masonryfeed|relatedarticle)\?'
    status_code: 200
    headers:
      Content-Type: application/json
    body: '{}'
  - match: '^https://mp\.weixin\.qq\.com/mp/relatedsearchword'
    status_code: 200
    headers:
      Content-Type: application/json
    body: '{}'
"""

REJECT_HOT_TEMPLATE = r"""# 热点去广告（NB助手 SDK / 得力开屏 SDK）
# 小表、优先于 Reject-Merged 加载，避免大表日更空窗导致广告回潮
# 完整清单仍在 Reject-Merged；此处为双层兜底
#
# NB 控制口（nbtool8.com:9527 / 硬编码 IP）不要进本表 REJECT：
# /nb/telnet 返回 "Network OK"，硬拦会「无网络」；域名拦死后改走 IP:80。
# 去开屏见 Egern.yaml map_locals + 合集 Map Local（scripts/apply-nb-ads-patch.py）。

no_resolve: true
domain_set:
  - open.e.kuaishou.cn
  - sdk.zhangyuyidong.cn
  - v66-ad.ndcjl.com
domain_suffix_set:
  - 66mobi.com
  - adintl.cn
  - adkwai.com
  - adn-plus.com.cn
  - adukwai.com
  - api-cfg.8ziben.com
  - api-dsp.8ziben.com
  - api-events.8ziben.com
  - bugly.qq.com
  - cdnhwc8.com
  - ctyunxs.cn
  - e.kuaishou.com
  - eos.huhehaote-8.cmecloud.cn
  - gepush.com
  - gifshow.com
  - hzzfcm.com
  - static-dsp.8ziben.com
  - static.fliduo.cn
  - yximgs.com
  - yxings.com
  - zhangyuyidong.cn
domain_keyword_set:
  - delicloud-operate-manager
"""


def _write_if_changed(path: Path, new: str, *, label: str | None = None) -> None:
    rel = path.relative_to(ROOT)
    old = path.read_text(encoding="utf-8") if path.is_file() else None
    if old == new:
        print(f"ok {rel}" + (f" ({label})" if label else ""))
        return
    path.write_text(new, encoding="utf-8")
    print(f"patched {rel}" + (f" ({label})" if label else ""))


def _strip_and_reject_nb(text: str) -> str:
    return re.sub(
        r"(?:^# NB 官方 9527.*\n)?"
        r"(?:^# NB 控制口勿.*\n)?"
        r"^AND,\(\(DOMAIN(?:,|-SUFFIX,)nbtool8\.com\),\(DST-PORT,9527\)\),REJECT.*\n",
        "",
        text,
        flags=re.M,
    )


def _strip_nb_url_lines(section: str) -> str:
    patterns = (
        r"^# NB全能助手.*\n",
        r"^# 截图实锤.*\n",
        r"^# 接口是 text/plain.*\n",
        r"^# 控制口假成功.*\n",
        r"^# NB助手.*\n",
        r"^.*nbtool8\.com.*\n",
        r"^.*124\.222\.32\.246.*\n",
    )
    for pat in patterns:
        section = re.sub(pat, "", section, flags=re.M)
    return section


def _ensure_section_block(text: str, section: str, block: str) -> str:
    m = re.search(rf"^\[{re.escape(section)}\]\s*$", text, re.M)
    if not m:
        mitm = re.search(r"^\[MITM\]\s*$", text, re.M)
        insert = f"\n[{section}]\n{block}\n"
        if mitm:
            return text[: mitm.start()] + insert + text[mitm.start() :]
        return text.rstrip() + "\n" + insert

    rest = text[m.end() :]
    nxt = re.search(r"^\[(?:[A-Za-z][A-Za-z0-9 ]*)\]\s*$", rest, re.M)
    end = m.end() + (nxt.start() if nxt else len(rest))
    body = _strip_nb_url_lines(text[m.end() : end])
    if section == "URL Rewrite" and "# 得力e+" in body:
        body = body.replace("# 得力e+", block + "\n# 得力e+", 1)
    else:
        body = "\n" + block + ("\n" if not body.startswith("\n") else "") + body.lstrip("\n")
        if not body.endswith("\n"):
            body += "\n"
    return text[: m.end()] + body + text[end:]


def patch_module_text(text: str) -> str:
    text = _strip_and_reject_nb(text)
    text = _ensure_section_block(text, "URL Rewrite", URL_REWRITE_BLOCK)
    text = _ensure_section_block(text, "Map Local", MAP_LOCAL_BLOCK)
    note = (
        "# NB 控制口勿 AND REJECT：/nb/telnet=Network OK；"
        "域名拦了会改走 124.222.32.246:80\n"
    )
    if "NB 控制口勿 AND REJECT" not in text and re.search(r"^\[Rule\]\s*$", text, re.M):
        text = re.sub(r"^(\[Rule\]\s*\n)", r"\1" + note, text, count=1, flags=re.M)
    return text


def ensure_custom_apps() -> None:
    if not CUSTOM_APPS.is_file():
        raise SystemExit(f"missing {CUSTOM_APPS}")
    _write_if_changed(CUSTOM_APPS, patch_module_text(CUSTOM_APPS.read_text(encoding="utf-8")))


def ensure_adblock_collections() -> None:
    for path in ADBLOCK_FILES:
        if not path.is_file():
            print(f"skip missing {path.relative_to(ROOT)}")
            continue
        _write_if_changed(
            path,
            patch_module_text(path.read_text(encoding="utf-8")),
        )


def ensure_egern_yaml() -> None:
    if not EGERN_YAML.is_file():
        raise SystemExit(f"missing {EGERN_YAML}")
    text = EGERN_YAML.read_text(encoding="utf-8")

    # Drop hard REJECT block for nbtool8:9527 if present
    text = re.sub(
        r"\n  # NB助手：9527.*?\n  - and:\n(?:      .*\n)+?  - url_regex:\n"
        r"      match:.*nbtool8.*\n      policy: REJECT\n",
        "\n",
        text,
        count=1,
    )

    # Normalize reject-section comment
    text = re.sub(
        r"\n  # NB助手控制口勿硬 REJECT：.*\n(?:  # .*\n)*",
        "\n  # NB助手控制口勿硬 REJECT：/nb/telnet=Network OK；"
        "改走 IP 用 map_locals（apply-nb-ads-patch）\n",
        text,
        count=1,
    )

    # Replace or insert map_locals (idempotent: wipe prior NB/微信 comments + block)
    text = re.sub(
        r"\n# NB助手：假成功去开屏[^\n]*\n(?:# [^\n]*\n)*map_locals:\n"
        r"(?:  .*\n)*",
        lambda _m: "\n" + EGERN_MAP_LOCALS,
        text,
        count=1,
    )
    if "map_locals:" not in text:
        anchor = re.search(r"^body_rewrites:\s*$", text, re.M) or re.search(
            r"^mitm:\s*$", text, re.M
        )
        if not anchor:
            raise SystemExit("Egern.yaml: cannot find insert point for map_locals")
        text = text[: anchor.start()] + EGERN_MAP_LOCALS + "\n" + text[anchor.start() :]

    _write_if_changed(EGERN_YAML, text)


def ensure_surge_conf() -> None:
    if not SURGE_CONF.is_file():
        print("skip missing surge/Surge.conf")
        return
    text = SURGE_CONF.read_text(encoding="utf-8")
    text = re.sub(
        r"^# NB助手 9527：.*\n"
        r"AND,\(\(DOMAIN-SUFFIX,nbtool8\.com\),\(DST-PORT,9527\)\),REJECT\n"
        r"URL-REGEX,\^https\?://\[\^/\]\*nbtool8\.com:\\d\+/,REJECT\n",
        "# NB助手控制口勿硬 REJECT（/nb/telnet=Network OK；IP 绕过用合集 Map Local）\n",
        text,
        flags=re.M,
    )
    text = re.sub(
        r"^AND,\(\(DOMAIN(?:-SUFFIX)?,nbtool8\.com\),\(DST-PORT,9527\)\),REJECT.*\n",
        "",
        text,
        flags=re.M,
    )
    text = re.sub(
        r"^URL-REGEX,\^https\?://\[\^/\]\*nbtool8\.com:\\d\+/,REJECT.*\n",
        "",
        text,
        flags=re.M,
    )
    if "NB助手控制口勿硬 REJECT" not in text and "Reject-Hot.list,REJECT" in text:
        text = text.replace(
            "# 去广告：热点小表优先 + Reject-Merged 全量\n",
            "# 去广告：热点小表优先 + Reject-Merged 全量\n"
            "# NB助手控制口勿硬 REJECT（/nb/telnet=Network OK；IP 绕过用合集 Map Local）\n",
            1,
        )
    _write_if_changed(SURGE_CONF, text)


def ensure_reject_hot() -> None:
    """Rewrite Reject-Hot to SDK-only template (never nbtool8 control url_regex)."""
    _write_if_changed(REJECT_HOT, REJECT_HOT_TEMPLATE)


def verify() -> None:
    errors: list[str] = []
    ca = CUSTOM_APPS.read_text(encoding="utf-8")
    if "Network OK" not in ca or "124\\.222\\.32\\.246" not in ca:
        errors.append("custom-apps missing Network OK / IP Map Local")
    if "DST-PORT,9527" in ca:
        errors.append("custom-apps still has DST-PORT 9527 REJECT")
    ey = EGERN_YAML.read_text(encoding="utf-8")
    if "map_locals:" not in ey or "Network OK" not in ey:
        errors.append("Egern.yaml missing map_locals Network OK")
    if ey.count("map_locals:") != 1:
        errors.append("Egern.yaml map_locals count != 1")
    if re.search(r"dest_port:\s*\n\s*match:\s*[\"']9527[\"']", ey):
        errors.append("Egern.yaml still hard-rejects dest_port 9527")
    rh = REJECT_HOT.read_text(encoding="utf-8")
    if "url_regex" in rh or rh.count("no_resolve:") != 1:
        errors.append("Reject-Hot malformed or still has url_regex")
    for path in ADBLOCK_FILES:
        if not path.is_file():
            continue
        t = path.read_text(encoding="utf-8")
        if "Network OK" not in t or "124\\.222\\.32\\.246" not in t:
            errors.append(f"{path.name} missing Network OK / IP")
        if "DST-PORT,9527" in t:
            errors.append(f"{path.name} still has DST-PORT 9527 REJECT")
    if errors:
        raise SystemExit("apply-nb-ads-patch verify failed:\n- " + "\n- ".join(errors))
    print("apply-nb-ads-patch: ok")


def main() -> None:
    ensure_custom_apps()
    ensure_adblock_collections()
    ensure_egern_yaml()
    ensure_surge_conf()
    ensure_reject_hot()
    verify()


if __name__ == "__main__":
    main()
