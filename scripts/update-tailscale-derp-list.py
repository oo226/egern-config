#!/usr/bin/env python3
"""Regenerate Surge Tailscale DERP + Direct RULE-SETs from derpmap."""
from __future__ import annotations

import json
import ssl
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "Surge" / "Rules"
DERP_OUT = RULES / "Tailscale-DERP.list"
DIRECT_OUT = RULES / "Tailscale-Direct.list"
URL = "https://login.tailscale.com/derpmap/default"

CONTROLPLANE = [
    "# --- controlplane (static; keep when regenerating derpmap) ---",
    "# ARIN TAILS 192.200.0.0/24 + 199.165.136.0/24；IPv6 2606:b740::/32",
    "DOMAIN,controlplane.tailscale.com",
    "DOMAIN,login.tailscale.com",
    "DOMAIN,log.tailscale.com",
    "IP-CIDR,192.200.0.0/24",
    "IP-CIDR,199.165.136.0/24",
    "IP-CIDR6,2606:b740::/32",
    "# --- end controlplane ---",
]


def fetch_derpmap() -> tuple[list[str], list[str], list[str]]:
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(URL, context=ctx, timeout=30) as r:
        data = json.load(r)
    regions = data.get("Regions") or {}
    hosts, ips4, ips6 = set(), set(), set()
    for reg in regions.values():
        for n in reg.get("Nodes") or []:
            if h := n.get("HostName"):
                hosts.add(h)
            if v := n.get("IPv4"):
                ips4.add(v.split("/")[0])
            if v := n.get("IPv6"):
                ips6.add(v.split("/")[0].split("%")[0])
    hosts_l = sorted(hosts)
    ips4_l = sorted(ips4, key=lambda x: tuple(int(p) for p in x.split(".")))
    ips6_l = sorted(ips6)
    return hosts_l, ips4_l, ips6_l


def main() -> None:
    hosts, ips4, ips6 = fetch_derpmap()
    derp_body = [f"DOMAIN,{h}" for h in hosts]
    derp_body += [f"IP-CIDR,{ip}/32" for ip in ips4]
    derp_body += [f"IP-CIDR6,{ip}/128" for ip in ips6]

    derp_lines = [
        "# Tailscale DERP relays (from login.tailscale.com/derpmap/default)",
        "# DERP 客户端常按 IP 拨号，DOMAIN-SUFFIX 匹配不到 → 掉进 FINAL/节点选择",
        "# 本表：DOMAIN + IP/32 + IP6/128 → 策略请挂 DIRECT",
        f"# nodes={len(hosts)} v4={len(ips4)} v6={len(ips6)}",
        "#",
        *CONTROLPLANE,
        *derp_body,
    ]
    RULES.mkdir(parents=True, exist_ok=True)
    DERP_OUT.write_text("\n".join(derp_lines) + "\n")
    print(f"wrote {DERP_OUT} lines={len(derp_lines)}")

    direct_lines = [
        "# Tailscale DIRECT 合集：控制面域名/IP + DERP + STUN/3478",
        "# 策略请挂 DIRECT（建议加 extended-matching）",
        "# 不含 MagicDNS / 100.64 CGNAT（那些走 Tailnet 策略，见 Tailscale-Tailnet.list）",
        f"# derp nodes={len(hosts)} v4={len(ips4)} v6={len(ips6)}",
        "#",
        "# --- domains ---",
        "DOMAIN-SUFFIX,tailscale.com",
        "DOMAIN-SUFFIX,tailscale.io",
        "DOMAIN-SUFFIX,tailscale.net",
        "DOMAIN-SUFFIX,ipn.dev",
        "DOMAIN,controlplane.tailscale.com",
        "DOMAIN,login.tailscale.com",
        "DOMAIN,log.tailscale.com",
        "#",
        "# --- controlplane IP (ARIN TAILS / TAILSCALE) ---",
        "IP-CIDR,192.200.0.0/24",
        "IP-CIDR,199.165.136.0/24",
        "IP-CIDR6,2606:b740::/32",
        "#",
        "# --- STUN / Port Map ---",
        "AND,((PROTOCOL,UDP),(DEST-PORT,3478))",
        "#",
        "# --- DERP relays ---",
        *derp_body,
    ]
    DIRECT_OUT.write_text("\n".join(direct_lines) + "\n")
    print(f"wrote {DIRECT_OUT} lines={len(direct_lines)}")


if __name__ == "__main__":
    main()
