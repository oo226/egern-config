# 模块（Modules）

> 镜像合并自用，上游版权归原作者。不合理请联系删除，见 [DISCLAIMER.md](../DISCLAIMER.md)。

目录名用英文，避免 raw 链接被 URL 编码。

**模块**通过 URL Rewrite、MITM、Script 拦截 App 内广告和开屏。

## 文件对照

| 文件 | 中文名 | 说明 |
|------|--------|------|
| `adblock-collection.module` | 去广告合集 | **唯一入口** — 奶思 + blackmatrix7 + 补全（**不含** skip-proxy / 签到 cron） |
| `unlock-collection.module` | 解锁合集 | **唯一入口** — 链接解锁、Spotify VIP、HTTPDNS、屏蔽更新等（**已含** Spotify，勿再装单独份） |
| `cookie-collection.module` | Cookie 合集 | **按需** — 签到前抓 ck，抓完关掉 |
| `qdreader.sgmodule` / `pingme.*` | 签到 | 带模版参数，单独保留 |
| `iringo-*.sgmodule` |  iRingo | 地图/天气/定位，与去广告无关 |

已从 main **停发**：`skip-proxy-collection`、`spotify-unlock`（仅 sync 工厂合并用）。`skip-proxy` / `always-real-ip` 只写主配置。

## 上游从哪来？

完整清单：`scripts/upstream-sources.yaml`（每日同步写入 `site/upstreams.json`）。

**原则：盯着的仓尽量全拉成本仓副本（防删库）；能进大合集的进合集；带 `#!arguments` 的签到模块单独保留，方便 Egern 里改模版参数。**

## raw 链接（用户入口）

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Modules/adblock-collection.module
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Modules/unlock-collection.module
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Modules/cookie-collection.module
```

改 `custom-apps.sgmodule` 后 push，Actions 下次合并进去广告合集。
