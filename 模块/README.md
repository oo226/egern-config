# 模块（重写 / MITM / 脚本）

**模块**通过 URL Rewrite、MITM、Script 拦截 App 内广告和开屏，与 `分流/` 的域名分流是两层防护。

## 你需要关注的文件

| 文件 | 说明 |
|------|------|
| `去广告净化合集.module` | **唯一入口** — 奶思 + blackmatrix7 + 银行/税务/NB助手 每日合并去重 |

## 源文件（维护用）

| 文件 | 说明 |
|------|------|
| `custom-apps.sgmodule` | 本仓库维护的银行/税务/NB/NBToolAds 补全，合并时自动并入主模块 |
| `manifest.yaml` | 上游源清单（给 CI 用） |

## 不用管的目录

| 目录 | 说明 |
|------|------|
| `_upstream/` | CI 缓存的上游模块，不提交 |

改 `custom-apps.sgmodule` 后 `git push` 即可；Actions 下次运行会把它合并进 `去广告净化合集.module`。
