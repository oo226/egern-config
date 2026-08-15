# Surge-native Rules

与 **Egern `Routing/*.yaml` 分开维护**。

| 目录/文件 | 来源 |
| --- | --- |
| `*.list`（根下） | [Rabbit-Spec/Surge](https://github.com/Rabbit-Spec/Surge) 镜像 |
| `Local/` | 本仓薄补丁（追风/Tailscale/App 策略等），从 `surge/egern-Rules` 抽取 |
| `surge/egern-Rules/` | Egern YAML 导出（对照用，**不进默认 Surge.conf**） |

更新：`python3 scripts/sync-surge-native-rules.py`
