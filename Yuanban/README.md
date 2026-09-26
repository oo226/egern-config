# Yuanban — 原版资源根（拼音目录）

全部去广告 / 开屏 / 解锁 / 抓参 / 签到 / 其他脚本 / 分流都在这一个文件夹下。

## 结构

```
Yuanban/
  zuozhe/                 # 按作者
    keli/                 # 可莉
      fenliu/  mokuai/  js/  official/
    naisi/  moyu/  …
  qiandao/                # 签到单件（无合集）
    keli/  official/  local/  js/
  qita/                   # 其他脚本/工具（无合集）
    official/  local/  ibl3nd/
  danxiang/               # 单件备份
  heji/                   # 合集 + 分流清单
    quguanggao(含开屏) / jiesuo / shibajia(18+) / zhuacan / fenliu/
```

## 原则

- `zuozhe` / `danxiang` / `qiandao` / `qita`：**原作者照搬**，文件字节不改
- `heji`：只拼装 + Fan.a.tail 分段；**规则正文不改**；script URL 改指本仓
- 去广告置顶：`广告平台拦截器` → `可莉广告过滤器`；开屏已并入 `quguanggao`
- **18+ 单独 `shibajia`，不进日常 `jiesuo`**
- **签到 / 其他脚本 / IBL3ND 小组件不做合集**

## 订阅（合集）

```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/quguanggao.module
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/jiesuo.module
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/shibajia.module
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/guize/Yuanban/heji/zhuacan.module
```

签到：`Yuanban/qiandao/`　其他/小组件：`Yuanban/qita/`　分流：`heji/fenliu/README.md`

可莉：模块←QingRex 作者仓；js←kelee.one（Surge UA，不是 sync）。
Yu9191：作者仓若删则用 sync 防删；Yuheng←Yuheng0101/X；老书←jnlaoshu/MySelf。

重建：`python3 scripts/build-yuanban.py`

与 sync 日更并行，不覆盖。
