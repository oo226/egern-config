# egern-config

个人 Egern **自用** 配置。去广告默认走 **上游原样合集**（不打本地补丁）。

> **搬运**：公开上游镜像，仅供个人学习。版权归原作者 → [DISCLAIMER.md](DISCLAIMER.md)  
> **怎么用**：[USAGE.md](USAGE.md)

[![Sync Rules](https://github.com/oo226/egern-config/actions/workflows/sync-rules.yml/badge.svg?branch=sync)](https://github.com/oo226/egern-config/actions/workflows/sync-rules.yml)

## 快速导入

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Egern.yaml
```

模块中心：https://oo226.github.io/egern-config/

## 去广告怎么来的

```
上游 raw（奶思 / blackmatrix7 / 毒奶 / chxm）
        │  1:1 下载，零改写
        ▼
Modules/vendors/*.module   ← 单源原样副本 + SHA256
        │  只做段落拼接 + 去重
        ▼
Modules/adblock-verbatim.module   ← Egern 默认用这个
```

旧版打补丁合集 `adblock-collection.module` 仍发布，仅作回滚。

## main 结构

```
main/
├── Egern.yaml
├── Modules/
│   ├── adblock-verbatim.module    # 默认去广告
│   ├── vendors/                   # 上游原样子文件
│   ├── unlock-collection.module
│   └── …
├── Routing/
├── Scripts/
├── Widgets/
└── site/
```

## 分支

| 分支 | 用途 |
|------|------|
| **main** | Egern 日常 |
| **surge** | Surge 成品 |
| **sync** | 工厂：同步上游 → 发布 |

常用链接见 [USAGE.md](USAGE.md)。
