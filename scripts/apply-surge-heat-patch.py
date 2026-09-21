#!/usr/bin/env python3
"""Re-apply Surge 防烫 (heat) patches after daily adblock merge.

Daily `merge-adblock-modules.py Modules/manifest.surge.yaml` regenerates
surge/Modules/adblock-collection.module from upstream and would wipe hand-tuned
anti-retry fixes. This script re-applies those fixes so publish never ships
empty reject-200 / hard REJECT for pangolin log-api, api-access stats, JPush.
"""

from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADBLOCK = ROOT / "surge" / "Modules" / "adblock-collection.module"
EGERN_ADBLOCK = ROOT / "Modules" / "adblock-collection.module"
PIPIXIA_HEAT = ROOT / "surge" / "Modules" / "pipixia-heat.sgmodule"
BYTEDANCE_HEAT = ROOT / "surge" / "Rules" / "ByteDance-Heat.list"
APP_HEAT = ROOT / "surge" / "Rules" / "App-Heat.list"
APP_HEAT_MODULE = ROOT / "surge" / "Modules" / "app-heat.sgmodule"
PANGOLIN_SCRIPT = ROOT / "surge" / "Scripts" / "pangolin-fake-log.js"
TG_MITM_HEAT = ROOT / "surge" / "Modules" / "tg-mitm-heat.sgmodule"
SURGE_CONF = ROOT / "surge" / "Surge.conf"

HEAT_MARKER = "heat16"
SCRIPT_URL = (
    "https://raw.githubusercontent.com/oo226/egern-config/refs/heads/surge/"
    "Scripts/pangolin-fake-log.js"
)

# 裸 IP + Telegram 域名前置 SNI（www.google.com）一律不解密。
BARE_IP_MITM_INSERT = (
    "hostname = %INSERT% -<ip-address>:0, -www.google.com, -www.google.com.hk"
)
TG_FRONTING_MITM_HOSTS = frozenset({"www.google.com", "www.google.com.hk"})

REQUIRED_MARKERS = (
    "DOMAIN,stats.jpush.cn,DIRECT",
    "DOMAIN,is-lq.snssdk.com,DIRECT",
    "pangolin-fake-log",
    "(?!log-api\\.)(?!api-access\\.)",
    "jpush-fake-stats",
    BARE_IP_MITM_INSERT,
)

DIRECT_BLOCK = """\
# heat5：字节埋点硬 REJECT 会立刻重试（最近请求一直跳）。
# 先 DIRECT，交给 Map Local / Script 有 body 假成功（勿用空 reject-200）。
# i-lq / is-lq snssdk settings 放行真实配置，不要假空包。
DOMAIN,mon.snssdk.com,DIRECT
DOMAIN,mon.zijieapi.com,DIRECT
DOMAIN,toblog.ctobsnssdk.com,DIRECT
DOMAIN,i-lq.snssdk.com,DIRECT
DOMAIN,is-lq.snssdk.com,DIRECT
DOMAIN,log.snssdk.com,DIRECT
DOMAIN,extlog.snssdk.com,DIRECT
DOMAIN,mcs.snssdk.com,DIRECT
DOMAIN,xlog.snssdk.com,DIRECT
DOMAIN,applog.zijieapi.com,DIRECT
DOMAIN,log-api.pangolin-sdk-toutiao.com,DIRECT
DOMAIN,log-api.pangolin-sdk-toutiao1.com,DIRECT
DOMAIN,log-api.pangolin-sdk-toutiao-b.com,DIRECT
DOMAIN,gromore.pangolin-sdk-toutiao.com,DIRECT
DOMAIN,api-access.pangolin-sdk-toutiao.com,DIRECT
DOMAIN,api-access.pangolin-sdk-toutiao1.com,DIRECT
DOMAIN,api-access.pangolin-sdk-toutiao-b.com,DIRECT
DOMAIN,stats.jpush.cn,DIRECT
DOMAIN,gd-stats.jpush.cn,DIRECT
DOMAIN,ali-stats.jpush.cn,DIRECT
# heat11：doudou TTS 一秒十几条已完成 DIRECT → 烫机；假成功，勿硬 REJECT
DOMAIN,tts.doudou520.online,DIRECT
DOMAIN-SUFFIX,doudou520.online,DIRECT
"""

SCRIPT_BLOCK = f"""\
# heat8：http-request 短路返回有 body 的假成功（比空 reject-200 可靠）
pangolin-fake-log = type=http-request,pattern=^https?:\\/\\/log-api\\.pangolin-sdk-toutiao,script-path={SCRIPT_URL},requires-body=0,max-size=0,timeout=5
pangolin-api-access = type=http-request,pattern=^https?:\\/\\/api-access\\.pangolin-sdk-toutiao,script-path={SCRIPT_URL},requires-body=0,max-size=0,timeout=5
jpush-fake-stats = type=http-request,pattern=^https?:\\/\\/(stats|gd-stats|ali-stats)\\.jpush\\.cn,script-path={SCRIPT_URL},requires-body=0,max-size=0,timeout=5
toblog-fake-log = type=http-request,pattern=^https?:\\/\\/toblog\\.ctobsnssdk\\.com,script-path={SCRIPT_URL},requires-body=0,max-size=0,timeout=5
applog-zijie-fake = type=http-request,pattern=^https?:\\/\\/applog\\.zijieapi\\.com,script-path={SCRIPT_URL},requires-body=0,max-size=0,timeout=5
"""

