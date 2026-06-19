# Git 版本管理规范

## 1. 版本管理方式

本项目使用 Git 进行版本管理，使用 GitHub 作为远程代码仓库。

本地项目目录：

```text
hotel-booking-analysis/
```

远程仓库：

```text
https://github.com/tedxu222-cpu/hotel-booking-analysis
```

Git 版本管理用于记录项目文件、数据处理脚本、Notebook、分析报告和阶段成果的变更过程，便于回溯、检查和协作。

## 2. Commit Message 规范

本项目提交信息采用统一格式：

```text
<type>: <中文说明>
```

其中，`type` 用于说明本次提交的变更类型，中文说明用于简要描述本次提交完成的具体内容。

常用 `type` 约定如下：

| type | 用途 |
|---|---|
| `init` | 初始化项目、目录结构、基础配置 |
| `docs` | 文档、说明文件、报告 |
| `data` | 数据读取、数据检查、数据处理结果 |
| `clean` | 数据清洗逻辑 |
| `feat` | 新功能，例如质量校验脚本、中间表构建脚本 |
| `report` | 实验报告、阶段总结 |
| `fix` | 修复问题，例如路径、编码、导入错误 |
| `refactor` | 重构代码，但不改变原有处理结果 |
| `chore` | 依赖、配置、杂项维护 |

示例：

```text
init: 初始化项目结构
docs: 添加Git分支管理规范
clean: 完成缺失值与异常值处理
feat: 添加数据质量校验脚本
report: 添加第一阶段实验报告
fix: 修复脚本输出乱码问题
```

## 3. 分支管理策略

本项目采用 `main/dev/feature` 三级分支策略。

### 3.1 main 分支

`main` 分支用于保存稳定版本和阶段性最终成果。

原则上不直接在 `main` 分支上进行频繁开发。阶段内容确认稳定后，再合并到 `main` 分支。

### 3.2 dev 分支

`dev` 分支用于日常开发和阶段性内容整合。

多个功能分支完成后，先合并到 `dev` 分支进行检查，再根据阶段完成情况合并到 `main` 分支。

### 3.3 feature 分支

`feature` 分支用于具体任务开发，命名格式为：

```text
feature/任务名称
```

示例：

```text
feature/project-setup
feature/data-cleaning
feature/eda
feature/modeling
```

## 4. 推荐开发流程

1. 从 `main` 创建 `dev` 分支。
2. 从 `dev` 创建具体的 `feature/...` 分支。
3. 在 `feature/...` 分支完成具体任务。
4. 将 `feature/...` 分支合并回 `dev`。
5. 阶段成果确认稳定后，将 `dev` 合并回 `main`。
6. 将更新后的分支推送到 GitHub。

## 5. 常用 Git 命令

查看当前状态：

```bash
git status
```

暂存修改：

```bash
git add .
```

提交修改：

```bash
git commit -m "clean: 完成缺失值与异常值处理"
```

推送到远程仓库：

```bash
git push
```

创建并切换到 `dev` 分支：

```bash
git checkout -b dev
```

创建并切换到功能分支：

```bash
git checkout -b feature/eda
```

切换回 `main` 分支：

```bash
git checkout main
```
