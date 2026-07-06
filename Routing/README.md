# 分流规则（Routing）

> 部分规则由上游镜像合并，仅供个人自用。见 [DISCLAIMER.md](../DISCLAIMER.md)。

目录名用英文，避免 raw 链接被 URL 编码。中文说明见下表。

**分流规则**决定流量走直连、代理还是 REJECT。与 `Modules/` 里的 URL 重写（去开屏）不是同一类东西。

## 文件对照

| 文件 | 中文名 | 说明 |
|------|--------|------|
| `Bootstrap-Direct.yaml` | 系统测网直连 | Captive/联网检测（不含公共 DNS IP，避免国内 dns relay timeout） |
| `Zhuifeng.yaml` | 追风挂机 | 途游 sq-hlsg / open-hlsg → 专用 HTTP 代理 |
| `Privacy-Reject.yaml` | WebRTC 防护 | STUN / webrtc.org 拦截 |
| `Lan.yaml` | 局域网 | 局域网直连 |
| `China-Direct.yaml` | 国内直连 | **合并去重** — Direct+微信+B站+苹果中国+国内域名/IP/ASN |
| `Reject-Merged.yaml` | 去广告 | **合并去重** — Repcz Reject + Sukka 广告域名集 |
| `Foreign/*.yaml` | 国外分流 | **按服务分开** — AI/Telegram/流媒体/游戏/兜底等 |

## raw 链接示例（可直接用）

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Routing/China-Direct.yaml
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Routing/Reject-Merged.yaml
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Routing/Foreign/AI.yaml
```

`_upstream/` 为 CI 临时目录，不提交。
