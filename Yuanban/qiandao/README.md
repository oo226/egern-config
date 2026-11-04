# 签到（单件，无合集）

签到模块差异大、依赖 Cookie/BoxJs，**不做 heji 合集**，按来源分文件夹自取。

上游能做成 Surge 模块的就这些；更多是 **Task/JS**（BoxJs 或手动），放在 `js/`。

- `keli/` — 可莉 Surge 根目录签到（WPS / 书香门第）
- `official/` — QingRex Official 签到 / 抢券 / 联通余量
- `local/` — Profile 默认原生 `qiandao.yaml`（PingMe+起点）；单件 `pingme.yaml` / `qdreader.sgmodule`；Surge 仍可用 `qiandao.sgmodule`  
  - **Egern 开关**：跟 IBL3ND 一样写 `compat_arguments` + `compat_arguments_schema`，`options: ['true','false']` 才会出 Toggle。抓参用正则里插入 `[^{{{capture}}}]`（同南网/联通小组件），**不是** `#` 注释，也不是 sgmodule 的 `#!arguments`。  
  - PingMe 签到脚本用 `js/PingMe-signin.js`（兼容 Egern 400 + `policy: DIRECT`）。强制更新模块后：开「PingMe 抓参」→ 打开 App → 关掉 → 签到。
- `zenmofeishi/` — 怎么肥事签到（PingMe/一点万象/NodeSeek…，中文文件名）
- `js/` — 其他 sync 签到脚本（fmz200 等）

抓参合集见 `heji/zhuacan.module`（抓完关掉）。工具类见 `Yuanban/qita/`。
