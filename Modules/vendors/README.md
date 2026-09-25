# Modules/vendors — 上游原样副本

每个文件是对应上游 raw **下载时刻** 的字节副本，不做任何改写。
合集 `adblock-verbatim.module` 由这些文件拼接而成（仅去重 + MITM 合并）。

校验：见同目录 `SHA256SUMS`。

本地补丁（NB / 微信 / heat）**不**进入此目录；需要时单独加模块。
