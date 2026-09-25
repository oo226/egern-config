# 去广告合集 — 上游合并说明

构建时间（UTC）：2026-09-25 19:07
分支：`cursor/adblock-formal-f611`

## 目录结构

```
Adblock/
  js/                 # 自托管脚本（按上游 host 分子目录）
  modules/
    qingrex/          # 可莉原样单模块
    fmz200/           # 奶思 blockAds 原样 + 差集模块
    moyu/             # 墨鱼开屏原样 + Surge 转换
  adblock-collection.module
  UPSTREAM.md         # 本文件
  SHA256SUMS
```

## 合并顺序

1. **可莉（QingRex/LoonKissSurge）** — 根目录 `Surge/*去广告.sgmodule` 原样拼合（不含 Beta）
2. **奶思（fmz200/wool_scripts blockAds）** — 相对可莉合集的差集
3. **墨鱼开屏（ddgksf2013 StartUpAds + FakeiOSAds）** — 相对上一步的差集；开屏与去广告同一大合集

未做：分流、解锁（下一批）。无 heat/NB 补丁；仅把可镜像的 script URL 改指本仓 `Adblock/js/`。

## 1) 可莉 QingRex

- 上游：https://github.com/QingRex/LoonKissSurge
- 成功镜像模块：**192** → `Adblock/modules/qingrex/`

角色：**大合集底座**（全部规则/改写/脚本/MITM 先并进来）。

## 2) 奶思 fmz200 blockAds

- 上游：https://github.com/fmz200/wool_scripts `Surge/module/blockAds.module`
- 原样：`Adblock/modules/fmz200/blockAds.module`
- 差集：`Adblock/modules/fmz200/blockAds-gaps.module`
- 差集行数：`{'Rule': 2993, 'Header Rewrite': 1, 'URL Rewrite': 510, 'Body Rewrite': 73, 'Map Local': 745, 'Script': 254, 'MITM': 15}`
- 已剔除：Spotify Crack 等解锁噪声（解锁另做）

角色：**补可莉没有的规则/改写/脚本/MITM**。

## 3) 墨鱼开屏

- StartUpAds：https://ddgksf2013.top/rewrite/StartUpAds.conf → `modules/moyu/`
- FakeiOSAds：https://github.com/ddgksf2013/Rewrite `AdBlock/FakeiOSAds.conf`
- 并入合集的差集：`{'StartUpAds.conf': {'Rule': 5, 'URL Rewrite': 371, 'Script': 27, 'MITM': 4}, 'FakeiOSAds.conf': {'URL Rewrite': 1, 'MITM': 1}}`

角色：**开屏规则并进同一去广告大合集**（不另开模块订阅）。

## 脚本自托管

- 成功：109 → `Adblock/js/<host>/...`
- 失败（保留上游 URL）：66

失败样例（多为 kelee.one Cloudflare 403）：
- `https://kelee.one/Resource/JavaScript/12306/12306_remove_splashscreen_ads.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/12306/12306_remove_ads.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/IThome/IThome_remove_ads.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/Soul/Soul_remove_ads.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/Spotify/Spotify_remove_ads.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/Uki/Uki_remove_ads.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/PICC_Insurance/PICC_Insurance_remove_ads.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/mobileClouds/mobileClouds_remove_ads.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/TV_Assistant/TV_Assistant_remove_ads.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/ShuQiCenterReader/ShuQiCenterReader_remove_ads.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/Script/UnionPay/UnionPay_remove_ads_with_ssl_unpinning.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/JD/JD_remove_ads.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/Script/Bilibili/Bilibili_proto_kokoryh.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/BiliComic/BiliComic_remove_ads.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/BabyTree/BabyTree_remove_ads.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/XiaojukejiCharge/XiaojukejiCharge_remove_ads.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/RedPaper/RedPaper_remove_ads.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/iMaiCai/iMaiCai_remove_ads.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/KebidaDushu/KebidaDushu_remove_ads.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/ColorfulClouds/ColorfulClouds_remove_ads.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/WexinMiniPrograms/kff/kff.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/WexinMiniPrograms/ems/ems.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/WexinMiniPrograms/xiaotucc/xiaotucc.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/WexinMiniPrograms/FamilyMart/FamilyMart.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/WexinMiniPrograms/lawson/lawson.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/WexinMiniPrograms/chayanyuese/chayanyuese_remove_ads.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/WexinMiniPrograms/coco/coco.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/WexinMiniPrograms/qingju/qingju.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/WexinMiniPrograms/alittle-tea/alittle-tea.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/WexinMiniPrograms/M_Stand/M_Stand.js (HTTP Error 403: FORBIDDEN)`

## 订阅（本分支）

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/cursor/adblock-formal-f611/Adblock/adblock-collection.module
```

重建：`python3 scripts/build-adblock-formal.py`
