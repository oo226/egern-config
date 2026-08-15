# Surge 配置（`surge` 分支）

与 **`main`（Egern）彻底分开**：不覆盖 `Egern.yaml` / `Routing/*.yaml`。  
两边**共用**的只有 `main` 上的模块 / Scripts / GeoIP 成品。

## 导入

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/surge/Surge.conf
```

分流（**Surge 专用**，深巷有喵 / Rabbit-Spec 风格）：

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/surge/Rules/
```

## 和 Egern 怎么分开？

| | Egern (`main`) | Surge (`surge`) |
| --- | --- | --- |
| 主配置 | `Egern.yaml` | `Surge.conf` |
| 分流 | `Routing/*.yaml` | `Rules/*.list`（Rabbit-Spec 镜像 + `Local/` 薄补丁） |
| 对照导出 | — | `egern-Rules/`（YAML→list，**默认 conf 不用**） |
| 去广告 | 模块 + YAML | 分流可选；模块按需（main） |
| DNS / Host | Egern dns | 对齐深巷：无大表 Local DNS Mapping，`hijack-dns` 仅 8.8.8.8 |

更新脚本：

```bash
python3 scripts/export-surge-rulesets.py   # → surge/egern-Rules/
python3 scripts/sync-surge-native-rules.py # → surge/Rules/（正式树）
python3 scripts/publish-surge.py           # → origin/surge
```

## 分流对比（为何换专用树）

| | 深巷有喵 | 旧：Egern 导出进 Surge | 现：Surge 专用 |
| --- | --- | --- | --- |
| China | `China.list` ~3.7k + `ChinaCIDR` ~5.4k | `China-Direct` ~2.5 万行合集 | 同深巷拆分镜像 |
| 广告 Reject | 默认**注释** | `Reject-Merged` ~11 万域名常开 | 默认注释（可开 Sukka） |
| Proxy | 一份 `Proxy.list` | Proxy + ProxyGFW 双表更胖 | 深巷 `Proxy.list` |
| `[Host]` | 空 | 曾把 Reject/China 挂 DNS 映射 | 仅静态 Host |
| 来源 | 自维护 list | Egern YAML 导出 | 镜像深巷 + Local 补丁 |

结论：旧树能分流，但比深巷胖一个数量级且和 Egern 绑死；现改为 **Surge 专用浅树**。

## 内存友好（对齐懒人包）

1. 分流 China / Proxy 用深巷体量，不挂 Reject 大表（默认）
2. 不要把规则再塞进 `[Host]` Local DNS Mapping
3. `hijack-dns = 8.8.8.8:53, 8.8.4.4:53`，避免 `*:53`
4. DoH / IPv6 默认关
5. MITM 模块按需

## 第三方懒人配置参考

| 作者 | 说明 | 链接 |
| --- | --- | --- |
| **深巷有喵（Rabbit-Spec）** | 本仓 Surge 分流主参考 | [Surge-CN.conf](https://raw.githubusercontent.com/Rabbit-Spec/Surge/Master/Conf/Spec/Surge-CN.conf) · [China.list](https://raw.githubusercontent.com/Rabbit-Spec/Surge/Master/Rules/China.list) · [仓库](https://github.com/Rabbit-Spec/Surge) |
| **耳东橙（erdongchanyo）** | Advertising RULE-SET 懒人 | [Surge_EDC-Lzay.conf](https://raw.githubusercontent.com/erdongchanyo/Rules/main/Surge/Surge_EDC-Lzay.conf) |
| **XiaoMao** | 全配置 + Ad DOMAIN-SET | [XiaoMaoSurge.conf](https://raw.githubusercontent.com/xiaomaoJT/Surge/main/config/XiaoMaoSurge.conf) |
| **可莉（iKeLee）** | Loon 插件中心，非完整 Surge conf | [hub.kelee.one](https://hub.kelee.one) |

## 图标

策略组图标见 [Icons.md](Icons.md)。

## 分支

| 分支 | 给谁 |
| --- | --- |
| `main` | Egern |
| `surge` | Surge（本页） |
| `sync` | 工厂 |
