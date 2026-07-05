# egern-config

个人 Egern（松鼠）配置 — **分流 / 模块 / 脚本** 分目录，整合结果每日同步到 `main`。

[![Sync Rules](https://github.com/oo226/egern-config/actions/workflows/sync-rules.yml/badge.svg)](https://github.com/oo226/egern-config/actions/workflows/sync-rules.yml)

## 导入地址

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Egern.yaml
```

## 目录一览（看 main 分支即可）

```
egern-config/
├── Egern.yaml                 # 主配置
├── 分流/                      # 分流规则（走哪个节点 / REJECT）
│   ├── 国内直连.yaml          # 国内合并去重（一个文件）
│   ├── 去广告.yaml            # 广告域名合并去重（一个文件）
│   ├── 局域网.yaml
│   └── 国外/                  # 国外按服务分开（节点不同）
│       ├── AI.yaml
│       ├── Telegram.yaml
│       └── …
├── 模块/                      # 去广告/去开屏/重写（一个合集）
│   └── 去广告净化合集.module
└── 脚本/                      # 签到脚本镜像
    └── *.js
```

## 三类文件怎么区分？

| 目录 | 是什么 | 举例 |
|------|--------|------|
| **分流/** | 域名/IP 走直连、代理还是 REJECT | `国内直连.yaml`、`去广告.yaml`、`国外/AI.yaml` |
| **模块/** | App 内 URL 重写、MITM、开屏脚本 | `去广告净化合集.module`（含 NB/银行补全） |
| **脚本/** | Egern 定时/抓参签到 JS | `PingMe.js`、`mixc_signin.js` |

## 分支说明

| 分支 | 用途 |
|------|------|
| `main` | **你用这个** — 每日整合后的干净快照 |
| `cursor/nb-rules-merge-ac83` | Actions 集成支 — 拉上游、合并、去重，完成后复制到 `main` |

## 自动同步

每天 **11:00 北京时间**，Actions 会：

1. 在 `cursor/nb-rules-merge-ac83` 拉取 Repcz / Sukka / fmz200 / blackmatrix7 等上游
2. 合并去重 → `分流/国内直连.yaml`、`分流/去广告.yaml`、`模块/去广告净化合集.module`
3. 将结果同步到 **`main`**

## 本地手动同步

```bash
python3 scripts/download-rules.py
python3 scripts/merge-china-rules.py
python3 scripts/merge-reject-rules.py
python3 scripts/merge-adblock-modules.py
```

`scripts/` 是开发/CI 工具目录，日常使用只看 `分流/`、`模块/`、`脚本/`。

## 许可

规则与模块版权归各上游项目所有，本仓库仅作个人镜像与引用。
