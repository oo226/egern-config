# 使用菜单（main）

> 只挑你要用的链接。技术细节 / 免责：[DISCLAIMER.md](DISCLAIMER.md)。

**主配置：**

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Egern.yaml
```

**模块中心：** https://oo226.github.io/egern-config/  
（打开默认是「默认开启」；镜像仓库副本不铺满列表）

**Surge：**

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/surge/Surge.conf
```

完整前缀：`https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main`

---

## 一、每天开着的

| 名称 | 路径 | 说明 |
|------|------|------|
| 去广告合集 | `Modules/adblock-collection.module` | **唯一入口名**；不含签到 cron |
| 解锁合集 | `Modules/unlock-collection.module` | 默认开；已含 Spotify |
| PingMe | `Modules/pingme.sgmodule` | 抓完参数改成 `#` |
| 插件跳转 | `Modules/ibl3nd-plugin-hub.yaml` | 默认开 |
| 今日油价 | `Widgets/IBL3ND/Oil_Widget.JS` | 只写 `widgets`，勿进 `scriptings` |
| 追风 | `Egern.yaml` + `Routing/Zhuifeng.yaml` | 途游挂机 |

兼容别名 `adblock-egern*.module` 仍发布（旧书签不断），**新配置请用 `adblock-collection`**。

---

## 二、按需

| 名称 | 路径 | 何时开 |
|------|------|--------|
| Cookie 合集 | `Modules/cookie-collection.module` | 签到前抓 ck，抓完关 |
| iRingo | `Modules/iringo-*.sgmodule` | 同时开 `iringo-mitm.yaml` |
| BoxJS 订阅 | `Modules/egern.boxjs.json` | BoxJS 里加这一条即可 |

---

## 三、签到脚本

镜像在 `Scripts/` 根目录 `*.js`，默认**不**写入 Egern。需要时在 `scriptings` 加 `schedule`。

详见 [Scripts/README.md](Scripts/README.md)。

---

## 四、分流（Egern 已引用）

| 文件 | 用途 |
|------|------|
| `Routing/Bootstrap-Direct.yaml` | 测网直连 |
| `Routing/Tailscale-Direct.yaml` | Tailscale |
| `Routing/China-Direct.yaml` | 国内直连 |
| `Routing/Reject-Hot.yaml` / `Reject-Merged.yaml` | 去广告 |
| `Routing/Foreign/AI-Merged.yaml` | AI（唯一 AI 入口） |
| `Routing/Foreign/*` | 按服务分流 |

说明：[Routing/README.md](Routing/README.md)

---

## 五、黑盒（别手改）

| 路径 | 说明 |
|------|------|
| `Scripts/_external/` | 合集依赖镜像 |
| `Scripts/fmz200/` 等作者目录 | 防删库全量镜像 |
| `Modules/adblock-egern*` | 合集兼容别名 |

---

## 六、分支

| 分支 | 你看吗 | 干什么 |
|------|--------|--------|
| **main** | **只看这个** | Egern 成品 |
| **surge** | Surge 用 | `Surge.conf` + `Rules/` |
| sync | 可忽略 | 每日上游同步 → 发布 |

---

## 七、BoxJS

合集已带 BoxJS 引擎（`http://boxjs.com`）。**只加这一条订阅：**

```
https://raw.githubusercontent.com/oo226/egern-config/main/Modules/egern.boxjs.json
```

播放器 / 签到 / iRingo / Cookie 都在订阅里，不必在中心页翻一百多个应用。

旧版 `yu9191-player.boxjs.json` 仍保留；新用户用统一订阅。

---

## 八、改哪里

| 想改 | 改哪里 |
|------|--------|
| 节点 / 策略组 / 开关 | `main` 的 `Egern.yaml` |
| 去广告源 / 合并逻辑 | `sync` 的 `scripts/`、`Modules/manifest.yaml` |
| 已填进 Egern 的路径 | **别改路径**（raw URL 要稳） |
