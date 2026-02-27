import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session as DbSession

from backend.app.agents.anthropic_agent import AnthropicAgent
from backend.app.db.database import get_db
from backend.app.db.models import Message, Session
from backend.app.models.schemas import SessionCreate, SessionResponse

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
# POST /sessions
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are an analytical thinker on a deliberation council. Your role is to evaluate "
    "arguments based on evidence, data, and logical reasoning. Look for factual accuracy, "
    "logical consistency, and strength of evidence. Challenge weak reasoning and support "
    "well-founded arguments."
)


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(
    body: SessionCreate,
    db: DbSession = Depends(get_db),
) -> Session:
    session = Session(
        id=uuid.uuid4(),
        prompt=body.prompt,
        status="in_progress",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    try:
        agent = AnthropicAgent(
            agent_id="agent-analytical-1",
            role="Analytical",
            pseudonym="Agent A",
            model_name="claude-sonnet-4-6",
        )

        result = await agent.generate(
            system_prompt=_SYSTEM_PROMPT,
            user_prompt=body.prompt,
        )

        message = Message(
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
        db.add(message)

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
