# DL Skills Manager

A CLI tool for managing Claude Code skills.

## Installation

```bash
# 克隆仓库
git clone <repo-url> ~/.skill-sync
cd ~/.skill-sync

# 安装为全局工具
uv tool install .
```

## Quick Start

```bash
# 初始化仓库
skill-sync init

# 查看所有可用技能
skill-sync list
```

## Commands

### `init` — 初始化仓库

创建 `~/.skill-sync/` 配置目录和技能存储目录。

```bash
skill-sync init [--skills-path <path>] [--link-mode <mode>]
```

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `--skills-path` | `~/.skill-sync/data/` | 技能存储根目录 |
| `--link-mode` | `copy` | 安装方式：`symlink` 或 `copy`（不指定时交互式询问） |

> **为什么默认是 copy？** 考虑到多设备同步场景（不同磁盘架构、跨盘存储），symlink 可能指向不可达路径。copy 模式确保技能文件独立可用。

### `install` — 安装技能到项目

将技能链接（或复制）到项目的 `.claude/skills/` 目录。安装方式取决于 `config.toml` 中的 `default_link_mode`，可通过 `--link-mode` 覆盖。

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
```

| 参数/选项 | 默认值 | 说明 |
|-----------|--------|------|
| `NAME` | （必填） | 技能名称，支持 `name@version` 语法 |
| `PROJECT` | `.` | 项目目录路径 |
| `--global` | `False` | 安装到 `~/.claude/skills/` 而非项目 |
| `--link-mode` | 从 config.toml 读取 | 覆盖默认安装方式：`symlink` 或 `copy` |

### `update` — 更新技能

将已安装的技能更新为最新稳定版本。如果技能是通过 symlink 安装的，则跳过更新（symlink 已指向仓库最新源）。

```bash
# 更新当前项目的技能
skill-sync update <skill-name>

# 更新指定项目目录的技能
skill-sync update <skill-name> <project-path>

# 更新全局技能
skill-sync update <skill-name> --global
```

| 参数/选项 | 默认值 | 说明 |
|-----------|--------|------|
| `NAME` | （必填） | 技能名称 |
| `PROJECT` | `.` | 项目目录路径 |
| `--global` | `False` | 更新 `~/.claude/skills/` 中的技能 |

### `mklink` — 批量链接技能

将指定路径下所有含 `SKILL.md` 的子文件夹通过 symlink 批量链接到项目的 `.claude/skills/` 目录。不依赖仓库配置，可从任意源路径链接。

```bash
# 链接源路径下所有技能到当前项目
skill-sync mklink /path/to/skills

# 链接到指定项目目录
skill-sync mklink /path/to/skills <project-path>

# 使用前缀避免命名冲突
skill-sync mklink ~/.claude/skills/gstack --prefix gstack- .
# 效果: .claude/skills/gstack-qa → ~/.claude/skills/gstack/qa
```

| 参数/选项 | 默认值 | 说明 |
|-----------|--------|------|
| `SOURCE_PATH` | （必填） | 源目录路径，扫描其子文件夹中的技能 |
| `PROJECT` | `.` | 目标项目目录 |
| `--prefix` | `""` | symlink 名称前缀（如 `gstack-`） |

> **跳过规则：** 隐藏目录（`.` 开头）、不含 `SKILL.md` 的目录、普通文件会被自动跳过。已存在的同名技能会被覆盖。

### `remove` — 移除技能

从项目中移除已安装的技能（删除链接或副本）。

```bash
# 从当前项目移除
skill-sync remove <skill-name>

# 从指定项目移除
skill-sync remove <skill-name> <project-path>

# 从全局目录移除
skill-sync remove <skill-name> --global
```

| 参数/选项 | 默认值 | 说明 |
|-----------|--------|------|
| `NAME` | （必填） | 技能名称 |
| `PROJECT` | `.` | 项目目录路径 |
| `--global` | `False` | 从 `~/.claude/skills/` 移除 |

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
