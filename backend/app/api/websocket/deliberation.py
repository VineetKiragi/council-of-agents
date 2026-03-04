import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.app.core.orchestrator import DeliberationOrchestrator
from backend.app.db.database import SessionLocal

logger = logging.getLogger(__name__)

router = APIRouter()

_TIMEOUT_SECONDS = 300  # 5 minutes


@router.websocket("/ws/deliberate")
async def deliberate(websocket: WebSocket) -> None:
    await websocket.accept()

    db = SessionLocal()
    deliberation_task: asyncio.Task | None = None

    try:
        # ── Receive the prompt ─────────────────────────────────────────
        raw = await websocket.receive_text()
        data = json.loads(raw)
        prompt = data.get("prompt", "").strip()

        if not prompt:
            await websocket.send_json({"type": "error", "detail": "prompt is required"})
            return

        # ── Callback: stream each saved message to the client ──────────
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

        # ── Run deliberation with a 5-minute timeout ───────────────────
        # asyncio.shield ensures the task keeps running even if wait_for
        # times out and cancels the wrapper future.
        orchestrator = DeliberationOrchestrator(db=db, callback=on_message)
        deliberation_task = asyncio.create_task(orchestrator.run_deliberation(prompt))

        try:
            session_id = await asyncio.wait_for(
                asyncio.shield(deliberation_task), timeout=_TIMEOUT_SECONDS
            )
            await websocket.send_json({"type": "complete", "session_id": str(session_id)})
            deliberation_task = None  # finished normally; finally will close db

        except asyncio.TimeoutError:
            logger.warning(
                "Deliberation exceeded %ds timeout; continuing in background", _TIMEOUT_SECONDS
            )
            try:
                await websocket.send_json(
                    {
                        "type": "error",
                        "detail": (
                            f"Deliberation timed out after {_TIMEOUT_SECONDS // 60} minutes. "
                            "It will continue saving in the background — check past sessions shortly."
                        ),
                    }
                )
            except Exception:
                pass
            # deliberation_task is still running; finally block schedules db close

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected during deliberation")

    except Exception as exc:
        logger.error("WebSocket deliberation error: %s", exc, exc_info=True)
        try:
            await websocket.send_json({"type": "error", "detail": str(exc)})
        except Exception:
            pass

    finally:
        if deliberation_task is not None and not deliberation_task.done():
            # Task is still running in the background — close db after it finishes
            async def _close_db_when_done(
                task: asyncio.Task, db_session: Any
            ) -> None:
                try:
                    await task
                except Exception:
                    pass
                finally:
                    db_session.close()

            asyncio.create_task(_close_db_when_done(deliberation_task, db))
        else:
            db.close()
