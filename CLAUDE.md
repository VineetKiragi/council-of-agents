# Council of Agents — CLAUDE.md

Project reference for Claude Code. Read this at the start of every session.
Updated at the end of every session / before every commit.

---

## PROJECT OVERVIEW
Multi-agent deliberation framework — FastAPI + React + PostgreSQL. A council of 5 AI agents (Anthropic, OpenAI, Google) deliberate over a user prompt across multiple rounds and produce a synthesised final decision. Agent identities are hidden during deliberation and revealed at the end.

---

## COMMANDS

```bash
# Activate environment (always first)
conda activate council

# Start backend server (from project root)
uvicorn backend.app.main:app --reload

# Start frontend dev server (from frontend/)
cd frontend && npm run dev

# Run database migrations (from backend/)
cd backend && alembic upgrade head

# Create a new migration (from backend/)
cd backend && alembic revision --autogenerate -m "description"

# Run manual test agent script (from project root)
python -m backend.test_agent
```

---

## CONVENTIONS

- **Import paths:** always `from backend.app.*` not `from app.*` — server runs from project root
  - Exception: `backend/alembic/env.py` keeps `from app.*` (alembic runs from `backend/`)
- **Commit messages:** conventional commits — `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`
- **Python version:** 3.11, conda environment named `council`
- **Dependencies:** pinned versions in `backend/requirements.txt`, no loose ranges

---

## ARCHITECTURE

```
backend/app/
├── api/routes/       # REST endpoints (health, sessions)
├── api/websocket/    # WebSocket handlers — NOT BUILT YET
├── core/             # Deliberation orchestration engine — NOT BUILT YET
├── agents/           # LLM provider adapters (base.py, anthropic_agent.py, agent_config.py)
├── db/               # SQLAlchemy models and database connection
├── models/           # Pydantic request/response schemas
└── observability/    # Logging, tracing, metrics — NOT BUILT YET

frontend/             # React + Vite app — NOT BUILT YET
```

---

## KEY DESIGN DECISIONS

- **Adapter pattern:** `BaseAgent` ABC defines the interface; each provider subclasses it. Routes and orchestrator only depend on `BaseAgent`, never on a specific provider.
- **Schemas separate from models:** SQLAlchemy models define DB storage; Pydantic schemas control what the API exposes. `MessageResponse` hides `agent_role` and `agent_provider` during deliberation; `MessageReveal` exposes them after.
- **Anonymisation at two layers:** (1) orchestrator builds prompts that don't reveal agent identities to each other; (2) Pydantic schemas hide role/provider from the frontend until deliberation ends.
- **CORS:** configured for `http://localhost:5173` (Vite dev server).
- **Sync SQLAlchemy for now:** async can be added later; keeping it simple for Phase 2.

---

## CURRENT STATE

**Phase 1** — complete (project structure, docs, ADRs)

**Phase 2** — in progress

| Component | Status |
|---|---|
| `config.py` — pydantic-settings, loads .env | ✅ done |
| `db/database.py` — engine, SessionLocal, Base, get_db | ✅ done |
| `db/models.py` — Session and Message ORM models | ✅ done |
| `models/schemas.py` — all Pydantic schemas | ✅ done |
| Alembic setup + first migration (tables in DB) | ✅ done |
| `agents/base.py` — BaseAgent ABC | ✅ done |
| `agents/anthropic_agent.py` — Anthropic adapter | ✅ done |
| `agents/agent_config.py` — 5 role definitions | ✅ done |
| `api/routes/health.py` — GET /api/health | ✅ done |
| `api/routes/sessions.py` — POST/GET /api/sessions | ✅ done (single-agent prototype) |
| `main.py` — FastAPI app, CORS, router registration | ✅ done |
| OpenAI agent adapter | ❌ not built |
| Google agent adapter | ❌ not built |
| Agent factory | ❌ not built |
| Deliberation orchestrator (core/) | ❌ not built |
| WebSocket handler | ❌ not built |
| React frontend | ❌ not built |
| Observability | ❌ not built |

**Next up:** OpenAI adapter → Google adapter → agent factory → deliberation orchestrator → wire into POST /sessions

---

## DATABASE

- **Engine:** PostgreSQL (local)
- **Database:** `council_of_agents` — **User:** `council_user`
- **Migrations:** Alembic, run from `backend/`

| Table | Columns |
|---|---|
| `sessions` | id (UUID PK), prompt, status (pending/in_progress/completed/failed), final_decision, created_at, updated_at |
| `messages` | id (UUID PK), session_id (FK), round_number, agent_pseudonym, agent_role, agent_provider, content, token_usage, latency_ms, created_at |

- `round_number = 0` reserved for Chairman's final synthesis
- Deleting a session cascades to all its messages

---

## GOTCHAS

- Always run commands from **project root**, not from `backend/` (except `alembic` commands)
- Always activate the conda env: `conda activate council`
- Never commit `.env` — it contains real API keys
- The Anthropic adapter is named `anthropic_agent.py` not `anthropic.py` — would conflict with the `anthropic` package name
- `backend/__init__.py` must exist for `backend.app.*` imports to work from project root
- `POST /api/sessions` currently runs only a single Anthropic agent — the full multi-agent orchestrator is not wired in yet