MAP_LOCAL_BLOCK = r"""
# heat8：base64 有 body（reject-200 空包会狂重试）；ss_app_log 格式
^https?:\/\/log-api\.pangolin-sdk-toutiao[-\w]*\.com\/service\/2\/app_log data-type=base64 data="eyJjb2RlIjowLCJtZXNzYWdlIjoic3VjY2VzcyIsIm1hZ2ljX3RhZyI6InNzX2FwcF9sb2ciLCJzZXJ2ZXJfdGltZSI6MTcyNDIyMDAwMCwiZGF0YSI6e319" status-code=200 header="Content-Type:application/json"
^https?:\/\/log-api\.pangolin-sdk-toutiao[-\w]*\.com data-type=base64 data="eyJjb2RlIjowLCJtZXNzYWdlIjoic3VjY2VzcyIsIm1hZ2ljX3RhZyI6InNzX2FwcF9sb2ciLCJzZXJ2ZXJfdGltZSI6MTcyNDIyMDAwMCwiZGF0YSI6e319" status-code=200 header="Content-Type:application/json"
# heat9：api-access stats/batch 有 body（禁空 reject-200）
^https?:\/\/api-access\.pangolin-sdk-toutiao[-\w]*\.com\/api\/ad\/union\/sdk\/stats data-type=base64 data="eyJjb2RlIjowLCJtZXNzYWdlIjoic3VjY2VzcyIsImRhdGEiOnt9fQ==" status-code=200 header="Content-Type:application/json"
# heat9：JPush stats 有 body
^https?:\/\/(stats|gd-stats|ali-stats)\.jpush\.cn data-type=base64 data="eyJjb2RlIjowLCJtZXNzYWdlIjoic3VjY2VzcyJ9" status-code=200 header="Content-Type:application/json"
# heat5 字节埋点假 200（合集内处理，不依赖小模块）
^https?:\/\/mon\.snssdk\.com\/monitor data-type=text data="{}" status-code=200 header="Content-Type:application/json"
^https?:\/\/mon\.zijieapi\.com data-type=text data="{}" status-code=200 header="Content-Type:application/json"
^https?:\/\/toblog\.ctobsnssdk\.com data-type=base64 data="eyJtZXNzYWdlIjoic3VjY2VzcyIsImNvZGUiOjAsImRldmljZV9pZCI6MSwiaW5zdGFsbF9pZCI6MSwic3NpZCI6IjAifQ==" status-code=200 header="Content-Type:application/json"
# heat15：applog.zijieapi 皮皮虾狂刷 TCP Dial Failed → 假成功（须 MITM）
^https?:\/\/applog\.zijieapi\.com data-type=base64 data="eyJtZXNzYWdlIjoic3VjY2VzcyIsImNvZGUiOjAsImRldmljZV9pZCI6MSwiaW5zdGFsbF9pZCI6MSwic3NpZCI6IjAifQ==" status-code=200 header="Content-Type:application/json"
# heat11：doudou TTS 狂刷假成功
^https?:\/\/tts\.doudou520\.online data-type=text data="{}" status-code=200 header="Content-Type:application/json"
^https?:\/\/([-\w]+\.)*doudou520\.online data-type=text data="{}" status-code=200 header="Content-Type:application/json"
""".lstrip(
    "\n"
)

BYTEDANCE_LIST = """\
# 字节埋点：不要硬 REJECT（会立刻重试，最近请求一直跳）。
# 策略 DIRECT 后由去广告合集 / pipixia-heat 的 Map Local / Script 有 body 假成功（禁空 reject-200）。
# i-lq / is-lq snssdk 放行 settings（真实 200）；不要对 /service/settings 假空包。
DOMAIN,mon.snssdk.com,extended-matching
DOMAIN,mon.zijieapi.com,extended-matching
DOMAIN,toblog.ctobsnssdk.com,extended-matching
DOMAIN,applog.zijieapi.com,extended-matching
DOMAIN,i-lq.snssdk.com,extended-matching
DOMAIN,is-lq.snssdk.com,extended-matching
DOMAIN,log-api.pangolin-sdk-toutiao.com,extended-matching
DOMAIN,log-api.pangolin-sdk-toutiao1.com,extended-matching
DOMAIN,log-api.pangolin-sdk-toutiao-b.com,extended-matching
DOMAIN,api-access.pangolin-sdk-toutiao.com,extended-matching
DOMAIN,api-access.pangolin-sdk-toutiao1.com,extended-matching
DOMAIN,api-access.pangolin-sdk-toutiao-b.com,extended-matching
DOMAIN,stats.jpush.cn,extended-matching
DOMAIN,gd-stats.jpush.cn,extended-matching
DOMAIN,ali-stats.jpush.cn,extended-matching
"""

