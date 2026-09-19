#!/usr/bin/env python3
"""Re-apply NB助手假成功 + 微信公众号 patches after daily adblock merge.

Daily merge rebuilds Modules/adblock-collection.module from upstream + supplements.
custom-apps.sgmodule is local:true (source of truth), but heat/finalize and accidental
hard REJECT can still drift. This script forces:

1. custom-apps Map Local / URL Rewrite（telnet=Network OK；/nb/app={} JSON，禁空正文）
2. Egern.yaml 原生 map_locals（合集 Surge Map Local 在 Egern 偶发不命中）
3. 去广告合集 Map Local + wxgzhad
4. Reject-Hot：SDK + QingRex 同款 wxs.qq.com（须在 Direct-Priority 前）
5. 主配置不挂独立微信模块

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

URL_REWRITE_BLOCK = r"""# NB全能助手 / NB Pro — 开屏广告路径拒掉；控制口假成功（勿空抓全部）
^https?:\/\/(api\.|www\.|app\.)?nbtool8\.com(:\d+)?\/.*(splash|startup|launch|open[Ss]creen|welcome|banner|popup|promo|advert|/ad/|/ads/) - reject-dict
^https?:\/\/[^:/]*nbtool8\.com(:\d+)?\/.*(splash|startup|launch|banner|popup|advert|/ad/|/ads/) - reject-dict
# telnet=Network OK；/nb/app 返回空 JSON（空正文会「格式不正确」）
^https?:\/\/[^:/]*nbtool8\.com(:\d+)?\/nb\/telnet data-type=text data="Network OK" status-code=200 header="Content-Type:text/plain"
^https?:\/\/124\.222\.32\.246(:\d+)?\/nb\/telnet data-type=text data="Network OK" status-code=200 header="Content-Type:text/plain"
^https?:\/\/[^:/]*nbtool8\.com(:\d+)?\/nb\/app data-type=text data="{}" status-code=200 header="Content-Type:application/json"
^https?:\/\/124\.222\.32\.246(:\d+)?\/nb\/app data-type=text data="{}" status-code=200 header="Content-Type:application/json"
"""

MAP_LOCAL_BLOCK = r"""# NB助手：假成功去开屏（勿硬 REJECT；勿用空正文；含 IP 绕过）
^https?:\/\/[^:/]*nbtool8\.com(:\d+)?\/nb\/telnet data-type=text data="Network OK" status-code=200 header="Content-Type:text/plain"
^https?:\/\/124\.222\.32\.246(:\d+)?\/nb\/telnet data-type=text data="Network OK" status-code=200 header="Content-Type:text/plain"
^https?:\/\/[^:/]*nbtool8\.com(:\d+)?\/nb\/app data-type=text data="{}" status-code=200 header="Content-Type:application/json"
^https?:\/\/124\.222\.32\.246(:\d+)?\/nb\/app data-type=text data="{}" status-code=200 header="Content-Type:application/json"
"""

# Egern 原生 Map Local（合集 Surge 写法在 Egern 上偶发不命中；主配置钉死）
EGERN_MAP_LOCALS = r"""# NB助手 + 微信公众号 Map Local（须 MITM；勿空正文否则 NB「格式不正确」）
map_locals:
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
  - match: '^https?://[^/]*nbtool8\.com(?::\d+)?/nb/app'
    status_code: 200
    headers:
      Content-Type: application/json
    body: "{}"
  - match: '^https?://124\.222\.32\.246(?::\d+)?/nb/app'
    status_code: 200
    headers:
      Content-Type: application/json
    body: "{}"
  - match: '^https?://mp\.weixin\.qq\.com(?::\d+)?/mp/getappmsgad'
    status_code: 200
    headers:
      Content-Type: application/json
    body: '{"advertisement_num":0,"advertisement_info":[]}'
  - match: '^https?://mp\.weixin\.qq\.com(?::\d+)?/mp/(cps_product_info|jsmonitor|masonryfeed|relatedarticle|relatedsearchword|searchkeywordreport)'
    status_code: 200
    headers:
      Content-Type: application/json
    body: '{}'
  - match: '^https?://mp\.weixin\.qq\.com(?::\d+)?/tp/datareport'
    status_code: 200
    headers:
      Content-Type: application/json
    body: '{}'
