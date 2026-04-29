---
name: registry-skill-workflow
description: Use when the user explicitly asks to publish, search, inspect, install, or load shared AgentScope skills through the PostgreSQL-backed registry workflow in this project.
---

# Registry Skill Workflow

## Overview

This skill guides Codex through the shared AgentScope skill registry workflow
used in this project.

The registry is PostgreSQL-backed.
The operational interface is the `agentscope-skill` CLI.
Runtime loading uses `Toolkit.register_registry_skill("skill_name@version")`.

## When to Use

Use this skill only when the user explicitly asks for the shared skill registry
workflow in this project, including requests to:

- publish a local skill directory to the registry
- search shared skills
- inspect a published skill version
- install or prewarm a published skill version
- load a published skill into Toolkit
- work with `agentscope-skill`
- work with `register_registry_skill`

Do not use this skill for ordinary local `register_agent_skill(path)` tasks.

## Required Environment

Check these before doing any registry operation:

- `AGENTSCOPE_SKILL_REGISTRY_DATABASE_URL`
- `AGENTSCOPE_SKILL_REGISTRY_TEST_DATABASE_URL` (only when running live smoke
  or integration checks)

If `AGENTSCOPE_SKILL_REGISTRY_DATABASE_URL` is missing, stop and tell the user
exactly which variable is missing.

## Core Rules

- Treat PostgreSQL as the only source of truth.
- Treat the managed cache as runtime-only, never as the source of truth.
- Require explicit `skill_name@version` for artifact-specific operations.
- Do not bypass `agentscope-skill` with direct database edits.
- Do not invent implicit `latest` behavior.
- Prefer project-local code paths and docs over memory.
- For Python verification in this repo, prefer `PYTHONPATH=src ...` commands.

## Supported Operations

### 1. Publish

Use when the user wants to push a local skill directory into the shared
registry.

Command pattern:

```bash
agentscope-skill publish <skill_dir> --name <skill_name> --version <version> --principal <principal>
```

Example:

```bash
agentscope-skill publish ./my-skill --name sql_analyzer --version 1.0.0 --principal postgres
```

Before publish:

- confirm the directory exists
- confirm top-level `SKILL.md` exists
- confirm the requested `--name` matches frontmatter `name`
- use explicit `--version`

### 2. Search

Use when the user wants to find shared skills by keyword.

Command pattern:

```bash
agentscope-skill search <query> --limit <n>
```

Example:

```bash
agentscope-skill search sql --limit 10
```

### 3. Show

Use when the user wants metadata and file listing for a published skill
version.

Command pattern:

```bash
agentscope-skill show <skill_name@version>
```

Example:

```bash
agentscope-skill show sql_analyzer@1.0.0
```

Always require explicit version.

### 4. Install

Use when the user wants to prewarm a published skill into the managed runtime
cache.

Command pattern:

```bash
agentscope-skill install <skill_name@version>
```

Example:

```bash
agentscope-skill install sql_analyzer@1.0.0
```

This is a cache prewarm step only.
It does not register the skill into Toolkit by itself.

### 5. Load

Use when the user wants to load a published registry skill into AgentScope
runtime.

Python pattern:

```python
from agentscope.tool import Toolkit

toolkit = Toolkit()
toolkit.register_registry_skill("sql_analyzer@1.0.0")
```

Always require explicit version.

## Suggested Workflow

### Consumer flow

1. Check `AGENTSCOPE_SKILL_REGISTRY_DATABASE_URL`
2. Search:
   `agentscope-skill search <query> --limit <n>`
3. Inspect:
   `agentscope-skill show <skill_name@version>`
4. Install:
   `agentscope-skill install <skill_name@version>`
5. Load:
   `Toolkit.register_registry_skill("<skill_name@version>")`

### Maintainer flow

1. Check `AGENTSCOPE_SKILL_REGISTRY_DATABASE_URL`
2. Validate local skill directory
3. Publish:
   `agentscope-skill publish <dir> --name <skill_name> --version <version> --principal <principal>`
4. Optionally verify with:
   - `agentscope-skill search ...`
   - `agentscope-skill show <skill_name@version>`

## Failure Handling

### Missing database URL

Report:
- `AGENTSCOPE_SKILL_REGISTRY_DATABASE_URL is not set`

### Missing explicit version

Reject:
- `show/install/load` without `skill_name@version`

### Publish conflict

If the same `skill_name@version` exists with different content:
- stop
- report conflict clearly
- do not suggest overwriting in place

### Driver missing

If PostgreSQL driver is missing:
- report that `asyncpg` is required
- prefer fixing the environment before retrying

### Runtime load failure

If `register_registry_skill(...)` fails:
- verify the ref is explicit
- verify the skill exists with `show`
- verify cache prewarm with `install`
- then retry loading

## Verification

When asked to verify registry workflow in this repo, prefer:

```bash
PYTHONPATH=src pytest tests/skill_registry_models_test.py \
tests/skill_registry_repository_test.py \
tests/skill_registry_publisher_test.py \
tests/skill_registry_publish_command_test.py \
tests/skill_registry_cache_test.py \
tests/skill_registry_loader_test.py \
tests/skill_registry_cli_test.py \
tests/skill_registry_e2e_test.py
```

For live PostgreSQL verification, use configured registry URLs and verify:

- publish succeeds
- search succeeds
- show succeeds
- install succeeds
- `register_registry_skill(...)` succeeds

## Examples

### Example: search then load

```bash
agentscope-skill search sql --limit 10
agentscope-skill show sql_analyzer@1.0.0
agentscope-skill install sql_analyzer@1.0.0
```

```python
from agentscope.tool import Toolkit

toolkit = Toolkit()
toolkit.register_registry_skill("sql_analyzer@1.0.0")
```

### Example: publish a new version

```bash
agentscope-skill publish ./my-skill --name sql_analyzer --version 1.1.0 --principal postgres
```
