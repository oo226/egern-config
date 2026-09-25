# vendors/qingrex — 可莉去广告原样副本

来源：https://github.com/QingRex/LoonKissSurge `Surge/*去广告.sgmodule`（不含 Beta）

字节与上游一致；合集构建时仅把 **可镜像** 的 script URL 改指本仓 `Scripts/vendors/`。

说明：部分模块脚本托管在 `kelee.one`，该站 Cloudflare 会拦截本仓库 CI/云构建 IP（403）。
这类 URL 在合集里仍保留上游地址（与可莉原样一致），待可拉取时再镜像。

重建：`python3 scripts/build-adblock-keli-nais.py`
