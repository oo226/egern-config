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
PIPIXIA_HEAT = ROOT / "surge" / "Modules" / "pipixia-heat.sgmodule"
BYTEDANCE_HEAT = ROOT / "surge" / "Rules" / "ByteDance-Heat.list"
APP_HEAT = ROOT / "surge" / "Rules" / "App-Heat.list"
APP_HEAT_MODULE = ROOT / "surge" / "Modules" / "app-heat.sgmodule"
GOOGLE_GEMINI_FIX = ROOT / "surge" / "Modules" / "google-gemini-fix.sgmodule"
PANGOLIN_SCRIPT = ROOT / "surge" / "Scripts" / "pangolin-fake-log.js"
SURGE_CONF = ROOT / "surge" / "Surge.conf"

HEAT_MARKER = "heat11"
SCRIPT_URL = (
    "https://raw.githubusercontent.com/oo226/egern-config/refs/heads/surge/"
    "Scripts/pangolin-fake-log.js"
)

REQUIRED_MARKERS = (
    "DOMAIN,stats.jpush.cn,DIRECT",
    "pangolin-fake-log",
    "(?!log-api\\.)(?!api-access\\.)",
    "jpush-fake-stats",
)

DIRECT_BLOCK = """\
# heat5：字节埋点硬 REJECT 会立刻重试（最近请求一直跳）。
# 先 DIRECT，交给 Map Local / Script 有 body 假成功（勿用空 reject-200）。
# i-lq.snssdk.com/service/settings 放行真实配置，不要假空包。
DOMAIN,mon.snssdk.com,DIRECT
DOMAIN,mon.zijieapi.com,DIRECT
DOMAIN,toblog.ctobsnssdk.com,DIRECT
DOMAIN,i-lq.snssdk.com,DIRECT
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
# heat11：doudou TTS 狂刷假成功
^https?:\/\/tts\.doudou520\.online data-type=text data="{}" status-code=200 header="Content-Type:application/json"
^https?:\/\/([-\w]+\.)*doudou520\.online data-type=text data="{}" status-code=200 header="Content-Type:application/json"
""".lstrip(
    "\n"
)

