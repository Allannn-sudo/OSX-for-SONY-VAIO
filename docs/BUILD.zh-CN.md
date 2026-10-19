# 离线构建研究对象

[English](BUILD.en.md) · [项目进度](PROGRESS.zh-CN.md) · [主页](../README.md)

此流程仅构建 `R3-OFFLINE` 的 32 位研究对象，**不能用于安装或加载驱动**。它修正一个已确认的 Tiger 旧加载器格式问题，但仍继承未解决的运行路径等待问题，尚未在 VAIO 上验证。

## 单独准备的依赖

仓库不包含 Apple SDK、旧工具链或驱动二进制。需要在 macOS 主机上自行准备：

| 依赖 | 用途与已验证版本 |
| --- | --- |
| Python 3 | 运行构建及只读格式检查；仅使用标准库 |
| Apple GCC `cc1plus` / `cc1` | 已验证 Apple GCC 4.2.1，Apple build 5666.3；使用对应 C++ / C 前端 |
| `MacOSX10.4u.sdk` | Tiger 内核头文件、用户头文件及下述静态库 |
| i386 `ld-classic` | 将对象与 Tiger 静态库组合为可重定位 `MH_OBJECT`；须支持本脚本使用的参数 |
| `clang` | **只汇编旧 GCC 产生的 `.s` 文件**；默认 `/usr/bin/clang` |

SDK 必须包含：

```text
System/Library/Frameworks/Kernel.framework/Headers/
usr/include/
usr/lib/libkmodc++.a
usr/lib/libkmod.a
usr/lib/gcc/i686-apple-darwin9/4.0.1/libcc_kext.a
```

本项目使用的旧 GCC 是能在现代主机运行的 x86_64 宿主程序；Apple Silicon 主机需要具备执行它的环境。脚本不安装运行环境、不下载依赖，也不修改系统工具。

现代 clang 在本项目中仅充当汇编器。把它改成 C++ 编译器并加上 `-fapple-kext`，不能替代已检查的旧 GCC 内核 C++ ABI。

## 构建命令

从仓库根目录执行，把示例路径替换为自己的工具位置。`--output` 必须是**尚不存在、位于仓库之外**的新目录；重复构建请换一个目录名。

```sh
python3 scripts/build_ps2_offline.py \
  --cc1plus "/path/to/apple-gcc42/cc1plus" \
  --cc1 "/path/to/apple-gcc42/cc1" \
  --sdk "/path/to/MacOSX10.4u.sdk" \
  --ld "/path/to/ld-classic" \
  --output "/private/tmp/vaio-ps2-research-001"
```

可用 `--clang` 指定汇编器前端。脚本拒绝把输出放进此仓库、SDK、已存在目录或受保护的系统路径。它只向新输出目录写入文件，不加载内核扩展、不访问硬件端口、不写磁盘设备、不改引导及缓存。

构建流程会：

1. 复制明确列出的源码及 PS/2 头文件到输出目录，独立生成 `module_info.c`。
2. 使用旧 GCC 编译成 i386 汇编。关键参数包含 `-mkernel`、`-fapple-kext`、`-fno-jump-tables` 和禁用 SSE/MMX/FPU 的参数。
3. 由 clang 汇编、`ld-classic` 组合，保留原模块名称及 `1.1.0` 版本；研究标记为 `VAIO-Y18C-PS2-R3-OFFLINE-20261019`。
4. 调用同目录的 `audit_tiger_kext_loader.py`，检查选定的旧加载器约束，并确认源码未改变及研究标记存在。

## 输出与证据

输出目录包含源码副本、汇编、对象、中间日志、`commands.json`、输入哈希、`loader-preflight.json` 和 `build-result.json`。`ApplePS2Controller` 是离线对象；目录不是可部署的 `.kext` 安装包。不要把它复制到 Tiger 的 Extensions 或缓存。

整理本仓库时，已用实际本地工具及 SDK 在仓库外完成一次构建：格式预检通过，340 个未定义符号与此前离线 R3 相同，研究标记存在，源码哈希保持不变；此次结果字节也与原离线构建一致。换工具或路径不应以字节相等代替语义检查。

此构建器没有重现全部历史 ABI、布局、指令及实机依赖审查。`loader_preflight_passed` 只表示选定的格式约束通过；`safe_to_install` 始终为 `false`。成功构建不证明设备可用、实际加载成功或运行安全。

代码和格式检查可独立保存在 Git 中；构建输出留在仓库外。日志含有本机工具路径，分享前应检查隐私内容。
