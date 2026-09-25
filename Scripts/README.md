# 签到脚本（Scripts）

镜像自用，**版权归上游**。见 [DISCLAIMER.md](../DISCLAIMER.md)。

## 目录怎么读（三层）

```
Scripts/
├── *.js                 ← 你可能启用的签到（根目录）
├── _external/           ← 合集黑盒依赖（勿手改、勿当目录逛）
├── _stubs/              ← 占位
└── <作者>/              ← 上游全量镜像（防删库；合集已指到这里）
    fmz200 / chxm1023 / yu9191 / yuheng / …
```

**别把作者仓目录当「模块列表」翻。** 日常入口是根目录那几个 `*.js` + [USAGE.md](../USAGE.md)。

## 常用 raw

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Scripts/PingMe-signin.js
```

| 脚本 | 来源 | 说明 |
|------|------|------|
| PingMe-capture / PingMe-signin | ZenmoFeiShi、oo226/quanx | 抓参 + 签到 |
| iios / mixc / Nodeseek / LaiChong 等 | ZenmoFeiShi | 清单在 sync 的 `scripts/manifest.yaml` |
| tieba / ximalaya / dianxin10000 / sfexpress | chavyleung | 配合 Cookie 合集 |

Egern **默认不写**签到 schedule；需要时在 `scriptings` 自行添加。
