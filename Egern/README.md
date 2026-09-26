# Egern 懒人配置（结构对齐老书 jnlaoshu）

自用总配置。分流 / 模块底座是本仓 `Yuanban/heji`（自托管），不是外站拼接。

## 一键订阅

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Egern/Profile.yaml
```

## 使用前

1. Egern 里导入上面的 Profile
2. 启用模块 **Sub-Store**，建合集名 `AllServer`（节点池从 `sub.store/download/collection/AllServer` 取）
3. 在 App 内生成并信任 MITM CA（`egern.p12` / 口令按你本地为准）
4. 按需打开：解锁、抓参、18+、PingMe、YouTube 增强

## 和旧 `main/Egern.yaml` 的差别

| | 旧 main | 本 Profile |
|--|---------|------------|
| 结构 | 零件堆叠、追风等私货 | 老书式分区注释 + smart 地区组 |
| 去广告 | 旧 Modules 合集 | `Yuanban/heji/quguanggao` + `qukaiping` |
| 分流 | `Routing/*`（main） | `Yuanban/heji/fenliu/*`（guize 自托管） |
| 节点 | 占位订阅链接 | Sub-Store AllServer |

## 目录

```
Egern/
  Profile.yaml          # 总配置
  Rule/BlockHttpDNS.yaml
  README.md
```

规则零件仍在 `Yuanban/`；改合集后重建：`python3 scripts/build-yuanban.py`。
