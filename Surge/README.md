# Surge 懒人（有喵镜像）— 链接在这里

分支：`cursor/surge-rabbit-f611` · PR：https://github.com/oo226/egern-config/pull/158  
仓内路径：`Surge/Conf/Spec/`、`Surge/Module/`、`Surge/Rules/`

## 直接复制用

**日常（有喵 CN 原样）：**
```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/cursor/surge-rabbit-f611/Surge/Conf/Spec/Surge-CN.conf
```

**CN + Tailscale（推荐）：**
```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/cursor/surge-rabbit-f611/Surge/Conf/Spec/Surge-CN-Plus.conf
```

导入后改三处：`policy-path`、`auth-key`、`YOURTAILNET.ts.net`。

**回环模块（官方写法；主配置不要写 `%INSERT%`）：**
```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/cursor/surge-rabbit-f611/Surge/Module/IP-Rewrite-Hairpin.sgmodule
```
Surge → 模块 → 安装 → 打开。需 App Store ≥ **5.23.0**。

**Mini 原样（仅冒烟）：**
```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/cursor/surge-rabbit-f611/Surge/Conf/Spec/Surge-Mini.conf
```

## 回环怎么用

手册写明：`tun-included-routes = %INSERT% 10.7.0.1/32` **只能出现在模块里**（`%INSERT%` / `%APPEND%` 是模块运算符）。  
主配置里写会报「无效配置」——已从 CN-Plus 去掉，请单独装上面的模块。

Surge 弹「绝大多数情况下不应配置 `tun-included-routes`」：说明你开了回环模块（主配置本身没有该参数）。  
不用 SideStore / 10.7.0.1 回环就关掉该模块；需要回环就点「好的」忽略即可。

## Tailscale DERP 怎么走美国了？

细节里若是 **规则 = FINAL、策略 = 美国某节点**：不是「美国 DERP 节点」本身的问题，而是  
`derp*.tailscale.com` **常按 IP 拨号**，只写 `DOMAIN-SUFFIX,tailscale.com,DIRECT` 匹配不到，掉进 `FINAL → 节点选择`。

CN-Plus 已挂 `Surge/Rules/Tailscale-DERP.list`（IP/域名直连）+ UDP 3478 DIRECT。  
重载后再看最近请求，DERP 应变 **DIRECT**。更新 DERP 表：`python3 scripts/update-tailscale-derp-list.py`。


## 网盘 / 视频 / PingMe

CN-Plus 已挂独立 RULE-SET（`Surge/Rules/PanVod.list`、`ResourceSite.list`、`PingMe.list` → DIRECT）。  
Egern 对应：`Egern/Routing/{PanVod,ResourceSite,PingMe}-Direct.yaml`（见 guize / ruleset PR）。

## DNS（防运营商泄漏）

有喵原版写了 `dns-server = system, …`，`system` = 当前网卡的运营商 DNS（截图里一片「中国移动」+ `2409:8028::` IPv6）。  
本仓库已改成只走 `223.5.5.5` / `119.29.29.29` + 阿里 DoH，并 `hijack-dns = *:53` 等。

重载 CN-Plus 后再测：不应再出现「中国移动」解析器；仍可能看到国内 DNS（阿里/DNSPod），那是分流解析，不是运营商旁路。  
WebRTC 测「连接错误」= STUN 被拦，正常。

## Mini vs CN

Mini 只有 Proxy/AIGC/GlobalMedia；CN 才有 Google/TG/Netflix 等分组。日常用 CN。