"""

# Surge/合集 Map Local：公众号（与 QingRex / chxm1023 同源，合集日更后仍钉死）
WEIXIN_MAP_LOCAL_BLOCK = r"""# 微信公众号：兼容 :443 / http(s) / 无 query（对齐 QingRex；Egern 另有原生 map_locals）
^https?:\/\/mp\.weixin\.qq\.com(:\d+)?\/mp\/getappmsgad data-type=text data="{\"advertisement_num\":0,\"advertisement_info\":[]}" status-code=200 header="Content-Type:application/json"
^https?:\/\/mp\.weixin\.qq\.com(:\d+)?\/mp\/(cps_product_info|jsmonitor|masonryfeed|relatedarticle|relatedsearchword) data-type=text data="{}" status-code=200 header="Content-Type:application/json"
"""

# 奶思残缺 Body Rewrite：把 advertisement 字面替换成 fmz200，会弄坏 JSON；改由 Map Local/脚本处理
BROKEN_FMZ200_WX_LINE = (
    r"^http-response \^https\?:\\/\\/mp\\.weixin\\.qq\\.com\\/mp\\/getappmsgad "
    r"advertisement fmz200\n"
)

REJECT_HOT_TEMPLATE = r"""# 热点去广告（须排在 Direct-Priority 之前）
# 含 QingRex 同款：DOMAIN-SUFFIX wxs.qq.com → 公众号广告卡片在、图/视频黑
# 完整清单仍在 Reject-Merged；Map Local / 脚本在去广告合集（apply-nb-ads-patch）
#
# NB 控制口（nbtool8.com:9527 / 硬编码 IP）不要进本表 REJECT：
# /nb/telnet 返回 "Network OK"；去开屏见合集 Map Local。

no_resolve: true

domain_set:
  - open.e.kuaishou.cn
  - sdk.zhangyuyidong.cn
  - v66-ad.ndcjl.com
  # 微信小程序广告素材（QingRex 微信小程序去广告）
  - wxsmsdy.video.qq.com

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
  # 微信公众号广告 CDN（QingRex 微信公众号去广告；须先于 Direct-Priority 的 wxs DIRECT）
  - wxs.qq.com

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
    # Surge 正则里点号常写成 \. ，剥离时要匹配字面反斜杠
    patterns = (
        r"^# NB全能助手.*\n",
        r"^# 截图实锤.*\n",
        r"^# 接口是 text/plain.*\n",
        r"^# 控制口假成功.*\n",
        r"^# telnet=Network OK.*\n",
        r"^# NB助手.*\n",
        r"^.*nbtool8\\?\.com.*\n",
        r"^.*124\\?\.222\\?\.32\\?\.246.*\n",
    )
    for pat in patterns:
        section = re.sub(pat, "", section, flags=re.M)
    return section


def _strip_weixin_map_local_lines(section: str) -> str:
    patterns = (
        r"^# 微信公众号.*\n",
        r"^# 公众号底栏.*\n",
        r"^# getappmsgad：.*\n",
        r"^# 小程序广告素材.*\n",
        r"^.*mp\\?\.weixin\\?\.qq\\?\.com.*getappmsgad.*\n",
        r"^.*mp\\?\.weixin\\?\.qq\\?\.com.*(cps_product_info|jsmonitor|masonryfeed|relatedarticle|relatedsearchword).*\n",
        r"^.*wxs\\?\.qq\\?\.com.*snscosdownload.*\n",
    )
    for pat in patterns:
        section = re.sub(pat, "", section, flags=re.M)
    return section


def _strip_map_local_managed(section: str) -> str:
    """Strip both NB + WeChat Map Local lines we manage."""
    return _strip_weixin_map_local_lines(_strip_nb_url_lines(section))


MAP_LOCAL_COMBINED = WEIXIN_MAP_LOCAL_BLOCK + MAP_LOCAL_BLOCK


def _strip_broken_fmz200_wx(text: str) -> str:
    return re.sub(BROKEN_FMZ200_WX_LINE, "", text, flags=re.M)


def _ensure_section_block(
    text: str,
    section: str,
    block: str,
    *,
    stripper=_strip_nb_url_lines,
    prepend: bool = True,
) -> str:
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
    body = stripper(text[m.end() : end])
    if section == "URL Rewrite" and "# 得力e+" in body:
        body = body.replace("# 得力e+", block + "\n# 得力e+", 1)
    elif prepend:
        body = "\n" + block + ("\n" if not body.startswith("\n") else "") + body.lstrip("\n")
        if not body.endswith("\n"):
            body += "\n"
    else:
        body = body.rstrip("\n") + "\n" + block
        if not body.endswith("\n"):
            body += "\n"
    return text[: m.end()] + body + text[end:]


def _ensure_wxgzhad_script(text: str) -> str:
    """Widen wxgzhad to getappmsgext + optional :port."""
    widened = (
        r"^https?:\/\/mp\.weixin\.qq\.com(:\d+)?\/mp\/(getappmsgad|getappmsgext),"
    )

    def _repl_named(m: re.Match[str]) -> str:
        return m.group(1) + widened

    text = re.sub(
        r"(wxgzhad\s*=\s*type=http-response,\s*pattern=)\S+",
        _repl_named,
        text,
    )

    def _repl_http(m: re.Match[str]) -> str:
        return (
            m.group(1)
            + r"(:\d+)?\/mp\/(getappmsgad|getappmsgext)"
            + m.group(2)
        )

    text = re.sub(
        r"(http-response \^https\?:\\/\\/mp\\.weixin\\.qq\\.com)"
        r"(?:\(:\\d\+\?\))?\\/mp\\/(?:\(getappmsgad\|getappmsgext\)|getappmsgad)(\s)",
        _repl_http,
        text,
    )
    return text


