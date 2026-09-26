# guize — 规则分支（干净目录）

本分支**只放规则资源**，不跟 sync 日更工厂混在一起。

## 懒人总配置（先看这个）

结构对齐 [jnlaoshu/MySelf Egern Profile](https://github.com/jnlaoshu/MySelf/tree/main/Egern)，底座用本仓 `Yuanban/heji`。

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Egern/Profile.yaml
```

说明：[`Egern/README.md`](Egern/README.md)。导入后先启用 **Sub-Store**，合集名 `AllServer`。

## 零件目录

```
Egern/
  Profile.yaml            # 总配置（DNS + 策略组 + 分流 + 模块）
Yuanban/
  zuozhe/                 # 作者拼音 / fenliu · mokuai · js
  qiandao/                # 签到单件
  qita/                   # 其他 / IBL3ND
  danxiang/               # 单件备份
  heji/
    quguanggao.module     # 去广告
    qukaiping.module      # 去开屏
    jiesuo.module         # 解锁（日常）
    shibajia.module       # 18+
    zhuacan.module        # 抓参
    fenliu/               # 分流单件
```

## 合集单独订阅（可选）

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/quguanggao.module
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/qukaiping.module
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/jiesuo.module
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/shibajia.module
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/zhuacan.module
```

原则：**文件名直白**；**脚本全自托管**。重建：`python3 scripts/build-yuanban.py`

与 `sync` / `main` 互不覆盖；旧 `main/Egern.yaml` 仍可对照，日常请用本 Profile。
