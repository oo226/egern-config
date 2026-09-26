# 解锁合集 — 上游合并说明

构建时间（UTC）：2026-09-26 00:13
分支：`cursor/adblock-formal-f611`

## 目录

```
Unlock/
  js/
  modules/{qingrex,fmz200,iewha,chxm1023,miranquil,weigiegie,liul0ng,yu9191,local}/
  unlock-collection.module
  UPSTREAM.md
```

## 合并顺序

1. **可莉** QingRex 解锁相关单模块原样拼合（底座）
2. **差集依次**：iEwha → chxm1023 Collections → miranquil → 本地 fmz200/weigiegie/liul0ng/yu9191 → Spotify Eevee → patches

已剔除：Spotify Crack / DualSubs Spotify、微信 CDN 整域 REJECT、configuration.apple.com REJECT；MITM 不含 TG/WhatsApp。

## 1) 可莉 — 20 模块

- 上游：https://github.com/QingRex/LoonKissSurge
- 目录：`Unlock/modules/qingrex/`
- `1.1.1.1配置管理.sgmodule`
- `DNS防泄露.sgmodule`
- `Fileball网盘挂载.sgmodule`
- `Google搜索重定向.sgmodule`
- `Google重定向.sgmodule`
- `HTTPDNS拦截器.sgmodule`
- `IPA工具箱助手.sgmodule`
- `Spotify歌词增强.sgmodule`
- `Spotify歌词翻译.sgmodule`
- `TikTok多地区解锁.sgmodule`
- `VVebo时间线修复.sgmodule`
- `YouTube翻译.sgmodule`
- `京东比价.sgmodule`
- `可莉广告过滤器.sgmodule`
- `广告平台拦截器.sgmodule`
- `微信外部链接解锁.sgmodule`
- `快捷搜索.sgmodule`
- `拦截HTTPDNS.sgmodule`
- `知识星球去水印.sgmodule`
- `自动加入TF.sgmodule`

## 2) 远程差集源

- OK `iewha/Unlock.sgmodule`
- OK `iewha/Script.sgmodule`
- OK `chxm1023/Collections.sgmodule`
- OK `miranquil/qq-c-pc-page.sgmodule`

## 3) 本地模块副本

- `spotify-unlock.sgmodule`
- `patches-unlock.sgmodule`
- `patches-alicloud.sgmodule`
- `yu9191-rewrite-unlock.sgmodule`
- `yu9191-ShortcutStudio.sgmodule`
- `weigiegie-unlock.sgmodule`
- `liul0ng-unlock.sgmodule`
- `fmz200-unlock-extra.sgmodule`

## 差集行数

`{'iewha/Unlock.sgmodule': {'Script': 6, 'MITM': 1}, 'iewha/Script.sgmodule': {'Rule': 5, 'URL Rewrite': 4, 'Map Local': 4, 'Script': 6, 'MITM': 1}, 'chxm1023/Collections.sgmodule': {'URL Rewrite': 5, 'Script': 190, 'MITM': 4}, 'miranquil/qq-c-pc-page.sgmodule': {'Script': 1}, 'local/spotify-unlock.sgmodule': {'URL Rewrite': 1, 'MITM': 1, 'Script': 2}, 'local/patches-unlock.sgmodule': {'Rule': 12, 'MITM': 1}, 'local/patches-alicloud.sgmodule': {'URL Rewrite': 2, 'Script': 8, 'MITM': 1}, 'local/yu9191-rewrite-unlock.sgmodule': {'Script': 90, 'MITM': 3, 'Rule': 17, 'URL Rewrite': 4}, 'local/yu9191-ShortcutStudio.sgmodule': {'Script': 4, 'MITM': 1}, 'local/weigiegie-unlock.sgmodule': {'Script': 459, 'MITM': 16}, 'local/liul0ng-unlock.sgmodule': {'Script': 13, 'MITM': 1}, 'local/fmz200-unlock-extra.sgmodule': {'URL Rewrite': 2, 'Map Local': 1, 'MITM': 1, 'Rule': 170}}`

## 脚本

- 镜像成功：619
- 失败：17

## 订阅

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/cursor/adblock-formal-f611/Unlock/unlock-collection.module
```

重建：`python3 scripts/build-unlock-formal.py`
