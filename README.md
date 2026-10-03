# DL Skills Manager

A CLI tool for managing Claude Code skills.

## Installation（新设备）

前置条件：

- [uv](https://docs.astral.sh/uv/)（Python 3.14+ 由 uv 自动获取，无需预装）
- git

```bash
# 1. 克隆代码仓库到任意代码目录
#    ⚠ 不要克隆到 ~/.skill-sync —— 那是数据仓库目录，由 skill-sync init 管理
git clone https://github.com/DennyLiSH/DL-skills-manager ~/tools/skills-manager
cd ~/tools/skills-manager

# 2. 安装为全局工具（提供 skill-sync 命令）
uv tool install .

# 3. 验证安装
uv tool list        # 应显示 dl-skills-manager 及版本（与 pyproject.toml 的 version 一致）
skill-sync --help
```

> **代码仓库 vs 数据仓库**：`git clone` 得到的是工具源码目录；`~/.skill-sync/`（由 `init` 创建）存放配置和技能数据，两者相互独立。多设备共享技能时只需同步数据仓库（或自定义的 `skills_store` 目录）。

## Update（升级已安装版本）

工具以快照方式安装（非 editable），仓库发版后需手动升级：

```bash
# 查看当前安装的版本
skill-sync --version

# 方式一：升级（从原始安装路径重新构建；若该克隆目录已删除/移动则改用方式二）
uv tool upgrade dl-skills-manager

# 方式二：强制重装（从任意仓库路径，如切换到新克隆目录后）
cd <repo-path>
uv tool install . --reinstall

# 验证：版本应与 pyproject.toml 的 version 一致
skill-sync --version
```

版本号采用 CalVer 格式 `YYYY.M.D`（如 `26.10.1`），定义在 `pyproject.toml`，可用 `skill-sync --version` 直接查询当前安装版本。

## Quick Start

```bash
# 初始化仓库
skill-sync init

# 查看所有可用技能
skill-sync list
```

## Agents

`install` / `update` / `remove` / `mklink` 均支持 `--agent <name>`（默认 `claude`）：

| Agent | 全局目录 | 项目级目录 |
|---|---|---|
| `claude` | `~/.claude/skills/` | `{project}/.claude/skills/` |
| `codex` | `~/.agents/skills/` | `{project}/.agents/skills/` |
| `pi` | `~/.pi/agent/skills/` | `{project}/.pi/skills/` |
| `zcode` | `~/.zcode/skills/` | `{project}/.zcode/skills/` |
| `workbuddy` | `~/.workbuddy/skills/` | 不支持（仅 `--global`） |

说明：

- `codex` 指向 `.agents/skills`（Agent Skills 开放标准，Pi 等兼容工具同样读取该目录）
- 各工具目录依据调研实证（2026-10），工具升级可能改变路径——用 `config.toml` 覆盖：

```toml
[agents.codex]
global_dir = "~/.codex/skills"    # 覆盖全局目录（可选）
project_dir = ".codex/skills"     # 覆盖项目级相对路径（可选）

[agents.mytool]                   # 亦可新增自定义 agent
global_dir = "~/.mytool/skills"
project_dir = ".mytool/skills"
```

- `[agents]` 覆盖对 `install` / `update` / `remove` 生效；`mklink` 保持无仓库依赖，仅使用内置注册表
- `remove` 自 0.5.0 起读取配置（解析与 install 相同的目标目录），因此要求仓库已初始化

## Commands

### `init` — 初始化仓库

创建 `~/.skill-sync/` 配置目录和技能存储目录。

```bash
skill-sync init [--skills-path <path>]
```

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `--skills-path` | `~/.skill-sync/data/` | 技能存储根目录 |

> **为什么默认是 copy？** 考虑到多设备同步场景（不同磁盘架构、跨盘存储），symlink 可能指向不可达路径。copy 模式确保技能文件独立可用。

### `install` — 安装技能到项目

将技能复制到项目的 `.claude/skills/` 目录（默认 copy，确保技能文件独立可用）。如需 symlink，使用 `--link-mode symlink` 覆盖。

```bash
# 安装最新版到当前项目
skill-sync install <skill-name>

# 安装指定版本
skill-sync install <skill-name>@<version>

# 安装到指定项目目录
skill-sync install <skill-name> <project-path>

# 全局安装（~/.claude/skills/）
skill-sync install <skill-name> --global

# 覆盖 link mode
skill-sync install <skill-name> --link-mode symlink

# 安装到指定 agent 的全局目录（codex → ~/.agents/skills/）
skill-sync install <name> --agent codex --global --link-mode symlink

# 安装到项目级 agent 目录（pi → <project>/.pi/skills/）
skill-sync install <name> --agent pi <project-path>
```

| 参数/选项 | 默认值 | 说明 |
|-----------|--------|------|
| `NAME` | （必填） | 技能名称，支持 `name@version` 语法 |
| `PROJECT` | `.` | 项目目录路径 |
| `--global` | `False` | 安装到 `~/.claude/skills/` 而非项目 |
| `--link-mode` | `copy` | 覆盖默认安装方式：`symlink` 或 `copy` |
| `--agent` | `claude` | 目标 agent 目录（claude/codex/pi/zcode/workbuddy 或 `[agents]` 自定义） |

### `update` — 更新技能

将已安装的技能更新为最新稳定版本。如果技能是通过 symlink 安装的，则跳过更新（symlink 已指向仓库最新源）。

```bash
# 更新当前项目的技能
skill-sync update <skill-name>

# 更新指定项目目录的技能
skill-sync update <skill-name> <project-path>

# 更新全局技能
skill-sync update <skill-name> --global

# 更新指定 agent 目录下的技能
skill-sync update <name> --agent codex --global
```

| 参数/选项 | 默认值 | 说明 |
|-----------|--------|------|
| `NAME` | （必填） | 技能名称 |
| `PROJECT` | `.` | 项目目录路径 |
| `--global` | `False` | 更新 `~/.claude/skills/` 中的技能 |
| `--agent` | `claude` | 目标 agent 目录（claude/codex/pi/zcode/workbuddy 或 `[agents]` 自定义） |

### `mklink` — 批量链接技能

将**源路径**下所有含 `SKILL.md` 的子文件夹，通过 symlink 批量链接到**目标**的 `.claude/skills/` 目录。不依赖仓库配置，可从任意源路径链接。

```bash
# 基本用法：将源路径下的技能链接到当前项目
# 源: /path/to/skills/*    目标: ./.claude/skills/
skill-sync mklink /path/to/skills

# 指定目标项目目录
# 源: /path/to/skills/*    目标: <project-path>/.claude/skills/
skill-sync mklink /path/to/skills <project-path>

# 使用前缀避免命名冲突
# 源: ~/.claude/skills/gstack/*    目标: ./.claude/skills/gstack-*
skill-sync mklink ~/.claude/skills/gstack --prefix gstack- .
# 实际效果:
#   ./.claude/skills/gstack-qa     → ~/.claude/skills/gstack/qa
#   ./.claude/skills/gstack-review → ~/.claude/skills/gstack/review

# 全局安装（链接到 ~/.claude/skills/）
# 源: /path/to/skills/*    目标: ~/.claude/skills/
skill-sync mklink /path/to/skills --global

# 批量链接到其他 agent 目录（仅内置注册表，不读 [agents] 配置）
skill-sync mklink <source-path> --agent codex <project-path>
```

| 参数/选项 | 默认值 | 说明 |
|-----------|--------|------|
| `SOURCE_PATH` | （必填） | 源目录路径，扫描其子文件夹中的技能 |
| `PROJECT` | `.` | 目标项目目录（决定 `.claude/skills/` 的位置） |
| `--prefix` | `""` | symlink 名称前缀（如 `gstack-`） |
| `--global` | `False` | 链接到 `~/.claude/skills/` 而非项目目录 |
| `--agent` | `claude` | 目标 agent 目录（仅内置注册表，不读 `[agents]` 配置） |

> **跳过规则：** 隐藏目录（`.` 开头）、不含 `SKILL.md` 的目录、普通文件会被自动跳过。已存在的同名技能会被覆盖。
>
> `--global` 与 `PROJECT` 参数互斥，不能同时指定。

### `remove` — 移除技能

从项目中移除已安装的技能（删除链接或副本）。

```bash
# 从当前项目移除
skill-sync remove <skill-name>

# 从指定项目移除
skill-sync remove <skill-name> <project-path>

# 从全局目录移除
skill-sync remove <skill-name> --global

# 移除指定 agent 目录下的技能
skill-sync remove <name> --agent codex --global
```

| 参数/选项 | 默认值 | 说明 |
|-----------|--------|------|
| `NAME` | （必填） | 技能名称 |
| `PROJECT` | `.` | 项目目录路径 |
| `--global` | `False` | 从 `~/.claude/skills/` 移除 |
| `--agent` | `claude` | 目标 agent 目录（claude/codex/pi/zcode/workbuddy 或 `[agents]` 自定义） |

### `list` — 列出所有技能

显示仓库中所有可用技能及其历史版本数量。

```bash
skill-sync list
```

### `versions` — 查看技能版本

列出指定技能的所有可用版本（包含当前版本和历史备份）。

```bash
skill-sync versions <skill-name>
```

| 参数 | 说明 |
|------|------|
| `NAME` | （必填）技能名称 |

### `mtp` — 提升开发版为生产版

将 `.dev/` 下的技能提升为生产版本：复制到 `skills/` 目录，并在 `.bk/` 创建版本备份。

```bash
skill-sync mtp <skill-name>
```

| 参数 | 说明 |
|------|------|
| `NAME` | （必填）`.dev/` 下的技能名称 |

版本号基于开发目录中最新文件的修改时间戳，格式为 `vYYYY.MM.DD[.N]`。

## Uninstallation

```bash
uv tool uninstall dl-skills-manager
```

手动删除 `~/.skill-sync/` 目录。
