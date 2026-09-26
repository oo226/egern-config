# Route — 分流（本分支正式树）

| 路径 | 内容 |
|------|------|
| `lists/` | 上游规则原样 |
| `modules/` | 预留 |
| `Reject-Merged.yaml` 等 | 合并产出 |
| `UPSTREAM.md` | 合并明细 |

与仓库根目录 `Routing/`（sync 日更）并行，互不覆盖。

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/cursor/adblock-formal-f611/Route/Reject-Merged.yaml
```

重建：`python3 scripts/build-route-formal.py`

总览见仓库根目录 [Formal.md](../Formal.md)。
