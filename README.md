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

## 分支

| 分支 | 给谁 |
| --- | --- |
| `main` | Egern |
| `surge` | Surge（本页） |
| `sync` | 工厂（含 `surge/` 源） |
