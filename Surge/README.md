# Surge 懒人（有喵镜像）— 链接在这里

分支：`cursor/surge-rabbit-f611` · PR：https://github.com/oo226/egern-config/pull/158  
仓内路径：`Surge/Conf/Spec/`、`Surge/Module/`、`Surge/Rules/`

## 直接复制用

**日常（有喵 CN 原样）：**
```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/cursor/surge-rabbit-f611/Surge/Conf/Spec/Surge-CN.conf
```

**CN + Tailscale（推荐）：**
```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/cursor/surge-rabbit-f611/Surge/Conf/Spec/Surge-CN-Plus.conf
```

导入后改三处：`policy-path`、`auth-key`、`YOURTAILNET.ts.net`。

**回环模块（官方写法；主配置不要写 `%INSERT%`）：**
```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/cursor/surge-rabbit-f611/Surge/Module/IP-Rewrite-Hairpin.sgmodule
```
Surge → 模块 → 安装 → 打开。需 App Store ≥ **5.23.0**。

**Mini 原样（仅冒烟）：**
```
https://raw.githubusercontent.com/oo226/egern-config/refs/heads/cursor/surge-rabbit-f611/Surge/Conf/Spec/Surge-Mini.conf
```

## 回环怎么用

手册写明：`tun-included-routes = %INSERT% 10.7.0.1/32` **只能出现在模块里**（`%INSERT%` / `%APPEND%` 是模块运算符）。  
主配置里写会报「无效配置」——已从 CN-Plus 去掉，请单独装上面的模块。
## Mini vs CN

Mini 只有 Proxy/AIGC/GlobalMedia；CN 才有 Google/TG/Netflix 等分组。日常用 CN。
