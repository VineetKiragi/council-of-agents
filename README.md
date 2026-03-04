# Council of Agents

A multi-agent deliberation framework where AI agents from different LLM providers debate topics anonymously, critique each other's positions, and arrive at collective decisions through structured rounds of discussion.

---

## Features

- **Multi-agent deliberation** — 5 agents debate across 3 structured rounds (initial positions → critique → final positions) then a Chairman synthesises a decision
- **3 LLM providers** — Anthropic (Claude), OpenAI (GPT), and Google (Gemini) agents in the same council
- **Anonymized discussion** — agents don't know each other's identities or providers during deliberation
- **Real-time WebSocket streaming** — messages appear in the UI as each agent responds
- **Agent reveal** — after deliberation, provider identity and role are revealed with colour-coded badges
- **Session stats / LLMOps** — per-agent and per-round token usage, latency, and estimated cost
- **Docker support** — full stack (PostgreSQL + FastAPI + React) via `docker compose up --build`

---

## Architecture Overview

### Tech Stack

**Backend**
- **Python 3.11+** — core runtime
- **FastAPI** — REST API and WebSocket server
- **SQLAlchemy 2.0** — ORM with async support
- **Alembic** — database migrations
- **PostgreSQL** — persistent storage
- **Uvicorn** — ASGI server

**AI Providers**
- **Anthropic** (Claude) — `anthropic` SDK
- **OpenAI** (GPT) — `openai` SDK
- **Google** (Gemini) — `google-generativeai` SDK

**Frontend**
- **React** — UI framework
- **Vite** — build tool and dev server

**Infrastructure**
- **Docker** — containerization
- **pytest** — backend testing

### Directory Structure

```
council-of-agents/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/        # HTTP route handlers
│   │   │   └── websocket/     # WebSocket handlers
│   │   ├── agents/            # Agent logic and orchestration
│   │   ├── core/              # Config, settings, startup
│   │   ├── db/                # Database session and migrations
│   │   ├── models/            # Pydantic and SQLAlchemy models
│   │   └── observability/     # Logging, tracing, metrics
│   ├── tests/
│   └── requirements.txt
├── frontend/                  # React + Vite app
├── docs/
│   └── adr/                   # Architecture Decision Records
├── docker/
├── .env.example
└── README.md
```

---

## Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- npm

### 1. Clone and Configure Environment

```bash
git clone <repo-url>
cd council-of-agents
cp .env.example .env
```

Edit `.env` and fill in your API keys and database credentials:

```
DATABASE_URL=postgresql://council_user:council_dev_123@localhost:5432/council_of_agents
ANTHROPIC_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here
GOOGLE_API_KEY=your-key-here
```

### 2. Backend Setup

```bash
pip install -r backend/requirements.txt
```

### 3. Database Setup

Create the PostgreSQL database and user:

```sql
CREATE USER council_user WITH PASSWORD 'council_dev_123';
CREATE DATABASE council_of_agents OWNER council_user;
```

Run migrations:

```bash
cd backend
alembic upgrade head
```

### 4. Frontend Setup

```bash
cd frontend
npm install
```

### 5. Running the App

**Backend** (from project root):

```bash
uvicorn backend.app.main:app --reload
```

API available at `http://localhost:8000`

**Frontend** (from `frontend/`):

```bash
npm run dev
```

UI available at `http://localhost:5173`

---

## Running with Docker

The easiest way to run the full stack (PostgreSQL + backend + frontend) without any local setup.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed

### 1. Configure API Keys

Edit `.env.docker` and fill in your real API keys:

```
ANTHROPIC_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here
GOOGLE_API_KEY=your-key-here
```

### 2. Build and Start

```bash
docker compose -f docker/docker-compose.yml up --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs
- PostgreSQL: `localhost:5450` (host-side port; the backend connects internally on port 5432)

### 3. Run Migrations

On first run (or after schema changes):

```bash
docker compose -f docker/docker-compose.yml exec backend alembic upgrade head
```

### 4. Stop

```bash
docker compose -f docker/docker-compose.yml down
```

To also delete the database volume:

```bash
docker compose -f docker/docker-compose.yml down -v
```

---

## Project Status

**Phase 5: Complete — MVP**