def patch_module_text(text: str) -> str:
    text = _strip_and_reject_nb(text)
    text = _strip_broken_fmz200_wx(text)
    text = _ensure_wxgzhad_script(text)
    text = _ensure_section_block(text, "URL Rewrite", URL_REWRITE_BLOCK)
    text = _ensure_section_block(
        text,
        "Map Local",
        MAP_LOCAL_COMBINED,
        stripper=_strip_map_local_managed,
    )
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
        "Map Local 在主配置 + 合集（apply-nb-ads-patch）\n",
        text,
        count=1,
    )

    # 主配置钉死 Map Local（Egern 对合集 Surge Map Local 偶发不命中）
    text = re.sub(
        r"\n# (?:NB助手|Map Local)[^\n]*\n(?:# [^\n]*\n)*map_locals:\n"
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

    # 去掉独立微信/Map Local 模块（已并进合集 + 主配置 map_locals）
    text = re.sub(
        r"\n  # (?:公众号去广告|NB开屏).*?\n"
        r"  - name: (?:微信公众号去广告|广告 Map Local)\n"
        r"    url: https://raw\.githubusercontent\.com/oo226/egern-config/refs/heads/main/Modules/(?:weixin-mp-ads|ads-map-local)\.yaml\n"
        r"    update_interval: \d+\n"
        r"    enabled: true\n",
        "\n",
        text,
        count=1,
    )

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
    """Rewrite Reject-Hot（含 QingRex 同款 wxs.qq.com；永不含 nbtool8 控制口）。"""
    _write_if_changed(REJECT_HOT, REJECT_HOT_TEMPLATE)


def verify() -> None:
    errors: list[str] = []
    ca = CUSTOM_APPS.read_text(encoding="utf-8")
    if "Network OK" not in ca or "124\\.222\\.32\\.246" not in ca:
        errors.append("custom-apps missing Network OK / IP Map Local")
    if re.search(r"nbtool8.*data=\"\"|124\\.222\\.32\\.246.*data=\"\"", ca):
        errors.append("custom-apps still has empty-body NB Map Local (causes format error)")
    if "DST-PORT,9527" in ca:
        errors.append("custom-apps still has DST-PORT 9527 REJECT")
    ey = EGERN_YAML.read_text(encoding="utf-8")
    if "map_locals:" not in ey or "Network OK" not in ey:
        errors.append("Egern.yaml missing map_locals Network OK")
    if ey.count("map_locals:") != 1:
        errors.append("Egern.yaml map_locals count != 1")
    if 'body: "{}"' not in ey and "body: '{}'" not in ey:
        errors.append("Egern.yaml /nb/app should return {} JSON not empty")
    if "getappmsgad" not in ey:
        errors.append("Egern.yaml missing WeChat getappmsgad map_local")
    if "ads-map-local.yaml" in ey or "weixin-mp-ads.yaml" in ey:
        errors.append("Egern.yaml still lists separate weixin/ads-map-local module")
    if re.search(r"dest_port:\s*\n\s*match:\s*[\"']9527[\"']", ey):
        errors.append("Egern.yaml still hard-rejects dest_port 9527")
    rh = REJECT_HOT.read_text(encoding="utf-8")
    if "url_regex" in rh or rh.count("no_resolve:") != 1:
        errors.append("Reject-Hot malformed or still has url_regex")
    if "wxs.qq.com" not in rh:
        errors.append("Reject-Hot missing wxs.qq.com (QingRex-style creative reject)")
    for path in ADBLOCK_FILES:
        if not path.is_file():
            continue
        t = path.read_text(encoding="utf-8")
        if "Network OK" not in t or "124\\.222\\.32\\.246" not in t:
            errors.append(f"{path.name} missing Network OK / IP")
        if re.search(r"nbtool8[^\n]*data=\"\"|124\\.222\\.32\\.246[^\n]*data=\"\"", t):
            errors.append(f"{path.name} still has empty-body NB Map Local")
        if "DST-PORT,9527" in t:
            errors.append(f"{path.name} still has DST-PORT 9527 REJECT")
        if "advertisement fmz200" in t:
            errors.append(f"{path.name} still has broken fmz200 WeChat body rewrite")
        if r"mp\.weixin\.qq\.com(:\d+)?" not in t:
            errors.append(f"{path.name} missing :443-safe WeChat Map Local")
        if "wxgzhad" not in t and "getappmsgad|getappmsgext" not in t:
            errors.append(f"{path.name} missing wxgzhad script")
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
