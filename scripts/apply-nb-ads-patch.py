#!/usr/bin/env python3
"""Re-apply NB助手假成功 + 微信公众号 + 墨鱼 NBProAds patches after daily adblock merge.

Daily merge rebuilds Modules/adblock-collection.module from upstream + supplements.
custom-apps.sgmodule is local:true (source of truth), but heat/finalize and accidental
hard REJECT can still drift. This script forces:

1. custom-apps Map Local / URL Rewrite（仅 telnet=Network OK；禁止拦 /nb/app）
2. /nb/app → nbpro-ads script-response-body（墨鱼 AES 改广告字段）
3. Egern.yaml 原生 map_locals + NBPro scripting（合集 Surge 写法在 Egern 偶发不命中）
4. 去广告合集 Map Local + wxgzhad + nbpro-ads
5. Reject-Hot：SDK（含 NBProAds）+ Lentin 精准 wxa/wximg/wxsmw.wxs.qq.com（须在 Direct-Priority 前）
6. 主配置不挂独立微信模块；另提供 Modules/nb-weixin-fix.yaml 供不拉主配置时手动加

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

URL_REWRITE_BLOCK = r"""# NB全能助手 / NB Pro — 只拒开屏路径；telnet 假成功；/nb/app 走脚本（墨鱼 NBProAds）
^https?:\/\/(api\.|www\.|app\.)?nbtool8\.com(:\d+)?\/.*(splash|startup|launch|open[Ss]creen|welcome|banner|popup|promo|advert|/ad/|/ads/) - reject-dict
^https?:\/\/[^:/]*nbtool8\.com(:\d+)?\/.*(splash|startup|launch|banner|popup|advert|/ad/|/ads/) - reject-dict
^https?:\/\/[^:/]*nbtool8\.com(:\d+)?\/nb\/telnet data-type=text data="Network OK" status-code=200 header="Content-Type:text/plain"
^https?:\/\/124\.222\.32\.246(:\d+)?\/nb\/telnet data-type=text data="Network OK" status-code=200 header="Content-Type:text/plain"
^https?:\/\/117\.72\.39\.157(:\d+)?\/nb\/telnet data-type=text data="Network OK" status-code=200 header="Content-Type:text/plain"
^https?:\/\/47\.243\.71\.210(:\d+)?\/nb\/telnet data-type=text data="Network OK" status-code=200 header="Content-Type:text/plain"
^https?:\/\/cesapp\.goypzc\.cn(:\d+)?\/nb\/telnet data-type=text data="Network OK" status-code=200 header="Content-Type:text/plain"
"""

MAP_LOCAL_BLOCK = r"""# NB助手：仅 telnet=Network OK（/nb/app 用 nbpro-ads 脚本，勿空抓）
^https?:\/\/[^:/]*nbtool8\.com(:\d+)?\/nb\/telnet data-type=text data="Network OK" status-code=200 header="Content-Type:text/plain"
^https?:\/\/124\.222\.32\.246(:\d+)?\/nb\/telnet data-type=text data="Network OK" status-code=200 header="Content-Type:text/plain"
^https?:\/\/117\.72\.39\.157(:\d+)?\/nb\/telnet data-type=text data="Network OK" status-code=200 header="Content-Type:text/plain"
^https?:\/\/47\.243\.71\.210(:\d+)?\/nb\/telnet data-type=text data="Network OK" status-code=200 header="Content-Type:text/plain"
^https?:\/\/cesapp\.goypzc\.cn(:\d+)?\/nb\/telnet data-type=text data="Network OK" status-code=200 header="Content-Type:text/plain"
"""

NBPRO_SCRIPT_LINE = (
    "nbpro-ads = type=http-response, pattern="
    r"^https?:\/\/(?:[^:/]*nbtool8\.com|124\.222\.32\.246|117\.72\.39\.157|47\.243\.71\.210|cesapp\.goypzc\.cn)(?::\d+)?\/nb\/app"
    ", script-path=https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Scripts/ddgksf2013/nbpro.ads.js"
    ", requires-body=true, max-size=-1, timeout=60\n"
)

# Egern 原生 Map Local（合集 Surge 写法在 Egern 上偶发不命中；主配置钉死）
EGERN_MAP_LOCALS = r"""# NB助手 + 微信公众号 Map Local（须 MITM；/nb/app 用脚本勿空抓）
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
  - match: '^https?://117\.72\.39\.157(?::\d+)?/nb/telnet'
    status_code: 200
    headers:
      Content-Type: text/plain
    body: "Network OK"
  - match: '^https?://47\.243\.71\.210(?::\d+)?/nb/telnet'
    status_code: 200
    headers:
      Content-Type: text/plain
    body: "Network OK"
  - match: '^https?://cesapp\.goypzc\.cn(?::\d+)?/nb/telnet'
    status_code: 200
    headers:
      Content-Type: text/plain
    body: "Network OK"
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
  # 穿山甲 app_log：- reject 会回 404，SDK 秒级重试烫机；假成功停重试
  - match: '^https?://log-api\.pangolin-sdk-toutiao[-\w]*\.com(?:/.*)?'
    status_code: 200
    headers:
      Content-Type: application/json
    body: '{"code":0,"message":"success","magic_tag":"ss_app_log","server_time":1724220000,"data":{}}'
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
# 微信广告素材：Lentin 精准三域名（勿整域 wxs.qq.com，免误伤正文图）
# 接口空响应 / wxgzhad 在去广告合集（apply-nb-ads-patch）
#
# NB 控制口（nbtool8.com:9527 / 硬编码 IP）不要进本表 REJECT：
# /nb/telnet 返回 "Network OK"；去开屏见合集 Map Local。

