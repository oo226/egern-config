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
| 去广告 / 去开屏 / 解锁 | 默认开；解锁含 Sub-Store、Script Hub、BoxJs、天气/地图、证书、屏蔽更新 |
| YouTube | 去广告合集里有老书段；解锁里是可莉字幕，用途不同 |
| 18+ / 抓参 / PingMe / iRingo 定位·其他 | 默认关 |

## 分流去重（Profile 已瘦身）

相对早期叠表版，去掉近重复引用：

- 广告：去掉 `Repcz-广告拒绝`（留 Loyalsoldier + Sukka）
- AI：只留 `VPSDance-AI合集`
- Google：只留 `Repcz-Google`（DNS/规则都不再叠 Loyalsoldier-Google）
- GitHub：只留 `BMJ-GitHub`
- GFW：去掉 `Repcz-GFW代理`（留 Loyalsoldier GFW + 代理）
- 直连：`本仓-直连补充`（网盘补缺+视频）+ Repcz 国内域名/IP + GeoIP + 直连大名单

`fenliu/` 里仍保留各上游原件，方便单件订阅；Profile 不再全开叠用。

## 使用前

1. 导入 Profile，信任 MITM CA  
2. 按上面建好自己的 `AllServer`  
3. 今日油价预填 `zhejiang/ningbo`；追风节点已带  

重建合集：`python3 scripts/build-yuanban.py`
