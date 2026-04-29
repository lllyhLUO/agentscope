# Requirements: AgentScope Skill Registry

**Defined:** 2026-04-28
**Core Value:** Any user can load a shared, versioned AgentScope skill from
PostgreSQL by explicit version, without manually copying skill directories
between machines.

## v1 Requirements

### Registry

- [x] **REG-01**: System can connect to PostgreSQL and create the registry
  schema needed for skills, versions, files, and maintainers
- [x] **REG-02**: System stores each skill as a globally unique name
- [x] **REG-03**: System stores each published version as an immutable artifact
- [x] **REG-04**: System stores skill contents as individual files per version,
  including `SKILL.md`, scripts, and resources

### Publishing

- [x] **PUB-01**: Maintainer can publish a local skill directory to PostgreSQL
  using an explicit skill name and version
- [x] **PUB-02**: Publish fails if the skill directory does not contain a valid
  top-level `SKILL.md`
- [x] **PUB-03**: Publish fails if the same `skill_name@version` already exists
  with different content

### Runtime Loading

- [x] **RUN-01**: User can load a skill only by explicit `skill_name@version`
- [x] **RUN-02**: System materializes a published skill version into a managed
  runtime cache directory when needed
- [x] **RUN-03**: Toolkit can register a PostgreSQL-backed skill through a new
  registry-aware API without changing the existing local directory API

### Discovery

- [x] **DISC-01**: User can search skills in PostgreSQL by name or descriptive
  metadata
- [x] **DISC-02**: User can inspect a specific `skill_name@version` and view
  its metadata and file list
- [x] **DISC-03**: User can pre-install a specific `skill_name@version` into
  the managed runtime cache

### Access and Safety

- [x] **ACC-01**: All users can read registry contents
- [x] **ACC-02**: Only maintainers can publish or update skill records
- [x] **ACC-03**: Runtime loading never treats the managed cache as the source
  of truth

### Quality

- [x] **TST-01**: New registry and loader behavior have unit and integration
  tests
- [x] **DOC-01**: Documentation explains how to publish, search, inspect,
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
| REG-01 | Phase 1 | Complete |
| REG-02 | Phase 1 | Complete |
| REG-03 | Phase 1 | Complete |
| REG-04 | Phase 1 | Complete |
| ACC-01 | Phase 1 | Complete |
| ACC-02 | Phase 1 | Complete |
| ACC-03 | Phase 3 | Complete |
| PUB-01 | Phase 2 | Complete |
| PUB-02 | Phase 2 | Complete |
| PUB-03 | Phase 2 | Complete |
| RUN-01 | Phase 3 | Complete |
| RUN-02 | Phase 3 | Complete |
| RUN-03 | Phase 3 | Complete |
| DISC-01 | Phase 4 | Complete |
| DISC-02 | Phase 4 | Complete |
| DISC-03 | Phase 4 | Complete |
| TST-01 | Phase 4 | Complete |
| DOC-01 | Phase 4 | Complete |

**Coverage:**
- v1 requirements: 18 total
- Mapped to phases: 18
- Unmapped: 0

---
*Requirements defined: 2026-04-28*
*Last updated: 2026-04-29 after Phase 4 completion*
