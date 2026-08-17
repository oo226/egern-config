# Surge Rules（从 Egern Routing YAML 导出）

| 后缀 | Surge 用法 | 说明 |
| --- | --- | --- |
| `.list` | `RULE-SET,url,策略` | 完整规则（blackmatrix7 同款；不含 DOMAIN/URL-REGEX） |
| `.domainset` | `DOMAIN-SET,url,策略` | 纯域名；`.` 前缀=后缀；中文域名已转 punycode |
| `.ip.list` | `RULE-SET,url,策略,no-resolve` | 仅 IP/ASN；放在域名规则之后 |

注意：外部 RULE-SET 不含 `DOMAIN-REGEX` / `URL-REGEX`（Surge iOS 会报 Invalid line）。
中文等 IDN 在 domainset/list 中转为 `xn--…` punycode。
域名行自带 `extended-matching`：只更新外部资源即可按 SNI 命中（不必改 Surge.conf）。

主配置在 `surge` 分支根目录 `Surge.conf`。
Egern 继续用 `main` 的 `Routing/*.yaml`，互不覆盖。