PIPIXIA_HEAT_MODULE = f"""\
#!name=皮皮虾防烫（Surge）
#!desc={HEAT_MARKER} · Map Local有body · 每日合并后由 apply-surge-heat-patch 保持
# UPDATE-MARKER {HEAT_MARKER}
#!category=Surge专用

# 大合集经常「已是最新」刷不动时，单独装本小模块即可。
# heat9：JPush stats + api-access stats/batch 勿用空 reject-200。

[Script]
pangolin-fake-log = type=http-request,pattern=^https?:\\/\\/log-api\\.pangolin-sdk-toutiao,script-path={SCRIPT_URL},requires-body=0,max-size=0,timeout=5
pangolin-api-access = type=http-request,pattern=^https?:\\/\\/api-access\\.pangolin-sdk-toutiao,script-path={SCRIPT_URL},requires-body=0,max-size=0,timeout=5
toblog-fake-log = type=http-request,pattern=^https?:\\/\\/toblog\\.ctobsnssdk\\.com,script-path={SCRIPT_URL},requires-body=0,max-size=0,timeout=5
jpush-fake-stats = type=http-request,pattern=^https?:\\/\\/(stats|gd-stats|ali-stats)\\.jpush\\.cn,script-path={SCRIPT_URL},requires-body=0,max-size=0,timeout=5
applog-zijie-fake = type=http-request,pattern=^https?:\\/\\/applog\\.zijieapi\\.com,script-path={SCRIPT_URL},requires-body=0,max-size=0,timeout=5

[Map Local]
^https?:\\/\\/log-api\\.pangolin-sdk-toutiao[-\\w]*\\.com\\/service\\/2\\/app_log data-type=base64 data="eyJjb2RlIjowLCJtZXNzYWdlIjoic3VjY2VzcyIsIm1hZ2ljX3RhZyI6InNzX2FwcF9sb2ciLCJzZXJ2ZXJfdGltZSI6MTcyNDIyMDAwMCwiZGF0YSI6e319" status-code=200 header="Content-Type:application/json"
^https?:\\/\\/log-api\\.pangolin-sdk-toutiao[-\\w]*\\.com data-type=base64 data="eyJjb2RlIjowLCJtZXNzYWdlIjoic3VjY2VzcyIsIm1hZ2ljX3RhZyI6InNzX2FwcF9sb2ciLCJzZXJ2ZXJfdGltZSI6MTcyNDIyMDAwMCwiZGF0YSI6e319" status-code=200 header="Content-Type:application/json"
^https?:\\/\\/api-access\\.pangolin-sdk-toutiao[-\\w]*\\.com\\/api\\/ad\\/union\\/sdk\\/stats data-type=base64 data="eyJjb2RlIjowLCJtZXNzYWdlIjoic3VjY2VzcyIsImRhdGEiOnt9fQ==" status-code=200 header="Content-Type:application/json"
^https?:\\/\\/mon\\.snssdk\\.com\\/monitor data-type=text data="{{}}" status-code=200 header="Content-Type:application/json"
^https?:\\/\\/mon\\.zijieapi\\.com data-type=text data="{{}}" status-code=200 header="Content-Type:application/json"
^https?:\\/\\/toblog\\.ctobsnssdk\\.com data-type=base64 data="eyJtZXNzYWdlIjoic3VjY2VzcyIsImNvZGUiOjAsImRldmljZV9pZCI6MSwiaW5zdGFsbF9pZCI6MSwic3NpZCI6IjAifQ==" status-code=200 header="Content-Type:application/json"
^https?:\\/\\/applog\\.zijieapi\\.com data-type=base64 data="eyJtZXNzYWdlIjoic3VjY2VzcyIsImNvZGUiOjAsImRldmljZV9pZCI6MSwiaW5zdGFsbF9pZCI6MSwic3NpZCI6IjAifQ==" status-code=200 header="Content-Type:application/json"
^https?:\\/\\/(stats|gd-stats|ali-stats)\\.jpush\\.cn data-type=base64 data="eyJjb2RlIjowLCJtZXNzYWdlIjoic3VjY2VzcyJ9" status-code=200 header="Content-Type:application/json"
^https?:\\/\\/sdk\\.e\\.qq\\.com data-type=text data="{{}}" status-code=200 header="Content-Type:application/json"
^https?:\\/\\/snowflake\\.qq\\.com\\/ola data-type=text data="{{}}" status-code=200 header="Content-Type:application/json"
^https?:\\/\\/mobads-logs\\.baidu\\.com data-type=text data="{{}}" status-code=200 header="Content-Type:application/json"

[Rule]
DOMAIN,mon.snssdk.com,DIRECT
DOMAIN,mon.zijieapi.com,DIRECT
DOMAIN,toblog.ctobsnssdk.com,DIRECT
DOMAIN,applog.zijieapi.com,DIRECT
DOMAIN,i-lq.snssdk.com,DIRECT
DOMAIN,is-lq.snssdk.com,DIRECT
DOMAIN,log-api.pangolin-sdk-toutiao.com,DIRECT
DOMAIN,log-api.pangolin-sdk-toutiao1.com,DIRECT
DOMAIN,log-api.pangolin-sdk-toutiao-b.com,DIRECT
DOMAIN,api-access.pangolin-sdk-toutiao.com,DIRECT
DOMAIN,api-access.pangolin-sdk-toutiao1.com,DIRECT
DOMAIN,api-access.pangolin-sdk-toutiao-b.com,DIRECT
DOMAIN,stats.jpush.cn,DIRECT
DOMAIN,gd-stats.jpush.cn,DIRECT
DOMAIN,ali-stats.jpush.cn,DIRECT

[MITM]
hostname = %INSERT% -<ip-address>:0, -www.google.com, -www.google.com.hk
hostname = %APPEND% log-api.pangolin-sdk-toutiao.com, log-api.pangolin-sdk-toutiao1.com, log-api.pangolin-sdk-toutiao-b.com, api-access.pangolin-sdk-toutiao.com, api-access.pangolin-sdk-toutiao1.com, api-access.pangolin-sdk-toutiao-b.com, gromore.pangolin-sdk-toutiao.com, mon.snssdk.com, mon.zijieapi.com, toblog.ctobsnssdk.com, applog.zijieapi.com, i-lq.snssdk.com, stats.jpush.cn, gd-stats.jpush.cn, ali-stats.jpush.cn, sdk.e.qq.com, snowflake.qq.com, mobads-logs.baidu.com
"""

