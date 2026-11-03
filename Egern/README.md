# Egern 懒人配置（guize）

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Egern/Profile.yaml
```

- **外观短**：Profile 只挂少量规则集名字；广告分流表在 `Routing/`  
- **去广告**：日常 `quguanggao`（可莉线）；`naisi-ads` 可选默认关，**勿同开**（学老书：拆开挂，别塞一个巨无霸）  
- **DNS**：无 `system` bootstrap；`hosts` 钉 DoH；Ali/Byte/Google 分流；直连大名单 DNS+分流双挂（对齐 [jnlaoshu/MySelf](https://github.com/jnlaoshu/MySelf/tree/main/Egern) 2026.09）  
- **客户端**：正式版按 App Store **2.20.0** 写（美区/台区一致；官方频道有 2.18→2.20 完整说明）。手机上若显示 2.21，多半是 TF/自签，**官方尚未公布 2.21 配置字段变更**。TF：https://testflight.apple.com/join/AzU6kAzX  
- **对照热度**（GitHub ★，抽样 2026-11-03）：[jnlaoshu/MySelf](https://github.com/jnlaoshu/MySelf) ≈606（专用 Profile 基线，跟这个）· [IBL3ND/Egern](https://github.com/IBL3ND/Egern)（iBL3ND/3N）≈34（懒人全包，DNS 含 `system` 易污染，不当骨架）· [fmz200/wool_scripts](https://github.com/fmz200/wool_scripts) ≈5.9k（规则/脚本仓，不是完整 Profile）

Sub-Store 组合订阅名填 `AllServer`。强制更新 Profile 后生效。
