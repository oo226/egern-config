# Surge 配置（`surge` 分支）

与 **`main`（Egern）分开**：不覆盖 `Egern.yaml` / `Routing/*.yaml`。  
**共用**：`main` 上的模块 / Scripts / GeoIP。  
**分流**：本仓 `Rules/`（由 `Routing` 合并导出）——可比懒人包更全；**运行时只引用本仓 raw 链接**。

## 导入

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/surge/Surge.conf
```

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/surge/Rules/
```

## 原则

1. **规则链接只用本仓**（`oo226/egern-config`）。上游（含深巷有喵 China 等）在 CI 合并进 `Routing/` 后再导出，不在 conf 里写第三方 RULE-SET URL。
2. **胖 = 更全，可以接受。** 真正要避免的是：大表再进 `[Host]` Local DNS Mapping、`hijack-dns = *:53`、无必要的多 DoH。
3. Egern / Surge 配置与分流树分开维护；模块成品共用。

## 更新

```bash
python3 scripts/export-surge-rulesets.py
python3 scripts/publish-surge.py
```

## 分支

| 分支 | 给谁 |
| --- | --- |
| `main` | Egern |
| `surge` | Surge（本页） |
| `sync` | 工厂 |

图标见 [Icons.md](Icons.md)。
