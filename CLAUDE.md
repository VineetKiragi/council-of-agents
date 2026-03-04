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
├── api/websocket/    # WebSocket handlers (deliberation.py — /ws/deliberate)
├── core/             # Deliberation orchestration engine (orchestrator.py)
├── agents/           # LLM provider adapters + factory + agent_config
├── db/               # SQLAlchemy models and database connection
├── models/           # Pydantic request/response schemas
└── observability/    # Logging, tracing, metrics — NOT BUILT YET

frontend/             # React + Vite app (SubmitPanel, DeliberationView, ResultPanel)
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

**Phase 2** — complete (backend infrastructure, DB, all agent adapters, REST API)

**Phase 3** — complete (orchestration, WebSocket streaming, React frontend)

**Phase 4** — complete

Full multi-agent orchestration with 5 agents across 3 providers, 3 rounds of anonymised deliberation, real-time WebSocket streaming, agent identity reveal, session stats with token/cost tracking, markdown rendering, and robust error handling throughout.

| Component | Status |
|---|---|
| `config.py` — pydantic-settings, loads .env | ✅ done |
| `db/database.py` — engine, SessionLocal, Base, get_db | ✅ done |
| `db/models.py` — Session and Message ORM models | ✅ done |
| `models/schemas.py` — Pydantic schemas incl. MessageReveal / SessionReveal | ✅ done |
| Alembic setup + first migration (tables in DB) | ✅ done |
| `agents/base.py` — BaseAgent ABC (max_tokens param) | ✅ done |
| `agents/anthropic_agent.py` — Anthropic adapter | ✅ done |
| `agents/openai_agent.py` — OpenAI adapter | ✅ done |
| `agents/google_agent.py` — Google Gemini adapter | ✅ done |
| `agents/agent_config.py` — 5 role definitions | ✅ done |
| `agents/factory.py` — create_agent / create_all_agents | ✅ done |
| `core/orchestrator.py` — DeliberationOrchestrator (silent callback, error resilience) | ✅ done |
| `api/routes/health.py` — GET /api/health | ✅ done |
| `api/routes/sessions.py` — POST/GET /api/sessions, /quick, /reveal, /stats | ✅ done |
| `api/websocket/deliberation.py` — WS /ws/deliberate (5 min timeout, bg completion) | ✅ done |
| `main.py` — FastAPI app, CORS, router registration | ✅ done |
| `observability/tracker.py` — SessionTracker (tokens, cost, per-agent/round stats) | ✅ done |
| React frontend — SubmitPanel, DeliberationView, StatsPanel | ✅ done |
| WebSocket real-time streaming to frontend | ✅ done |
| Agent identity reveal (GET /reveal → colour-coded provider badges) | ✅ done |
| Markdown rendering (react-markdown + remark-gfm) | ✅ done |
| Error card styling for failed agent responses | ✅ done |
| Docker / containerisation | ❌ not built |
| Final documentation | ❌ not built |

**Next up:** Phase 5 — Docker (backend + frontend + PostgreSQL), final documentation

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
- Google model must be `gemini-2.5-flash` — older names (gemini-1.5-*, gemini-2.0-flash) return 404 on the Cloud Console API key
- `response.text` on Gemini 2.5 Flash can fail with multi-part responses (thinking tokens); use explicit part-joining instead
