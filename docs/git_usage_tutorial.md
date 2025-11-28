# Git 使用方法教学

本教程介绍常见的 Git 工作流程，包括从仓库拉取代码、修改、提交、合并和推送。
在开发流程中，repo拉取链接及项目路径应根据实际需要做出更改。

## 1、克隆仓库
如果你要参与一个已有的项目，首先需要将远程仓库克隆到本地：

```powershell
git clone https://github.com/username/repo.git
cd repo
```

## 2、创建新分支
为了避免直接在 main 或 master 分支上进行开发，通常会创建一个新的分支：

```powershell
git checkout -b new-feature
```

## 3、工作目录
在工作目录中进行代码编辑、添加新文件或删除不需要的文件。

在提交更改前，建议使用 pre-commit 工具对代码进行格式统一化和规范检查：

```powershell
pre-commit run --all-files
```

## 4、暂存文件
将修改过的文件添加到暂存区，以便进行下一步的提交操作：

```powershell
git add filename
# 或者添加所有修改的文件
git add .
```

## 5、提交更改
将暂存区的更改提交到本地仓库，并添加提交信息：

```powershell
git commit -m "Add new feature"
```

## 6. 拉取最新更改
在推送本地更改之前，最好从远程仓库拉取最新的更改，以避免冲突：

```powershell
git pull origin main
# 或者如果在新的分支上工作
git pull origin new-feature
```

## 7. 推送更改
将本地的提交推送到远程仓库：

```powershell
git push origin new-feature
```

## 8. 创建 Pull Request（PR）
在 GitHub 或其他托管平台上创建 Pull Request，邀请团队成员进行代码审查。PR 合并后，你的更改就会合并到主分支。

## 9. 合并更改
在 PR 审核通过并合并后，可以将远程仓库的主分支合并到本地分支：

```powershell
git checkout main
git pull origin main
git merge new-feature
```

---

# Git Usage Tutorial (English)

This tutorial introduces the common Git workflow, including pulling code, creating branches, editing, formatting, staging, and committing.

## 1. Clone the repository
If you want to contribute to an existing project, first clone the remote repository:

```powershell
git clone https://github.com/username/repo.git
cd repo
```

## 2. Create a new branch
To avoid developing directly on main or master, usually create a new branch:

```powershell
git checkout -b new-feature
```

## 3. Working directory
Edit code, add new files, or delete unnecessary files in your working directory.

Before committing changes, it is recommended to use pre-commit to format and check your code:

```powershell
pre-commit run --all-files
```

## 4. Stage files
Add modified files to the staging area for the next commit:

```powershell
git add filename
# Or add all modified files
git add .
```

## 5. Commit changes
Commit staged changes to the local repository with a message:

```powershell
git commit -m "Add new feature"
```

## 6. Pull the Latest Changes
Before pushing local changes, it's best to pull the latest updates from the remote repository to avoid conflicts:

```powershell
git pull origin main
# Or if working on a new branch
git pull origin new-feature
```

## 7. Push Changes
Push local commits to the remote repository:

```powershell
git push origin new-feature
```

## 8. Create a Pull Request (PR)
Create a Pull Request on GitHub or another hosting platform to invite team members for code review. Once the PR is merged, your changes will be integrated into the main branch.

## 9. Merge Changes
After the PR is reviewed and merged, you can merge the remote main branch into your local branch:

```powershell
git checkout main
git pull origin main
git merge new-feature
```

Translated with DeepL.com (free version)
