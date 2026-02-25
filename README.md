# Council of Agents

A multi-agent deliberation framework where AI agents from different LLM providers debate topics anonymously, critique each other's positions, and arrive at collective decisions through structured rounds of discussion.

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

## Project Status

**Phase 1: Foundation — In Progress**
