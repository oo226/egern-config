# Surge 懒人（有喵镜像）— 链接在这里

分支：`cursor/surge-rabbit-f611` · PR：https://github.com/oo226/egern-config/pull/158  
仓内路径：`Surge/Conf/Spec/`、`Surge/Module/`、`Surge/Rules/`

## 直接复制用

**日常（有喵 CN 原样）：**
```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/cursor/surge-rabbit-f611/Surge/Conf/Spec/Surge-CN.conf
```

**CN + Tailscale + 回环（推荐试这个）：**
```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/cursor/surge-rabbit-f611/Surge/Conf/Spec/Surge-CN-Plus.conf
```

导入后改三处：`policy-path`、`auth-key`、`YOURTAILNET.ts.net`。

**Mini 原样（仅冒烟，日常别用）：**
```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/cursor/surge-rabbit-f611/Surge/Conf/Spec/Surge-Mini.conf
```

**回环单独模块（可选；Plus 里已内置，一般不用再装）：**
```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/cursor/surge-rabbit-f611/Surge/Module/IP-Rewrite-Hairpin.sgmodule
```

## 回环已上正式版

App Store **5.23.0**（2026-10-12）已含 `[IP Rewrite]`。  
CN-Plus 已写入：`tun-included-routes` + `10.7.0.1 = reflect`（不再当 TF 专用）。

## Mini vs CN

Mini 只有 Proxy/AIGC/GlobalMedia；CN 才有 Google/TG/Netflix 等分组。日常用 CN。
