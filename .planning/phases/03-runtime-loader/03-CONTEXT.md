# Phase 3: Runtime Loader - Context

**Gathered:** 2026-04-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement runtime loading for registry-backed skills by explicit
`skill_name@version`, materialize them into a managed cache directory, and
expose a registry-aware Toolkit API that reuses the existing
`register_agent_skill()` execution model.

</domain>

<decisions>
## Implementation Decisions

### Runtime contract
- **D-01:** Runtime loading must require explicit `skill_name@version`; no
  implicit latest lookup is allowed in v1.
- **D-02:** The runtime cache is internal infrastructure, not a second source of
  truth; PostgreSQL stays authoritative.
- **D-03:** Cache entries should be keyed by at least skill name, explicit
  version, and content hash so stale directories can be invalidated safely.

### Cache behavior
- **D-04:** Cache should live in a managed local directory outside the repo
  working tree by default, not in project source paths.
- **D-05:** Cache hydration must recreate a real directory tree with a top-level
  `SKILL.md` and any additional files so the existing local skill mechanism can
  consume it unchanged.

### Toolkit integration
- **D-06:** Phase 3 must add a registry-specific API rather than overloading
  `register_agent_skill(path)`.
- **D-07:** The new API should reuse the existing
  `Toolkit.register_agent_skill()` implementation after cache hydration instead
  of reimplementing YAML parsing and skill prompt assembly.

### Error handling and configuration
- **D-08:** Invalid skill references, cache mismatches, and missing versions
  should fail clearly before mutating Toolkit state.
- **D-09:** Runtime loading should accept an injected repository/loader for
  tests, while still supporting env-based configuration for normal use.

### the agent's Discretion
- Exact class names for cache and loader helpers
- Whether cache-dir override comes from an env var, constructor arg, or both,
  as long as the default path stays outside the repo
- Whether loader convenience APIs live in `agentscope.skill` or are only exposed
  through `Toolkit`, as long as Phase 3 keeps the boundary explicit

</decisions>

<specifics>
## Specific Ideas

- Existing `FileEmbeddingCache` already shows a local file-backed cache pattern
  that can inform directory creation and cleanup policy.
- Existing `Toolkit.register_agent_skill()` already performs all local skill
  validation and registration work once a real directory exists.
- Publish flow now produces stable manifests and explicit `content_hash`, which
  Phase 3 can reuse for cache-key validation.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product and scope
- `docs/superpowers/specs/2026-04-28-skill-registry-design.md` — Approved
  runtime cache and loader architecture
- `.planning/PROJECT.md` — Project identity and constraints
- `.planning/REQUIREMENTS.md` — Phase 3 runtime requirements
- `.planning/ROADMAP.md` — Phase 3 goal and success criteria

### Prior phase outputs
- `.planning/phases/02-publish-workflow/02-01-SUMMARY.md` — Stable manifest and
  hashing behavior from local skill directories
- `.planning/phases/02-publish-workflow/02-02-SUMMARY.md` — Publish flow,
  explicit version persistence, and repository write behavior

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/agentscope/tool/_toolkit.py`: existing `register_agent_skill()` local
  directory registration path
- `src/agentscope/embedding/_file_cache.py`: file-backed cache lifecycle and
  directory management pattern
- `src/agentscope/skill/_repository.py`: exact version lookup and file listing
  behavior for published skills
- `src/agentscope/skill/_publisher.py`: manifest and content hash conventions

### Established Patterns
- Public package exports stay intentionally small and are assembled through
  `src/agentscope/skill/__init__.py`
- Tests for toolkit behavior live under the main `tests/` tree and often use
  temp directories plus mock-driven assertions
- Current verification uses `PYTHONPATH=src` because the shell still sees an
  older installed `agentscope` package by default

### Integration Points
- Cache hydration should write the file tree that `register_agent_skill()` expects
- Toolkit integration should be additive and avoid breaking local directory use
- Loader tests should verify that Toolkit-visible skill metadata matches the
  hydrated registry artifact

</code_context>

<deferred>
## Deferred Ideas

- Search/show/install consumer UX belongs to Phase 4
- Fully virtual no-cache runtime remains deferred to v2
- Richer cache eviction policy is optional after Phase 3 unless it becomes
  necessary for correctness

</deferred>

---

*Phase: 03-runtime-loader*
*Context gathered: 2026-04-29*
