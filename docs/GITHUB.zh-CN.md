# GitHub 上传、分支与个人成就

[English](GITHUB.en.md) · [项目主页](../README.md)

目标仓库：[Allannn-sudo/OSX-for-SONY-VAIO](https://github.com/Allannn-sudo/OSX-for-SONY-VAIO)。这份文件包已写入真实仓库地址，尚未替你提交、推送或创建远程分支。

## 这次准备了什么

| 内容 | 上传后的作用 | 还需要做什么 |
| --- | --- | --- |
| `README.md` / `README.en.md` | `main` 展示整个 Sony VAIO 跑 OS X 项目的背景、实机照片和进度 | 将更新合并到 `main` |
| `models/vgn-y18c/` | 随时可访问的 VGN-Y18C 中英文机型档案 | 后续根据实机结果更新 |
| `Create VGN-Y18C branch` 工作流 | 创建真正的 `vgn-y18c` 分支，并使用机型专属主页 | 上传后手动运行一次；已有同名分支时不覆盖 |
| `Offline checks` 工作流 | 检查仓库内容与离线工具；README 显示实际运行状态 | 让 Actions 完成运行 |
| Issue 表单、PR 模板、贡献指南 | 接收其他 VAIO 机型的测试、修复和资料贡献 | 有真实问题或改动时使用 |

**上传一个 ZIP 或创建一个同名文件夹，都不会创建 Git 分支。** Git 分支是提交历史中的一条开发线。工作流在 GitHub 上运行后才会出现 `vgn-y18c`。

## 替换现有仓库内容

沿用网页上传也可以：在仓库选择 **Add file → Upload files**，上传解压后的目录内容，包含 `.github`。Finder 按 **Command–Shift–.** 可显示隐藏文件。提交时可选择新建 `feature/project-overview`，再创建 PR 合并到 `main`；直接提交到 `main` 也能完成本次更新。[GitHub 网页上传说明](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository)

使用 GitHub Desktop 则更方便检查整个变更及不再需要的旧文件：

1. 在 GitHub Desktop 克隆或打开现有 `OSX-for-SONY-VAIO` 仓库，从最新 `main` 创建 `feature/project-overview` 分支。
2. 将解压得到的仓库内容复制到该本地仓库根目录，包含 `.github` 和 `.gitignore`。保留现有的 `.git` 目录；不要把整个外层文件夹再嵌套一层。
3. 在 **Changes** 查看新文件、替换项及不再需要的旧文件。确认根目录能看到 `README.md`、`models/`、`docs/` 和 `.github/`，没有 ISO、私人日志或密钥。
4. 提交这次真实的结构调整，推送分支，创建发往 `main` 的 Pull Request。检查差异及 `Offline checks` 结果后合并。

也可以直接更新 `main`，但通过 PR 保存这次结构调整，更容易查看变更与回退。无需删除仓库、重建仓库或强制推送。GitHub 网页上传只添加或替换选中的文件，**不会自动删除旧文件，也不会解压上传的 ZIP**；请上传解压后的内容。

## 创建 VGN-Y18C 分支

1. 先确保 `.github/workflows/create-model-branch.yml` 已合并到默认分支 `main`。
2. 打开 [Create VGN-Y18C branch](https://github.com/Allannn-sudo/OSX-for-SONY-VAIO/actions/workflows/create-model-branch.yml)，点击 **Run workflow**，选择 `main` 后运行。
3. 成功后，在仓库分支下拉菜单选择 `vgn-y18c`。其根目录 README 会展示这台机器的安装成果、限制与研究状态；`main` 继续展示整体项目。
4. 分支创建使用 `GITHUB_TOKEN`，不会因此自动触发 CI。需要该分支自己的 CI 记录时，打开 **Actions → Offline checks → Run workflow**，选择 `vgn-y18c` 运行。参见 [工作流触发规则](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)。

GitHub 要求手动工作流先存在于默认分支，且操作者有仓库写权限。参见 [手动运行工作流](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow)。

工作流已声明创建分支所需的 `contents: write`。若运行被权限策略拒绝，先查看日志，再检查 **Settings → Actions → General → Workflow permissions**；只有策略确实要求时才调整为允许写入。组织级策略仍可能限制仓库权限。参见 [Actions 设置](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository)。

`main` 与 `vgn-y18c` 创建后会分别演进，不会自动同步。后续修复可使用 `fix/ps2-…` 等短期分支，经 PR 合并到对应目标；不要把整体项目主页误覆盖成单一机型主页。

## 你已有 Pull Shark，下一步关注什么

**README 上的状态徽章与个人主页 Achievements 是两种东西。** 这里加入的 CI、机型和研究状态徽章用于展示项目；它们不增加个人成就数量。GitHub 自行判定个人成就，官方也没有公布完整的解锁规则，因此不承诺具体数量或必定到账。[GitHub 官方介绍](https://github.blog/news-insights/product-news/introducing-achievements-recognizing-the-many-stages-of-a-developers-coding-journey/)

| 方向 | 对这个项目有价值的做法 | 当前限制 |
| --- | --- | --- |
| **Galaxy Brain** | 在 Q&A 中解答真实的 VAIO、Tiger 或驱动问题，由提问者认可答案 | 需要真实问答与采纳；仅开启 Discussions 不会解锁 |
| **共同创作**，常见成就名 **Pair Extraordinaire** | 和真实贡献者共同完成一个修复或文档提交，正确标注共同作者，经 PR 合并 | 需要实际合作；完整触发规则未在官方文档中明确列出 |
| **项目获得关注**，常见成就名 **Starstruck** | 分享实机成果、清楚的兼容性表格和可复现研究，吸引有兴趣的人收藏 | 取决于其他用户；此包不承诺星数或奖章 |
| **Pull Shark** | 继续用 PR 记录有意义的修复、机型报告与文档改进 | 你已拥有；不计作本次新增成就 |

Galaxy Brain 与有帮助的讨论答案之间的关系有上述官方介绍支持。其他成就名称常见于 GitHub 个人主页，但这里把它们作为可关注的方向，不把社区流传的数量门槛当成官方规则。

先到 **Settings → General → Features** 开启 **Discussions**，并保留或创建 **Q&A** 类别。目前仓库仍需手动开启这项设置，文件包不能替你切换。Q&A 支持提问者或有相应权限的维护者点击 **Mark as answer**。参见 [开启 Discussions](https://docs.github.com/en/discussions/quickstart)、[问答类别](https://docs.github.com/en/discussions/managing-discussions-for-your-community/managing-categories-for-discussions)、[采纳答案](https://docs.github.com/en/discussions/collaborating-with-your-community-using-discussions/participating-in-a-discussion)。

共同创作时，使用真实贡献者同意公开的姓名与 GitHub 关联邮箱，或其 GitHub `no-reply` 邮箱，再添加 `Co-authored-by`，让记录对应实际参与。参见 [GitHub 共同作者说明](https://docs.github.com/en/pull-requests/how-tos/commit-changes/creating-a-commit-with-multiple-authors)。

Quickdraw、YOLO 等其他常见名称的完整规则也没有在这些官方资料中公开，因此本指南不提供“快速必得”的操作承诺。按实际需要及时处理问题和维护文档，出现新成就时再记录即可。历史活动奖章不能通过这次上传补领。

想让更多人找到项目，可在仓库 **About** 设置简短介绍和 topics，例如 `sony-vaio`、`mac-os-x`、`tiger`、`retrocomputing`、`legacy-bios`。介绍、Issue 表单和真实实机结果有助于交流；这些设置也不会直接授予个人奖章。
