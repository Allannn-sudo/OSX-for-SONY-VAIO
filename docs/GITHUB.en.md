# GitHub upload, branches, and profile achievements

[中文](GITHUB.zh-CN.md) · [Project home](../README.en.md)

Target repository: [Allannn-sudo/OSX-for-SONY-VAIO](https://github.com/Allannn-sudo/OSX-for-SONY-VAIO). This package uses the actual repository address. It has not committed, pushed, or created a remote branch on your behalf.

## What is ready

| Item | Purpose after upload | Remaining action |
| --- | --- | --- |
| `README.md` / `README.en.md` | Present the overall Sony VAIO OS X project, its story, hardware photo, and progress on `main` | Merge the update into `main` |
| `models/vgn-y18c/` | Provide an always-accessible bilingual machine profile | Update it with future hardware results |
| `Create VGN-Y18C branch` workflow | Create a real `vgn-y18c` branch with machine-specific home pages | Run once after upload; an existing branch is left intact |
| `Offline checks` workflow | Check repository content and offline tools; report actual CI status in the README | Allow Actions to complete |
| Issue forms, PR template, contributing guide | Support reports, fixes, and research for other VAIO models | Use them for real work |

**Uploading a ZIP or creating a folder does not create a Git branch.** A Git branch is a line of development in commit history. The `vgn-y18c` branch appears after the workflow runs on GitHub.

## Update the existing repository

You can continue using the web uploader: choose **Add file → Upload files** and upload the extracted contents, including `.github`. In macOS Finder, **Command–Shift–.** shows hidden files. You can commit to a new `feature/project-overview` branch and merge through a PR, or update `main` directly. See [GitHub's upload instructions](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository).

GitHub Desktop is another option for reviewing the entire change and obsolete files:

1. Clone or open the existing `OSX-for-SONY-VAIO` repository in GitHub Desktop. Create `feature/project-overview` from the latest `main`.
2. Copy the extracted repository contents into that checkout's root, including `.github` and `.gitignore`. Keep the existing `.git` directory. Do not nest an additional outer folder inside the repository.
3. Review **Changes**, including additions, replacements, and obsolete files. The root should contain `README.md`, `models/`, `docs/`, and `.github/`, with no ISO, private logs, or credentials.
4. Commit this substantive restructuring, push the branch, and open a pull request targeting `main`. Review the diff and `Offline checks` results, then merge.

A direct update to `main` is possible, but a PR makes this restructuring easier to review and revert. There is no need to recreate the repository or force-push. GitHub's web uploader adds or replaces selected files; **it does not remove obsolete files or extract an uploaded ZIP**. Upload the extracted contents.

## Create the VGN-Y18C branch

1. Ensure `.github/workflows/create-model-branch.yml` has been merged into the default branch, `main`.
2. Open [Create VGN-Y18C branch](https://github.com/Allannn-sudo/OSX-for-SONY-VAIO/actions/workflows/create-model-branch.yml). Select **Run workflow**, choose `main`, and run it.
3. On success, select `vgn-y18c` in the repository's branch selector. Its root READMEs present this machine's installation results, limitations, and research status. `main` retains the overall project home page.
4. Branch creation uses `GITHUB_TOKEN`, so this operation does not automatically trigger CI. To obtain CI results for the new branch, open **Actions → Offline checks → Run workflow**, select `vgn-y18c`, and run it. See [Workflow trigger rules](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow).

GitHub requires a manually dispatched workflow to exist on the default branch, and the operator needs repository write access. See [Manually running a workflow](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow).

The workflow declares `contents: write` for branch creation. If policy rejects the run, read the log and check **Settings → Actions → General → Workflow permissions**; change write permissions only if the applicable policy requires it. Organization policies may still restrict access. See [Managing Actions settings](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository).

After creation, `main` and `vgn-y18c` evolve independently. Future fixes can use short-lived branches such as `fix/ps2-…` and PRs into the appropriate target. Keep the overall home page distinct from the machine-specific home page when merging.

## Beyond your existing Pull Shark

**README status badges and profile Achievements are different.** This package adds CI, machine, and research indicators to describe the project; they do not add profile achievements. GitHub awards achievements itself and does not publish complete unlock rules, so no specific number or award is guaranteed. See [GitHub's official introduction](https://github.blog/news-insights/product-news/introducing-achievements-recognizing-the-many-stages-of-a-developers-coding-journey/).

| Direction | Useful activity for this project | What is still required |
| --- | --- | --- |
| **Galaxy Brain** | Answer genuine VAIO, Tiger, or driver questions in Q&A and help the questioner reach a solution | Real answers recognized as helpful; enabling Discussions alone earns nothing |
| **Coauthorship**, commonly associated with **Pair Extraordinaire** | Complete a genuine fix or documentation change with another contributor, attribute authorship correctly, and merge through a PR | Actual collaboration; complete award rules are not specified in official documentation |
| **Project recognition**, commonly associated with **Starstruck** | Share hardware results, clear compatibility tables, and reproducible research that interested users may star | Other users' interest; no star count or award is promised |
| **Pull Shark** | Keep documenting meaningful fixes, model reports, and documentation improvements through PRs | Already owned; it is not counted as a new achievement here |

The official introduction supports the connection between Galaxy Brain and helpful discussion answers. Other achievement names appear on GitHub profiles, but this guide treats them as possible directions, without presenting community-reported thresholds as official rules.

Enable **Discussions** under **Settings → General → Features**, and retain or create a **Q&A** category. This repository setting still needs to be enabled manually; uploading files cannot toggle it. Q&A lets the discussion author or an appropriately authorized maintainer select **Mark as answer**. See [Discussions quickstart](https://docs.github.com/en/discussions/quickstart), [Discussion categories](https://docs.github.com/en/discussions/managing-discussions-for-your-community/managing-categories-for-discussions), and [Marking an answer](https://docs.github.com/en/discussions/collaborating-with-your-community-using-discussions/participating-in-a-discussion).

For genuine coauthorship, obtain each contributor's preferred name and GitHub-linked email, or their GitHub `no-reply` address, before adding `Co-authored-by`, so attribution reflects actual participation. See [GitHub's coauthor documentation](https://docs.github.com/en/pull-requests/how-tos/commit-changes/creating-a-commit-with-multiple-authors).

The cited official material does not publish complete rules for other commonly seen names such as Quickdraw and YOLO either, so this guide promises no quick guaranteed method. Handle real issues and documentation when needed, and record new achievements if awarded. Historical event awards cannot be earned retroactively through this upload.

To help interested users find the project, set a short repository **About** description and topics such as `sony-vaio`, `mac-os-x`, `tiger`, `retrocomputing` and `legacy-bios`. A clear introduction, useful issue forms and observed hardware results support discussion; these settings do not directly award profile achievements.
