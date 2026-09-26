# 合集上游说明

构建：2026-09-26 05:45 UTC
分支：`guize`

## zuozhe 作者统计

- **blackmatrix7**: mokuai=0 js=0 fenliu=0
- **dunai**: mokuai=0 js=0 fenliu=0
- **keli**: mokuai=0 js=0 fenliu=0
- **laoshu**: mokuai=9 js=21 fenliu=0
- **moyu**: mokuai=0 js=2 fenliu=0
- **naisi**: mokuai=0 js=5 fenliu=0
- **zenmofeishi**: mokuai=0 js=0 fenliu=0

## qiandao 签到单件（无合集）

`{}`

## qita 其他脚本（无合集）

`{}`

## heji 分段袋数 / 分流文件数

`{'quguanggao': 250}`

脚本镜像成功约 183，占位/失败 0（仍写本仓占位，不留外站）
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

## 可莉来源说明（不是 sync 日更）

- **模块**：`QingRex/LoonKissSurge` 作者仓直拉 → `zuozhe/keli/mokuai`
- **脚本 CDN**：`kelee.one`（不在 GitHub 仓内）；需 **Surge UA**，QX UA 会 403
- 规则/Map Local **不依赖** js，可莉主体（域名拦截）一直有效
- js 拉不到时才写占位；已用 Surge UA + Maasea/app2smile/墨鱼替身补齐绝大多数

## 老书 jnlaoshu

- `zuozhe/laoshu` ← https://github.com/jnlaoshu/MySelf/tree/main/Egern/Module
- Video/Music/YouTube 等进 `heji/quguanggao`（Rule+Map Local 为主）
