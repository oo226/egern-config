# Surge 懒人（有喵镜像）

分支 `cursor/surge-rabbit-f611`。**不改 Egern。**  
上游：[Rabbit-Spec/Surge](https://github.com/Rabbit-Spec/Surge)

## Mini 够用吗？

| | Mini | CN（推荐你们用） |
|--|------|------------------|
| 策略组 | 就 3 个：Proxy / AIGC / GlobalMedia | Google、Apple、TG、Netflix、油管、B 站、微软、游戏…各自一组 |
| 分流 | 媒体一把梭进 GlobalMedia | 各服务独立 RULE-SET |
| 适合 | 快速冒烟、懒得点策略 | **非小白日常**（和你们 Egern 精细分流习惯更接近） |

**结论：日常直接用 CN 原样，别用 Mini。** Mini 不是「功能阉割版 Surge」，只是策略组极少；代理协议、Smart 地区组、外部订阅都有，但 Netflix/TG/Google 不能单独拧。

## 怎么用（原样）

1. Surge → 从 URL 下载配置  
2. 文本模式 → 改 `✈️ 我的节点` 的 `policy-path=`  
3. 保存 → 更新外部资源  

**CN 原样（日常）：**  
`https://raw.githubusercontent.com/oo226/egern-config/refs/heads/cursor/surge-rabbit-f611/Surge/Conf/Spec/Surge-CN.conf`

**Mini 原样（仅试水）：**  
`https://raw.githubusercontent.com/oo226/egern-config/refs/heads/cursor/surge-rabbit-f611/Surge/Conf/Spec/Surge-Mini.conf`

分流仍指向有喵 GitHub（跟上游日更）。`Surge/Rules/` 是同内容备份。

## Tailscale（按官方手册 + 社区实战）

依据：

- [Surge Manual · Tailscale](https://manual.nssurge.com/policies/tailscale.html)
- [jizhi0v0：用 Surge Mac 接入 Tailscale](https://www.jizhiovo.com/posts/surge-mac-tailscale)（最小可抄配置）
- [原子比特：Surge 内置 Tailscale 三端实战](https://www.geekhuashan.com/blog/tailnet-integration-runbook)

**人家怎么用（共同点）：**

1. 主配置几乎不动，只加三块：`[Proxy]` 一条 `tailscale`、`[Tailscale xxx]`、`[Rule]` **最前面**几条。  
2. **登录**：生产向多用后台生成的 `auth-key`（每台设备一把、预授权）；5.21+/6.8+ 也可用策略编辑器 `interactive-login`（状态不能拷贝到别的手机）。  
3. **规则**：控制面 `tailscale.com` / `tailscale.io` / `ipn.dev` → `DIRECT`（防死锁）；MagicDNS 后缀 + `100.64.0.0/10` + `fd7a:115c:a1e0::/48` → Tailnet 策略。  
4. **必删** `skip-proxy` / `bypass-tun` 里的 `100.64.0.0/10` 和 `*.ts.net`，否则流量绕过 Surge，内置 Tailscale 永不命中。  
5. `idle-keepalive = 0` 保持会话；`auto-add-magic-dns-rule` 默认 true；`underlying-proxy` 仅控制面被墙再加（加了会偏 DERP）。  
6. 内置 Tailscale **只作出站**，当不了 exit node / 子网路由器；家里要进 LAN 仍靠 NAS/另一台机器 advertise routes。

**已打好补丁的配置（CN 结构零改，只加上述最小补丁）：**  
`https://raw.githubusercontent.com/oo226/egern-config/refs/heads/cursor/surge-rabbit-f611/Surge/Conf/Spec/Surge-CN-Plus.conf`

导入后你要改三处：

1. `policy-path=` 机场订阅  
2. `auth-key = tskey-auth-...`（或改成 `interactive-login = true` 并注释 auth-key）  
3. `DOMAIN-SUFFIX,YOURTAILNET.ts.net` → 你的 MagicDNS 后缀  

## 回环（IP Rewrite）

与懒人骨架无关，SideStore / `10.7.0.1` 场景用模块（需 **TF ≥ 5.23**）：  
`https://raw.githubusercontent.com/oo226/egern-config/refs/heads/cursor/surge-rabbit-f611/Surge/Module/IP-Rewrite-Hairpin.sgmodule`

## 目录

```
Surge/Conf/Spec/   有喵原样 *.conf + Surge-CN-Plus.conf
Surge/Rules/       有喵 list 一比一备份
Surge/Module/      IP-Rewrite-Hairpin.sgmodule
```
