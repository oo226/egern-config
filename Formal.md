# 正式树（本分支 `cursor/adblock-formal-f611`）

与 sync 日更的 `Modules/` / `Routing/` **并行**，互不覆盖。

| 大文件夹 | 原材料 | 单件 | 合集/产出 |
|----------|--------|------|-----------|
| `Adblock/` | `js/` | `modules/{qingrex,fmz200,moyu}/` | `adblock-collection.module` |
| `Unlock/` | `js/` | `modules/{qingrex,iewha,…,local}/` | `unlock-collection.module` |
| `Route/` | `lists/` | `modules/`（预留） | `Reject-Merged.yaml` / `China-Direct.yaml` / `Foreign/` |

明细：各目录下 `UPSTREAM.md`。

重建：

```bash
python3 scripts/build-adblock-formal.py
python3 scripts/build-unlock-formal.py
python3 scripts/build-route-formal.py
```
