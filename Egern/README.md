# Egern 懒人配置（结构对齐老书 jnlaoshu）

自用总配置。分流 / 模块底座是本仓 `Yuanban/heji`（自托管），不是外站拼接。

## 一键订阅

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Egern/Profile.yaml
```

## 使用前

1. Egern 里导入上面的 Profile
2. 启用模块 **Sub-Store**，建合集名 `AllServer`（节点池从 `sub.store/download/collection/AllServer` 取）
3. 在 App 内生成并信任 MITM CA（`egern.p12` / 口令按你本地为准）
4. 解锁合集已含 BoxJs、iRingo 天气/地图原版、AntiRevoke、屏蔽更新；按需开 18+ / 抓参 / PingMe / 定位
5. 小组件「今日油价」已预填 `zhejiang/ningbo`；视频/网盘规则默认关闭，要开把 `disabled` 改 `false`

## 模块里那几个是啥

| 模块 | 干什么 |
|------|--------|
| **Sub-Store** | 订阅转换 / 节点合集（本配置节点池靠它的 `AllServer`） |
| **Script Hub** | 把 QX/Surge/Loon 重写、规则集转成 Egern 能用的 |
| **BoxJs** | 脚本参数面板（`boxjs.com`），已并进解锁合集 |
| **WeatherKit / Maps** | NSRingo iRingo 天气/地图增强原版，已并进解锁合集 |
| **插件跳转** | kelee/qingrex 插件中心一键改成 Egern 安装链接 |
| **YouTube 增强** | 老书精选单件；去广告合集里已有老书 YouTube 段，单件可另开 |

## 和旧 `main/Egern.yaml` 的差别

| | 旧 main | 本 Profile |
|--|---------|------------|
| 结构 | 零件堆叠 | 老书式分区 + smart 地区组 |
| 图标 | iili + lige47 | 同左（地区/AI/Spotify/Emby…） |
| 去广告 | 旧 Modules 合集 | `Yuanban/heji/quguanggao` + `qukaiping` |
| 解锁 | unlock-collection | `jiesuo`（含工具/证书/天气地图） |
| 分流 | `Routing/*` | `Yuanban/heji/fenliu/*` + 追风/视频/网盘 |
| 节点 | 占位订阅 | Sub-Store AllServer |

## 目录

```
Egern/
  Profile.yaml          # 总配置
  Rule/BlockHttpDNS.yaml
  README.md
```

规则零件仍在 `Yuanban/`；改合集后重建：`python3 scripts/build-yuanban.py`（工具补丁也可跑 `scripts/apply-tools-to-jiesuo.py`）。
