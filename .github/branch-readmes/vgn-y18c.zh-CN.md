# VGN-Y18C · Tiger 10.4.8 机型分支

[整个 VAIO 项目（main）](https://github.com/Allannn-sudo/OSX-for-SONY-VAIO/tree/main) · [机型档案](models/vgn-y18c/README.md)

[![Offline checks](https://github.com/Allannn-sudo/OSX-for-SONY-VAIO/actions/workflows/offline-checks.yml/badge.svg?branch=vgn-y18c)](https://github.com/Allannn-sudo/OSX-for-SONY-VAIO/actions/workflows/offline-checks.yml)

**简体中文** · [English](README.en.md)

一台 Pentium M 时代的 Sony VAIO，运行 Mac OS X Tiger，并保留 Windows XP。
这里记录这台机器的安装过程、兼容性现状和驱动研究。更新于 **2026-10-19**。

![Sony VAIO VGN-Y18C 运行 Mac OS X Tiger 10.4.8](github-ph.jpg)

*项目所有者提供的实机照片。关于本机的文字曾做显示调整；照片本身不代表所有硬件功能已正常。*

## 当前进度

**Tiger 已成功安装并进入桌面，内置键盘和触摸板仍未稳定。** 一次 PS/2 实验驱动造成启动崩溃，恢复原始控制器后已重新进入桌面。新的候选仅保留为离线研究源码。

| 项目 | 状态 |
| --- | --- |
| USB 安装、内置硬盘启动 | 已完成实机安装；故障恢复后已再次进入桌面 |
| Windows XP | 分区保留，之前确认能启动；最新恢复后的完整双系统往返待复核 |
| Darwin 启动菜单 | 已配置；采用 Legacy BIOS + MBR |
| USB 键盘、鼠标 | 实机可用 |
| 内置键盘、触摸板 | 曾短暂可用，重启后再次失灵，仍在排查 |
| Intel 2200BG Wi-Fi | 完成历史驱动研究，尚无成功联网记录 |
| 睡眠、合盖睡眠 | 尚未解决 |
| 图形、声音及其他设备 | 图形桌面可显示；硬件加速、声音及其他功能未完成验证 |

完整经过、失败记录及下一步见 [中文进度](docs/PROGRESS.zh-CN.md)。

## 这台机器

| 配置 | 本项目记录 |
| --- | --- |
| 型号 | Sony VAIO VGN-Y18C |
| 处理器 | Intel Pentium M 755，2.00 GHz，32 位 / SSE2 |
| 内存 | 2 GB DDR |
| 芯片组 / 显卡 | Intel 855GME / ICH4-M；Intel Extreme Graphics 2 |
| 无线网卡 | Intel PRO/Wireless 2200BG，`8086:4220` |
| 硬盘 | 128 GB Kingston，Tiger 分区约 38.86 GB，XP 保留 |
| 系统 / 引导 | Mac OS X 10.4.8，semthex Darwin 8.8.1，BIOS / MBR / Darwin |
| 安装介质 | 32 GB USB 安装盘；本次没有可用光驱 |

这些是本机的配置，不是全部 VGN-Y18C 的出厂规格。硬盘转接主控、屏幕实际分辨率及其他设备仍有待核实。此方案不使用 EFI、OpenCore 或 rEFInd。

## 仓库内容

```text
README.md / README.en.md          中英文主页
github-ph.jpg                     实机照片，保留原像素，移除拍摄元数据
docs/                             双语进度、离线构建和归档范围说明
drivers/VAIOPS2Controller-r3-offline/
                                  仅供离线研究的 PS/2 源码
scripts/                          离线构建、加载器预检和协议模拟
tests/                            自行构造 Mach-O 数据的便携测试
tools/Tiger-Input-State/           Tiger 只读输入状态采集工具
evidence/                         不含私人诊断的状态及历史文件哈希摘要
licenses/                         Apple 源码适用的 APSL 1.1 全文
```

本目录是可版本管理的源码与研究快照，不包含 ISO、安装镜像、Apple 系统二进制、驱动二进制、SDK、编译器、原始诊断或个人备份。完整本地工作目录仍需单独保存。[归档范围](docs/ARCHIVE.zh-CN.md)

## 离线检查

在现代开发机上，Python 3.9+ 可直接运行不依赖原驱动文件的测试：

```sh
python3 -B -m unittest discover -s tests -v
```

主机协议模拟使用替代端口模型，不接触硬件：

```sh
c++ -std=c++11 -Wall -Wextra -Werror scripts/ps2_init_protocol_sim.cpp -o /tmp/vaio-ps2-protocol-sim
/tmp/vaio-ps2-protocol-sim
```

完整候选构建需要另备旧 Apple GCC、Tiger SDK 和合适的链接器，见 [中文构建说明](docs/BUILD.zh-CN.md)。通过格式、ABI 或模拟检查，不代表内核驱动可以安全加载。

## PS/2 研究状态

R2 已撤回：其五个 const scattered relocation 触发 Tiger 旧加载器的空指针路径。R3-OFFLINE 使用 `-fno-jump-tables` 消除这项已知构建缺陷，但仍继承无界等待及 IRQ 处理风险，尚未实机加载。本仓库不提供驱动安装入口。

下一步先确认恢复后的输入状态，再离线处理运行路径的超时和错误传播。之后才评估与内置系统隔离的外部诊断环境；Wi-Fi 和睡眠测试继续排在输入稳定之后。

## 来源与许可

Apple 衍生源码保留原版权和适用许可证，详见 [第三方说明](THIRD_PARTY_NOTICES.md)及[许可范围](LICENSE.md)。实机照片由项目所有者提供。项目独立记录这台机器的研究过程，与 Sony 或 Apple 没有隶属关系。
