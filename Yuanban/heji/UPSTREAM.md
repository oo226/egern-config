# 合集上游说明

构建：2026-09-26 05:05 UTC
分支：`guize`

## zuozhe 作者统计

- **blackmatrix7**: mokuai=2 js=2 fenliu=10
- **chxm**: mokuai=1 js=181 fenliu=0
- **dunai**: mokuai=1 js=1 fenliu=0
- **iewha**: mokuai=2 js=8 fenliu=0
- **keli**: mokuai=283 js=82 fenliu=0
- **liulong**: mokuai=1 js=13 fenliu=0
- **local**: mokuai=4 js=186 fenliu=0
- **loyalsoldier**: mokuai=0 js=0 fenliu=12
- **miranquil**: mokuai=1 js=1 fenliu=0
- **moli**: mokuai=1 js=1 fenliu=60
- **moyu**: mokuai=34 js=47 fenliu=0
- **naisi**: mokuai=3 js=143 fenliu=0
- **nobyda**: mokuai=1 js=0 fenliu=0
- **repcz**: mokuai=0 js=0 fenliu=25
- **sukka**: mokuai=0 js=0 fenliu=12
- **vpsdance**: mokuai=0 js=0 fenliu=1
- **weigiegie**: mokuai=1 js=376 fenliu=0
- **yu9191**: mokuai=2 js=32 fenliu=0
- **yuheng**: mokuai=1 js=0 fenliu=0

## qiandao 签到单件（无合集）

`{'keli': 2, 'official': 9, 'local': 2, 'js': 18}`

## qita 其他脚本（无合集）

`{'official': 45, 'local': 9, 'ibl3nd': 51}`

## heji 分段袋数 / 分流文件数

`{'quguanggao': 223, 'qukaiping': 2, 'jiesuo': 33, 'zhuacan': 3, 'fenliu': 120}`

脚本镜像成功约 1073，失败 124（多为 kelee.one 403，合集保留上游 URL）

## 解锁近重复（合集已跳过，单件仍保留）

- 跳过 `Google重定向` → 用 `Google搜索重定向`
- 跳过 `拦截HTTPDNS` → 用 `HTTPDNS拦截器`
- 跳过 `Spotify歌词翻译` → 用 `Spotify歌词增强`

## 去广告置顶

1. `zuozhe/keli/mokuai/广告平台拦截器.sgmodule`
2. `zuozhe/keli/mokuai/可莉广告过滤器.sgmodule`
3. 可莉各 App `*去广告.sgmodule`
4. 墨鱼 AdBlock + NBPro
5. 毒奶 `Adblock4limbo.sgmodule`
6. blackmatrix7 Advertising(+Script)
7. 奶思 `blockAds.module` 整块

## 解锁补充（墨鱼）

- 微信110：`UnblockURLinWeChat.conf` + `weixin110.js`
- 专属VIP：`ForOwnUse.conf`（ddgksf2013/dev）
- Function：TF / Emby / Upos / Bilibili_CC

## 小组件

- `Yuanban/qita/ibl3nd/` — IBL3ND/module 原样（单件）

## 分流上游

- Repcz（Egern 骨架）+ 莫离 Ruleset + Sukka + Loyalsoldier 大名单 + VPSDance AI + BMJ 细分
- 清单见 `heji/fenliu/README.md`

## 抓参

- `heji/zhuacan`：sync Cookie合集 + 奶思原版 + NobyDa GetCookie + 莫离京东 + 起点

## js 镜像失败（节选）

- `https://kelee.one/Resource/JavaScript/12306/12306_remove_splashscreen_ads.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/12306/12306_remove_ads.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/Fileball/Fileball_mount.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/IPATool/AppStoreAPI.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/IPATool/Installer.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/IThome/IThome_remove_ads.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/Soul/Soul_remove_ads.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/Spotify/Spotify_remove_ads.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/Spotify/Spotify_response.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/Spotify/Spotify_request.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/Spotify/Translate_response.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/Spotify/External_Lyrics_response.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/Script/TikTok/TikTok_redirect.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/Uki/Uki_remove_ads.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/VVebo/VVebo_repair.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/WPS/WPS_checkin.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/Script/YouTube/YouTube_Subtitles_Translate/YouTube_Subtitles_request.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/Script/YouTube/YouTube_Subtitles_Translate/YouTube_Subtitles_response.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/Script/YouTube/YouTube_Subtitles_Translate/YouTube_Composite_Subtitles_response.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/Script/YouTube/YouTube_Subtitles_Translate/YouTube_Subtitles_Translate_response.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/PICC_Insurance/PICC_Insurance_remove_ads.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/mobileClouds/mobileClouds_remove_ads.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/TV_Assistant/TV_Assistant_remove_ads.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/ShuQiCenterReader/ShuQiCenterReader_remove_ads.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/Script/UnionPay/UnionPay_remove_ads_with_ssl_unpinning.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/JD/JD_remove_ads.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/JD/JD_Price.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/Script/Bilibili/Bilibili_proto_kokoryh.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/BiliComic/BiliComic_remove_ads.js (HTTP Error 403: FORBIDDEN)`
- `https://kelee.one/Resource/JavaScript/BabyTree/BabyTree_remove_ads.js (HTTP Error 403: FORBIDDEN)`
