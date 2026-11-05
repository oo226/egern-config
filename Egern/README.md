# Egern 懒人配置（guize）

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Egern/Profile.yaml
```

- **外观短**：Profile 只挂少量规则集名字；广告分流表在 `Routing/`  
- **去广告**：日常 `quguanggao`（可莉线）；`naisi-ads` 可选默认关，**勿同开**（学老书：拆开挂，别塞一个巨无霸）  
- **DNS**：无 `system` bootstrap；`hosts` 钉 DoH；Ali/Byte/Google 分流；直连大名单 DNS+分流双挂（对齐 [jnlaoshu/MySelf](https://github.com/jnlaoshu/MySelf/tree/main/Egern) 2026.09 + Egern 2.20）  
- **客户端**：建议 App Store / TF ≥ **2.20.0**（策略组直接 `urls`、Smart 记真实失败、`h3://` DNS、Snell/REALITY 等）。TF：https://testflight.apple.com/join/AzU6kAzX
- **Tailscale（Egern 内置）**：`Tailscale-Direct` + `real_ip` + `bypass_tunnel_proxy`；DNS 把 `ts.net` 转到 `100.100.100.100`（MagicDNS）。**不要**把 `100.64/10` 放进 `vif_excluded`。能开 `100.x` 但打不开 `xxx.ts.net`：先试 **http://**（https 要在 Tailscale 后台打开 Enable HTTPS）；再强制更新 Profile。官方 App 双开时才把 `100.64/10`、`fd7a::/48` 加回 excluded。

Sub-Store 组合订阅名填 `AllServer`。强制更新 Profile 后生效。
