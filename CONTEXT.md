# CONTEXT — skill-sync 领域词汇表

## 存储模型

- **仓库 (repo)**：`~/.skill-sync/`，含 `config.toml`，由 `init` 创建。
- **skills_store**：技能存储根目录，默认 `~/.skill-sync/data`。
- **生产版**：`{store}/skills/{name}/`；目录含 `SKILL.md` 才是有效技能。
- **开发版 (.dev/)**：`{store}/.dev/{name}/`。
- **历史备份 (.bk/)**：`{store}/.bk/{name}@{version}/`。备份命名 `{name}@{version}` 是 SkillsStore 的实现细节，调用方不得自行拼串。
- **版本号**：`vYYYY.MM.DD`，同日多版 `.N` 递增；开发版可带 `-dev` 后缀。

## 模块词汇

- **SkillsStore**（`core/store.py`）：仓库布局与备份命名的唯一所有者。查询：`find_skill` / `find_version` / `list_backups` / `list_skills`；版本号生成：`next_backup_version`；写入：`promote`（.dev → 生产 + 备份）。
- **安装目标 (target dir)**：技能被安装到的目录——项目内 `{project}/{agent.project_dir}` 或全局 `{home}/{agent.global_dir}`，解析入口 `resolve_command_target_dir`。
- **Agent 注册表**（`core/agents.py`）：内置 agent 目录布局 + `config.toml [agents]` 覆盖；纯函数，无 I/O。
- **技能标记**：`SKILL.md`。
