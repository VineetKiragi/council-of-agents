# ADR 003: PostgreSQL over SQLite

**Status:** Accepted

## Context

The backend requires a relational database to persist deliberation sessions, agent configurations, round-by-round message history, and voting outcomes. The two realistic options for a project at this stage are SQLite (zero-configuration, file-based) and PostgreSQL (full client-server RDBMS). Both are well-supported by SQLAlchemy.

## Decision

Use PostgreSQL as the primary database rather than SQLite.

## Reasoning

- **Production realism:** The architecture is designed to reflect industry practice. SQLite is not used in production web services that handle concurrent writes; PostgreSQL is. Using PostgreSQL from the start means deployment never requires a database migration.
- **Concurrent access:** Deliberation sessions involve multiple agents writing messages within the same round. PostgreSQL's row-level locking and MVCC handle concurrent writes correctly; SQLite's file-level locking does not.
- **SQL familiarity:** Existing SQL experience maps directly onto PostgreSQL. The additional setup cost is low given that background.
- **Ecosystem:** PostgreSQL's support for JSONB, full-text search, and advisory locks provides headroom for future features (e.g., storing unstructured agent metadata, searching deliberation transcripts) without a database change.
- **Alembic migrations:** Schema evolution via Alembic works identically with both databases, so there is no migration tooling advantage to SQLite.

## Tradeoffs

| Consideration | PostgreSQL | SQLite |
|---|---|---|
| Setup complexity | Requires a running server | Zero configuration |
| Concurrent write support | Full (MVCC) | Limited (file lock) |
| Production suitability | Industry standard | Not recommended |
| Local dev friction | Moderate (Docker or native install) | None |
| JSONB / advanced types | Supported | Limited |
| Alembic compatibility | Full | Full |
| Deployment portability | Requires managed DB or container | Single file |
