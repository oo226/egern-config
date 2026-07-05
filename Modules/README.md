# 模块（Modules）

目录名用英文，避免 raw 链接被 URL 编码。

**模块**通过 URL Rewrite、MITM、Script 拦截 App 内广告和开屏。

## 文件对照

| 文件 | 中文名 | 说明 |
|------|--------|------|
| `adblock-collection.module` | 去广告净化合集 | **唯一入口** — 奶思 + blackmatrix7 + 毒奶网页去广告 + 银行/NB 每日合并去重 |
| `unlock-collection.module` | 解锁增强合集 | **唯一入口** — 跳过代理、链接解锁、Spotify、VIP、屏蔽更新等 |
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

改 `custom-apps.sgmodule` 后 push，Actions 下次运行会合并进 `adblock-collection.module`。
