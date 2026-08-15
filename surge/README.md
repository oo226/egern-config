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

模块继续装 `main` 的 `.module` / `.sgmodule`（Surge 原生）；不要装 Egern 专用 YAML。

`skip-proxy` / `always-real-ip` **只写在本分支 `Surge.conf`**。去广告/解锁合集已剥离这两项，勿再叠装 Fries `General.sgmodule` 或 `skip-proxy-collection`（会截断 + 费内存）。

### 内存友好写法（对齐常见懒人包）

1. **分流去广告**：`[Rule]` 里 `DOMAIN-SET …Reject-Merged → REJECT`（常开）
2. **不要**把 Reject / China 大表再挂进 `[Host]` Local DNS Mapping（会双倍占内存）
3. **`hijack-dns`** 用 `8.8.8.8:53, 8.8.4.4:53`，避免 `*:53`
4. **DoH / IPv6** 默认关；需要再开
5. **MITM 模块按需**：开屏/App 内 JSON 广告再订合集或小模块

### 第三方懒人配置参考（只读对照，非本仓）

| 作者 | 说明 | 链接 |
| --- | --- | --- |
| **深巷有喵（Rabbit-Spec）** | 干净懒人包；`hijack-dns` 仅 8.8.8.8；广告 RULE 默认注释，靠模块 | [Surge-Mini.conf](https://raw.githubusercontent.com/Rabbit-Spec/Surge/Master/Conf/Spec/Surge-Mini.conf) · [Surge-Lite-CN.conf](https://raw.githubusercontent.com/Rabbit-Spec/Surge/Master/Conf/Spec/Surge-Lite-CN.conf) · [仓库](https://github.com/Rabbit-Spec/Surge) |
| **耳东橙（erdongchanyo）** | 保姆级懒人；广告走 blackmatrix7 `Advertising`/`Privacy`→策略组 | [Surge_EDC-Lzay.conf](https://raw.githubusercontent.com/erdongchanyo/Rules/main/Surge/Surge_EDC-Lzay.conf) · [说明文](https://erdongchan.cn/surgeconf.html) |
| **XiaoMao（xiaomaoJT）** | 懒人全配置；`[Rule]` 挂 AdBlock + Advertising DOMAIN-SET，无 Host 大表映射 | [XiaoMaoSurge.conf](https://raw.githubusercontent.com/xiaomaoJT/Surge/main/config/XiaoMaoSurge.conf) · [仓库](https://github.com/xiaomaoJT/Surge) |
| **Blankwonder 系最小示例** | 社区常用「中国区最小配置」转述；强调少开 DoH/IPv6 | [gist 远程引用版](https://gist.githubusercontent.com/Zeaphyou/864aebea248ca1bb8000e0e5623b65f3/raw/c36413c715f43f22772d3c2353358e1ff936b2e6/Surge.conf) · [社区帖](https://community.nssurge.com/d/1214) |
| **可莉（iKeLee / QingRex）** | **主要是 Loon 插件中心**，不是完整 Surge 懒人 conf；Surge 需 Script Hub 转换按需装插件 | [插件中心 hub.kelee.one](https://hub.kelee.one) · [Yu9191 适配模块](https://raw.githubusercontent.com/Yu9191/Rewrite/refs/heads/main/pluginhub.sgmodule) · [luestr/ProxyResource](https://github.com/luestr/ProxyResource) |

社区汇总入口：[Surge 社区 Wiki · 导入配置](https://wiki.surge.community/basic/dao-ru-pei-zhi)

## 图标

策略组图标见 [Icons.md](Icons.md)（Koolson/Qure Color）。

## 分支

| 分支 | 给谁 |
| --- | --- |
| `main` | Egern |
| `surge` | Surge（本页） |
| `sync` | 工厂（含 `surge/` 源） |
