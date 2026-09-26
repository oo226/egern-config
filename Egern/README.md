# Egern 懒人配置（结构对齐老书 jnlaoshu）

自用总配置。分流 / 模块底座是本仓 `Yuanban/heji`（自托管）。

## 一键订阅

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Egern/Profile.yaml
```

## AllServer 是啥（最容易懵）

不是仓库文件，是 **Sub-Store App 里的组合订阅名字**。

1. 打开本 Profile，确保 **解锁增强合集** 开着（里面已有 Sub-Store / Script Hub）
2. 浏览器进 `http://sub.store`（或 App 内打开）
3. 添加你的机场订阅后，新建一个 **组合订阅**，名字填死：`AllServer`
4. 配置里节点池写的是  
   `https://sub.store/download/collection/AllServer?target=Egern`  
   名字对不上就拉不到节点，面板「全部节点」会空。

## 使用前

1. 导入上面的 Profile，信任 MITM CA
2. 按上面建好 `AllServer`
3. 解锁合集已含：Sub-Store、Script Hub、BoxJs、iRingo 天气/地图、AntiRevoke、屏蔽更新
4. YouTube 增强在 **去广告合集**（老书段），不用再开单件
5. 今日油价预填 `zhejiang/ningbo`；视频资源站规则默认关（网盘与国内直连重叠，未再挂）

## 模块简表

| 东西 | 在哪 |
|------|------|
| Sub-Store / Script Hub / BoxJs / 天气地图 / 证书 / 屏蔽更新 | `heji/jiesuo` |
| YouTube 增强（老书） | `heji/quguanggao` |
| 插件跳转 | Profile 默认开 |
| iRingo 定位/其他 | Profile 单件，默认关 |
| 视频资源站 | `fenliu/eulac-视频资源站`（Profile 默认关） |
| 网盘点播原料 | `fenliu/eulac-网盘点播`（与国内直连重叠，Profile 不挂） |

## 目录

```
Egern/
  Profile.yaml
  Rule/BlockHttpDNS.yaml
  README.md
```

重建合集：`python3 scripts/build-yuanban.py`  
工具补丁：`python3 scripts/apply-tools-to-jiesuo.py`