BYTEDANCE_LIST = """\
# 字节埋点：不要硬 REJECT（会立刻重试，最近请求一直跳）。
# 策略 DIRECT 后由去广告合集 / pipixia-heat 的 Map Local / Script 有 body 假成功（禁空 reject-200）。
# i-lq.snssdk.com 放行 settings（真实 200）；不要对 /service/settings 假空包。
DOMAIN,mon.snssdk.com,extended-matching
DOMAIN,mon.zijieapi.com,extended-matching
DOMAIN,toblog.ctobsnssdk.com,extended-matching
DOMAIN,i-lq.snssdk.com,extended-matching
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

[Map Local]
^https?:\\/\\/log-api\\.pangolin-sdk-toutiao[-\\w]*\\.com\\/service\\/2\\/app_log data-type=base64 data="eyJjb2RlIjowLCJtZXNzYWdlIjoic3VjY2VzcyIsIm1hZ2ljX3RhZyI6InNzX2FwcF9sb2ciLCJzZXJ2ZXJfdGltZSI6MTcyNDIyMDAwMCwiZGF0YSI6e319" status-code=200 header="Content-Type:application/json"
^https?:\\/\\/log-api\\.pangolin-sdk-toutiao[-\\w]*\\.com data-type=base64 data="eyJjb2RlIjowLCJtZXNzYWdlIjoic3VjY2VzcyIsIm1hZ2ljX3RhZyI6InNzX2FwcF9sb2ciLCJzZXJ2ZXJfdGltZSI6MTcyNDIyMDAwMCwiZGF0YSI6e319" status-code=200 header="Content-Type:application/json"
^https?:\\/\\/api-access\\.pangolin-sdk-toutiao[-\\w]*\\.com\\/api\\/ad\\/union\\/sdk\\/stats data-type=base64 data="eyJjb2RlIjowLCJtZXNzYWdlIjoic3VjY2VzcyIsImRhdGEiOnt9fQ==" status-code=200 header="Content-Type:application/json"
^https?:\\/\\/mon\\.snssdk\\.com\\/monitor data-type=text data="{{}}" status-code=200 header="Content-Type:application/json"
^https?:\\/\\/mon\\.zijieapi\\.com data-type=text data="{{}}" status-code=200 header="Content-Type:application/json"
^https?:\\/\\/toblog\\.ctobsnssdk\\.com data-type=base64 data="eyJtZXNzYWdlIjoic3VjY2VzcyIsImNvZGUiOjAsImRldmljZV9pZCI6MSwiaW5zdGFsbF9pZCI6MSwic3NpZCI6IjAifQ==" status-code=200 header="Content-Type:application/json"
^https?:\\/\\/(stats|gd-stats|ali-stats)\\.jpush\\.cn data-type=base64 data="eyJjb2RlIjowLCJtZXNzYWdlIjoic3VjY2VzcyJ9" status-code=200 header="Content-Type:application/json"
^https?:\\/\\/sdk\\.e\\.qq\\.com data-type=text data="{{}}" status-code=200 header="Content-Type:application/json"
^https?:\\/\\/snowflake\\.qq\\.com\\/ola data-type=text data="{{}}" status-code=200 header="Content-Type:application/json"
^https?:\\/\\/mobads-logs\\.baidu\\.com data-type=text data="{{}}" status-code=200 header="Content-Type:application/json"

[Rule]
DOMAIN,mon.snssdk.com,DIRECT
DOMAIN,mon.zijieapi.com,DIRECT
DOMAIN,toblog.ctobsnssdk.com,DIRECT
DOMAIN,i-lq.snssdk.com,DIRECT
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
hostname = %APPEND% log-api.pangolin-sdk-toutiao.com, log-api.pangolin-sdk-toutiao1.com, log-api.pangolin-sdk-toutiao-b.com, api-access.pangolin-sdk-toutiao.com, api-access.pangolin-sdk-toutiao1.com, api-access.pangolin-sdk-toutiao-b.com, gromore.pangolin-sdk-toutiao.com, mon.snssdk.com, mon.zijieapi.com, toblog.ctobsnssdk.com, i-lq.snssdk.com, stats.jpush.cn, gd-stats.jpush.cn, ali-stats.jpush.cn, sdk.e.qq.com, snowflake.qq.com, mobads-logs.baidu.com
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
#!desc=heat11 · doudou TTS 等狂刷假成功（禁空 reject / 硬 REJECT）
# UPDATE-MARKER heat11-doudou-tts
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

GOOGLE_GEMINI_SGMODULE = """
#!name=Google / Gemini 修复（Surge）
#!desc=修 FINAL dns-failed；Google DNS；钉美国；关 IPv6 说明见主配置
# UPDATE-MARKER gemini-dns-us2
#!category=Surge专用

# 你细节里的根因：
#   [Rule] DNS lookup failed, use FINAL rule → 兜底（新/港/韩）
# Tailscale-Direct.list 曾含 IP-CIDR 且无 no-resolve → 每条连接都要 DNS；
# 主配置 Google.list = AliDNS → 解析失败 → 永远走不进 AI/Google 规则。
#
# 本模块：内联域名规则（不依赖 RULE-SET 下载）+ dns.google + DoH 走代理。
# 主配置请同时：ipv6=false；ChatGPT 不要挂韩国/兜底；Google DNS 改 dns.google。

[General]
# 模块无法可靠覆盖主配置 ipv6；请在主配置设 ipv6 = false

[Host]
RULE-SET:https://raw.githubusercontent.com/oo226/egern-config/refs/heads/surge/Rules/Foreign/AI-Merged.list = server:https://dns.google/dns-query
RULE-SET:https://raw.githubusercontent.com/oo226/egern-config/refs/heads/surge/Rules/Foreign/Google.list = server:https://dns.google/dns-query
RULE-SET:https://raw.githubusercontent.com/oo226/egern-config/refs/heads/surge/Rules/Foreign/YouTube.list = server:https://dns.google/dns-query

[Rule]
# 最高优先：SNI 直接钉美国，不先 DNS
DOMAIN-SUFFIX,googleapis.com,美国节点,extended-matching,dns-failed
DOMAIN-SUFFIX,google.com,美国节点,extended-matching,dns-failed
DOMAIN-SUFFIX,googleusercontent.com,美国节点,extended-matching,dns-failed
DOMAIN-SUFFIX,gstatic.com,美国节点,extended-matching,dns-failed
DOMAIN-SUFFIX,gemini.google,美国节点,extended-matching,dns-failed
DOMAIN-KEYWORD,google,美国节点,extended-matching,dns-failed
IP-CIDR,8.8.8.8/32,新国节点,no-resolve
IP-CIDR,8.8.4.4/32,新国节点,no-resolve
IP-CIDR,1.1.1.1/32,新国节点,no-resolve
IP-CIDR,1.0.0.1/32,新国节点,no-resolve
DOMAIN,dns.google,新国节点,extended-matching
DOMAIN,cloudflare-dns.com,新国节点,extended-matching
RULE-SET,https://raw.githubusercontent.com/oo226/egern-config/refs/heads/surge/Rules/Foreign/AI-Merged.list,美国节点,extended-matching,dns-failed
RULE-SET,https://raw.githubusercontent.com/oo226/egern-config/refs/heads/surge/Rules/Foreign/Google.list,美国节点,extended-matching,dns-failed

