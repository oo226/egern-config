# Egern/Routing（guize）

本分支自用的合并分流表，供 `Profile.yaml` 引用。  
广告 → `Reject-Merged`；国内 → `China-Direct`；结构与日用懒人一致。

## 优先直连（整表）

`Direct-Priority.yaml` 已合并：

- 基表（Microsoft / AppleServers 等）
- **eulac 网盘点播**（`PanVod-Direct.yaml` / `Yuanban/heji/fenliu/eulac-网盘点播.yaml`）
- **eulac 视频资源站**（`ResourceSite-Direct.yaml` / `eulac-视频资源站.yaml`）
- **PingMe**（`PingMe-Direct.yaml`）
- 120399 / 起点 / DoH IP 等原散落后缀

Profile 只挂这一张「优先直连」，不要再往 rules 里塞单行 `ip_cidr` / `domain`。  
重跑合并：`python3 scripts/publish-direct-priority.py`

## Tailscale

`Tailscale-Direct.yaml`：控制面后缀（`tailscale.com` / `ts.net`）+ CGNAT + **DERP 主机/IP**  
（按 IP 拨号时仅 DOMAIN 会掉 FINAL → 美国节点）。

上游单件仍保留在 `Yuanban/heji/fenliu/eulac-*.yaml|.lsr` 供 Surge/Loon 引用。
