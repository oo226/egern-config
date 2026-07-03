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

1. 需要抓参的脚本：先开 MITM + 对应「参数」http_request，打开 App 触发一次
2. chavyleung 脚本需同时启用 **BoxJs** 模块
3. 再启用对应「签到」schedule

新增脚本：编辑 `scripts/manifest.yaml` 后 push，Actions 会自动下载。
