# egern-config

个人 Egern **自用** 配置仓库。目录英文命名，避免 raw 链接 URL 编码。

> **搬运说明**：规则/模块/脚本来自公开上游镜像与合并，仅供个人学习使用。  
> **版权**：版权归原作者及原项目；若认为不合理请 [联系删除](DISCLAIMER.md)。  
> **怎么用**：请看 **[USAGE.md](USAGE.md)**（菜单） · **[DISCLAIMER.md](DISCLAIMER.md)**（免责）

[![Sync Rules](https://github.com/oo226/egern-config/actions/workflows/sync-rules.yml/badge.svg)](https://github.com/oo226/egern-config/actions/workflows/sync-rules.yml)

## 快速导入

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Egern.yaml
```

**模块中心（网页浏览 / 一键添加）：** https://oo226.github.io/egern-config/

## main 里有什么（一眼看懂）

```
main/
├── Egern.yaml              # 主配置模板
├── USAGE.md                # ← 你要的链接菜单
├── DISCLAIMER.md           # 搬运工免责 / 删除联系
├── Routing/                # 分流成品（无 _upstream）
├── Modules/                # 三个大合集 + 插件跳转
├── Scripts/                # 签到 JS + 模块依赖镜像
├── Assets/geoip/           # GeoIP 数据库
└── Widgets/IBL3ND/         # 小组件脚本
```

**不在 main**：`scripts/`（Python 工具）、`Modules/_upstream/`、`publish/` — 仅在 `sync` 分支。

## 分支

| 分支 | 用途 |
|------|------|
| **`main`** | 日常用 — Egern 拉这个 |
| **`sync`** | Actions 每日上游同步，自动发布到 main |

## 常用链接

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Modules/adblock-collection.module
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Modules/unlock-collection.module
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Routing/China-Direct.yaml
```

完整列表见 [USAGE.md](USAGE.md)。
