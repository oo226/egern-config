# 分流 — 上游合并说明

构建时间（UTC）：2026-09-26 00:13
分支：`cursor/adblock-formal-f611`

## 目录

```
Route/
  lists/          # 上游规则原样（≈ Adblock/js）
    repcz/ skk/ vpsdance/ rabbit/ eulac/ apps/
  modules/        # 预留
  Reject-Merged.yaml / China-Direct.yaml / Foreign/
  UPSTREAM.md
```

## 上游

| 源 | 用途 |
|----|------|
| Repcz/Tool Egern Rules | Reject / China* / Foreign* |
| Sukka reject.conf + ai.conf | 去广告域名 + AI |
| VPSDance ai-proxy-rules | AI 补充 |
| Rabbit-Spec China/ChinaCIDR | 国内直连补充 |
| eulac ResourceSite/PanVod | 资源站/网盘 |
| Matrix-io Unbreak | Unbreak.yaml |
| 本仓 Routing 本地件 | Bootstrap/Lan/Privacy/追风等 |

拉取成功：32　失败：1

## 产出条目数

- `Reject-Merged.yaml`: 139190
- `China-Direct.yaml`: 31742
- `Foreign/AI.yaml`: 445
- `Foreign/Telegram.yaml`: mirrored
- `Foreign/Twitter.yaml`: mirrored
- `Foreign/TikTok.yaml`: mirrored
- `Foreign/YouTube.yaml`: mirrored
- `Foreign/Netflix.yaml`: mirrored
- `Foreign/Disney.yaml`: mirrored
- `Foreign/Spotify.yaml`: mirrored
- `Foreign/Emby.yaml`: mirrored
- `Foreign/Google.yaml`: mirrored
- `Foreign/Github.yaml`: mirrored
- `Foreign/Microsoft.yaml`: mirrored
- `Foreign/AppleServers.yaml`: mirrored
- `Foreign/Game.yaml`: mirrored
- `Foreign/ProxyGFW.yaml`: mirrored
- `Foreign/Proxy.yaml`: mirrored
- `Lan.yaml`: copied-from-Routing
- `Bootstrap-Direct.yaml`: copied-from-Routing
- `Privacy-Reject.yaml`: copied-from-Routing
- `Tailscale-Direct.yaml`: copied-from-Routing
- `Zhuifeng.yaml`: copied-from-Routing
- `Direct-Priority.yaml`: copied-from-Routing
- `Reject-Hot.yaml`: copied-from-Routing

## 订阅示例

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/cursor/adblock-formal-f611/Route/Reject-Merged.yaml
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/cursor/adblock-formal-f611/Route/China-Direct.yaml
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/cursor/adblock-formal-f611/Route/Foreign/AI.yaml
```

重建：`python3 scripts/build-route-formal.py`

说明：本树与 sync 日更的 `Routing/` 并行；Egern 主配置仍默认定 `Routing/`，本分支用 `Route/` 试验。

## 拉取失败

- Unbreak.yaml: HTTP Error 404: NOT FOUND

## Unbreak

Matrix-io 上游 404，已用本仓 `Routing/Unbreak.yaml` 副本写入 `Route/Unbreak.yaml`。
