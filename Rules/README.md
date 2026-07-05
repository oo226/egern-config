# 规则文件说明

本目录为 **自托管镜像**，Egern 主配置 `Egern.yaml` 仅引用本仓库 raw 链接。

## 合并产物（Actions 每日自动生成）

| 文件 | 合并来源 | 说明 |
|------|----------|------|
| `China-Direct.yaml` | Direct + WeChat + Bilibili + AppleCN + ChinaDomain + ChinaIP + ChinaASN | 国内直连，去重后单文件，**头注释标注各源** |
| `Reject-Merged.yaml` | `Reject.yaml` + `skk/reject.conf` | 去广告域名 REJECT，去重后单文件 |

上游镜像仍保留在 `Reject.yaml`、`skk/reject.conf` 等路径，供合并脚本读取；**Egern 只引用合并后的文件**。

## 来源与许可

| 文件 | 上游 |
|------|------|
| `*.yaml` | [Repcz/Tool/X/Egern/Rules](https://github.com/Repcz/Tool/tree/X/Egern/Rules) |
| `skk/reject.conf` | [ruleset.skk.moe](https://ruleset.skk.moe/List/domainset/reject.conf) |

上游基于 blackmatrix7、ACL4SSR、Sukka 等社区规则转换，版权归原作者所有。

## 更新方式

- **GitHub Actions**：仓库 Actions → `Sync Egern Rules` → Run workflow（推荐，每日自动）
- **本地脚本**：
  ```bash
  python3 scripts/download-rules.py
  python3 scripts/merge-china-rules.py
  python3 scripts/merge-reject-rules.py
  ```

## 自托管链接格式

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Rules/<文件名>.yaml
```