[MITM]
hostname = %INSERT% -www.google.com, -www.google.com.hk
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


def comment_rejects(text: str) -> str:
    out_lines: list[str] = []
    for line in text.splitlines():
        orig = line
        line = comment_line_if_active(line, "DOMAIN,stats.jpush.cn,REJECT", "heat9 假成功")
        line = comment_line_if_active(line, "DOMAIN,gd-stats.jpush.cn,REJECT", "heat9 假成功")
        line = comment_line_if_active(line, "DOMAIN,ali-stats.jpush.cn,REJECT", "heat9 假成功")
        line = comment_line_if_active(line, "DOMAIN,toblog.ctobsnssdk.com,REJECT", "heat9 假成功")
        line = comment_line_if_active(line, "DOMAIN,mon.snssdk.com,REJECT", "heat9 假成功")
        line = comment_line_if_active(line, "DOMAIN,mon.zijieapi.com,REJECT", "heat9 假成功")
        if "log-api.pangolin-sdk-toutiao" in line and ",REJECT" in line:
            line = comment_line_if_active(line, "log-api.pangolin-sdk-toutiao", "heat9 假成功")
        if "api-access.pangolin-sdk-toutiao" in line and ",REJECT" in line:
            line = comment_line_if_active(line, "api-access.pangolin-sdk-toutiao", "heat9 假成功")

        # Empty reject-200 for heat hosts
        s = line.strip()
        if not s.startswith("#"):
            if re.match(
                r"\^https\?:\\/\\/log-api\\.pangolin-sdk-toutiao.* - reject-200$",
                s,
            ):
                line = f"# heat9：log-api 禁止空 reject-200；改 Map Local / Script\n# {s}"
            elif re.match(
                r"\^https\?:\\/\\/api-access\\.pangolin-sdk-toutiao.* - reject-200$",
                s,
            ):
                line = f"# heat9：api-access 禁止空 reject-200（stats/batch 狂刷）\n# {s}"
            elif re.match(
                r"\^https\?:\\/\\/toblog\\.ctobsnssdk\\.com.* - reject-200$",
                s,
            ):
                line = f"# heat8：toblog 禁止空 reject-200；改 Map Local / Script\n# {s}"
            elif (
                "pangolin-sdk-toutiao" in s
                and "reject-200" in s
                and "(?!log-api" not in s
                and "(service|api|ad|sdk|batch|config)" in s
            ):
                # Broad pangolin rewrite without exclusions
                line = (
                    "# heat9：排除 log-api / api-access（空 reject-200 狂重试）；其它广告路径仍假空 200\n"
                    r"^https?:\/\/(?!log-api\.)(?!api-access\.)[-\w]*\.pangolin-sdk-toutiao[-\w]*\.com\/.*(service|api|ad|sdk|batch|config).* - reject-200"
                )
        if line != orig or True:
            out_lines.append(line)
    return "\n".join(out_lines) + ("\n" if text.endswith("\n") else "")


