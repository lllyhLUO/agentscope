# Requirements: AgentScope Skill Registry

**Defined:** 2026-04-28
**Core Value:** Any user can load a shared, versioned AgentScope skill from
PostgreSQL by explicit version, without manually copying skill directories
between machines.

## v1 Requirements

### Registry

- [ ] **REG-01**: System can connect to PostgreSQL and create the registry
  schema needed for skills, versions, files, and maintainers
- [ ] **REG-02**: System stores each skill as a globally unique name
- [ ] **REG-03**: System stores each published version as an immutable artifact
- [ ] **REG-04**: System stores skill contents as individual files per version,
  including `SKILL.md`, scripts, and resources

### Publishing

- [ ] **PUB-01**: Maintainer can publish a local skill directory to PostgreSQL
  using an explicit skill name and version
- [ ] **PUB-02**: Publish fails if the skill directory does not contain a valid
  top-level `SKILL.md`
- [ ] **PUB-03**: Publish fails if the same `skill_name@version` already exists
  with different content

### Runtime Loading

- [ ] **RUN-01**: User can load a skill only by explicit `skill_name@version`
- [ ] **RUN-02**: System materializes a published skill version into a managed
  runtime cache directory when needed
- [ ] **RUN-03**: Toolkit can register a PostgreSQL-backed skill through a new
  registry-aware API without changing the existing local directory API

### Discovery

- [ ] **DISC-01**: User can search skills in PostgreSQL by name or descriptive
  metadata
- [ ] **DISC-02**: User can inspect a specific `skill_name@version` and view
  its metadata and file list
- [ ] **DISC-03**: User can pre-install a specific `skill_name@version` into
  the managed runtime cache

### Access and Safety

- [ ] **ACC-01**: All users can read registry contents
- [ ] **ACC-02**: Only maintainers can publish or update skill records
- [ ] **ACC-03**: Runtime loading never treats the managed cache as the source
  of truth

### Quality

- [ ] **TST-01**: New registry and loader behavior have unit and integration
  tests
- [ ] **DOC-01**: Documentation explains how to publish, search, inspect,
  install, and load skills from PostgreSQL

## v2 Requirements

### Registry Service

- **SRV-01**: Users can access the registry through an HTTP API instead of
  direct PostgreSQL access
- **SRV-02**: Registry exposes audit logs for publish and update actions

### Identity and Access

- **IAM-01**: Skills support namespace-based identity
- **IAM-02**: Registry supports richer RBAC than public-read plus maintainer-write

### Runtime

- **RTM-01**: Runtime can execute registry skills without materializing managed
  cache directories
- **RTM-02**: Users can opt into a `latest` alias policy where allowed

## Out of Scope

| Feature | Reason |
|---------|--------|
| HTTP registry service | Direct PostgreSQL access is the chosen v1 integration path |
| Namespace-based skill identity | v1 uses global unique names to reduce complexity |
| Loading by implicit latest version | Explicit versioning avoids ambiguity and drift |
| In-database skill editing UI | v1 publishes from local directories only |
| Full RBAC and org-level permissions | v1 only needs public read plus maintainer write |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| REG-01 | Phase 1 | Pending |
| REG-02 | Phase 1 | Pending |
| REG-03 | Phase 1 | Pending |
| REG-04 | Phase 1 | Pending |
| ACC-01 | Phase 1 | Pending |
| ACC-02 | Phase 1 | Pending |
| ACC-03 | Phase 3 | Pending |
| PUB-01 | Phase 2 | Pending |
| PUB-02 | Phase 2 | Pending |
| PUB-03 | Phase 2 | Pending |
| RUN-01 | Phase 3 | Pending |
| RUN-02 | Phase 3 | Pending |
| RUN-03 | Phase 3 | Pending |
| DISC-01 | Phase 4 | Pending |
| DISC-02 | Phase 4 | Pending |
| DISC-03 | Phase 4 | Pending |
| TST-01 | Phase 4 | Pending |
| DOC-01 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 18 total
- Mapped to phases: 18
- Unmapped: 0

---
*Requirements defined: 2026-04-28*
*Last updated: 2026-04-28 after initial definition*
