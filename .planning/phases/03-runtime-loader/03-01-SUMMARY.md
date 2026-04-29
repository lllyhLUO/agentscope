---
phase: 03-runtime-loader
plan: 01
subsystem: infra
tags: [cache, runtime, hydrate, postgres]
requires:
  - phase: 02
    provides: "Stable content-hashed manifests and published skill file rows"
provides:
  - Managed runtime cache keyed by skill name, version, and content hash
  - Explicit `skill_name@version` parsing for runtime refs
  - Cache hydration, reuse, and stale-directory invalidation
affects: [loader, toolkit, discovery, tests]
tech-stack:
  added: []
  patterns:
    - Registry-backed runtime artifacts hydrate into real local directories before execution
    - Cache directories are invalidated by content hash, not by mutable latest pointers
key-files:
  created:
    - src/agentscope/skill/_cache.py
    - tests/skill_registry_cache_test.py
  modified:
    - src/agentscope/skill/__init__.py
key-decisions:
  - "Default runtime cache lives outside the repo working tree under a managed cache root"
  - "Hydrated cache reuse is allowed only when the exact content hash matches the registry version metadata"
patterns-established:
  - "Runtime cache is an internal execution detail and never treated as the source of truth"
  - "Per-version stale cache cleanup happens at the skill/version directory level"
requirements-completed: [RUN-02, ACC-03]
duration: 1 min
completed: 2026-04-29
---

# Phase 3: Runtime Loader Summary

**Registry skill versions now hydrate into managed local directories keyed by explicit version and content hash**

## Performance

- **Duration:** 1 min
- **Started:** 2026-04-29T10:53:01+08:00
- **Completed:** 2026-04-29T10:53:15+08:00
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- Added `SkillRuntimeCache` with explicit `skill_name@version` parsing
- Implemented managed cache hydration from repository file rows
- Added stale cache cleanup when registry content hash changes
- Added cache tests for reuse, invalid refs, invalidation, and real directory materialization

## Task Commits

Each task was committed atomically:

1. **Task 1: Add failing runtime cache tests** - `efec0d8` (test)
2. **Task 2 + Task 3: Implement runtime skill cache** - `df27780` (feat)

**Plan metadata:** `8f385f6` (docs: create phase plan)

## Files Created/Modified
- `src/agentscope/skill/_cache.py` - Managed runtime cache, explicit ref parsing, and hydration logic
- `src/agentscope/skill/__init__.py` - Exposes `SkillRuntimeCache`
- `tests/skill_registry_cache_test.py` - Covers parsing, hydration, reuse, invalidation, and missing-version behavior

## Decisions Made
- Used `skill_name/version/content_hash` path nesting so stale cache directories can be deleted without ambiguity
- Reused the repository's exact version lookup as the single source for content-hash freshness

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Runtime cache now provides real local skill directories suitable for existing Toolkit registration flow
- Loader integration can focus purely on bridging cache hydration into Toolkit without re-solving manifest or file-write behavior

---
*Phase: 03-runtime-loader*
*Completed: 2026-04-29*
