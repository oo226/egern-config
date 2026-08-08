# 模块（Modules）

> 镜像合并自用，上游版权归原作者。不合理请联系删除，见 [DISCLAIMER.md](../DISCLAIMER.md)。

目录名用英文，避免 raw 链接被 URL 编码。

**模块**通过 URL Rewrite、MITM、Script 拦截 App 内广告和开屏。

## 文件对照

| 文件 | 中文名 | 说明 |
|------|--------|------|
| `adblock-collection.module` | 去广告净化合集 | **唯一入口** — 奶思 + blackmatrix7 + 毒奶网页去广告 + 银行/NB 每日合并去重（**不含签到/cron**） |
| `unlock-collection.module` | 解锁增强合集 | **唯一入口** — 跳过代理、链接解锁、Spotify、VIP、ddm1023、ShortcutStudio 等 |
| `cookie-collection.module` | 抓参 Cookie 合集 | **按需启用** — 奶思 cookies.module，签到前抓 ck/token，抓完建议关闭 |
| `qdreader.sgmodule` | 起点读书签到 | Yuheng 镜像；**保留 Egern 模版参数**（抓写/激励/抽奖等） |
| `Modules/yuheng/` | Yuheng 其它签到模块 | 全量 profiles 镜像，防删库 |
| `Modules/qingrex-signin/` | 可莉签到模块 | 逐个镜像，保留参数 |

## 上游从哪来？

完整清单：`scripts/upstream-sources.yaml`（每日同步写入 `site/upstreams.json`）。

**原则：盯着的仓尽量全拉成本仓副本（防删库）；能进大合集的进合集；带 `#!arguments` 的签到模块单独保留，方便 Egern 里改模版参数。**

**代理检测（skip-proxy / always-real-ip）**：只写在主配置（`surge/Surge.conf` / `Egern.yaml`）。去广告/解锁合集已剥离，勿再叠装 Fries General 或本目录 `skip-proxy-collection`。


## raw 链接

去广告：
```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Modules/adblock-collection.module
```

解锁：
```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Modules/unlock-collection.module
```

抓参（默认关，抓完关闭省电）：
```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Modules/cookie-collection.module
```

改 `custom-apps.sgmodule` 后 push，Actions 下次运行会合并进 `adblock-collection.module`。

**ddm1023（chxm1023）**：`Collections` + `AppAd` 已并入合集；`Scripts/chxm1023/` 每日镜像 Rewrite（318）+ Advertising（39）全部 JS，上游删库仍可用本仓库副本。
