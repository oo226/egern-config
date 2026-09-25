# 模块（Modules）

> 镜像自用，版权归上游。见 [DISCLAIMER.md](../DISCLAIMER.md)。

## 去广告：两套合集

| 文件 | 策略 | 何时用 |
|------|------|--------|
| **`adblock-verbatim.module`** | 上游 **原样** 拼接（奶思 / blackmatrix7 / 毒奶 / chxm） | **默认** — 不改 URL、不打 heat/NB 补丁 |
| `adblock-collection.module` | 旧流水线：改写 + divert + heat/NB | 仅回滚 |

单源 1:1 副本在 **`Modules/vendors/`**（带 `SHA256SUMS`）。清单：`manifest.verbatim.yaml`（仅 sync）。

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Modules/adblock-verbatim.module
```

NB / 微信等本地补丁**不进**原样合集；需要时单独加 `nb-weixin-fix.yaml`。

## 其他日常入口

| 文件 | 说明 |
|------|------|
| `unlock-collection.module` | 解锁合集 |
| `cookie-collection.module` | 按需抓 Cookie |
| `pingme.sgmodule` | PingMe |
| `ibl3nd-plugin-hub.yaml` | 插件跳转 |
| `iringo-*` |  iRingo |
| `egern.boxjs.json` | 统一 BoxJS |

## 原则

1. **原样优先**：合集内容 = 上游模块字节级副本的拼接去重，脚本 URL 仍指向上游。
2. **补丁隔离**：自定义修复单独成模块，绝不再塞进「原样合集」。
3. **防删库**：`vendors/` + 作者仓镜像在；坏了对照 `SHA256SUMS` 即可。
