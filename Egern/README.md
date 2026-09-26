# Egern 懒人配置

模块用本仓 `Yuanban/heji`；**分流挂每日 `main/Routing` 合并表**（和 IBL3ND/3d 同源），面板更短。  
DNS 防污染仍按本仓更严的写法（无 `system` bootstrap）。

## 一键订阅

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Egern/Profile.yaml
```

## 别人会不会拉到我的节点？

**不会。** `sub.store` 是导入者**自己手机上**的 Sub-Store。仓库里没有任何机场链接。

## AllServer 怎么建

1. 开 **解锁增强合集**（已含 Sub-Store）
2. 浏览器打开 `http://sub.store`
3. 添加机场订阅 → 新建**组合订阅**，名字填死：`AllServer`

## 为啥比以前「优雅」

| | 以前（叠原件） | 现在 |
|---|---|---|
| 广告 | Loyalsoldier + Sukka + 补充 三行 | `Reject-Hot` + `Reject-Merged`（main CI 合并） |
| 国内 | 域名 + IP + 直连大名单 + 微信/苹果… | 一条 `China-Direct`（已含上述） |
| DNS forward | 多张原件 | 与 rules **同源**合并表 |
| 顺序 | 广告过早、Spotify 可能被误拒 | 对齐 main：热点拒 → 优先直连 → Spotify → 广告大表 → 服务 → 国内 |

不新建 fenliu；引用的是每日分支已有的 `Routing/*`。

## 主机映射是啥

`dns.hosts`：只钉 DoH / App Store CDN，防「解析 dns.google 本身被污染」。不是业务分流表。

## DNS 防污染

- bootstrap **只用** `223.5.5.5` / `119.29.29.29`，**不要** `system`
- `hosts` 钉死 DoH + `iosapps…ks-cdn.com`
- 境外 DoH 优先 `https://8.8.8.8` / `https://1.1.1.1`
- `hijack_dns` + `block_ips`

## 其它

- 追风：与 main `Zhuifeng.yaml` 一致（`sq-hlsg` / `open-hlsg`）；节点 `120.53.245.215:8688` 宕则超时
- 小桔充电脚本：本仓 raw（避开 `kelee.one` UA/TLS）
- MITM 排除：对齐 main，不整域砍 `*.weixin.qq.com`（留 `mp.weixin.qq.com` 给公众号去广告）
- 图标：追风=Loon，全部节点=Surge，其他节点=Egern

## 使用前

1. 导入 Profile，信任 MITM CA  
2. 建好自己的 `AllServer`  
3. **强制更新**配置（不要只在 DNS 面板点保存）

重建合集：`python3 scripts/build-yuanban.py`
