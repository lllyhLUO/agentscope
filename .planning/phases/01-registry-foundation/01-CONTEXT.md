# Phase 1: Registry Foundation - Context

**Gathered:** 2026-04-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Define the PostgreSQL-backed registry foundation inside AgentScope: persistent
schema, repository boundary, and access rules. This phase does not yet build the
publish CLI, runtime loader, or discovery/install UX.

</domain>

<decisions>
## Implementation Decisions

### Registry identity and storage
- **D-01:** v1 skill identity is a globally unique `skill_name` plus explicit
  `version`; this phase must model both fields directly in the schema.
- **D-02:** The canonical v1 tables are `skills`, `skill_versions`,
  `skill_files`, and `skill_maintainers`.
- **D-03:** Published versions are immutable artifacts; the schema and
  repository must make it possible to reject conflicting re-publish of the same
  `skill_name@version`.

### Access and module boundary
- **D-04:** Public read and maintainer write must be explicit repository-level
  concepts, even before publish flow exists.
- **D-05:** New code lives under `src/agentscope/skill/` and follows existing
  underscore-based internal module conventions.

### Connection and testability
- **D-06:** Registry database configuration uses
  `AGENTSCOPE_SKILL_REGISTRY_DATABASE_URL` for runtime wiring, while repository
  code must also accept injected `AsyncEngine` or `AsyncSession` values so tests
  do not depend on a live PostgreSQL process.

### the agent's Discretion
- Exact helper names inside `_repository.py`
- Whether repository read methods return internal typed dicts or lightweight
  row serializers, as long as ORM rows do not leak broadly outside the module
- Exact index names and helper function decomposition

</decisions>

<specifics>
## Specific Ideas

- The developer already installed local PostgreSQL 18 and wants this project to
  grow into a reusable workflow other users can follow.
- The current project direction is closer to a shared executable skill registry
  than to a generic human-skill taxonomy database.
- Explicit versioning is mandatory everywhere; no `latest` fallback in v1.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product and scope
- `docs/superpowers/specs/2026-04-28-skill-registry-design.md` — Approved v1
  architecture, data model, CLI workflow, and runtime boundary
- `.planning/PROJECT.md` — Project identity, core value, and locked decisions
- `.planning/REQUIREMENTS.md` — Phase requirements and traceability targets
- `.planning/ROADMAP.md` — Phase goal, success criteria, and phase ordering

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/agentscope/memory/_working_memory/_sqlalchemy_memory.py`: existing async
  SQLAlchemy engine/session management pattern, table initialization flow, and
  commit/rollback behavior
- `src/agentscope/memory/_working_memory/__init__.py`: established package
  export style for internal underscore modules
- `src/agentscope/session/__init__.py`: another small package surface following
  the same pattern

### Established Patterns
- Internal modules under `src/agentscope` use underscore-prefixed filenames and
  expose selected public symbols through `__init__.py`
- Tests commonly use `IsolatedAsyncioTestCase` and mock-driven coverage in the
  `tests/` tree
- SQLAlchemy code in this repo currently keeps persistence concerns encapsulated
  rather than threading ORM details through unrelated modules

### Integration Points
- Phase 1 should not wire into `Toolkit` yet; it creates the registry foundation
  that Phase 3 will consume
- Repository code should be designed so later publish and loader flows can reuse
  the same schema and access checks without redefining data shapes

</code_context>

<deferred>
## Deferred Ideas

- Publish/import CLI behavior belongs to Phase 2
- Managed runtime cache and registry-aware Toolkit loading belong to Phase 3
- Search/show/install UX, docs, and hardening belong to Phase 4

</deferred>

---

*Phase: 01-registry-foundation*
*Context gathered: 2026-04-28*