no_resolve: true

domain_set:
  - open.e.kuaishou.cn
  - sdk.zhangyuyidong.cn
  - sdk6.zhangyuyidong.cn
  - v66-ad.ndcjl.com
  - wxsmsdy.video.qq.com
  # 微信公众号/小程序广告素材（Lentin；须先于 Direct-Priority 的 wxs DIRECT）
  - wxa.wxs.qq.com
  - wximg.wxs.qq.com
  - wxsmw.wxs.qq.com
  # NBPro 墨鱼版补充（ddgksf2013/NBProAds.conf；须 Reject-Hot 早拦，部分后缀在 China-Direct）
  - capsinfo.anythink.com
  - showtime.anythink.com
  - api.bridgeoos.com
  - pitk.birdgesdk.com
  - aa.birdgesdk.com
  - fusion-static.oss-cn-shenzhen.aliyuncs.com
  - mobads.baidu.com
  - cpu.baidu.com
  - cpu-openapi.baidu.com
  - mobads-pre-config.bj.bcebos.com
  - mobads-pre-config.cdn.bcebos.com
  - cpro.baidustatic.com
  - render-server.cdn.bcebos.com
  - adservice.sigmob.cn
  - api.htp.ad-scope.com.cn
  - bid.ad-scope.com.cn
  - api-htp.beizi.biz
  - sdk.beizi.biz
  - sdktmp.hubcloud.com.cn
  - sdkcfg.adintl.cn
  - test.s.adintl.cn
  - api-incentive.8ziben.com
  - static.8ziben.com
  - opehs.tanx.com
  - videoproxy.tanx.com
  - c.etoolads.cn
  - sdk.adx.adwangmai.com
  - sdk-cfg.adx.adwangmai.com
  - static.adwangmai.com
  - open.e.kuaishou.com
  - s.e.kuaishou.com

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
    # Surge 正则里点号常写成 \. ，剥离时要匹配字面反斜杠
    patterns = (
        r"^# NB全能助手.*\n",
        r"^# 截图实锤.*\n",
        r"^# 接口是 text/plain.*\n",
        r"^# 控制口假成功.*\n",
        r"^# telnet=Network OK.*\n",
        r"^# NB助手.*\n",
        r"^# NB：.*\n",
        r"^.*nbtool8\\?\.com.*\n",
        r"^.*124\\?\.222\\?\.32\\?\.246.*\n",
        r"^.*117\\?\.72\\?\.39\\?\.157.*\n",
        r"^.*47\\?\.243\\?\.71\\?\.210.*\n",
        r"^.*cesapp\\?\.goypzc\\?\.cn.*\n",
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


def _ensure_nbpro_script(text: str) -> str:
    """墨鱼 NBProAds：/nb/app AES 改广告字段（勿空 Map Local）。"""
    text = re.sub(
        r"^# NBPro /nb/app.*\n|^nbpro-ads\s*=\s*type=http-response,.*\n",
        "",
        text,
        flags=re.M,
    )
    line = (
        "# NBPro /nb/app：墨鱼版解密改广告字段再写回（勿空正文）\n"
        + NBPRO_SCRIPT_LINE
    )
    m = re.search(r"^\[Script\]\s*$", text, re.M)
    if m:
        rest = text[m.end() :]
        nxt = re.search(r"^\[(?:[A-Za-z][A-Za-z0-9 ]*)\]\s*$", rest, re.M)
        end = m.end() + (nxt.start() if nxt else len(rest))
        body = text[m.end() : end]
        if not body.startswith("\n"):
            body = "\n" + body
        body = "\n" + line + body.lstrip("\n")
        if not body.endswith("\n"):
            body += "\n"
        return text[: m.end()] + body + text[end:]

    mitm = re.search(r"^\[MITM\]\s*$", text, re.M)
    insert = f"\n[Script]\n{line}\n"
    if mitm:
        return text[: mitm.start()] + insert + text[mitm.start() :]
    return text.rstrip() + "\n" + insert


def patch_module_text(text: str) -> str:
    text = _strip_and_reject_nb(text)
    text = _strip_broken_fmz200_wx(text)
    text = _ensure_wxgzhad_script(text)
    text = _ensure_nbpro_script(text)
    text = _ensure_section_block(text, "URL Rewrite", URL_REWRITE_BLOCK)
    text = _ensure_section_block(
        text,
        "Map Local",
        MAP_LOCAL_COMBINED,
        stripper=_strip_map_local_managed,
    )
    note = (
        "# NB 控制口勿 AND REJECT：/nb/telnet=Network OK；"
        "/nb/app 用脚本改广告；域名拦了会改走硬编码 IP\n"
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

    # NBPro /nb/app 脚本（墨鱼；须 MITM）
    nbpro_block = (
        "  - http_response:\n"
        "      name: NBPro去广告\n"
        "      match: '^https?://(?:[^/]*nbtool8\\.com|124\\.222\\.32\\.246|117\\.72\\.39\\.157|"
        "47\\.243\\.71\\.210|cesapp\\.goypzc\\.cn)(?::\\d+)?/nb/app'\n"
        "      script_url: https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/"
        "Scripts/ddgksf2013/nbpro.ads.js\n"
        "      body_required: true\n"
        "      max_size: -1\n"
        "      timeout: 60\n"
        "      update_interval: 3600\n"
    )
    text = re.sub(
        r"\n  - http_response:\n"
        r"      name: NBPro去广告\n"
        r"(?:      .*\n)+?",
        "\n",
        text,
        count=1,
    )
    if "name: 微信公众号广告" in text and "name: NBPro去广告" not in text:
        text = text.replace(
            "      update_interval: 3600\n\nmitm:",
            "      update_interval: 3600\n" + nbpro_block + "\nmitm:",
            1,
        )
        if "name: NBPro去广告" not in text:
            text = text.replace(
                "scriptings:\n",
                "scriptings:\n" + nbpro_block,
                1,
            )

    # MITM：墨鱼 hostname + 控制口 IP
    for host in (
        "cesapp.goypzc.cn",
        "124.222.32.246",
        "117.72.39.157",
        "47.243.71.210",
    ):
        needle = f"      - {host}\n"
        if needle not in text and "app.nbtool8.com" in text:
            text = text.replace(
                "      - app.nbtool8.com\n",
                f"      - app.nbtool8.com\n{needle}",
                1,
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
    """Rewrite Reject-Hot（含 Lentin 精准微信 CDN；永不含 nbtool8 控制口）。"""
    _write_if_changed(REJECT_HOT, REJECT_HOT_TEMPLATE)


def verify() -> None:
    errors: list[str] = []
    ca = CUSTOM_APPS.read_text(encoding="utf-8")
    if "Network OK" not in ca or "124\\.222\\.32\\.246" not in ca:
        errors.append("custom-apps missing Network OK / IP Map Local")
    if "nbpro-ads" not in ca or "nbpro.ads.js" not in ca:
        errors.append("custom-apps missing nbpro-ads script")
    if "capsinfo.anythink.com" not in ca or "c.etoolads.cn" not in ca:
        errors.append("custom-apps missing NBProAds SDK hosts")
    if "DOMAIN,wxa.wxs.qq.com,REJECT" not in ca:
        errors.append("custom-apps missing Lentin WeChat CDN # @keep rules")
    if re.search(r"nbtool8.*data=\"\"|124\\.222\\.32\\.246.*data=\"\"", ca):
        errors.append("custom-apps still has empty-body NB Map Local (causes format error)")
    if re.search(r"/nb/app[^\n]*data=", ca):
        errors.append("custom-apps must not Map Local /nb/app")
    if "DST-PORT,9527" in ca:
        errors.append("custom-apps still has DST-PORT 9527 REJECT")
    ey = EGERN_YAML.read_text(encoding="utf-8")
    if "map_locals:" not in ey or "Network OK" not in ey:
        errors.append("Egern.yaml missing map_locals Network OK")
    if ey.count("map_locals:") != 1:
        errors.append("Egern.yaml map_locals count != 1")
    ml = re.search(r"^map_locals:\n((?:  .*\n)*)", ey, re.M)
    if ml and "/nb/app" in ml.group(1):
        errors.append("Egern.yaml must not Map Local /nb/app (causes NB format error)")
    if "name: NBPro去广告" not in ey or "nbpro.ads.js" not in ey:
        errors.append("Egern.yaml missing NBPro scripting")
    if "getappmsgad" not in ey:
        errors.append("Egern.yaml missing WeChat getappmsgad map_local")
    if "ads-map-local.yaml" in ey or "weixin-mp-ads.yaml" in ey:
        errors.append("Egern.yaml still lists separate weixin/ads-map-local module")
    if re.search(r"dest_port:\s*\n\s*match:\s*[\"']9527[\"']", ey):
        errors.append("Egern.yaml still hard-rejects dest_port 9527")
    if "cesapp.goypzc.cn" not in ey:
        errors.append("Egern.yaml missing cesapp MITM hostname")
    rh = REJECT_HOT.read_text(encoding="utf-8")
    if "url_regex" in rh or rh.count("no_resolve:") != 1:
        errors.append("Reject-Hot malformed or still has url_regex")
    if "wxa.wxs.qq.com" not in rh or "wximg.wxs.qq.com" not in rh:
        errors.append("Reject-Hot missing Lentin WeChat CDN hosts")
    if re.search(r"^\s*-\s*wxs\.qq\.com\s*$", rh, re.M):
        errors.append("Reject-Hot must not whole-suffix reject wxs.qq.com")
    if "capsinfo.anythink.com" not in rh or "c.etoolads.cn" not in rh:
        errors.append("Reject-Hot missing NBProAds SDK hosts")
    for path in ADBLOCK_FILES:
        if not path.is_file():
            continue
        t = path.read_text(encoding="utf-8")
        if "Network OK" not in t or "124\\.222\\.32\\.246" not in t:
            errors.append(f"{path.name} missing Network OK / IP")
        if "DOMAIN,wxa.wxs.qq.com,REJECT" not in t:
            errors.append(f"{path.name} missing Lentin WeChat CDN rules")
        if re.search(r"^[^#\n]*/nb/app[^\n]*data=", t, re.M):
            errors.append(f"{path.name} still Map Locals /nb/app (remove it)")
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
        if "nbpro-ads" not in t and "nbpro.ads.js" not in t:
            errors.append(f"{path.name} missing nbpro-ads script")
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
