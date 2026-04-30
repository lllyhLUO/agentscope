# PostgreSQL Skill Registry 使用说明

本文记录 AgentScope 共享 skill registry 的本地使用流程。当前实现以
PostgreSQL 为唯一真源，本地 managed cache 只用于运行时加载。

## 环境准备

先确保当前 Python 环境使用的是包含 registry 功能的 AgentScope 代码：

```bash
python3 -m pip install -e /Users/mac29/workspace/skillDB/agentscope
hash -r
agentscope-skill --help
```

配置开发库连接。不要把真实密码提交到仓库；本机使用时把 `<password>` 换成
你的 PostgreSQL 密码：

```bash
export AGENTSCOPE_SKILL_REGISTRY_DATABASE_URL='postgresql+asyncpg://postgres:<password>@localhost:5432/skilldb_dev'
```

第一次使用一个新数据库时，需要初始化 registry schema：

```bash
PYTHONPATH=/Users/mac29/workspace/skillDB/agentscope/src AGENTSCOPE_SKILL_REGISTRY_DATABASE_URL='postgresql+asyncpg://postgres:<password>@localhost:5432/skilldb_dev' python3 -c $'import asyncio\nfrom agentscope.skill import SkillRegistryRepository\n\nasync def main():\n    repo = SkillRegistryRepository.from_env()\n    try:\n        await repo.init_schema()\n        print("schema initialized")\n    finally:\n        await repo.close()\n\nasyncio.run(main())'
```

看到 `schema initialized` 后，`publish/search/show/install` 才能正常访问
`skills`、`skill_versions`、`skill_files`、`skill_maintainers` 等表。

## 准备一个新的 skill

发布输入必须是一个 skill 目录，不是单个 `SKILL.md` 文件。推荐目录尽量干净，
只放运行这个 skill 真正需要的文件：

```text
my_skill/
  SKILL.md
  tool.py
  assets/
```

`SKILL.md` 必须放在目录顶层，并包含 `name` 和 `description`：

```markdown
---
name: my_skill
description: 这里写这个 skill 的用途
---

# My Skill

这里写给 agent 看的说明、触发方式和操作流程。
```

发布时传入的 `--name` 必须和 `SKILL.md` frontmatter 里的 `name` 完全一致。

发布器会默认忽略常见本地工件，例如 `.git`、`.venv`、`.pytest_cache`、
`node_modules`、隐藏文件和嵌套 git 仓库。但不要依赖过滤器来整理包内容；
最稳的方式仍然是维护一个干净的 skill 目录。

## 发布到 PostgreSQL

发布命令：

```bash
agentscope-skill publish /path/to/my_skill --name my_skill --version 1.0.0 --principal postgres
```

规则：

- `--version` 必须显式指定。
- 同一个 `skill_name@version` 已发布后不可覆盖。
- 相同内容重复发布会返回幂等成功。
- 同名同版本但内容不同会被拒绝；应发布新版本，例如 `1.0.1`。

示例：

```bash
agentscope-skill publish /Users/mac29/workspace/skills/my_skill --name my_skill --version 1.0.0 --principal postgres
```

## 搜索、查看和安装

搜索：

```bash
agentscope-skill search my_skill --limit 10
```

查看指定版本：

```bash
agentscope-skill show my_skill@1.0.0
```

预热安装到 managed cache：

```bash
agentscope-skill install my_skill@1.0.0
```

`install` 只是把指定版本物化到 AgentScope 管理的缓存目录，不会把 skill
复制到你的项目目录，也不会自动注册到 `Toolkit`。

## 在代码里使用

运行时加载 registry skill：

```python
from agentscope.tool import Toolkit

toolkit = Toolkit()
toolkit.register_registry_skill("my_skill@1.0.0")
```

这里必须使用显式版本，例如 `my_skill@1.0.0`。当前设计不使用隐式 `latest`。

## 在 Codex 里使用

如果希望 Codex 帮你操作这套流程，可以显式提到项目内 skill：

```text
用 registry-skill-workflow 搜索 my_skill
用 registry-skill-workflow 查看 my_skill@1.0.0
用 registry-skill-workflow 安装 my_skill@1.0.0
用 registry-skill-workflow 发布 /path/to/my_skill 为 my_skill@1.0.1
```

Codex 侧最终仍然调用同一套命令：`agentscope-skill publish/search/show/install`。

## 当前已验证示例

本地 `skilldb_dev` 中已经验证过一个干净版本：

```bash
agentscope-skill show ops@1.0.1
agentscope-skill install ops@1.0.1
```

不要继续使用 `ops@1.0.0`。这个旧版本是在发布过滤修复前写入的，包含了过多
本地仓库文件。

## 常见问题

`agentscope-skill: command not found`

当前 Python 环境没有安装本仓库的 editable 包。执行：

```bash
python3 -m pip install -e /Users/mac29/workspace/skillDB/agentscope
hash -r
```

`relation "skills" does not exist`

目标数据库还没有初始化 schema。先执行本文“环境准备”里的 schema 初始化命令。

`argument --principal: expected one argument`

命令被换行拆断了。`--principal postgres` 必须在同一条命令里完整出现：

```bash
agentscope-skill publish /path/to/my_skill --name my_skill --version 1.0.0 --principal postgres
```

`SKILL.md file at the top level`

你传入的不是 skill 目录，或者目录顶层没有 `SKILL.md`。发布命令第一个参数必须是
目录路径。

`requested skill name ... frontmatter name ...`

`--name` 和 `SKILL.md` 里的 `name` 不一致。修改其中一个，让它们完全相同。

`Cannot publish the same skill_name@version with different content`

同名同版本已经存在，但内容不同。不要覆盖旧版本，发布一个新版本号。

