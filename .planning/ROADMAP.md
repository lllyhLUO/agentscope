# Roadmap: AgentScope Skill Registry

## Overview

This roadmap adds a PostgreSQL-backed shared skill registry to AgentScope in a
way that preserves compatibility with the current directory-based skill runtime.
The work starts by establishing the registry schema and repository boundary,
then adds publish flow, runtime loading, and finally discovery UX plus tests and
documentation.

## Phases

- [x] **Phase 1: Registry Foundation** - Define the PostgreSQL schema,
  repository layer, and access rules
- [x] **Phase 2: Publish Workflow** - Publish local skill directories as
  immutable versioned artifacts
- [ ] **Phase 3: Runtime Loader** - Load `skill_name@version` through managed
  runtime cache and Toolkit integration
- [ ] **Phase 4: Discovery and Hardening** - Ship search/show/install flows,
  tests, and documentation

## Phase Details

### Phase 1: Registry Foundation
**Goal**: Establish the PostgreSQL-backed registry model and repository APIs
inside AgentScope
**Depends on**: Nothing
**Requirements**: [REG-01, REG-02, REG-03, REG-04, ACC-01, ACC-02]
**Success Criteria** (what must be TRUE):
1. Registry schema for skills, versions, files, and maintainers exists and can
   be initialized from AgentScope
2. Repository layer can create and read registry records for explicit skill
   names and versions
3. Access model distinguishes public read from maintainer write at the
   application boundary
**Plans**: 2 plans

Plans:
**Wave 1** *(unblocked)*
- [x] 01-01: Define registry module structure and persistent models

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 01-02: Implement repository APIs and connection/config plumbing

### Phase 2: Publish Workflow
**Goal**: Let maintainers publish local skill directories as immutable
versioned records in PostgreSQL
**Depends on**: Phase 1
**Requirements**: [PUB-01, PUB-02, PUB-03]
**Success Criteria** (what must be TRUE):
1. Maintainer can publish a local skill directory by explicit name and version
2. Publish validates `SKILL.md` and required metadata before writing
3. Republishing conflicting content for the same version is rejected
**Plans**: 2 plans

Plans:
**Wave 1** *(unblocked)*
- [x] 02-01: Implement skill directory scanner and validator

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 02-02: Implement publish/import command path

### Phase 3: Runtime Loader
**Goal**: Load registry-backed skills into Toolkit by explicit version while
keeping PostgreSQL as the source of truth
**Depends on**: Phase 2
**Requirements**: [RUN-01, RUN-02, RUN-03, ACC-03]
**Success Criteria** (what must be TRUE):
1. Toolkit can load a PostgreSQL-backed skill only when given
   `skill_name@version`
2. Runtime cache materializes a requested version into a managed execution
   directory and validates cache integrity
3. Existing local skill registration flow is reused behind a registry-aware API
**Plans**: 2 plans

Plans:
**Wave 1** *(unblocked)*
- [ ] 03-01: Implement managed runtime cache

**Wave 2** *(blocked on Wave 1 completion)*
- [ ] 03-02: Implement registry-aware Toolkit loading path

### Phase 4: Discovery and Hardening
**Goal**: Make the workflow usable end-to-end with discovery, inspection,
install, tests, and docs
**Depends on**: Phase 3
**Requirements**: [DISC-01, DISC-02, DISC-03, TST-01, DOC-01]
**Success Criteria** (what must be TRUE):
1. Users can search registry skills and inspect a specific version
2. Users can pre-install a specific version into managed cache
3. Test coverage exists for publish, read, install, and runtime load flows
4. Documentation explains how to manage and consume shared skills
**Plans**: 2 plans

Plans:
- [ ] 04-01: Implement search/show/install CLI commands
- [ ] 04-02: Add tests and end-user documentation

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Registry Foundation | 2/2 | Complete | 2026-04-28 |
| 2. Publish Workflow | 2/2 | Complete | 2026-04-29 |
| 3. Runtime Loader | 0/2 | Not started | - |
| 4. Discovery and Hardening | 0/2 | Not started | - |
