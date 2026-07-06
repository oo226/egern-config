# Publish → main

`scripts/publish-main.py` reads `publish/manifest.yaml` and copies **成品** from `sync` 工作区到 `main`。

- **main**：Egern 拉取，路径稳定，见 [USAGE.md](../USAGE.md)
- **sync**：上游同步 + 合并，可含 `scripts/`、`Modules/_upstream/`、中间 `.sgmodule` 等

Actions 在 `sync` 跑完全部构建后执行 publish，**不会**再把整棵 `sync` 树 merge 进 `main`。