TG_MITM_HEAT_MODULE = """\
#!name=Telegram 防烫（Surge）
#!desc=heat16 · 裸 IP + www.google.com SNI 跳过 MitM，打断 TLS/MitM 狂重试
# UPDATE-MARKER heat16-tg-mitm
#!category=Surge专用

# 最近请求里 194.221.250.50 (www.google.com) :443/:80/:5222 狂刷 TLS 连接失败 → 烫机。
# 根因：Telegram 裸 IP + 证书钉扎，且常用 SNI=www.google.com 域名前置；
# 去广告合集若 MitM www.google.com（内容农场），解密必失败然后立刻重试。
#
# 排除必须在最终 hostname 列表最前面：用 %INSERT%（%APPEND% 无效）。
# 去广告大合集 heat16+ 已含同一 INSERT 并剔除 www.google.com；本小模块可单独装。

[MITM]
hostname = %INSERT% -<ip-address>:0, -www.google.com, -www.google.com.hk, -*.telegram.org, -*.telegram-cdn.org, -*.t.me, -*.whatsapp.com, -*.whatsapp.net, -*.wa.me
"""

PANGOLIN_FAKE_LOG_JS = """\
/**
 * Surge http-request short-circuit: return JSON success body for pangolin /
 * JPush stats so SDKs stop retrying (empty reject-200 causes 狂刷).
 */
const body = JSON.stringify({
  code: 0,
  message: "success",
  magic_tag: "ss_app_log",
  server_time: Math.floor(Date.now() / 1000),
  data: {},
});
$done({
  response: {
    status: 200,
    headers: { "Content-Type": "application/json" },
    body,
  },
});
"""

HEAT_LINES = (
    (
        "RULE-SET,https://raw.githubusercontent.com/oo226/egern-config/"
        "refs/heads/surge/Rules/ByteDance-Heat.list,DIRECT,extended-matching",
        "ByteDance-Heat",
    ),
    (
        "RULE-SET,https://raw.githubusercontent.com/oo226/egern-config/"
        "refs/heads/surge/Rules/App-Heat.list,DIRECT,extended-matching",
        "App-Heat",
    ),
)

APP_HEAT_LIST = """\
# 杂项狂刷域名：不要硬 REJECT（部分 SDK 会立刻重试）。
# Surge.conf 里 RULE-SET → DIRECT，再由 app-heat / 去广告合集 Map Local 有 body 假成功。
DOMAIN,tts.doudou520.online,extended-matching
DOMAIN-SUFFIX,doudou520.online,extended-matching
"""

APP_HEAT_SGMODULE = """\
#!name=杂项防烫（Surge）
#!desc=heat14 · doudou TTS 等狂刷假成功（禁空 reject / 硬 REJECT）
# UPDATE-MARKER heat14-doudou-tts
#!category=Surge专用

# 最近请求：tts.doudou520.online:443 DIRECT 已完成，一秒十几条 → 烫机。
# 走 DIRECT + Map Local 有 body；勿硬 REJECT（易更刷）。

[Rule]
DOMAIN,tts.doudou520.online,DIRECT
DOMAIN-SUFFIX,doudou520.online,DIRECT

[Map Local]
^https?:\\/\\/tts\\.doudou520\\.online data-type=text data="{}" status-code=200 header="Content-Type:application/json"
^https?:\\/\\/([-\\w]+\\.)*doudou520\\.online data-type=text data="{}" status-code=200 header="Content-Type:application/json"

[MITM]
hostname = %APPEND% tts.doudou520.online, *.doudou520.online
"""


def has_markers(text: str) -> bool:
    return all(m in text for m in REQUIRED_MARKERS)


def stamp_header(text: str) -> str:
    now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
    marker = f"# UPDATE-MARKER {HEAT_MARKER}-{now}"
    lines = text.splitlines()
    out: list[str] = []
    saw_desc = False
    saw_marker = False
    for line in lines:
        if line.startswith("#!desc=") and not saw_desc:
            out.append(
                f"#!desc={HEAT_MARKER} {now} · 防烫补丁 · 含皮皮虾 · "
                "apply-surge-heat-patch"
            )
            saw_desc = True
            continue
        if line.startswith("# UPDATE-MARKER"):
            if not saw_marker:
                out.append(marker)
                saw_marker = True
            continue
        out.append(line)
    if not saw_marker:
        insert_at = 0
        for i, line in enumerate(out):
            if line.startswith("#!") or not line.strip():
                insert_at = i + 1
                continue
            break
        out.insert(insert_at, marker)
        out.insert(insert_at + 1, "")
    ended = text.endswith("\n")
    return "\n".join(out) + ("\n" if ended else "")


def comment_line_if_active(line: str, needle: str, note: str) -> str:
    stripped = line.strip()
    if stripped.startswith("#"):
        return line
    if needle in stripped:
        return f"# {note}：{stripped}"
    return line


def _is_active_line(s: str) -> bool:
    return bool(s) and not s.startswith("#")


def _ends_with_reject(s: str) -> bool:
    return s.endswith(" - reject") or s.endswith(" - reject-200")


