# Egern/Routing（guize）

本分支自用的合并分流表，供 `Profile.yaml` 引用。  
广告 → `Reject-Merged`；国内 → `China-Direct`；结构与日用懒人一致，文件在 guize 内。

## 独立直连规则集（整表挂载，勿散落单行）

| 规则集 | 文件 | 策略 |
|--------|------|------|
| 网盘点播 | `PanVod-Direct.yaml` | DIRECT |
| 视频资源站 | `ResourceSite-Direct.yaml` | DIRECT |
| PingMe | `PingMe-Direct.yaml` | DIRECT |

上游镜像仍在 `Yuanban/zuozhe/eulac/fenliu/` 与 `Yuanban/heji/fenliu/eulac-*.yaml|.lsr`。  
`China-Direct` 仍合并了 eulac 内容作兜底；Profile 靠前挂独立规则集，面板里能看见「网盘点播 / 视频资源站 / PingMe」。
