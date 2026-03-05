import asyncio
import logging
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy.orm import Session as DbSession

from backend.app.agents.agent_config import AgentConfig, get_agent_configs
from backend.app.agents.base import BaseAgent
from backend.app.agents.factory import create_all_agents
from backend.app.db.models import Message, Session

logger = logging.getLogger(__name__)

_COUNCIL_PSEUDONYMS = ["Agent A", "Agent B", "Agent C", "Agent D"]

# Type alias for the optional real-time callback (used by WebSocket layer later)
Callback = Callable[[dict[str, Any]], Awaitable[None]]


class DeliberationOrchestrator:
    def __init__(
        self,
        db: DbSession,
        callback: Callback | None = None,
        agents: list[BaseAgent] | None = None,
    ) -> None:
        self.db = db
        self.callback = callback
        self._agents = agents  # if None, create_all_agents() is called at run time

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def run_deliberation(self, prompt: str) -> uuid.UUID:
        session = Session(id=uuid.uuid4(), prompt=prompt, status="in_progress")
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        agents = self._agents if self._agents is not None else create_all_agents()
        configs = get_agent_configs()

        # Index 0 is always the Chairman; indices 1-4 are council members.
        chairman, chairman_config = agents[0], configs[0]
        chairman.pseudonym = "Chairman"

        council: list[BaseAgent] = agents[1:]
        council_configs: list[AgentConfig] = configs[1:]
        for agent, pseudonym in zip(council, _COUNCIL_PSEUDONYMS):
            agent.pseudonym = pseudonym

        # ── Round 1 — Initial positions ────────────────────────────────
        round1 = await self._run_round(
            session_id=session.id,
            round_number=1,
            agents=council,
            configs=council_configs,
            user_prompt=(
                f"The council is deliberating on: {prompt}. "
                "Provide your initial position and reasoning."
            ),
            prior_messages=[],
        )

        # ── Round 2 — Critique ─────────────────────────────────────────
        round2 = await self._run_round(
            session_id=session.id,
            round_number=2,
            agents=council,
            configs=council_configs,
            user_prompt=(
                "Review the Round 1 positions below. Critique arguments you disagree with, "
                "acknowledge strong points from others, and refine your own position."
            ),
            prior_messages=round1,
        )

        # ── Round 3 — Final positions ──────────────────────────────────
        round3 = await self._run_round(
            session_id=session.id,
            round_number=3,
            agents=council,
            configs=council_configs,
            user_prompt=(
                "This is the final round. Based on all previous discussion, provide your final "
                "position with clear reasoning. State whether you've changed your mind and why."
            ),
            prior_messages=round1 + round2,
        )

        # ── Chairman synthesis ─────────────────────────────────────────
        all_messages = round1 + round2 + round3
        chairman_prompt = self._build_chairman_prompt(all_messages, prompt)

        try:
            result = await chairman.generate(
                system_prompt=chairman_config.system_prompt,
                user_prompt=chairman_prompt,
                max_tokens=4096,
            )
            synthesis = result["content"]

            chairman_msg = Message(
                id=uuid.uuid4(),
                session_id=session.id,
                round_number=0,
                agent_pseudonym="Chairman",
                agent_role=chairman.role,
                agent_provider=chairman.provider_name,
                content=synthesis,
                token_usage=result["token_usage"],
                latency_ms=result["latency_ms"],
            )
            self.db.add(chairman_msg)
            session.final_decision = synthesis
            session.status = "completed"
            self.db.commit()
            self.db.refresh(chairman_msg)

            await self._fire(self._msg_to_dict(chairman_msg))

        except Exception as exc:
            logger.error("Chairman synthesis failed: %s", exc, exc_info=True)
            session.status = "failed"
            self.db.commit()

        return session.id

    # ------------------------------------------------------------------
    # Round runner
    # ------------------------------------------------------------------

    async def _run_round(
        self,
        session_id: uuid.UUID,
        round_number: int,
        agents: list[BaseAgent],
        configs: list[AgentConfig],
        user_prompt: str,
        prior_messages: list[Message],
    ) -> list[Message]:
        tasks = []
        for agent, config in zip(agents, configs):
            if prior_messages:
                context = self._build_prior_context(prior_messages, agent.pseudonym)
                full_prompt = f"{context}\n\n{user_prompt}"
            else:
                full_prompt = user_prompt
            tasks.append(self._call_agent_safe(agent, config.system_prompt, full_prompt))

        results = await asyncio.gather(*tasks)

        saved: list[Message] = []
        for agent, result in zip(agents, results):
            msg = Message(
                id=uuid.uuid4(),
                session_id=session_id,
                round_number=round_number,
                agent_pseudonym=agent.pseudonym,
                agent_role=agent.role,
                agent_provider=agent.provider_name,
                content=result["content"],
                token_usage=result["token_usage"],
                latency_ms=result["latency_ms"],
            )
            self.db.add(msg)
            saved.append(msg)

        self.db.commit()
        for msg in saved:
            self.db.refresh(msg)
            await self._fire(self._msg_to_dict(msg))

        return saved

    # ------------------------------------------------------------------
    # Safe agent call — errors become error-content messages, not exceptions
    # ------------------------------------------------------------------

    async def _call_agent_safe(
        self,
        agent: BaseAgent,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        try:
            return await agent.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
        except Exception as exc:
            logger.error(
                "Agent %s (%s) raised an unexpected error: %s",
                agent.pseudonym,
                agent.provider_name,
                exc,
                exc_info=True,
            )
            return {
                "content": f"[Agent error: {exc}]",
                "token_usage": None,
                "latency_ms": None,
            }

    # ------------------------------------------------------------------
    # Context builders
    # ------------------------------------------------------------------

    def _build_round_context(
        self,
        messages: list[Message],
        current_pseudonym: str,
        round_label: str,
    ) -> str:
        """Format one round's messages with pseudonyms, marking the current agent's own response."""
        lines = [f"--- {round_label} ---"]
        for msg in messages:
            marker = " (you)" if msg.agent_pseudonym == current_pseudonym else ""
            lines.append(f"\n{msg.agent_pseudonym}{marker}:\n{msg.content}")
        return "\n".join(lines)

    def _build_prior_context(
        self,
        messages: list[Message],
        current_pseudonym: str,
    ) -> str:
        """Build multi-round context from a flat list of prior messages, grouped by round."""
        by_round: dict[int, list[Message]] = {}
        for msg in messages:
            by_round.setdefault(msg.round_number, []).append(msg)

        sections = [
            self._build_round_context(by_round[rnum], current_pseudonym, f"Round {rnum}")
            for rnum in sorted(by_round)
        ]
        return "\n\n".join(sections)

    def _build_chairman_prompt(self, messages: list[Message], original_prompt: str) -> str:
        """Build the Chairman's synthesis prompt from all council messages across all rounds."""
        by_round: dict[int, list[Message]] = {}
        for msg in messages:
            by_round.setdefault(msg.round_number, []).append(msg)

        lines = [
            f"The council has deliberated on the following question:\n{original_prompt}\n",
            "Here is the full discussion:",
        ]
        for rnum in sorted(by_round):
            lines.append(f"\n--- Round {rnum} ---")
            for msg in by_round[rnum]:
                lines.append(f"\n{msg.agent_pseudonym}:\n{msg.content}")

        lines.append(
            "\n\nAs Chairman, synthesize the council's deliberation. Summarize the key "
            "arguments, areas of agreement and disagreement, and deliver a final collective "
            "decision with reasoning. Note any significant dissenting views."
        )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _fire(self, data: dict[str, Any]) -> None:
        """Send a real-time update via the callback if one is registered.

        Silently swallows all exceptions so a disconnected WebSocket client
        (or any other callback failure) never interrupts the deliberation.
        """
        if self.callback is not None:
            try:
                await self.callback(data)
            except Exception as exc:
                logger.debug("Callback failed (client likely disconnected): %s", exc)

    @staticmethod
    def _msg_to_dict(msg: Message) -> dict[str, Any]:
        return {
            "id": str(msg.id),
            "round_number": msg.round_number,
            "agent_pseudonym": msg.agent_pseudonym,
            "content": msg.content,
            "token_usage": msg.token_usage,
            "latency_ms": msg.latency_ms,
        }