def _heat_url_reject_note(s: str) -> str | None:
    if not _is_active_line(s) or not _ends_with_reject(s):
        return None
    if "(?!log-api" in s or "(?!api-access" in s:
        return None
    if "log-api\\.pangolin-sdk-toutiao" in s:
        return "heat13：log-api 禁止 reject；改 Map Local / Script"
    if "api-access\\.pangolin-sdk-toutiao" in s:
        return "heat13：api-access 禁止 reject（stats/batch 狂刷）"
    if "toblog\\.ctobsnssdk\\.com" in s:
        return "heat13：toblog 禁止 reject；改 Map Local / Script"
    if "gromore\\.pangolin-sdk-toutiao" in s:
        return "heat13：gromore 埋点勿 hard reject"
    if "snssdk\\.com\\/(bds|monitor|trace|log)" in s:
        return "heat13：snssdk monitor/trace 改 Map Local 假 200"
    if (
        "pangolin-sdk-toutiao" in s
        and "(service|api|ad|sdk|batch|config)" in s
    ):
        return "heat13：穿山甲 broad 会误伤 log-api/api-access"
    return None


def comment_rejects(text: str) -> str:
    # URL Rewrite / Rule 里对防烫域名的 hard reject 必须在 Map Local 之前注释掉，
    # 否则 SDK 收到空包会秒级重试（最近请求「Modified by URL rewrite rule」狂刷）。
    heat_domain_rejects = (
        ("DOMAIN,stats.jpush.cn,REJECT", "heat9 假成功"),
        ("DOMAIN,gd-stats.jpush.cn,REJECT", "heat9 假成功"),
        ("DOMAIN,ali-stats.jpush.cn,REJECT", "heat9 假成功"),
        ("DOMAIN,toblog.ctobsnssdk.com,REJECT", "heat9 假成功"),
        ("DOMAIN,mon.snssdk.com,REJECT", "heat9 假成功"),
        ("DOMAIN,mon.zijieapi.com,REJECT", "heat9 假成功"),
        ("DOMAIN,applog.zijieapi.com,REJECT", "heat15 假成功"),
        ("DOMAIN,i-lq.snssdk.com,REJECT", "heat13 settings 放行"),
        ("DOMAIN,is-lq.snssdk.com,REJECT", "heat13 settings 放行"),
    )

    out_lines: list[str] = []
    for line in text.splitlines():
        for needle, note in heat_domain_rejects:
            line = comment_line_if_active(line, needle, note)
        if "log-api.pangolin-sdk-toutiao" in line and ",REJECT" in line:
            line = comment_line_if_active(line, "log-api.pangolin-sdk-toutiao", "heat9 假成功")
        if "api-access.pangolin-sdk-toutiao" in line and ",REJECT" in line:
            line = comment_line_if_active(line, "api-access.pangolin-sdk-toutiao", "heat9 假成功")

        s = line.strip()
        note = _heat_url_reject_note(s)
        if note:
            line = f"# {note}\n# {s}"
        elif _is_active_line(s) and "pangolin-sdk-toutiao" in s and "reject-200" in s:
            if "(?!log-api" not in s and "(?!api-access" not in s and "(service|api|ad|sdk|batch|config)" in s:
                line = (
                    "# heat9：排除 log-api / api-access（空 reject-200 狂重试）；其它广告路径仍假空 200\n"
                    r"^https?:\/\/(?!log-api\.)(?!api-access\.)[-\w]*\.pangolin-sdk-toutiao[-\w]*\.com\/.*(service|api|ad|sdk|batch|config).* - reject-200"
                )
        out_lines.append(line)
    return "\n".join(out_lines) + ("\n" if text.endswith("\n") else "")


FORBIDDEN_ACTIVE_CHECKS = (
    ("DOMAIN,i-lq.snssdk.com,REJECT", lambda s: s == "DOMAIN,i-lq.snssdk.com,REJECT"),
    ("DOMAIN,is-lq.snssdk.com,REJECT", lambda s: s == "DOMAIN,is-lq.snssdk.com,REJECT"),
    ("DOMAIN,applog.zijieapi.com,REJECT", lambda s: s == "DOMAIN,applog.zijieapi.com,REJECT"),
    ("log-api pangolin reject rewrite", lambda s: _heat_url_reject_note(s) == "heat13：log-api 禁止 reject；改 Map Local / Script"),
    ("api-access pangolin reject rewrite", lambda s: _heat_url_reject_note(s) == "heat13：api-access 禁止 reject（stats/batch 狂刷）"),
    ("toblog reject rewrite", lambda s: _heat_url_reject_note(s) == "heat13：toblog 禁止 reject；改 Map Local / Script"),
    ("pangolin broad reject rewrite", lambda s: _heat_url_reject_note(s) == "heat13：穿山甲 broad 会误伤 log-api/api-access"),
    ("snssdk monitor reject rewrite", lambda s: _heat_url_reject_note(s) == "heat13：snssdk monitor/trace 改 Map Local 假 200"),
)


def find_forbidden_active(text: str) -> list[str]:
    bad: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not _is_active_line(s):
            continue
        for _label, check in FORBIDDEN_ACTIVE_CHECKS:
            if check(s):
                bad.append(s[:120])
                break
    return bad


def validate_no_conflicts(text: str) -> None:
    bad = find_forbidden_active(text)
    if bad:
        raise SystemExit(
            "apply-surge-heat-patch: still has active anti-heat rules: "
            + "; ".join(bad[:5])
        )


