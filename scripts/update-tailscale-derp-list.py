#!/usr/bin/env python3
"""Regenerate Surge/Rules/Tailscale-DERP.list from Tailscale derpmap."""
from __future__ import annotations
import json, ssl, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Surge" / "Rules" / "Tailscale-DERP.list"
URL = "https://login.tailscale.com/derpmap/default"

def main() -> None:
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
    lines = [
        "# Tailscale DERP relays (from login.tailscale.com/derpmap/default)",
        "# DERP 客户端常按 IP 拨号，DOMAIN-SUFFIX 匹配不到 → 掉进 FINAL/节点选择",
        "# 本表：DOMAIN + IP/32 + IP6/128 → 策略请挂 DIRECT",
        f"# nodes={len(hosts)} v4={len(ips4)} v6={len(ips6)}",
    ]
    for h in sorted(hosts):
        lines.append(f"DOMAIN,{h}")
    for ip in sorted(ips4, key=lambda x: tuple(int(p) for p in x.split("."))):
        lines.append(f"IP-CIDR,{ip}/32")
    for ip in sorted(ips6):
        lines.append(f"IP-CIDR6,{ip}/128")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT} lines={len(lines)}")

if __name__ == "__main__":
    main()