def ensure_direct_block(text: str) -> str:
    need_bytedance = not (
        "DOMAIN,stats.jpush.cn,DIRECT" in text
        and "DOMAIN,log-api.pangolin-sdk-toutiao.com,DIRECT" in text
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
    if not need_core and not need_doudou:
        return text
    if need_core:
        block = MAP_LOCAL_BLOCK
    else:
        block = (
            "# heat11：doudou TTS 狂刷假成功\n"
            '^https?:\\/\\/tts\\.doudou520\\.online data-type=text data="{}" status-code=200 header="Content-Type:application/json"\n'
            '^https?:\\/\\/([-\\w]+\\.)*doudou520\\.online data-type=text data="{}" status-code=200 header="Content-Type:application/json"\n'
        )
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
    if not add:
        return text
    return text[: m.start(2)] + ", ".join(add) + ", " + hosts + text[m.end(2) :]


def ensure_script_block(text: str) -> str:
    if "pangolin-fake-log" in text and "jpush-fake-stats" in text:
        return text
    m = re.search(r"^\[Script\]\s*$", text, re.M)
    if m:
        insert_at = m.end()
        return text[:insert_at] + "\n" + SCRIPT_BLOCK + text[insert_at:]
    m = re.search(r"^\[Map Local\]\s*$", text, re.M)
    if m:
        return (
            text[: m.start()]
            + "[Script]\n"
            + SCRIPT_BLOCK
            + "\n"
            + text[m.start() :]
        )
    return text.rstrip() + "\n\n[Script]\n" + SCRIPT_BLOCK + "\n"


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
    if has_markers(text):
        print("adblock already has anti-retry markers; refresh heat extras")
        text = ensure_direct_block(text)
        text = ensure_map_local_block(text)
        text = ensure_doudou_mitm(text)
        return stamp_header(text)
    text = comment_rejects(text)
    text = ensure_direct_block(text)
    text = ensure_excluded_pangolin_rewrite(text)
    text = ensure_script_block(text)
    text = ensure_map_local_block(text)
    text = ensure_doudou_mitm(text)
    text = stamp_header(text)
    if not has_markers(text):
        missing = [m for m in REQUIRED_MARKERS if m not in text]
        raise SystemExit(
            "apply-surge-heat-patch: still missing markers after patch: "
            + ", ".join(missing)
        )
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

    GOOGLE_GEMINI_FIX.parent.mkdir(parents=True, exist_ok=True)
    GOOGLE_GEMINI_FIX.write_text(GOOGLE_GEMINI_SGMODULE, encoding="utf-8")
    print(f"wrote {GOOGLE_GEMINI_FIX}")

    PIPIXIA_HEAT.parent.mkdir(parents=True, exist_ok=True)
    PIPIXIA_HEAT.write_text(PIPIXIA_HEAT_MODULE, encoding="utf-8")
    print(f"wrote {PIPIXIA_HEAT}")

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

    ip_excl = "-<ip-address>:0"
    if ip_excl not in text:
        text2, n = re.subn(
            r"^(hostname\s*=\s*)",
            rf"\g<1>{ip_excl}, ",
            text,
            count=1,
            flags=re.M,
        )
        if n:
            text = text2
            changed = True
            print("inserted -<ip-address>:0 into Surge.conf MITM hostname")
        else:
            print("warn: Surge.conf has no hostname= line to patch")
    else:
        print("Surge.conf already has -<ip-address>:0 MitM exclude")

    # Google/Gemini：AI+Google 必须用国外 DoH；AliDNS 易解析到国内 IP。
    if "AI-Merged.list = server:https://dns.google/dns-query" not in text:
        text2, n = re.subn(
            r"^RULE-SET:https://raw\.githubusercontent\.com/oo226/egern-config/"
            r"refs/heads/surge/Rules/Foreign/Google\.list = server:.*$",
            "RULE-SET:https://raw.githubusercontent.com/oo226/egern-config/"
            "refs/heads/surge/Rules/Foreign/AI-Merged.list = server:https://dns.google/dns-query\n"
            "RULE-SET:https://raw.githubusercontent.com/oo226/egern-config/"
            "refs/heads/surge/Rules/Foreign/Google.list = server:https://dns.google/dns-query",
            text,
            count=1,
            flags=re.M,
        )
        if n:
            text = text2
            changed = True
            print("restored AI-Merged+Google DNS → dns.google in Surge.conf")
        else:
            print("warn: could not restore Google/AI dns.google mapping")
    else:
        print("Surge.conf already maps AI-Merged to dns.google")

    if "ChatGPT = select, 美国节点" not in text or "日本节点" in (
        next(
            (
                line
                for line in text.splitlines()
                if line.startswith("ChatGPT =")
            ),
            "",
        )
    ):
        text2, n = re.subn(
            r"^ChatGPT\s*=\s*.*$",
            "ChatGPT = select, 美国节点, icon-url="
            "https://raw.githubusercontent.com/lige47/QuanX-icon-rule/main/icon/04ProxySoft/chatgpt4.0.png?v=3",
            text,
            count=1,
            flags=re.M,
        )
        if n:
            text = text2
            changed = True
            print("restored ChatGPT = select 美国节点 only in Surge.conf")
    else:
        print("Surge.conf already has ChatGPT select 美国节点 only")

    ai_us = (
        "Rules/Foreign/AI-Merged.list,美国节点,extended-matching,dns-failed"
    )
    if ai_us not in text:
        text2, n = re.subn(
            r"RULE-SET,https://raw\.githubusercontent\.com/oo226/egern-config/"
            r"refs/heads/surge/Rules/Foreign/AI-Merged\.list,[^\n]+",
            "RULE-SET,https://raw.githubusercontent.com/oo226/egern-config/"
            "refs/heads/surge/Rules/Foreign/AI-Merged.list,美国节点,extended-matching,dns-failed",
            text,
            count=1,
        )
        if n:
            text = text2
            changed = True
            print("pinned AI-Merged → 美国节点,dns-failed in Surge.conf")
    else:
        print("Surge.conf already pins AI-Merged → 美国节点")

    google_us = (
        "Rules/Foreign/Google.list,美国节点,extended-matching,dns-failed"
    )
    if google_us not in text:
        text2, n = re.subn(
            r"RULE-SET,https://raw\.githubusercontent\.com/oo226/egern-config/"
            r"refs/heads/surge/Rules/Foreign/Google\.list,[^\n]+",
            "RULE-SET,https://raw.githubusercontent.com/oo226/egern-config/"
            "refs/heads/surge/Rules/Foreign/Google.list,美国节点,extended-matching,dns-failed",
            text,
            count=1,
        )
        if n:
            text = text2
            changed = True
            print("pinned Google.list → 美国节点,dns-failed in Surge.conf")
    else:
        print("Surge.conf already pins Google.list → 美国节点")

    doh_rule = "IP-CIDR,8.8.8.8/32,新国节点,no-resolve"
    if doh_rule not in text:
        text2, n = re.subn(
            r"^\[Rule\]\s*$",
            "[Rule]\n"
            "# 国外 DoH 出口：否则 Google/AI 的 dns.google / 1.1.1.1 直连空解析。\n"
            "IP-CIDR,8.8.8.8/32,新国节点,no-resolve\n"
            "IP-CIDR,8.8.4.4/32,新国节点,no-resolve\n"
            "IP-CIDR,1.1.1.1/32,新国节点,no-resolve\n"
            "IP-CIDR,1.0.0.1/32,新国节点,no-resolve\n"
            "DOMAIN,dns.google,新国节点,extended-matching\n"
            "DOMAIN,cloudflare-dns.com,新国节点,extended-matching\n",
            text,
            count=1,
            flags=re.M,
        )
        if n:
            text = text2
            changed = True
            print("inserted DoH proxy rules into Surge.conf [Rule]")
    else:
        print("Surge.conf already has DoH proxy IP-CIDR rules")

    if "-www.google.com" not in text and "hostname" in text:
        text2, n = re.subn(
            r"^(hostname\s*=\s*)",
            r"\g<1>-www.google.com, -www.google.com.hk, ",
            text,
            count=1,
            flags=re.M,
        )
        if n:
            text = text2
            changed = True
            print("inserted -www.google.com MitM exclude into Surge.conf")
    elif "-www.google.com" in text:
        print("Surge.conf already excludes www.google.com from MitM")

    ts = "Tailscale-Direct.list,DIRECT,extended-matching,no-resolve"
    if "Tailscale-Direct.list" in text and ts not in text:
        text2, n = re.subn(
            r"RULE-SET,https://raw\.githubusercontent\.com/oo226/egern-config/"
            r"refs/heads/surge/Rules/Tailscale-Direct\.list,DIRECT,extended-matching(?!,no-resolve)",
            "RULE-SET,https://raw.githubusercontent.com/oo226/egern-config/"
            "refs/heads/surge/Rules/Tailscale-Direct.list,DIRECT,extended-matching,no-resolve",
            text,
            count=1,
        )
        if n:
            text = text2
            changed = True
            print("added no-resolve to Tailscale-Direct.list RULE-SET")
    else:
        print("Surge.conf Tailscale-Direct.list already has no-resolve")


    if changed:
        SURGE_CONF.write_text(text, encoding="utf-8")


def main() -> None:
    if not ADBLOCK.is_file():
        raise SystemExit(f"missing {ADBLOCK}; run surge adblock merge first")
    original = ADBLOCK.read_text(encoding="utf-8", errors="replace")
    patched = patch_adblock(original)
    if patched != original:
        ADBLOCK.write_text(patched, encoding="utf-8")
        print(f"patched {ADBLOCK}")
    else:
        print(f"unchanged {ADBLOCK}")
    ensure_sidecars()
    ensure_surge_conf_ruleset()
    print("apply-surge-heat-patch: ok")


if __name__ == "__main__":
    main()
