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
| `iringo-maps.sgmodule` |  iRingo 地图 | **按需启用** — NSRingo 地图增强（国际版功能、高德/Apple 切换） |
| `iringo-weather.sgmodule` |  iRingo 天气 | **按需启用** — NSRingo WeatherKit 增强（彩云/和风数据源） |
| `iringo-location.sgmodule` |  iRingo 定位 | **按需启用** — NSRingo 定位服务增强 |
| `iringo-others.sgmodule` |  iRingo 其他 | **按需启用** — TV / TestFlight / News |
| `custom-apps.sgmodule` | 本地补全源 | 银行/税务/NBToolAds，合并时自动并入去广告合集 |
| `patches-unlock.sgmodule` | 本地解锁补全 | P12/OCSP、系统更新屏蔽，合并时自动并入解锁合集 |

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
