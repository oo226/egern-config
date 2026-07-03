# Modules

去广告 / 去开屏 **单一合集**，由 GitHub Actions 从上游镜像。

## 合集内容

| 文件 | 上游 | 说明 |
|------|------|------|
| `adblock-collection.module` | [fmz200 奶思 blockAds](https://github.com/fmz200/wool_scripts) | App/小程序净化 + **去开屏**（约 730 款） |

这一份替代了原先 Egern.yaml 里多个 QingRex Beta、可莉、微信分模块，规则不重复、更省电。

## 墨鱼去开屏？

墨鱼 `StartUpAds.conf` 官方域名从自动化环境无法稳定下载，因此**不单独镜像**。奶思合集内已含大量开屏规则；若你手机能访问墨鱼官网，可在 Egern 模块里自行追加：

```
https://ddgksf2013.top/module/ScriptHub.Egern.sgmodule
```

## 分流

分流不在 Modules，已合并到 `Rules/China-Direct.yaml` + 各 `Rules/*.yaml`。

## 同步

```powershell
python scripts/download-modules.py
git add Modules/
git commit -m "chore: sync adblock collection"
git push
```
