# egern-config

个人 Egern **自用** 配置。三层分工，别把工厂目录当成品逛。

> **搬运**：规则/模块/脚本来自公开上游镜像，仅供个人学习。  
> **版权**：归原作者；不合理请 [联系删除](DISCLAIMER.md)。  
> **怎么用**：[USAGE.md](USAGE.md) · [DISCLAIMER.md](DISCLAIMER.md)

[![Sync Rules](https://github.com/oo226/egern-config/actions/workflows/sync-rules.yml/badge.svg?branch=sync)](https://github.com/oo226/egern-config/actions/workflows/sync-rules.yml)

## 30 秒导入

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Egern.yaml
```

模块中心（默认只看「默认开启」）：https://oo226.github.io/egern-config/

Surge 独立分支：

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/surge/Surge.conf
```

## 你真正要看的（main）

```
main/
├── Egern.yaml                 # 唯一主配置
├── USAGE.md                   # 链接菜单
├── Modules/
│   ├── adblock-collection.module   # 去广告 · 唯一入口名
│   ├── unlock-collection.module
│   ├── cookie-collection.module    # 按需
│   ├── pingme.sgmodule
│   ├── ibl3nd-plugin-hub.yaml
│   └── iringo-* / egern.boxjs.json
├── Routing/                   # 分流（Egern 已引用）
├── Scripts/*.js               # 常用签到（默认不写入 Egern）
├── Widgets/IBL3ND/            # 小组件
└── site/                      # 模块中心网页
```

## 不用当目录逛的（仍要发布）

| 路径 | 为什么在 |
|------|----------|
| `Modules/adblock-egern*.module` | **兼容别名**（与合集同内容），旧 URL 不断 |
| `Scripts/_external/` | 合集内部依赖镜像，**勿手改** |
| `Scripts/<作者>/` | 上游全量镜像，防删库；合集已指到这里 |
| `Modules/qingrex-signin/`、`yuheng/` | 带参数的签到模块镜像 |

## 分支

| 分支 | 干什么 |
|------|--------|
| **`main`** | 日常用 — Egern / 中心页只盯这个 |
| **`surge`** | Surge 成品 |
| **`sync`** | 工厂：上游同步、合并、再发布到 main/surge |

## 常用链接

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Modules/adblock-collection.module
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Modules/unlock-collection.module
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Routing/China-Direct.yaml
```

完整列表见 [USAGE.md](USAGE.md)。
