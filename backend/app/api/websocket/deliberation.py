import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.app.core.orchestrator import DeliberationOrchestrator
from backend.app.db.database import SessionLocal

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/deliberate")
async def deliberate(websocket: WebSocket) -> None:
    await websocket.accept()

    db = SessionLocal()
    try:
        # ── Receive the prompt ─────────────────────────────────────────
        raw = await websocket.receive_text()
        data = json.loads(raw)
        prompt = data.get("prompt", "").strip()

        if not prompt:
            await websocket.send_json({"type": "error", "detail": "prompt is required"})
            return

        # ── Callback: stream each message as it is saved ───────────────
        async def on_message(msg: dict[str, Any]) -> None:
            await websocket.send_json(
                {
                    "type": "message",
                    "round_number": msg["round_number"],
                    "agent_pseudonym": msg["agent_pseudonym"],
                    "content": msg["content"],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )

        # ── Run deliberation ───────────────────────────────────────────
        orchestrator = DeliberationOrchestrator(db=db, callback=on_message)
        session_id = await orchestrator.run_deliberation(prompt)

        await websocket.send_json(
            {
                "type": "complete",
                "session_id": str(session_id),
            }
        )

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected during deliberation")

    except Exception as exc:
        logger.error("WebSocket deliberation error: %s", exc, exc_info=True)
        try:
            await websocket.send_json({"type": "error", "detail": str(exc)})
        except Exception:
            pass  # connection may already be closed

    finally:
        db.close()
