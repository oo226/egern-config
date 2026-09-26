# Egern 懒人配置（guize 自托管）

模块、分流、DNS **全部挂本分支** `Yuanban/heji` / `Egern/Rule`，不引用每日 `main`。

## 一键订阅

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Egern/Profile.yaml
```

## 别人会不会拉到我的节点？

**不会。** `sub.store` 是导入者本机 Sub-Store。仓库里没有任何机场链接。

## AllServer

1. 开 **解锁增强合集**  
2. 打开 `http://sub.store` → 组合订阅名填死 `AllServer`

## 收束说明（都在 guize 里）

- DNS：广告两表 + BlockHttpDNS → reject；局域网/私有网 → system；**直连大名单 → DNSPod**（不拆阿里/腾讯/字节）；YT/Google → Google
- 分流顺序：基建 → 追风 → **Spotify（广告前）** → 广告 → 服务 → 国内域名/IP/直连补充 → GFW
- 规则层不再叠「直连大名单」（只给 DNS 用）；广告去掉第三张「再补」
- 短视频进 `Repcz-国内域名`；`windowsupdate` 进 `Repcz-Microsoft`
- 主机映射：只钉 DoH / App Store CDN
- MITM：不整域排除 `*.weixin.qq.com`，留 `mp.weixin.qq.com` 给公众号去广告

## DNS 防污染

- bootstrap 只用 `223.5.5.5` / `119.29.29.29`，不要 `system`
- `hosts` 钉死 DoH；境外 IP 字面量 DoH；`hijack_dns` + `block_ips`

## 其它

- 追风：`本仓-追风`（`sq-hlsg` / `open-hlsg`）+ 节点 IP DIRECT；节点宕则超时
- 小桔脚本：本仓 raw（避开 kelee UA/TLS）
- 图标：追风=Loon，全部节点=Surge，其他节点=Egern

强制更新 Profile 后再看；不要只在 DNS 面板点保存。
