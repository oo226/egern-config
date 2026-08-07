# Surge Rules（从 Egern Routing YAML 导出）

| 后缀 | Surge 用法 | 说明 |
| --- | --- | --- |
| `.list` | `RULE-SET,url,策略` | 完整规则（blackmatrix7 同款） |
| `.domainset` | `DOMAIN-SET,url,策略` | 纯域名；`.` 前缀=后缀匹配（Sukka domainset） |
| `.ip.list` | `RULE-SET,url,策略,no-resolve` | 仅 IP/ASN；放在域名规则之后 |

主配置在 `surge` 分支根目录 `Surge.conf`。
Egern 继续用 `main` 的 `Routing/*.yaml`，互不覆盖。
