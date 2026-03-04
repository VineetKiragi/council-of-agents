import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session as DbSession

from backend.app.agents.anthropic_agent import AnthropicAgent
from backend.app.core.orchestrator import DeliberationOrchestrator
from backend.app.db.database import get_db
from backend.app.db.models import Message, Session
from backend.app.models.schemas import SessionCreate, SessionResponse, SessionReveal
from backend.app.observability.tracker import SessionTracker

router = APIRouter(prefix="/sessions")


# ---------------------------------------------------------------------------
# List-view schema (no messages, just summary fields)
# ---------------------------------------------------------------------------


class SessionSummary(BaseModel):
    id: uuid.UUID
    prompt: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# POST /sessions — full multi-agent deliberation (30-60 s)
#
# FastAPI and Uvicorn impose no response timeout by default, so long-running
# async handlers are fine. The 16 LLM calls are all awaited concurrently per
# round via asyncio.gather inside the orchestrator, keeping wall-clock time
# to roughly max(round_latencies) × 3 rounds + chairman, not the sum.
# ---------------------------------------------------------------------------


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(
    body: SessionCreate,
    db: DbSession = Depends(get_db),
) -> Session:
    if not body.prompt.strip():
        raise HTTPException(status_code=400, detail="prompt must not be empty")

    orchestrator = DeliberationOrchestrator(db=db, callback=None)

    try:
        session_id = await orchestrator.run_deliberation(body.prompt)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    session = db.get(Session, session_id)
    if session is None:  # should never happen, but guard anyway
        raise HTTPException(status_code=500, detail="Session lost after deliberation")

    return session


# ---------------------------------------------------------------------------
# POST /sessions/quick — single Anthropic agent, fast response for testing
# Note: must be registered before /{session_id} to avoid route shadowing.
# ---------------------------------------------------------------------------

_QUICK_SYSTEM_PROMPT = (
    "You are an analytical thinker on a deliberation council. Your role is to evaluate "
    "arguments based on evidence, data, and logical reasoning. Look for factual accuracy, "
    "logical consistency, and strength of evidence. Challenge weak reasoning and support "
    "well-founded arguments."
)


@router.post("/quick", response_model=SessionResponse, status_code=201)
async def create_session_quick(
    body: SessionCreate,
    db: DbSession = Depends(get_db),
) -> Session:
    if not body.prompt.strip():
        raise HTTPException(status_code=400, detail="prompt must not be empty")

    session = Session(id=uuid.uuid4(), prompt=body.prompt, status="in_progress")
    db.add(session)
    db.commit()
    db.refresh(session)

    try:
        agent = AnthropicAgent(
            agent_id="agent-analytical-quick",
            role="Analytical",
            pseudonym="Agent A",
            model_name="claude-sonnet-4-6",
        )
        result = await agent.generate(
            system_prompt=_QUICK_SYSTEM_PROMPT,
            user_prompt=body.prompt,
        )
        db.add(
            Message(
                id=uuid.uuid4(),
                session_id=session.id,
                round_number=1,
                agent_pseudonym="Agent A",
                agent_role="Analytical",
                agent_provider="anthropic",
                content=result["content"],
                token_usage=result["token_usage"],
                latency_ms=result["latency_ms"],
            )
        )
        session.status = "completed"
        db.commit()
        db.refresh(session)

    except Exception as exc:
        session.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return session


# ---------------------------------------------------------------------------
# GET /sessions
# ---------------------------------------------------------------------------


@router.get("", response_model=list[SessionSummary])
def list_sessions(db: DbSession = Depends(get_db)) -> list[Session]:
    return db.query(Session).order_by(Session.created_at.desc()).all()


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}
# ---------------------------------------------------------------------------


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: uuid.UUID, db: DbSession = Depends(get_db)) -> Session:
    session = db.get(Session, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/reveal — identities exposed, completed only
# ---------------------------------------------------------------------------


@router.get("/{session_id}/reveal", response_model=SessionReveal)
def reveal_session(session_id: uuid.UUID, db: DbSession = Depends(get_db)) -> Session:
    session = db.get(Session, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="Reveal is only available after deliberation completes.",
        )
    return session


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/stats — LLMOps stats, completed only
# ---------------------------------------------------------------------------


@router.get("/{session_id}/stats")
def get_session_stats(session_id: uuid.UUID, db: DbSession = Depends(get_db)) -> dict:
    session = db.get(Session, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="Stats are only available after deliberation completes.",
        )
    return SessionTracker.get_session_stats(session_id, db)
