# 上传后，从这里开始 / Start here after upload

## 简体中文

1. 将本目录**内部内容**放到现有仓库根目录，包含隐藏的 `.github`、`.gitignore` 和 `.gitattributes`。macOS Finder 可按 **Command–Shift–.** 显示隐藏文件。保留你本地克隆已有的 `.git`，不用删除仓库或重建历史。
2. 提交并合并到 `main`。主页会介绍整个 Sony VAIO + OS X 项目，机型档案在 `models/vgn-y18c/`。
3. 打开 **Actions → Create VGN-Y18C branch → Run workflow**，选择 `main`。成功后会出现真正的 `vgn-y18c` 分支，并拥有机型专属的中英文主页。已有同名分支不会被覆盖。
4. 需要机型分支的测试徽章时，运行 **Offline checks**，选择 `vgn-y18c`。初次提交 `main` 的测试会正常触发。
5. 到仓库 **Settings → General → Features** 开启 **Discussions**，用 Q&A 记录真实问答。你已有 Pull Shark；其他个人成就仍由 GitHub 根据后续真实活动授予。

ZIP 只提供文件；分支需要第 3 步，成就不会随上传自动到账。[详细中文指南](docs/GITHUB.zh-CN.md)

## English

1. Copy this directory's **contents** into the existing checkout root, including hidden `.github`, `.gitignore` and `.gitattributes`. In macOS Finder, **Command–Shift–.** shows hidden files. Keep the existing `.git` directory; repository recreation or history replacement is unnecessary.
2. Commit and merge into `main`. Its home page presents the overall Sony VAIO + OS X project; the model profile lives in `models/vgn-y18c/`.
3. Run **Actions → Create VGN-Y18C branch → Run workflow**, selecting `main`. This creates the real `vgn-y18c` branch with bilingual model home pages. An existing branch is preserved.
4. For the model branch's test badge, manually run **Offline checks** on `vgn-y18c`. The initial user commit to `main` triggers its checks normally.
5. Enable **Discussions** under **Settings → General → Features** and use Q&A for real questions. The owner already has Pull Shark; other profile achievements depend on future genuine activity and GitHub's award rules.

The ZIP supplies files. Step 3 creates the branch; uploading alone earns no achievements. [Detailed English guide](docs/GITHUB.en.md)
