# 签到（单件，无合集）

签到模块差异大、依赖 Cookie/BoxJs，**不做 heji 合集**，按来源分文件夹自取。

上游能做成 Surge 模块的就这些；更多是 **Task/JS**（BoxJs 或手动），放在 `js/`。

- `keli/` — 可莉 Surge 根目录签到（WPS / 书香门第）
- `official/` — QingRex Official 签到 / 抢券 / 联通余量
- `local/` — Profile 默认 `qiandao.sgmodule`（PingMe+起点）；单件 `pingme.yaml` / `qdreader.sgmodule` 仍保留
- `zenmofeishi/` — 怎么肥事签到（PingMe/一点万象/NodeSeek…，中文文件名）
- `js/` — 其他 sync 签到脚本（fmz200 等）

抓参合集见 `heji/zhuacan.module`（抓完关掉）。工具类见 `Yuanban/qita/`。
