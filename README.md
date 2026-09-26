# guize — 规则分支（干净目录）

本分支**只放规则资源**，不跟 sync 日更工厂混在一起。

## 打开就看这个

```
Yuanban/
  zuozhe/     # 作者拼音 / fenliu · mokuai · js · official（原样）
  qiandao/    # 签到单件（无合集）：keli / official / local / js
  qita/       # 其他脚本/工具（无合集）：official / local / ibl3nd
  danxiang/   # 单件备份
  heji/       # 四个合集 + 分流清单
    quguanggao.module   # 去广告（可莉+墨鱼+毒奶+BMJ+奶思）
    qukaiping.module    # 去开屏
    jiesuo.module       # 解锁增强（含微信110 / 墨鱼VIP）
    zhuacan.module      # 抓参
    fenliu/             # 分流单件（Repcz+莫离+Sukka+Loyalsoldier+…）
```

说明见 [`Yuanban/README.md`](Yuanban/README.md)。分流怎么选见 [`Yuanban/heji/fenliu/README.md`](Yuanban/heji/fenliu/README.md)。

## 订阅

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/quguanggao.module
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/qukaiping.module
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/jiesuo.module
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/zhuacan.module
```

签到：`Yuanban/qiandao/`　其他/小组件：`Yuanban/qita/`（IBL3ND 在 `qita/ibl3nd/`）　分流：`Yuanban/heji/fenliu/README.md`

重建：`python3 scripts/build-yuanban.py`

与 `sync` / `main` 互不覆盖；日更工厂请继续用 sync。
