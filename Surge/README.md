# Surge 懒人配置（有喵镜像 + Plus）

本目录在分支 `cursor/surge-rabbit-f611`，**不改动 Egern/**。  
上游：[Rabbit-Spec/Surge](https://github.com/Rabbit-Spec/Surge)（深巷有喵）。

## 怎么试

1. Surge → 从 URL 下载配置，选下面任一链接。  
2. 文本编辑 → 把 `✈️ 我的节点` 的 `policy-path=` 改成你的机场订阅。  
3. 保存 → 更新外部资源。

### 原样（有喵一字未改）

| 文件 | URL |
|------|-----|
| Mini（推荐先试） | `https://raw.githubusercontent.com/oo226/egern-config/refs/heads/cursor/surge-rabbit-f611/Surge/Conf/Spec/Surge-Mini.conf` |
| CN 完整中文 | `https://raw.githubusercontent.com/oo226/egern-config/refs/heads/cursor/surge-rabbit-f611/Surge/Conf/Spec/Surge-CN.conf` |
| 其余 Spec | 同目录 `Surge-EN` / `Family` / `Developer` …（均原样） |

分流仍指向有喵 GitHub `Rules/*.list`（与官方一致，会跟上游日更）。

### Plus（Mini + 近期 Surge 能力）

`https://raw.githubusercontent.com/oo226/egern-config/refs/heads/cursor/surge-rabbit-f611/Surge/Conf/Spec/Surge-Mini-Plus.conf`

相对原版多了：

| 项 | 说明 |
|----|------|
| `block-quic = true` | 显式全局拦 QUIC |
| DoH `encrypted-dns-server` | 阿里 / DNSPod |
| 加强 `hijack-dns` | 多拦 1.1.1.1 / 9.9.9.9 |
| **Tailscale** | `[Proxy] 我的Tailnet` + `[Tailscale Home]` 交互登录；规则兜底 `ts.net` / `100.64/10` / `fd7a::/48`；并从 `skip-proxy` 去掉 `100.64/10` |
| 策略组 `category=` | 主选 / 服务 / 地区 / 订阅 |
| `GEOIP,UNKNOWN` | 无库命中走 Proxy（需 ≥ 5.22.1） |
| 分流 RULE-SET | 改指本仓库 `Surge/Rules`（有喵 list 一比一拷贝） |

**回环（IP Rewrite）** 因需 **TF ≥ 5.23**，未写进主配置，请另装模块：

`https://raw.githubusercontent.com/oo226/egern-config/refs/heads/cursor/surge-rabbit-f611/Surge/Module/IP-Rewrite-Hairpin.sgmodule`

### Tailscale 怎么开

1. 用 Plus 配置。  
2. 策略 → `我的Tailnet` → 交互登录（不要同时填 auth-key）。  
3. 控制台批准设备后，MagicDNS / peer 地址会自动进规则；显式 CIDR 作兜底。  
4. 不用 Tailscale：注释掉 `[Proxy]`/`[Tailscale Home]` 里相关行，以及 `[Rule]` 里四条 Tailscale 规则，并把 `100.64.0.0/10` 加回 `skip-proxy`（与有喵原版一致）。

## 目录

```
Surge/
  Conf/Spec/     # 有喵原样 *.conf + Surge-Mini-Plus.conf
  Rules/         # 有喵 Rules/*.list 一比一
  Module/        # IP-Rewrite-Hairpin 等可选模块
  README.md
```

## 说明

- 图标仍用有喵 CDN（未镜像 png）。  
- 合入 `guize` 后，把 Plus 里 RULE-SET 的分支名改成 `guize` 即可。  
- Egern 配置本分支故意不动。
