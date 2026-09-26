# Yuanban — 原版资源根（拼音目录）

全部去广告 / 开屏 / 解锁 / 抓参 / 分流原材料与合集都在这一个文件夹下。

## 结构

```
Yuanban/
  zuozhe/                 # 按作者
    keli/                 # 可莉
      fenliu/  mokuai/  js/
    naisi/                # 奶思
    moyu/                 # 墨鱼
    …
  danxiang/               # 单件备份（作者__文件名）
    fenliu/  mokuai/  js/
  heji/                   # 合集（四分）
    quguanggao.module     # 去广告
    qukaiping.module      # 去开屏
    jiesuo.module         # 解锁增强
    zhuacan.module        # 抓参
```

## 原则

- `zuozhe` / `danxiang`：**原作者照搬**，文件字节不改
- `heji`：只拼装 + Fan.a.tail 风格分段注释；**规则正文不改**；script URL 改指本仓 `zuozhe/*/js`
- 去广告合集最上方：`广告平台拦截器` → `可莉广告过滤器`（基础，最先生效）

## 订阅

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/quguanggao.module
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/qukaiping.module
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/jiesuo.module
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/zhuacan.module
```

重建：`python3 scripts/build-yuanban.py`

与 sync 日更的 `Modules/` `Routing/` 并行，不覆盖。
