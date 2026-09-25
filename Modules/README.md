# 模块（Modules）

> 镜像合并自用。版权归上游；不合理见 [DISCLAIMER.md](../DISCLAIMER.md)。

## 日常入口（只认这些）

| 文件 | 说明 |
|------|------|
| `adblock-collection.module` | **去广告唯一入口** |
| `unlock-collection.module` | **解锁唯一入口**（已含 Spotify） |
| `cookie-collection.module` | 按需抓 Cookie |
| `pingme.sgmodule` | PingMe（带模版参数） |
| `ibl3nd-plugin-hub.yaml` | 插件跳转 |
| `iringo-*.sgmodule` + `iringo-mitm.yaml` |  iRingo |
| `egern.boxjs.json` | 统一 BoxJS 订阅 |

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Modules/adblock-collection.module
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Modules/unlock-collection.module
```

## 兼容 / 镜像（可忽略）

| 文件 | 说明 |
|------|------|
| `adblock-egern.module` / `adblock-egern-v0815b/c.module` | 与合集**同内容**的旧别名，URL 不断 |
| `pingme.yaml` | 已不推荐，请用 `pingme.sgmodule` |
| `qingrex-signin/`、`yuheng/` | 带 `#!arguments` 的签到模块镜像 |
| `nb-weixin-fix.yaml` | 不拉主配置时的独立 NB/微信模块 |

工厂中间件（`custom-apps`、`*-extra`、`skip-proxy-collection` 等）**只在 sync**，不进 main。

## 分流 vs 模块

整域广告 → `Reject-Merged` REJECT。同域混业务 → 合集 MITM/改写。合集里的 DOMAIN REJECT 会并进 `Reject-Merged.yaml`；热点标 `# @keep` 的两边都留。更新合集后请强制更新 `Reject-Merged`。
