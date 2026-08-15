# egern-Rules（Egern Routing YAML 导出 · 对照用）

**默认 Surge.conf 不用这棵树。** 正式分流见 `surge/Rules/`（Rabbit-Spec 镜像）。

| 后缀 | Surge 用法 | 说明 |
| --- | --- | --- |
| `.list` | `RULE-SET,url,策略` | 完整规则（blackmatrix7 同款；不含 DOMAIN/URL-REGEX） |
| `.domainset` | `DOMAIN-SET,url,策略` | 纯域名；`.` 前缀=后缀；中文域名已转 punycode |
| `.ip.list` | `RULE-SET,url,策略,no-resolve` | 仅 IP/ASN；放在域名规则之后 |

注意：外部 RULE-SET 不含 `DOMAIN-REGEX` / `URL-REGEX`（Surge iOS 会报 Invalid line）。
中文等 IDN 在 domainset/list 中转为 `xn--…` punycode。

生成：`python3 scripts/export-surge-rulesets.py`
Surge 原生树：`python3 scripts/sync-surge-native-rules.py`
