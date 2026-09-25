# 分流规则（Routing）

> 部分规则由上游镜像合并。见 [DISCLAIMER.md](../DISCLAIMER.md)。

**分流** = 直连 / 代理 / REJECT。与 `Modules/` 的 URL 改写不是一类东西。

## Egern 在用的

| 文件 | 说明 |
|------|------|
| `Bootstrap-Direct.yaml` | 测网直连 |
| `Tailscale-Direct.yaml` | Tailscale 域名 + CGNAT |
| `Unbreak.yaml` | 防误代理 |
| `Reject-Hot.yaml` | 热点广告（先于大表） |
| `Direct-Priority.yaml` | 优先直连 |
| `China-Direct.yaml` | 国内直连大合集 |
| `Reject-Merged.yaml` | 去广告统一表 |
| `Privacy-Reject.yaml` | WebRTC |
| `Lan.yaml` / `Zhuifeng.yaml` | 局域网 / 追风 |
| `Foreign/AI-Merged.yaml` | **AI 唯一入口** |
| `Foreign/*.yaml` + `Foreign/App/*` | 按服务 / App |

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Routing/China-Direct.yaml
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Routing/Foreign/AI-Merged.yaml
```

## 不在 main 的

| 路径 | 说明 |
|------|------|
| `Foreign/AI.yaml`、`AI-supplement.yaml` | 合并中间件，只留在 **sync** |
| `_upstream/` | CI 临时目录，不提交 |

## Surge

不要直接引用本目录 `*.yaml`。成品在 **`surge` 分支** `Rules/`。

备份点：`backup/adblock-before-rule-split-ac83`。
