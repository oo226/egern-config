# Surge 配置（`surge` 分支）

与 **`main`（Egern）完全分开**：不覆盖 `Egern.yaml` / `Routing/*.yaml`。

## 导入

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/surge/Surge.conf
```

规则目录：

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/surge/Rules/
```

## 分流怎么给 Surge 用？

手册（[Rule Sets](https://manual.nssurge.com/rules/ruleset.html)）：

| 格式 | 用法 | 本仓库 |
| --- | --- | --- |
| **RULE-SET** | 每行 `DOMAIN-SUFFIX,example.com` 等（无策略） | `Rules/**/*.list`（同 blackmatrix7） |
| **DOMAIN-SET** | 每行一个域名；`.example.com` = 后缀 | `Rules/**/*.domainset`（同 Sukka domainset） |
| Egern YAML | `domain_suffix_set:` … | **不能**给 Surge 用 |

`sync` 每日把 Egern `Routing/*.yaml` 导出成上述文件，再发布到本分支。

规则顺序（对齐 Sukka）：先域名 `DOMAIN-SET` / 非 IP `RULE-SET`，再 IP `*.ip.list` + `GEOIP`，最后 `FINAL`。

## 和别人大佬比一眼

| | 本仓库 surge | SukkaW/Surge | blackmatrix7 | tutu Surge.conf |
| --- | --- | --- | --- | --- |
| 规则形态 | 自用 Egern 表导出 | 维护 domainset / non_ip / ip | 按 App 的 `.list` | 引用第三方 RULE-SET |
| 主配置 | 对齐你的 Egern 策略组 | 规则片段为主 | 规则库 | 完整懒人包 |
| 订阅 | `policy-path` 占位 | — | — | Sub-Store / policy-path |

模块：去广告请用 **本分支大合集**（完整副本，已修好皮皮虾：QingRex + 我的 + 福利），与 `main`（Egern）**不共用**：

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/surge/Modules/adblock-collection.module
```

对照 QingRex：https://raw.githubusercontent.com/QingRex/LoonKissSurge/refs/heads/main/Surge/皮皮虾去广告.sgmodule

其它 unlock / pingme / iringo 等仍可装 `main` 的模块。皮皮虾短模块一般不必再开（已并进上份大合集）。

`skip-proxy` / `always-real-ip` **只写在本分支 `Surge.conf`**。去广告/解锁合集已剥离这两项，勿再叠装 Fries `General.sgmodule` 或 `skip-proxy-collection`（会截断 + 费内存）。




## 签到（Surge 注意）

Surge **不能像脚本编辑器那样“运行模块里的脚本”**，也不像 Egern 能点跑模块脚本。  
模块装上后只会：

- `http-request` / `http-response`：MITM 命中时自动抓参  
- `cron`：到点自动签到  

要手动测：把下面 `[Script]` **贴进配置**（或脚本编辑器），在脚本列表里点运行。

### PingMe（参考 fmz200 截图拆分写法）

模块（参数面板开关抓参）：

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/surge/Modules/pingme.sgmodule
```

或直接贴配置（与截图同结构）：

```
[Script]
PingMe获取签到参数 = type=http-request, pattern=^https:\/\/api\.pingmeapp\.net\/app\/queryBalanceAndBonus, script-path=https://raw.githubusercontent.com/oo226/egern-config/refs/heads/surge/Scripts/PingMe-capture.js, timeout=60
PingMe签到 = type=cron, cronexp=30 8,20 * * *, script-path=https://raw.githubusercontent.com/oo226/egern-config/refs/heads/surge/Scripts/PingMe-signin.js, timeout=300, script-update-interval=0

[MITM]
hostname = %APPEND% api.pingmeapp.net
```

流程：开着抓参脚本 → 打开 PingMe → 通知成功 → **注释/删掉抓参那行** → 到点或手动跑「PingMe签到」。

### 起点读书（对齐 Yuheng 官方 `qdreader.surge.sgmodule`）

上游：https://raw.githubusercontent.com/Yuheng0101/X/main/Tasks/QDReader/profiles/qdreader.surge.sgmodule  

本分支镜像（脚本仍用 main 上与上游 hash 一致的 js）：

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/surge/Modules/qdreader.sgmodule
```

流程：参数「是否开启抓取重写」=`起点读书` → 打开起点触发登录接口 → 改成 `#` → 等 cron（默认 2:11）或把 cron 行贴进配置后手动跑。

MITM 需含：`h5.if.qidian.com`（模块会 `%APPEND%`）。

## 图标

策略组图标见 [Icons.md](Icons.md)（Koolson/Qure Color）。

## 分支

| 分支 | 给谁 |
| --- | --- |
| `main` | Egern |
| `surge` | Surge（本页） |
| `sync` | 工厂（含 `surge/` 源） |