def ensure_direct_block(text: str) -> str:
    need_bytedance = not (
        "DOMAIN,stats.jpush.cn,DIRECT" in text
        and "DOMAIN,log-api.pangolin-sdk-toutiao.com,DIRECT" in text
        and "DOMAIN,is-lq.snssdk.com,DIRECT" in text
    )
    need_doudou = "DOMAIN,tts.doudou520.online,DIRECT" not in text
    if not need_bytedance and not need_doudou:
        return text
    m = re.search(r"^\[Rule\]\s*$", text, re.M)
    if not m:
        raise SystemExit("apply-surge-heat-patch: missing [Rule] section")
    if need_bytedance:
        insert = DIRECT_BLOCK
    else:
        insert = (
            "# heat11：doudou TTS\n"
            "DOMAIN,tts.doudou520.online,DIRECT\n"
            "DOMAIN-SUFFIX,doudou520.online,DIRECT\n"
        )
    insert_at = m.end()
    return text[:insert_at] + "\n" + insert + text[insert_at:]


def ensure_map_local_block(text: str) -> str:
    need_core = not (
        "jpush.cn data-type=base64" in text
        and "log-api.pangolin-sdk-toutiao" in text
        and "api-access.pangolin-sdk-toutiao" in text
        and "data-type=base64" in text
    )
    need_doudou = "tts.doudou520.online data-type=text" not in text
    need_applog = "applog.zijieapi.com data-type=base64" not in text
    if not need_core and not need_doudou and not need_applog:
        return text
    parts: list[str] = []
    if need_core:
        parts.append(MAP_LOCAL_BLOCK)
    else:
        if need_applog:
            parts.append(
                "# heat15：applog.zijieapi 皮皮虾狂刷 TCP Dial Failed → 假成功（须 MITM）\n"
                '^https?:\\/\\/applog\\.zijieapi\\.com data-type=base64 data="eyJtZXNzYWdlIjoic3VjY2VzcyIsImNvZGUiOjAsImRldmljZV9pZCI6MSwiaW5zdGFsbF9pZCI6MSwic3NpZCI6IjAifQ==" status-code=200 header="Content-Type:application/json"\n'
            )
        if need_doudou:
            parts.append(
                "# heat11：doudou TTS 狂刷假成功\n"
                '^https?:\\/\\/tts\\.doudou520\\.online data-type=text data="{}" status-code=200 header="Content-Type:application/json"\n'
                '^https?:\\/\\/([-\\w]+\\.)*doudou520\\.online data-type=text data="{}" status-code=200 header="Content-Type:application/json"\n'
            )
    block = "".join(parts)
    m = re.search(r"^\[Map Local\]\s*$", text, re.M)
    if m:
        insert_at = m.end()
        return text[:insert_at] + "\n" + block + text[insert_at:]
    return text.rstrip() + "\n\n[Map Local]\n" + block + "\n"


def ensure_doudou_mitm(text: str) -> str:
    m = re.search(r"^(hostname\s*=\s*%APPEND%\s*)(.+)$", text, re.M)
    if not m:
        return text
    hosts = m.group(2)
    add: list[str] = []
    if "tts.doudou520.online" not in hosts:
        add.append("tts.doudou520.online")
    if "*.doudou520.online" not in hosts:
        add.append("*.doudou520.online")
    if "applog.zijieapi.com" not in hosts:
        add.append("applog.zijieapi.com")
    if not add:
        return text
    return text[: m.start(2)] + ", ".join(add) + ", " + hosts + text[m.end(2) :]


def ensure_script_block(text: str) -> str:
    need_core = not ("pangolin-fake-log" in text and "jpush-fake-stats" in text)
    need_applog = "applog-zijie-fake" not in text
    if not need_core and not need_applog:
        return text
    if need_core:
        block = SCRIPT_BLOCK
    else:
        block = (
            f"applog-zijie-fake = type=http-request,pattern=^https?:\\/\\/applog\\.zijieapi\\.com,"
            f"script-path={SCRIPT_URL},requires-body=0,max-size=0,timeout=5\n"
        )
    m = re.search(r"^\[Script\]\s*$", text, re.M)
    if m:
        insert_at = m.end()
        return text[:insert_at] + "\n" + block + text[insert_at:]
    m = re.search(r"^\[Map Local\]\s*$", text, re.M)
    if m:
        return (
            text[: m.start()]
            + "[Script]\n"
            + block
            + "\n"
            + text[m.start() :]
        )
    return text.rstrip() + "\n\n[Script]\n" + block + "\n"


def ensure_bare_ip_mitm_insert(text: str) -> str:
    """Put -<ip-address>:0 + TG fronting SNI excludes at hostname front via %INSERT%.

    Telegram / WhatsApp 常用裸 IP + 证书钉扎；MitM 必失败并秒级重试 → 烫机。
    Telegram 还常用 SNI=www.google.com 域名前置；合集若 MitM 该主机名同样狂刷。
    排除必须在最终 hostname 列表最前；模块 %APPEND% 排在后面无效。
    用户只更新「去广告大合集」也能带上此排除，不必重导主配置。
    """
    # Upgrade heat14-only INSERT (bare IP alone) to heat16 (+ google SNI).
    old = "hostname = %INSERT% -<ip-address>:0"
    if BARE_IP_MITM_INSERT in text:
        pass
    elif old in text:
        text = text.replace(old, BARE_IP_MITM_INSERT, 1)
    else:
        m = re.search(r"^\[MITM\]\s*$", text, re.M)
        if not m:
            text = text.rstrip() + f"\n\n[MITM]\n{BARE_IP_MITM_INSERT}\n"
        else:
            insert_at = m.end()
            text = text[:insert_at] + f"\n{BARE_IP_MITM_INSERT}\n" + text[insert_at:]
    return strip_tg_fronting_mitm_hosts(text)


