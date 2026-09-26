# 分流规则集（单件）

不合并成一个 module（用途不同，按策略组自选）。原料在 `zuozhe/*/fenliu/`。

## 上游怎么选

| 前缀 | 上游 | 适合 |
|------|------|------|
| `repcz__` | Repcz/Tool Egern | **骨架**：国内/代理/流媒体，Egern 原生 yaml |
| `moli__` | 莫离 Moli-X Ruleset | **分类多**：Ads/CDN/Claude/Steam/PayPal… |
| `sukka__` | Sukka ruleset.skk.moe | reject/AI/CDN/流媒体/Apple |
| `loyalsoldier__` | Loyalsoldier surge-rules | **大名单底**：direct/proxy/gfw/reject |
| `vpsdance__` | VPSDance | AI 专项最全 |
| `blackmatrix7__` | blackmatrix7 | 细分补洞：ChinaMax/Steam/GlobalMedia… |

广告类 Reject 与去广告合集会叠，别无脑全开。

## 订阅示例

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/blackmatrix7__AdvertisingLite.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/blackmatrix7__ChinaMax.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/blackmatrix7__Claude.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/blackmatrix7__Cloudflare.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/blackmatrix7__Gemini.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/blackmatrix7__GitHub.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/blackmatrix7__GlobalMedia.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/blackmatrix7__OpenAI.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/blackmatrix7__PayPal.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/blackmatrix7__Steam.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/loyalsoldier__apple.txt
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/loyalsoldier__cncidr.txt
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/loyalsoldier__direct.txt
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/loyalsoldier__gfw.txt
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/loyalsoldier__google.txt
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/loyalsoldier__greatfire.txt
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/loyalsoldier__icloud.txt
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/loyalsoldier__private.txt
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/loyalsoldier__proxy.txt
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/loyalsoldier__reject.txt
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/loyalsoldier__telegramcidr.txt
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/loyalsoldier__tld-not-cn.txt
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__AI.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__APNs.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Ads_AWAvenue.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Ads_Dlerio.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Ads_EasyListChina.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Ads_EasyListPrivacy.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Ads_SukkaW.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Ads_limbopro.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Anti-Ad.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__AppStore.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Apple.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__AppleID.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__AppleProxy.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__AutoBilibili.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Bilibili.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Bing.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__CDN.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__ChinaASN.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__ChinaDomain.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Claude.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Cloudflare.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Disney.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__DouYin.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__DownloadCDN_CN.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__DownloadCDN_Global.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Epic.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Facebook.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Game.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Gemini.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__GitHub.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__GitLab.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Google.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__HBO.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__HTTPDNS.Block.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Instagram.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Lan.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Microsoft.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Netflix.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Notion.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__OneDrive.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__OpenAI.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Oracle.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__PayPal.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__PrimeVideo.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__ProxyGFW.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Reject.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Spotify.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Steam.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Taida.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__TeamViewer.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Telegram.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Tencent.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__TestFlight.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__TikTok.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Trendmicro.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Twitter.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__Update.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__VSCode.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__WeChat.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/moli__YouTube.list
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/repcz__AI.yaml
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/repcz__AppleCN.yaml
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/repcz__AppleServers.yaml
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/repcz__Bilibili.yaml
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/repcz__ChinaASN.yaml
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/repcz__ChinaDomain.yaml
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/repcz__ChinaIP.yaml
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/repcz__Direct.yaml
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/repcz__Disney.yaml
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/repcz__Emby.yaml
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/repcz__Game.yaml
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/repcz__Github.yaml
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/repcz__Google.yaml
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/repcz__Lan.yaml
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/repcz__Microsoft.yaml
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/repcz__Netflix.yaml
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/repcz__Proxy.yaml
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/repcz__ProxyGFW.yaml
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/repcz__Reject.yaml
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/repcz__Spotify.yaml
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/repcz__Telegram.yaml
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/repcz__TikTok.yaml
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/repcz__Twitter.yaml
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/repcz__WeChat.yaml
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/repcz__YouTube.yaml
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/sukka__ai.conf
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/sukka__apple_cn.conf
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/sukka__apple_services.conf
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/sukka__cdn.conf
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/sukka__china_ip.conf
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/sukka__download.conf
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/sukka__microsoft.conf
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/sukka__reject.conf
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/sukka__reject_extra.conf
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/sukka__stream.conf
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/sukka__telegram.conf
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/sukka__telegram_ip.conf
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/fenliu/vpsdance__all.yaml
```

共 120 个文件。
