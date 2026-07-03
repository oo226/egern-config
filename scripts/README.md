# Scripts

签到脚本镜像目录，由 GitHub Actions 自动从上游同步。

| 脚本 | 来源 | 说明 |
|------|------|------|
| PingMe.js | [ZenmoFeiShi/Qx](https://github.com/ZenmoFeiShi/Qx) | 抓参+签到合一，本仓库镜像 |
| iios_checkin.js | ZenmoFeiShi/Qx | 本仓库镜像 |
| qdreader.js | Yuheng0101/X 起点读书 | 关闭 |
| dianxin10000.js | chavyleung 电信 | 关闭 |
| tieba.js | chavyleung 贴吧 | 关闭 |
| sfexpress.js | chavyleung 顺丰 | 关闭 |
| yanxuan.js | chavyleung 严选 | 关闭 |
| ximalaya.js | chavyleung 喜马拉雅 | 关闭 |

在 Egern 里启用前，需先在对应 App 手动签到一次以获取 Cookie。

新增脚本：编辑 `scripts/manifest.yaml` 后 push，Actions 会自动下载。