def strip_tg_fronting_mitm_hosts(text: str) -> str:
    """Drop www.google.com(.hk) from hostname %APPEND% so TG fronting is never decrypted."""

    def _filter_line(match: re.Match[str]) -> str:
        prefix, rest = match.group(1), match.group(2)
        hosts = [h.strip() for h in rest.split(",") if h.strip()]
        kept = [h for h in hosts if h.lower() not in TG_FRONTING_MITM_HOSTS]
        if not kept:
            return f"{prefix.strip()} "  # unlikely; keep line syntactically valid
        return prefix + ", ".join(kept)

    return re.sub(
        r"^(hostname\s*=\s*%APPEND%\s*)(.+)$",
        _filter_line,
        text,
        flags=re.M,
    )


EGERN_TG_MITM_EXCLUDES = (
    "www.google.com",
    "www.google.com.hk",
    "*.telegram.org",
    "*.telegram-cdn.org",
    "*.t.me",
    "194.221.250.50",
    "149.154.*",
    "91.108.*",
    "91.105.*",
)


def ensure_egern_tg_mitm_excludes() -> None:
    """Keep Egern.yaml mitm.excludes covering TG bare IP + google SNI fronting."""
    path = ROOT / "Egern.yaml"
    if not path.is_file():
        print("skip Egern.yaml (missing)")
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    # excludes 块含注释行；勿只匹配 `      - `，否则会把注释当块结束并重复插入。
    m = re.search(
        r"(^mitm:\n(?:  .*\n)*?    excludes:\n)"
        r"((?:      (?:#.*|- .*)\n)*)",
        text,
        re.M,
    )
    if not m:
        print("warn: Egern.yaml has no mitm.excludes block")
        return
    existing = m.group(2)
    existing_hosts = {
        ln.strip()[2:].strip().strip('"').strip("'")
        for ln in existing.splitlines()
        if ln.strip().startswith("- ")
    }
    missing = [h for h in EGERN_TG_MITM_EXCLUDES if h not in existing_hosts]
    if not missing:
        print("Egern.yaml mitm.excludes already has TG/google SNI heat excludes")
        return
    insert = "".join(
        f'      - "{h}"\n' if "*" in h or h[0].isdigit() else f"      - {h}\n"
        for h in missing
    )
    note = (
        "      # Telegram 裸 IP + SNI=www.google.com：MitM 会 TLS 失败狂重试烫机\n"
        if "Telegram 裸 IP" not in existing
        else ""
    )
    text = text[: m.end(1)] + note + insert + existing + text[m.end() :]
    path.write_text(text, encoding="utf-8")
    print(f"Egern.yaml mitm.excludes += {', '.join(missing)}")


EXCLUDED_PANGOLIN_REWRITE = (
    "# heat9：排除 log-api / api-access（空 reject-200 狂重试）；其它广告路径仍假空 200\n"
    r"^https?:\/\/(?!log-api\.)(?!api-access\.)[-\w]*\.pangolin-sdk-toutiao[-\w]*\.com\/.*(service|api|ad|sdk|batch|config).* - reject-200"
)


def ensure_excluded_pangolin_rewrite(text: str) -> str:
    if "(?!log-api\\.)(?!api-access\\.)" in text:
        return text
    m = re.search(r"^\[URL Rewrite\]\s*$", text, re.M)
    if m:
        insert_at = m.end()
        return text[:insert_at] + "\n" + EXCLUDED_PANGOLIN_REWRITE + "\n" + text[insert_at:]
    for section in ("[Script]", "[Map Local]", "[MITM]"):
        idx = text.find(section)
        if idx != -1:
            return (
                text[:idx]
                + "[URL Rewrite]\n"
                + EXCLUDED_PANGOLIN_REWRITE
                + "\n\n"
                + text[idx:]
            )
    return text.rstrip() + "\n\n[URL Rewrite]\n" + EXCLUDED_PANGOLIN_REWRITE + "\n"


def patch_adblock(text: str) -> str:
    had_markers = has_markers(text)
    if had_markers:
        print("adblock already has anti-retry markers; re-scan rejects + refresh extras")
    text = comment_rejects(text)
    text = ensure_direct_block(text)
    text = ensure_excluded_pangolin_rewrite(text)
    text = ensure_script_block(text)
    text = ensure_map_local_block(text)
    text = ensure_doudou_mitm(text)
    text = ensure_bare_ip_mitm_insert(text)
    text = stamp_header(text)
    if not has_markers(text):
        missing = [m for m in REQUIRED_MARKERS if m not in text]
        raise SystemExit(
            "apply-surge-heat-patch: still missing markers after patch: "
            + ", ".join(missing)
        )
    validate_no_conflicts(text)
    return text


