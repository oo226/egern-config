# 使用菜单（main 分支）

> 打开本页即可挑选 Egern 要用的链接。技术细节与免责见 [DISCLAIMER.md](DISCLAIMER.md)。

**主配置导入：**

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Egern.yaml
```

---

## 一、我每天开着的

| 名称 | 类型 | raw 链接 | 说明 |
|------|------|----------|------|
| 去广告净化合集 | 模块 | `.../Modules/adblock-collection.module` | 默认开；**不含签到 cron** |
| 解锁增强合集 | 模块 | `.../Modules/unlock-collection.module` | 默认开 |
| PingMe 抓参签到 | 模块 | 外部 `oo226/quanx` `pingme.yaml` | 不在本仓库 |
| 插件跳转 Egern | 模块 | `.../Modules/ibl3nd-plugin-hub.yaml` | 默认开 |
| 追风挂机 | 节点+规则 | `Egern.yaml` 内 `proxies` + `Routing/Zhuifeng.yaml` | 途游小程序专用 |
| 今日油价 | 小组件 | `.../Widgets/IBL3ND/Oil_Widget.JS` | **仅 `widgets` 段**，勿加 `scriptings` |

完整前缀：`https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main`

---

## 二、按需开关

| 名称 | raw 链接 | 何时开 |
|------|----------|--------|
| 抓参 Cookie 合集 | `.../Modules/cookie-collection.module` | 签到前抓 ck，**抓完关掉**省电 |
| 追风 mitm 证书 | 系统设置 → 证书信任 | 仅挂机时段开信任，平时关 |

---

## 三、签到脚本（镜像存库，默认不写入 Egern）

由 Actions 从上游同步到 `Scripts/`，详见 [Scripts/README.md](Scripts/README.md)。

| 脚本 | 说明 |
|------|------|
| `PingMe-capture.js` / `PingMe-signin.js` | 抓参 + 签到拆分 |
| `tieba.js` / `ximalaya.js` / `dianxin10000.js` 等 | chavyleung 系，需配合 Cookie 合集 |

启用：在 `Egern.yaml` 的 `scriptings` 里自行添加 `schedule`，URL 指向 `.../main/Scripts/文件名.js`。

---

## 四、分流规则（Egern.yaml 已引用）

| 文件 | 用途 |
|------|------|
| `Routing/Bootstrap-Direct.yaml` | 测网直连 |
| `Routing/China-Direct.yaml` | 国内直连大合集 |
| `Routing/Reject-Merged.yaml` | 去广告域名 |
| `Routing/Zhuifeng.yaml` | 追风挂机两条域名 |
| `Routing/Foreign/*` | 按服务分流（AI、TG、流媒体…） |

目录说明：[Routing/README.md](Routing/README.md)

---

## 五、不用管的（黑盒依赖）

| 路径 | 说明 |
|------|------|
| `Scripts/_external/` | 去广告/解锁模块内部引用的镜像 JS，**勿手改** |
| `Scripts/fmz200/`、`Scripts/chxm1023/` 等 | 模块依赖的本地镜像 |

---

## 六、仓库分支

| 分支 | 你看不看 | 干什么 |
|------|----------|--------|
| **`main`** | **只看这个** | 成品；Egern 全部拉 `main` |
| `sync` | 可忽略 | 每日上游同步 + 合并，再发布到 `main` |

---

## 七、BoxJS（统一订阅）

去广告合集里已带 BoxJS 引擎（访问 `http://boxjs.com`）。**只需添加下面这一条订阅**，即可配置本仓库里所有支持 BoxJS 的脚本（播放器、签到、抓参、Cookie 等）。

**订阅链接（BoxJS → 应用订阅 → 添加）：**

```
https://raw.githubusercontent.com/oo226/egern-config/main/Modules/egern.boxjs.json
```

### 常用应用

| 分类 | BoxJS 应用名 | 说明 |
|------|-------------|------|
| 播放器 | 妻友社区 / PearVideo / insav / porntube / xjh51 | 改播放器后保存，**不要**在 Egern 模块参数里填 |
| 微信 | **微信跳过中间界面** | 解除微信内打开链接的中间确认页 |
| iRingo | **WeatherKit / 定位服务 / 地图** 等 | 地图天气定位增强系列，已并入统一订阅 |
| 签到 | 百度签到、10000、顺丰、喜马拉雅、网易严选、**起点读书**、花城汇 | 配合 Cookie 合集抓参后使用 |
| Yuheng | **酷我音乐**、吾爱破解、4K世界、豆瓣、i茅台 等 | 已并入统一订阅，无需再单独加 Yuheng 订阅 |
| 抓参 | PingMe 抓参、一点万象、iios、来充、Soul 唱歌 | 先 MITM 抓参，再开签到任务 |
| Cookie | 京东/美团/什么值得买 cookie、阿里云盘 cookie 等 | 配合 Cookie 合集 |
| 青龙 | 青龙同步 BoxJS | 同步 BoxJS 键到青龙环境变量 |

改完保存 → 完全退出相关 App 再开 → 测试。

**Relay 客户端**：若日志出现 `Key 'icons' not found` 或订阅解析失败，请删除旧订阅后重新添加上面的链接（新版已为每个应用补齐 `icons`）。后端地址请用 **`http://boxjs.com`**（不要用 https），并确保 Egern 代理已开启。

**若点击应用无反应（页面跳到顶部）**：删除旧订阅后重新添加上面的链接。早期版本应用 ID 带 `egern.` 前缀，与 BoxJS 路由不兼容，需重新订阅一次。

> 旧版 `yu9191-player.boxjs.json` 仍保留（仅播放器子集），新用户请直接用 `egern.boxjs.json`。

签到流程详见 [Scripts/README.md](Scripts/README.md)。

---

## 八、修改习惯

- **改自己的偏好**：直接改 `main` 上的 `Egern.yaml`（订阅、节点、策略组顺序）
- **改去广告源**：在 `sync` 分支改 `scripts/`、`Modules/manifest.yaml`，等 Actions 发布到 `main`
- **链接别乱动路径**：已填进 Egern 的 `.../main/Routing/...`、`.../main/Modules/...` 路径保持不变
