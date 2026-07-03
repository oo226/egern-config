# egern-config

个人 Egern（松鼠）配置文件与规则镜像仓库。

规则自 [Repcz/Tool](https://github.com/Repcz/Tool/tree/X/Egern/Rules)（blackmatrix7 等转换）与 [skk.moe](https://ruleset.skk.moe) 每日自动同步到 `Rules/`，主配置 `Egern.yaml` 引用本仓库 raw 地址。

## 目录结构

```
egern-config/
├── Egern.yaml              # 主配置 (导入 Egern)
├── Rules/                  # 规则镜像 (Actions 自动填充)
│   ├── Reject.yaml
│   ├── ChinaDomain.yaml
│   └── skk/reject.conf
├── .github/workflows/
│   └── sync-rules.yml      # 每日同步上游规则
└── scripts/sync-rules.ps1  # 本地手动同步
```

## 快速开始

### 1. 创建 GitHub 仓库

在 GitHub 新建仓库，例如 `egern-config`（Public）。

### 2. 推送本目录

```powershell
cd d:\共享\egern-config
git init
git add .
git commit -m "init: egern config and rule sync workflow"
git branch -M main
git remote add origin https://github.com/oo226/egern-config.git
git push -u origin main
```

### 3. 首次同步规则

GitHub 仓库 → **Actions** → **Sync Egern Rules** → **Run workflow**

运行完成后 `Rules/` 下会出现 25+ 规则文件。

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