def ensure_sidecars() -> None:
    BYTEDANCE_HEAT.parent.mkdir(parents=True, exist_ok=True)
    BYTEDANCE_HEAT.write_text(BYTEDANCE_LIST, encoding="utf-8")
    print(f"wrote {BYTEDANCE_HEAT}")

    APP_HEAT.parent.mkdir(parents=True, exist_ok=True)
    APP_HEAT.write_text(APP_HEAT_LIST, encoding="utf-8")
    print(f"wrote {APP_HEAT}")

    APP_HEAT_MODULE.parent.mkdir(parents=True, exist_ok=True)
    APP_HEAT_MODULE.write_text(APP_HEAT_SGMODULE, encoding="utf-8")
    print(f"wrote {APP_HEAT_MODULE}")

    PIPIXIA_HEAT.parent.mkdir(parents=True, exist_ok=True)
    PIPIXIA_HEAT.write_text(PIPIXIA_HEAT_MODULE, encoding="utf-8")
    print(f"wrote {PIPIXIA_HEAT}")

    TG_MITM_HEAT.parent.mkdir(parents=True, exist_ok=True)
    TG_MITM_HEAT.write_text(TG_MITM_HEAT_MODULE, encoding="utf-8")
    print(f"wrote {TG_MITM_HEAT}")

    PANGOLIN_SCRIPT.parent.mkdir(parents=True, exist_ok=True)
    if not PANGOLIN_SCRIPT.is_file():
        PANGOLIN_SCRIPT.write_text(PANGOLIN_FAKE_LOG_JS, encoding="utf-8")
        print(f"wrote {PANGOLIN_SCRIPT}")
    else:
        print(f"keep {PANGOLIN_SCRIPT}")


def ensure_surge_conf_ruleset() -> None:
    if not SURGE_CONF.is_file():
        print("skip Surge.conf (missing)")
        return
    text = SURGE_CONF.read_text(encoding="utf-8", errors="replace")
    changed = False
    needle = (
        "DOMAIN-SET,https://raw.githubusercontent.com/oo226/egern-config/"
        "refs/heads/surge/Rules/Reject-Merged.domainset"
    )

    for heat_line, label in HEAT_LINES:
        if heat_line in text:
            print(f"Surge.conf already has {label} RULE-SET")
            continue
        comment = f"{heat_line}\n"
        if needle in text:
            text = text.replace(needle, comment + needle, 1)
        else:
            text = text.rstrip() + "\n" + comment
        changed = True
        print(f"inserted {label} RULE-SET into Surge.conf")

    tg_domain = (
        "RULE-SET,https://raw.githubusercontent.com/oo226/egern-config/"
        "refs/heads/surge/Rules/Foreign/Telegram.list,Telegram,extended-matching"
    )
    tg_ip = (
        "RULE-SET,https://raw.githubusercontent.com/oo226/egern-config/"
        "refs/heads/surge/Rules/Foreign/Telegram.ip.list,Telegram,no-resolve"
    )
    if tg_domain in text and tg_ip not in text:
        text = text.replace(tg_domain, tg_domain + "\n" + tg_ip, 1)
        changed = True
        print("inserted Telegram.ip.list RULE-SET (no-resolve) into Surge.conf")
    elif tg_ip in text:
        print("Surge.conf already has Telegram.ip.list RULE-SET")

    ip_excl = "-<ip-address>:0"
    google_excl = "-www.google.com, -www.google.com.hk"
    if ip_excl not in text:
        text2, n = re.subn(
            r"^(hostname\s*=\s*)",
            rf"\g<1>{ip_excl}, {google_excl}, ",
            text,
            count=1,
            flags=re.M,
        )
        if n:
            text = text2
            changed = True
            print("inserted -<ip-address>:0 + google SNI MitM excludes into Surge.conf")
        else:
            print("warn: Surge.conf has no hostname= line to patch")
    else:
        print("Surge.conf already has -<ip-address>:0 MitM exclude")
        host_m = re.search(r"^(hostname\s*=\s*.+)$", text, re.M)
        if host_m and "-www.google.com" not in host_m.group(1):
            old_line = host_m.group(1)
            new_line = re.sub(
                r"(-<ip-address>:0)",
                rf"\1, {google_excl}",
                old_line,
                count=1,
            )
            if new_line != old_line:
                text = text[: host_m.start()] + new_line + text[host_m.end() :]
                changed = True
                print("inserted google SNI MitM excludes into Surge.conf hostname")
            else:
                # ip exclude may use different spelling; prepend after hostname =
                text = (
                    text[: host_m.start()]
                    + re.sub(
                        r"^(hostname\s*=\s*)",
                        rf"\g<1>{google_excl}, ",
                        old_line,
                        count=1,
                    )
                    + text[host_m.end() :]
                )
                changed = True
                print("prepended google SNI MitM excludes into Surge.conf hostname")

    if changed:
        SURGE_CONF.write_text(text, encoding="utf-8")


def patch_adblock_file(path: Path, *, label: str) -> None:
    if not path.is_file():
        print(f"skip missing {path} ({label})")
        return
    original = path.read_text(encoding="utf-8", errors="replace")
    patched = patch_adblock(original)
    if patched != original:
        path.write_text(patched, encoding="utf-8")
        print(f"patched {path} ({label})")
    else:
        print(f"unchanged {path} ({label})")


def main() -> None:
    if not ADBLOCK.is_file() and not EGERN_ADBLOCK.is_file():
        raise SystemExit(
            f"missing both {ADBLOCK} and {EGERN_ADBLOCK}; run adblock merge first"
        )
    patch_adblock_file(ADBLOCK, label="surge")
    # Egern 去广告合集同样会硬 REJECT 穿山甲埋点 → 狂刷烫机；与 Surge 共用同一套补丁。
    patch_adblock_file(EGERN_ADBLOCK, label="egern")
    ensure_sidecars()
    ensure_surge_conf_ruleset()
    ensure_egern_tg_mitm_excludes()
    print("apply-surge-heat-patch: ok")


if __name__ == "__main__":
    main()
