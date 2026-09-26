# 合集上游说明

构建：2026-09-26 05:30 UTC
分支：`guize`

## zuozhe 作者统计

- **blackmatrix7**: mokuai=2 js=2 fenliu=10
- **chxm**: mokuai=1 js=181 fenliu=0
- **dunai**: mokuai=1 js=1 fenliu=0
- **iewha**: mokuai=2 js=8 fenliu=0
- **keli**: mokuai=283 js=168 fenliu=0
- **liulong**: mokuai=1 js=13 fenliu=0
- **local**: mokuai=4 js=177 fenliu=0
- **loyalsoldier**: mokuai=0 js=0 fenliu=12
- **miranquil**: mokuai=1 js=1 fenliu=0
- **moli**: mokuai=1 js=1 fenliu=60
- **moyu**: mokuai=34 js=47 fenliu=0
- **naisi**: mokuai=3 js=144 fenliu=0
- **nobyda**: mokuai=1 js=0 fenliu=0
- **repcz**: mokuai=0 js=0 fenliu=25
- **sukka**: mokuai=0 js=0 fenliu=12
- **vpsdance**: mokuai=0 js=0 fenliu=1
- **weigiegie**: mokuai=1 js=376 fenliu=0
- **yu9191**: mokuai=2 js=301 fenliu=0
- **yuheng**: mokuai=5 js=22 fenliu=0
- **zenmofeishi**: mokuai=23 js=27 fenliu=0

## qiandao 签到单件（无合集）

`{'keli': 2, 'official': 9, 'local': 2, 'js': 15, 'zenmofeishi': 12}`

## qita 其他脚本（无合集）

`{'official': 45, 'local': 9, 'ibl3nd': 51}`

## heji 分段袋数 / 分流文件数

`{'quguanggao': 241, 'qukaiping': 2, 'jiesuo': 38, 'shibajia': 2, 'zhuacan': 3, 'fenliu': 120}`

脚本镜像成功约 1505，占位/失败 108（仍写本仓占位，不留外站）
合集外站泄漏: ?

## 自依赖

- 所有 `script-path` 指向 `raw.githubusercontent.com/oo226/egern-config/.../Yuanban/`
- 上游删库不影响：规则与脚本都在本仓
- 文件名：`作者-用途` / 中文直白名（怎么肥事、分流 heji 等）

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

## 18+

- `heji/shibajia`：Yu9191 Rewrite 成人段 + WeiGiegie 少量（18pcs/含羞/mjgs…）
- 日常解锁 `jiesuo` 已剥离上述分段
- Yuheng 巴士/JAVDay/黑料/1024/4K世界：签到推送脚本在 `zuozhe/yuheng/js`

## kelee.one

- 可莉官方 CDN；常 403，构建时改走 GitHub 镜像/本仓占位，合集不挂外链

## js 镜像失败（节选）

- `https://kelee.one/Resource/JavaScript/12306/12306_remove_splashscreen_ads.js`
- `https://kelee.one/Resource/JavaScript/12306/12306_remove_ads.js`
- `https://kelee.one/Resource/JavaScript/Fileball/Fileball_mount.js`
- `https://kelee.one/Resource/JavaScript/IPATool/AppStoreAPI.js`
- `https://kelee.one/Resource/JavaScript/IPATool/Installer.js`
- `https://kelee.one/Resource/JavaScript/IThome/IThome_remove_ads.js`
- `https://kelee.one/Resource/JavaScript/Soul/Soul_remove_ads.js`
- `https://kelee.one/Resource/JavaScript/Spotify/Spotify_remove_ads.js`
- `https://kelee.one/Resource/JavaScript/Spotify/Spotify_response.js`
- `https://kelee.one/Resource/JavaScript/Spotify/Spotify_request.js`
- `https://kelee.one/Resource/JavaScript/Spotify/Translate_response.js`
- `https://kelee.one/Resource/JavaScript/Spotify/External_Lyrics_response.js`
- `https://kelee.one/Resource/JavaScript/Uki/Uki_remove_ads.js`
- `https://kelee.one/Resource/JavaScript/WPS/WPS_checkin.js`
- `https://kelee.one/Resource/Script/YouTube/YouTube_Subtitles_Translate/YouTube_Subtitles_request.js`
- `https://kelee.one/Resource/Script/YouTube/YouTube_Subtitles_Translate/YouTube_Subtitles_response.js`
- `https://kelee.one/Resource/Script/YouTube/YouTube_Subtitles_Translate/YouTube_Composite_Subtitles_response.js`
- `https://kelee.one/Resource/Script/YouTube/YouTube_Subtitles_Translate/YouTube_Subtitles_Translate_response.js`
- `https://kelee.one/Resource/JavaScript/PICC_Insurance/PICC_Insurance_remove_ads.js`
- `https://kelee.one/Resource/JavaScript/mobileClouds/mobileClouds_remove_ads.js`
- `https://kelee.one/Resource/JavaScript/TV_Assistant/TV_Assistant_remove_ads.js`
- `https://kelee.one/Resource/JavaScript/ShuQiCenterReader/ShuQiCenterReader_remove_ads.js`
- `https://kelee.one/Resource/Script/UnionPay/UnionPay_remove_ads_with_ssl_unpinning.js`
- `https://kelee.one/Resource/JavaScript/JD/JD_remove_ads.js`
- `https://kelee.one/Resource/JavaScript/JD/JD_Price.js`
- `https://kelee.one/Resource/Script/Bilibili/Bilibili_proto_kokoryh.js`
- `https://kelee.one/Resource/JavaScript/BiliComic/BiliComic_remove_ads.js`
- `https://kelee.one/Resource/JavaScript/BabyTree/BabyTree_remove_ads.js`
- `https://kelee.one/Resource/JavaScript/RedPaper/RedPaper_remove_ads.js`
- `https://kelee.one/Resource/JavaScript/iMaiCai/iMaiCai_remove_ads.js`
