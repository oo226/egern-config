# Modules

去广告 / 去开屏 **多源合并合集**，由 GitHub Actions 每日从上游拉取、去重、合并。

## 合集架构

| 输出文件 | 上游（每日同步） | 说明 |
|----------|------------------|------|
| `adblock-collection.module` | **fmz200** 奶思 blockAds（主） + **blackmatrix7** Advertising / AdvertisingScript（补） | App/小程序净化 + 去开屏，Actions 自动去重合并 |
| `custom-apps.sgmodule` | 本仓库维护 | 邮储/动卡 MITM、税务局 bypass、**NB助手** 补全 |

原先十几个 QingRex / 可莉 / 微信分模块，已收敛为 **一个自动合并合集** + **一个本地补全模块**。

合并脚本：`python3 scripts/merge-adblock-modules.py`  
上游缓存：`Modules/_upstream/`（不提交，仅 CI / 本地生成用）

## 自定义补全 `custom-apps.sgmodule`

| 功能 | 说明 |
|------|------|
| 邮储银行 | 补 MITM 子域 + 升级弹窗拦截（开屏见奶思合集） |
| 动卡空间 | 开屏接口重写 |
| 电子税务局 | `bypass` / `skip-proxy` 直连，降低 VPN 检测 |
| NB全能助手 | `nbtool8` 广告接口 + 8ziben/快手 SDK 域名 + 穿山甲/广点通 |

改完后 `git push` 即可，不经过 Actions 覆盖。

## 墨鱼去开屏？

墨鱼 `StartUpAds.conf` 官方域名从自动化环境无法稳定下载，因此**不纳入合并源**。奶思 + blackmatrix7 已含大量开屏规则；若你手机能访问墨鱼官网，可在 Egern 模块里自行追加：

```
https://ddgksf2013.top/module/ScriptHub.Egern.sgmodule
```

## 分流 & 去广告域名

- **国内直连**：`Rules/China-Direct.yaml`（7 源合并去重，带来源标注）
- **去广告域名**：`Rules/Reject-Merged.yaml`（Repcz Reject + Sukka reject.conf 合并去重）

## 同步

```bash
python3 scripts/merge-adblock-modules.py
git add Modules/adblock-collection.module
git commit -m "chore: sync adblock collection"
git push
```

完整流水线（规则 + 模块）由 GitHub Actions `Sync Egern Rules` 每日 11:00 北京时间自动执行。
