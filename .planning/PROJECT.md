# AgentScope Skill Registry

## What This Is

AgentScope Skill Registry is a PostgreSQL-backed workflow for publishing,
discovering, versioning, and loading agent skills inside AgentScope. Maintainers
publish local skill directories as immutable versions, and consumers search,
inspect, install, and load a specific skill version without manually exchanging
skill files.

## Core Value

Any user can load a shared, versioned AgentScope skill from PostgreSQL by
explicit version, without manually copying skill directories between machines.

## Requirements

### Validated

- ✓ AgentScope can register local directory-based skills through
  `Toolkit.register_agent_skill()` - existing
- ✓ AgentScope already contains async SQLAlchemy-based database integration
  patterns - existing

### Active

- [ ] Build a PostgreSQL-backed shared skill registry inside AgentScope
- [ ] Publish local skill directories as immutable versioned artifacts
- [ ] Support search, inspect, install, and load workflows for shared skills
- [ ] Require explicit `skill_name@version` references for runtime loading
- [ ] Keep PostgreSQL as the only source of truth while using managed runtime
  cache directories for execution compatibility

### Out of Scope

- HTTP registry service in v1 - direct PostgreSQL access is the chosen first
  integration path
- Namespace-based identity - v1 uses globally unique skill names
- "latest" alias loading - v1 requires explicit versions everywhere
- In-database skill editing - v1 publishes from local directories only
- Full RBAC - v1 uses public read plus maintainer write

## Context

AgentScope already has a local skill model based on a real directory with a
top-level `SKILL.md` file and optional scripts/resources. The existing toolkit
flow is well-suited to local execution but not to a shared registry. The codebase
also already contains async SQLAlchemy-based storage patterns that can inform the
new registry implementation.

The project target is not a generic skill taxonomy system. It is an executable
workflow for real AgentScope skills that other users can publish to and consume
from a shared PostgreSQL database.

## Constraints

- **Compatibility**: Reuse the existing local skill registration flow where
  possible - minimize disruption to `Toolkit`
- **Storage**: PostgreSQL is the single source of truth - local files are not a
  parallel source
- **Versioning**: Runtime loads must use explicit versions - no implicit latest
- **Access**: Everyone can read; only maintainers can publish or update
- **Runtime**: Skills may contain scripts and resources, so runtime execution
  must preserve real file layout semantics

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use PostgreSQL as the only source of truth | Shared registry without file exchange is the primary goal | - Pending |
| Use globally unique skill names | Keeps v1 identity model simple | - Pending |
| Require explicit version on every load | Prevents ambiguity and silent drift | - Pending |
| Publish from local directories | Matches current AgentScope skill authoring model | - Pending |
| Use managed runtime cache internally | Preserves compatibility with directory-based execution | - Pending |
| Start with direct PostgreSQL access instead of HTTP service | Smallest usable end-to-end workflow | - Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition**:
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone**:
1. Full review of all sections
2. Core Value check - still the right priority?
3. Audit Out of Scope - reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-28 after initialization*
