# Surge RULE-SET 镜像

由 `scripts/export-surge-rulesets.py` 从同目录结构的 Egern `*.yaml` 自动导出。

Surge **不能**直接引用 `Routing/*.yaml`（Egern 的 `domain_suffix_set` 语法）。
请用本目录下的 `.list`，例如：

```
RULE-SET,https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Routing/Surge/China-Direct.list,DIRECT,no-resolve
```

主配置见仓库根目录 `Surge.conf`。
