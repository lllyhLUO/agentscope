# Phase 4: Discovery and Hardening - Context

**Gathered:** 2026-04-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Make the registry workflow usable end-to-end for consumers: searchable skill
discovery, explicit-version inspection, install/prewarm into managed cache,
plus the tests and documentation needed so other users can adopt the workflow.

</domain>

<decisions>
## Implementation Decisions

### Consumer command surface
- **D-01:** Phase 4 extends the existing skill CLI instead of introducing a
  second binary or command family.
- **D-02:** `search` and `show` are read-only registry operations and should not
  require a writable database principal.
- **D-03:** `install` is a cache prewarm operation for an explicit
  `skill_name@version`; it does not auto-register the skill into Toolkit.
- **D-04:** Output should stay understandable from plain terminal usage first,
  even if richer formatting is added later.

### Explicit version and source of truth
- **D-05:** Any consumer operation that addresses a concrete skill artifact
  (`show`, `install`) must require explicit `skill_name@version`.
- **D-06:** `install` should surface the hydrated cache path but continue to
  treat PostgreSQL as the source of truth, not the cache directory.

### Documentation scope
- **D-07:** Documentation should explain both maintainer publish flow and
  consumer search/show/install/load flow, not just one side.
- **D-08:** Because this repo already maintains English and Chinese tutorial
  sources, Phase 4 docs should update both language tracks rather than leaving
  one stale.

### Testing scope
- **D-09:** Phase 4 should add CLI-focused tests and full skill-registry
  regression coverage across Phase 1-4 behavior, while keeping live PostgreSQL
  checks env-gated.

### the agent's Discretion
- Exact CLI output formatting for list/show/install
- Whether to add a console script entrypoint in `pyproject.toml` or document
  `python -m agentscope.skill._cli`, as long as the chosen path is consistent in
  code and docs
- How much README surface area to dedicate to registry skill workflow vs the
  tutorial docs

</decisions>

<specifics>
## Specific Ideas

- Existing `_cli.py` already has a minimal `publish` path, so Phase 4 can extend
  that parser instead of replacing it.
- Existing `task_agent_skill.py` tutorial pages in both languages are the most
  natural place to document registry-backed skills alongside local skills.
- The user explicitly wants other people to be able to connect to the shared
  database and reuse skills without manually downloading skill files.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product and scope
- `docs/superpowers/specs/2026-04-28-skill-registry-design.md` — Approved
  end-to-end workflow, including search/show/install/load scope
- `.planning/PROJECT.md` — Project identity and constraints
- `.planning/REQUIREMENTS.md` — Phase 4 discovery, test, and docs requirements
- `.planning/ROADMAP.md` — Phase 4 goal and success criteria

### Prior phase outputs
- `.planning/phases/03-runtime-loader/03-01-SUMMARY.md` — Managed runtime cache
- `.planning/phases/03-runtime-loader/03-02-SUMMARY.md` — Loader and Toolkit
  integration

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/agentscope/skill/_cli.py`: current minimal `publish` command path
- `src/agentscope/skill/_repository.py`: existing search, exact version lookup,
  and file-list methods
- `src/agentscope/skill/_cache.py`: install/prewarm foundation via cache
  hydration
- `src/agentscope/skill/_loader.py`: load path for explicit version refs

### Established Patterns
- CLI entrypoints currently live in `_cli.py` and are invoked through `main()`
- Tests use repository/cache doubles and env-gated live checks rather than
  hard depending on a configured PostgreSQL instance
- Tutorial docs are maintained in paired English/Chinese sources under
  `docs/tutorial/en/src/` and `docs/tutorial/zh_CN/src/`

### Integration Points
- `search` can reuse `search_skills()` directly
- `show` can combine `get_skill_version()` and `list_skill_files()`
- `install` can reuse `SkillRuntimeCache.hydrate_skill_ref()`
- Docs should point users from discovery/install into `Toolkit.register_registry_skill()`

</code_context>

<deferred>
## Deferred Ideas

- Rich HTTP registry service stays out of scope
- Fully virtual no-cache runtime stays deferred to v2
- Authenticated multi-tenant sharing or richer RBAC stays out of v1

</deferred>

---

*Phase: 04-discovery-and-hardening*
*Context gathered: 2026-04-29*
