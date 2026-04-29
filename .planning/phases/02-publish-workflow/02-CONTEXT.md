# Phase 2: Publish Workflow - Context

**Gathered:** 2026-04-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement the publish workflow that takes a local skill directory and stores it
in PostgreSQL as an immutable, versioned artifact. This phase does not yet load
skills into Toolkit from PostgreSQL and does not yet implement search/show/install
consumer UX.

</domain>

<decisions>
## Implementation Decisions

### Publish input and validation
- **D-01:** The publish source of truth is a local skill directory rooted at a
  real filesystem path.
- **D-02:** A valid publish target must contain a top-level `SKILL.md` with
  parseable frontmatter and required `name` and `description` metadata.
- **D-03:** The explicit `skill_name` provided by the caller must match the
  `name` in `SKILL.md` frontmatter to avoid ambiguous registry identity.

### File capture and hashing
- **D-04:** Publish stores skill content as per-file records, not as a single
  blob, so the publisher must build a stable ordered manifest and compute both
  per-file hashes and a version-level content hash.
- **D-05:** Publish must ignore transient local artifacts such as
  `__pycache__/`, `.pyc`, and `.DS_Store` so machine-specific noise does not
  affect registry versions.

### Version conflict handling
- **D-06:** Re-publishing the same `skill_name@version` with different content
  must fail.
- **D-07:** Re-publishing the same `skill_name@version` with identical content
  may return the existing version as an idempotent success instead of creating a
  duplicate row.

### Access and command path
- **D-08:** The publish path must enforce maintainer write authorization before
  inserting skill/version/file records.
- **D-09:** This phase should expose a minimal publish command path now, but
  broader search/show/install CLI work remains Phase 4 scope.

### the agent's Discretion
- Exact internal dataclass names for manifests and publish results
- Whether maintainer identity is sourced from an explicit CLI argument or an
  environment-backed default, as long as write authorization remains explicit
- Exact publish success output format

</decisions>

<specifics>
## Specific Ideas

- AgentScope already has a real skill example at
  `examples/functionality/agent_skill/skill/analyzing-agentscope-library/`
  which can act as a realistic scanner/validator fixture.
- The current environment imports an installed `agentscope` by default during
  pytest, so plan verification should continue to use `PYTHONPATH=src` for
  worktree-local tests until packaging/installation flow is revisited.
- Local PostgreSQL 18 is installed, but database URLs are not yet wired into the
  project environment.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product and scope
- `docs/superpowers/specs/2026-04-28-skill-registry-design.md` — Approved
  publisher architecture, data model, and CLI direction
- `.planning/PROJECT.md` — Project identity and locked product constraints
- `.planning/REQUIREMENTS.md` — Phase 2 publish requirements
- `.planning/ROADMAP.md` — Phase 2 goal and success criteria

### Phase 1 outputs
- `.planning/phases/01-registry-foundation/01-01-SUMMARY.md` — Established
  schema and model patterns
- `.planning/phases/01-registry-foundation/01-02-SUMMARY.md` — Established
  repository APIs, env wiring, and optional dependency path

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/agentscope/skill/_models.py`: canonical registry tables and constraints
- `src/agentscope/skill/_repository.py`: schema initialization, read APIs, and
  maintainer authorization helpers
- `python-frontmatter` is already a core dependency, so publisher metadata
  parsing does not require a new package

### Established Patterns
- Internal modules in `src/agentscope` stay underscore-prefixed and are exposed
  selectively through `__init__.py`
- Phase 1 established dictionary serialization at the repository boundary rather
  than returning raw ORM rows everywhere
- Tests are currently structured to avoid hard dependency on optional local
  drivers unless the environment explicitly opts in

### Integration Points
- Publisher logic should compose with `SkillRegistryRepository` instead of
  bypassing the repository boundary
- Minimal command-path work in this phase should leave room for Phase 4 to grow
  into the broader `agentscope skill ...` workflow

</code_context>

<deferred>
## Deferred Ideas

- Runtime cache and registry-aware Toolkit loading belong to Phase 3
- Search/show/install UX belongs to Phase 4
- HTTP registry service and namespace-based identity remain out of scope for v1

</deferred>

---

*Phase: 02-publish-workflow*
*Context gathered: 2026-04-29*
