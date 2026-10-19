# OSX for SONY VAIO

**简体中文** · [English](README.en.md)

**让 VAIO 跑起 Mac OS X，保存每一步真实进展。**

[![Offline checks](https://github.com/Allannn-sudo/OSX-for-SONY-VAIO/actions/workflows/offline-checks.yml/badge.svg?branch=main)](https://github.com/Allannn-sudo/OSX-for-SONY-VAIO/actions/workflows/offline-checks.yml)
![Research in progress](https://img.shields.io/badge/status-active_research-d9a441)
![First model VGN-Y18C](https://img.shields.io/badge/first_model-VGN--Y18C-395b80)
[![GitHub stars](https://img.shields.io/github/stars/Allannn-sudo/OSX-for-SONY-VAIO?style=flat)](https://github.com/Allannn-sudo/OSX-for-SONY-VAIO/stargazers)

这是一项在 Sony VAIO 老硬件上研究 Mac OS X 的个人项目：按机型记录安装、驱动、引导、失败与恢复。目前第一台实验机器 **VGN-Y18C 已运行 Tiger 10.4.8 并进入桌面**；输入稳定性、无线和睡眠仍在继续排查。更新于 **2026-10-19**。

![Sony VAIO VGN-Y18C 运行 Mac OS X Tiger](github-ph.jpg)

*第一台实验机器的实机照片，由项目所有者提供。关于本机的文字曾作显示调整；桌面照片不代表全部硬件功能已经适配。*

## 为什么做这个项目

林信行公开的采访文章转述了安藤国威的回忆：乔布斯曾向索尼展示运行 Mac OS 的 VAIO。这个项目受到那条未走完的路线启发，希望用老硬件探索「VAIO + Mac OS X」的体验。关于具体日期及系统版本，原文也保留了不确定性。[采访者原文](https://nobi.com/en/Steve%20Jobs%20and%20Japan/entry-1212.html)

本项目是今天的复古硬件实践；VGN-Y18C 与 Tiger 10.4.8 代表本次实验选择。更多背景见 [中文故事](docs/STORY.zh-CN.md)。

## 项目进度

| 方向 | 已确认结果 | 当前重点 |
| --- | --- | --- |
| 第一台机型：VGN-Y18C | USB 安装完成；Tiger 已在内置盘进入桌面 | 保持可启动基线，继续修复输入 |
| XP 与引导 | XP 分区保留，曾确认可启动；Darwin 菜单已配置 | 最新恢复后的双系统完整往返待复核 |
| 内置键盘 / 触摸板 | BIOS、启动菜单与 XP 正常；Tiger 曾短暂恢复 | Tiger 内可靠初始化与绑定尚未解决 |
| Wi-Fi / 睡眠 | 完成历史驱动和电源报告研究 | 尚无成功联网或睡眠/唤醒验证 |
| PS/2 源码研究 | 已定位 R2 加载崩溃；R3 离线修正该项构建缺陷 | 无界等待、IRQ 和实机安全验证仍待处理 |
| 更多 VAIO 机型 | 当前只有 VGN-Y18C 的实机记录 | 收集带证据的机型报告，逐台建立档案 |

[完整中文进度](docs/PROGRESS.zh-CN.md) · [English progress](docs/PROGRESS.en.md)

## 机型档案与分支

| 入口 | 用途 |
| --- | --- |
| `main`（当前主页） | 整个项目的介绍、路线和各机型进度 |
| [VGN-Y18C 机型档案](models/vgn-y18c/README.md) | 当前已进入桌面的配置、验证边界与待修复项 |
| [`vgn-y18c` 分支](https://github.com/Allannn-sudo/OSX-for-SONY-VAIO/tree/vgn-y18c) | 首次运行创建工作流后，拥有独立机型主页的阶段快照 |
| `feature/<change>` | 一次具体改动，完成后通过 Pull Request 评审合并 |

**替换文件并提交到 `main` 后，运行一次 Actions → Create VGN-Y18C branch。** 它才会创建真实 Git 分支，并把分支主页换成 VGN-Y18C 页面；同名分支已存在时保留原样。ZIP 本身不携带远端分支。[中文操作指南](docs/GITHUB.zh-CN.md)

## 下一步

- [x] 用 USB 完成首台 VAIO 的 Tiger 安装并保存实机照片。
- [x] 记录真实故障、原始控制器恢复和离线加载器分析。
- [x] 整理中英文档案、便携测试、机型分支创建入口。
- [ ] 取得恢复后的新输入报告，修正运行路径超时和错误传播。
- [ ] 准备足够的离线证据后，评估隔离于内置盘的外部诊断环境。
- [ ] 输入稳定后，分别验证 Wi-Fi、睡眠和双系统往返。

## 如何参与

用 [Issue 模板](https://github.com/Allannn-sudo/OSX-for-SONY-VAIO/issues/new/choose)提交可复查的机型报告或问题；通过真实 PR 贡献文档、分析或代码。Discussions 可在仓库设置启用后用于问答和经验交流。[贡献说明](CONTRIBUTING.md)

仓库提供实际测试状态徽章、PR 模板、Issue 表单和 GitHub Actions。个人 Achievements 由 GitHub 按真实活动授予，和仓库状态徽章分别计算。[个人成就与参与路径](docs/GITHUB.zh-CN.md)

## 源码与检查

保留 `drivers/`、`scripts/`、`tests/`、`tools/`、`evidence/` 与双语 `docs/`。R2 已撤回；R3-OFFLINE 尚未在 VAIO 加载，仍有运行路径风险。**本仓库没有驱动安装入口。**

现代开发机可执行：

```sh
python3 -B -m unittest discover -s tests -v
c++ -std=c++11 -Wall -Wextra -Werror scripts/ps2_init_protocol_sim.cpp -o /tmp/vaio-ps2-protocol-sim
/tmp/vaio-ps2-protocol-sim
```

[离线构建说明](docs/BUILD.zh-CN.md) · [归档范围](docs/ARCHIVE.zh-CN.md) · [第三方来源](THIRD_PARTY_NOTICES.md) · [许可范围](LICENSE.md)

安装介质、Apple 系统/驱动二进制、SDK、原始私人诊断和个人备份保留在本地。项目独立于 Apple、Sony 和 VAIO。
