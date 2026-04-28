# AgentScope PostgreSQL Skill Registry Design

**Date:** 2026-04-28
**Status:** Drafted from approved brainstorming decisions
**Target codebase:** `agentscope`

## Problem

AgentScope currently treats an agent skill as a local directory with a top-level
`SKILL.md` file and optional scripts/resources. That works for local use, but it
does not provide a shared workflow for publishing, discovering, versioning, and
loading skills across users without manually exchanging files.

## Goal

Build a usable skill management workflow inside AgentScope where:

- PostgreSQL is the single source of truth
- skills are published from local directories
- every load uses an explicit version
- all users can search, inspect, install, and load skills from the shared
  registry
- maintainers can publish and update by creating new immutable versions

## Non-Goals for v1

- HTTP registry service
- namespace-based identity
- "latest" version shortcuts
- database-side live editing of skill files
- full RBAC
- fully virtual runtime with no managed cache directory

## Approved Product Decisions

- Shared public registry
- Everyone can read
- Only maintainers can write
- PostgreSQL is the only source of truth
- Skill identity is globally unique: `skill_name@version`
- Version must always be explicit
- Publish source is a local skill directory
- Discovery and use both ship in v1: search, show, install, and load
- Agent and CLI connect directly to PostgreSQL
- Runtime uses a transparent managed cache directory for execution compatibility

## Architecture

### 1. Publisher

Responsible for importing a local skill directory into PostgreSQL as an
immutable versioned artifact.

Responsibilities:

- validate the directory shape
- require a top-level `SKILL.md`
- parse frontmatter metadata
- scan all files under the skill root
- calculate per-file hashes and a version-level content hash
- reject conflicting republish of the same `skill_name@version`

### 2. Registry Repository

Single read/write boundary around PostgreSQL.

Responsibilities:

- create and query skill records
- list versions
- fetch metadata
- fetch file sets for a specific version
- enforce maintainer write checks at application level

### 3. Runtime Cache

Managed local execution cache, not a user-managed source tree.

Responsibilities:

- materialize a registry skill version into a cache directory
- validate cached content by version hash
- reuse existing cached versions when unchanged
- keep the database as the only source of truth

### 4. Runtime Loader

Bridge between the registry and the existing `Toolkit.register_agent_skill()`
flow.

Responsibilities:

- resolve `skill_name@version`
- fetch the file set from PostgreSQL
- hydrate the managed cache directory
- pass the cached directory to existing local skill registration logic

### 5. CLI

Expose the workflow to maintainers and consumers.

Initial commands:

- `agentscope skill publish`
- `agentscope skill search`
- `agentscope skill show`
- `agentscope skill install`

## Proposed Code Layout

```text
src/agentscope/skill/
├── __init__.py
├── _cache.py
├── _cli.py
├── _loader.py
├── _models.py
├── _publisher.py
└── _repository.py
```

Toolkit integration should stay thin. The registry logic should not be spread
throughout `src/agentscope/tool/_toolkit.py`.

## Data Model

### `skills`

Stable identity for a skill.

Suggested fields:

- `id`
- `name`
- `latest_version`
- `status`
- `created_at`
- `created_by`

Constraints:

- `name` unique across the registry

### `skill_versions`

Immutable published versions of a skill.

Suggested fields:

- `id`
- `skill_id`
- `version`
- `description`
- `metadata_json`
- `content_hash`
- `published_at`
- `published_by`

Constraints:

- `(skill_id, version)` unique
- published rows are immutable

### `skill_files`

One row per file in a published version.

Suggested fields:

- `id`
- `skill_version_id`
- `path`
- `file_type`
- `content_text`
- `content_bytes`
- `sha256`
- `size`

Constraints:

- `(skill_version_id, path)` unique

### `skill_maintainers`

Application-level write authority.

Suggested fields:

- `id`
- `skill_id`
- `principal`
- `role`

## CLI and User Workflow

### Maintainer flow

1. Create or update a local skill directory
2. Publish an explicit version

Example:

```bash
agentscope skill publish ./skills/sql_analyzer \
  --name sql_analyzer \
  --version 1.0.0
```

### Consumer flow

Search:

```bash
agentscope skill search sql
```

Inspect:

```bash
agentscope skill show sql_analyzer@1.0.0
```

Install to managed cache:

```bash
agentscope skill install sql_analyzer@1.0.0
```

Load in Python:

```python
from agentscope.skill import PostgresSkillRegistry
from agentscope.tool import Toolkit

registry = PostgresSkillRegistry.from_env()

toolkit = Toolkit()
toolkit.register_registry_skill(
    "sql_analyzer@1.0.0",
    registry=registry,
)
```

## Runtime Load Sequence

1. Parse `skill_name@version`
2. Query PostgreSQL for that exact version
3. Check managed cache for a matching `content_hash`
4. If missing or stale, materialize the version into cache
5. Call existing local skill registration with the cached path
6. Expose the skill to the agent exactly like a normal local skill

This preserves the user-facing "load from PG" model while avoiding a risky
rewrite of the current skill execution assumptions.

## Validation Rules

- top-level `SKILL.md` is required
- version is mandatory everywhere
- republishing the same version with different content is rejected
- duplicate skill names are rejected
- publish must fail if required metadata is missing

## Error Handling

- invalid skill directory -> explicit validation error
- unknown `skill_name@version` -> not found error
- cache hash mismatch -> delete stale cache and rebuild
- PostgreSQL connection failure -> repository error with connection guidance
- unauthorized publish/update -> permission error

## Testing Strategy

### Unit tests

- frontmatter parsing and validation
- directory scanning and hash generation
- version conflict detection
- repository query behavior
- cache hydration and cache-hit logic
- toolkit integration for registry skill loading

### Integration tests

- publish a fixture skill to PostgreSQL
- search and show the published skill
- install to managed cache
- load through Toolkit and confirm skill prompt registration

### Regression tests

- explicit version required
- immutable published versions
- text and binary file storage both round-trip correctly

## Delivery Shape for v1

Phaseable implementation:

1. Registry schema and repository
2. Publish workflow
3. Runtime load path and managed cache
4. Search/show/install CLI and documentation

## Why This Is the Right v1

This design keeps the product promise intact:

- shared registry
- versioned skill management
- no manual file exchange
- direct PostgreSQL consumption

At the same time, it avoids a deep runtime rewrite by reusing the current
directory-based execution model behind a controlled cache boundary.
