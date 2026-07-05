# Scripts

签到脚本镜像目录，由 GitHub Actions 自动从上游同步。

| 脚本 | 来源 | 说明 |
|------|------|------|
| PingMe.js | [ZenmoFeiShi/Qx](https://github.com/ZenmoFeiShi/Qx) | 抓参+签到 |
| iios_checkin.js | ZenmoFeiShi/Qx | iios 签到 |
| mixc_signin.js | ZenmoFeiShi/Qx | 一点万象抓参+签到 |
| Nodeseek_NsCheckin.js | ZenmoFeiShi/Qx | NodeSeek 抓参+签到 |
| LaiChong.js | ZenmoFeiShi/Qx | 来充抓参+签到 |
| SoulSing.js | ZenmoFeiShi/Qx | Soul 唱歌抓参+签到 |
| SLY.js | ZenmoFeiShi/Qx | 岁乐游抓参+签到 |
| qdreader.js | Yuheng0101/X | 起点读书 |
| dianxin10000.js | chavyleung | 电信营业厅 |
| tieba.js | chavyleung | 百度贴吧 |
| sfexpress.js | chavyleung | 顺丰速运 |
| yanxuan.js | chavyleung | 网易严选 |
| ximalaya.js | chavyleung | 喜马拉雅 |

Egern 里默认全部 `disabled: true`。启用步骤：

1. **ZenmoFeiShi 二合一脚本**（PingMe 等）：开 MITM + `http_request` 抓参 → 打开 App 一次 → 再开 `schedule` 签到
2. **chavyleung 脚本**（贴吧/电信/喜马拉雅等）：启用 **抓参 Cookie 合集**（默认关）+ **BoxJs** → 打开 App 抓 ck → **抓完关闭抓参合集** → 再开签到 `schedule`
3. 去广告/解锁与抓参已拆分，日常不必开着抓参模块

新增脚本：编辑 `scripts/manifest.yaml` 后 push，Actions 会自动下载。
