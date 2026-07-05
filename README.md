# egern-config

个人 Egern 配置。**目录用英文命名**，避免 raw 链接出现 `%E6%...` 编码；中文说明见各目录 README。

[![Sync Rules](https://github.com/oo226/egern-config/actions/workflows/sync-rules.yml/badge.svg)](https://github.com/oo226/egern-config/actions/workflows/sync-rules.yml)

## 导入地址

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Egern.yaml
```

## 目录一览（看 main 即可）

```
egern-config/
├── Egern.yaml
├── Routing/                   # 分流规则
│   ├── China-Direct.yaml      # 国内直连（合并去重）
│   ├── Reject-Merged.yaml     # 去广告域名（合并去重）
│   ├── Lan.yaml               # 局域网
│   └── Foreign/               # 国外按服务分开
├── Modules/                   # 去广告/去开屏（一个合集）
│   └── adblock-collection.module
└── Scripts/                   # 签到脚本
    └── *.js
```

## 三类文件

| 目录 | 中文 | 干什么 |
|------|------|--------|
| `Routing/` | 分流 | 域名走直连 / 代理 / REJECT |
| `Modules/` | 模块 | App URL 重写、MITM、开屏脚本 |
| `Scripts/` | 脚本 | 签到 JS |

## 分支

| 分支 | 用途 |
|------|------|
| **`main`** | 你用这个 — 每日整合快照 |
| `cursor/nb-rules-merge-ac83` | Actions 集成支 → 自动同步到 main |

## 链接示例（干净、无中文编码）

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Modules/adblock-collection.module
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Routing/China-Direct.yaml
```

`scripts/` 是 CI 工具目录，日常使用可忽略。
