# egern-config

个人 Egern（松鼠）配置文件与规则镜像仓库。

[![Sync Rules](https://github.com/oo226/egern-config/actions/workflows/sync-rules.yml/badge.svg)](https://github.com/oo226/egern-config/actions/workflows/sync-rules.yml)

## 自动同步（不依赖本地电脑）

**GitHub Actions 会在云端自动运行**，你的电脑关机也没关系：

| 触发方式 | 说明 |
|---------|------|
| **定时** | 每天 **11:00（北京时间）** 自动从上游拉取最新规则 |
| **手动** | Actions 页 → Sync Egern Rules → Run workflow |

规则自 [Repcz/Tool](https://github.com/Repcz/Tool/tree/X/Egern/Rules) 与 [skk.moe](https://ruleset.skk.moe) 同步到 `Rules/`，`Egern.yaml` 只引用本仓库链接。

## Egern 导入地址

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Egern.yaml
```

## 目录结构

```
egern-config/
├── Egern.yaml              # 主配置
├── Rules/
│   ├── China-Direct.yaml   # 国内规则合并去重 (Actions 自动生成)
│   ├── Reject.yaml         # 去广告
│   └── ...                 # 各分类规则 (上游镜像)
├── Modules/                # 去广告合集 adblock-collection.module
├── scripts/                # 签到脚本镜像 + 同步工具
└── .github/workflows/      # 每日自动同步
```

## 国内规则合并

`Rules/China-Direct.yaml` 由 Actions 自动合并以下上游文件并去重：

Direct + WeChat + Bilibili + AppleCN + ChinaDomain + ChinaIP + ChinaASN

`Egern.yaml` 只引用 `Lan.yaml` + `China-Direct.yaml`，上游更新后合并文件会自动刷新。

## 去广告 / 去开屏合集

原先十几个 QingRex / 可莉 / 微信模块，已合并为 **一个合集**：

| 文件 | 上游 | 说明 |
|------|------|------|
| `Modules/adblock-collection.module` | fmz200 奶思 blockAds | App/小程序净化 + 去开屏（约 730 款） |

Egern 另保留 **HTTPDNS 拦截**、**BoxJs**（签到）、**跳过代理列表** 三个基础模块。

分流已合并：`Rules/China-Direct.yaml` + `Rules/Reject.yaml`。

## 签到脚本

`scripts/` 目录镜像签到脚本（ZenmoFeiShi / chavyleung / Yuheng0101 等，见 `scripts/manifest.yaml`）。Actions 每日自动同步。

## 快速开始

### 1. 创建 GitHub 仓库

在 GitHub 新建仓库，例如 `egern-config`（Public）。

### 2. 推送本目录

```powershell
cd C:\Users\Administrator\egern-config
.\push-github.ps1
```

### 3. 规则自动更新

**无需操作。** GitHub Actions 每天自动同步；也可在 Actions 页手动 Run workflow。

### 4. 修改 Egern.yaml

全局替换：

- 配置已使用 GitHub 用户名 `oo226`（若 fork 请自行替换）
- `https://你的订阅链接` → 机场订阅

### 5. 导入 Egern

iPhone 打开 raw 链接或 AirDrop 本地 `Egern.yaml`：

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Egern.yaml
```

## 规则来源

| 文件 | 上游 |
|------|------|
| `Rules/*.yaml` | [Repcz/Tool/X/Egern/Rules](https://github.com/Repcz/Tool/tree/X/Egern/Rules) |
| `Rules/skk/reject.conf` | [ruleset.skk.moe](https://ruleset.skk.moe/List/domainset/reject.conf) |

## 本地手动同步

```powershell
.\scripts\sync-rules.ps1
git add Rules/
git commit -m "chore: manual rule sync"
git push
```

## 许可说明

规则文件版权归各上游项目所有，本仓库仅作个人镜像与引用。
