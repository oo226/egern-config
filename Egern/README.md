# Egern 懒人配置（结构对齐老书 jnlaoshu）

自用总配置。分流 / 模块底座是本仓 `Yuanban/heji`（自托管）。

## 一键订阅

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Egern/Profile.yaml
```

## 别人会不会拉到我的节点？

**不会。** `sub.store` 是导入者**自己手机上**的 Sub-Store（靠 MITM 转到本机脚本），不是你的云端订阅地址。别人用这份 Profile，只会读他们自己 Sub-Store 里的 `AllServer`；仓库里也没有任何机场链接。

## AllServer 怎么建（你自己的）

1. 开 **解锁增强合集**（已含 Sub-Store）
2. 浏览器打开 `http://sub.store`
3. 添加你的机场订阅 → 新建**组合订阅**，名字填死：`AllServer`
4. 面板「全部节点」就会从  
   `https://sub.store/download/collection/AllServer?target=Egern`  
   拉到**你本机**这份合集

## 「Profile 不挂」是啥意思

分流文件可以躺在 `Yuanban/heji/fenliu/` 里备用，但 **Profile.yaml 的 `rules:` 里不引用**就不生效。  
网盘大半本就在 `Repcz-国内域名`；剩下的网盘补缺 + 视频资源站已**并进现有的** `Repcz-直连.yaml`（不另开分流；文件内注释标了「以下起为视频规则」）。

## 模块（已避免重复挂）

| 模块 | 说明 |
|------|------|
| 去广告 / 去开屏 / 解锁 | 默认开；解锁含 Sub-Store、Script Hub、BoxJs、插件跳转、TG外链跳转、天气/地图、证书、屏蔽更新 |
| YouTube | 去广告合集里有老书段；解锁里是可莉字幕，用途不同 |
| 起点读书签到 | 默认开；先抓 CK 再关「抓取重写」参数 |
| 18+ / 抓参 / PingMe / iRingo 定位·其他 | 默认关 |

全局含 `vif_hairpin_addresses: 10.7.0.1`（回流）；DNS forward / real_ip 已按老书补齐高频域名与 NAS/路由项。

## 分流 / 策略（已收束）

- **不新建规则集**：DNS / 短视频都并进已有表
  - 国内 DNS → 已有 `Loyalsoldier-直连大名单` → DNSPod（不再拆阿里/腾讯/字节三表）
  - 保留域 reject → 已有 `BlockHttpDNS`；局域网/私有网 → system
  - 短视频 → 已有 `Repcz-国内域名`；`windowsupdate.com` → 已有 `Repcz-Microsoft`
- 去掉多余策略组：广告→REJECT，微信/苹果/微软→DIRECT，Google/GitHub→Proxy，Netflix/Disney+/Twitter/PayPal→美国，TikTok→台湾
- 保留：地区池、Proxy、AIGC、YouTube、Spotify、Telegram、Emby、追风
- 图标：追风=Loon，全部节点=Surge，其他节点=Egern
- 追风：与每日 `main` 一致，仅 `sq-hlsg` / `open-hlsg`；节点 IP `120.53.245.215/32` DIRECT。节点 `8688` 宕则超时（配置对、服务端挂）
- 小桔充电脚本改走本仓 raw（`kelee.one` 要 Surge UA，Egern 拉会 TLS/403）

`fenliu/` 仍保留上游原件；Profile 用短名引用。Egern「DNS 流量控制」面板会把规则集展开成行，属 UI 展开，不是 Profile 又写回单条。

相对每日 IBL3ND（3d）懒人：他看着行少，是因为广告/国内表在 CI 里**合并去重**过；不是覆盖更弱。我们这边 DNS 防污染（无 system bootstrap、`block_ips`、IP 字面量 DoH）反而更严。

## DNS 防污染（已写进 Profile）

- **主机映射 `hosts`**：只钉 DoH / App Store CDN 域名→IP（或 CNAME），避免「解析 dns.google 本身被污染」；不是业务分流表
- bootstrap **只用** `223.5.5.5` / `119.29.29.29`，**不要**加 `system`（4G 易污染出证书伪装）
- `hosts` 钉死 `dns.google` / `cloudflare-dns.com` / `dns.alidns.com` / `doh.pub`，并跟 main 补 `iosapps…ks-cdn.com`
- 境外 DoH 优先 `https://8.8.8.8` / `https://1.1.1.1` 字面量
- `hijack_dns` 含 `*:53` 与 `8.8.8.8` / `1.1.1.1` / `114.114.114.114`（防 App 硬编码绕过）
- `block_ips` 丢掉假/保留地址应答

## 使用前

1. 导入 Profile，信任 MITM CA  
2. 按上面建好自己的 `AllServer`  
3. 今日油价预填 `zhejiang/ningbo`；追风节点已带  

重建合集：`python3 scripts/build-yuanban.py`
