# 规则文件说明

本目录为 **自托管镜像**，Egern 主配置 `Egern.yaml` 仅引用本仓库 raw 链接。

## 来源与许可

| 文件 | 上游 |
|------|------|
| `*.yaml` | [Repcz/Tool/X/Egern/Rules](https://github.com/Repcz/Tool/tree/X/Egern/Rules) |
| `skk/reject.conf` | [ruleset.skk.moe](https://ruleset.skk.moe/List/domainset/reject.conf) |

上游基于 blackmatrix7、ACL4SSR 等社区规则转换，版权归原作者所有。

## 更新方式

- **GitHub Actions**：仓库 Actions → `Sync Egern Rules` → Run workflow（推荐，每日自动）
- **本地脚本**：`python scripts/download-rules.py`

## 自托管链接格式

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Rules/<文件名>.yaml
```
