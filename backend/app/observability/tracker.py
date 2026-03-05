import uuid

from sqlalchemy.orm import Session as DbSession

from backend.app.db.models import Message

# Rough blended cost per 1K tokens (input+output averaged) by provider.
# These are estimates for LLMOps awareness, not billing.
_COST_PER_1K_TOKENS: dict[str, float] = {
    "anthropic": 0.015,  # claude-sonnet: ~$3/1M input, $15/1M output → blended ~$15/1M
    "openai": 0.0004,  # gpt-4o-mini:  $0.15/1M input, $0.60/1M output → blended
    "google": 0.0002,  # gemini-2.5-flash: ~$0.15/1M input
}


class SessionTracker:
    @staticmethod
    def get_session_stats(session_id: uuid.UUID, db: DbSession) -> dict:
        messages: list[Message] = db.query(Message).filter(Message.session_id == session_id).all()

        if not messages:
            return {
                "total_tokens": 0,
                "total_latency_ms": 0,
                "estimated_cost": 0.0,
                "per_agent": [],
                "per_round": [],
            }

        total_tokens = sum(m.token_usage or 0 for m in messages)
        total_latency_ms = sum(m.latency_ms or 0 for m in messages)

        estimated_cost = sum(
            (m.token_usage or 0) / 1000 * _COST_PER_1K_TOKENS.get(m.agent_provider, 0.0)
            for m in messages
        )

        # ── Per-agent breakdown ────────────────────────────────────────
        agents: dict[str, dict] = {}
        for m in messages:
            key = m.agent_pseudonym
            if key not in agents:
                agents[key] = {
                    "pseudonym": m.agent_pseudonym,
                    "role": m.agent_role,
                    "provider": m.agent_provider,
                    "total_tokens": 0,
                    "total_latency_ms": 0,
                    "num_messages": 0,
                }
            agents[key]["total_tokens"] += m.token_usage or 0
            agents[key]["total_latency_ms"] += m.latency_ms or 0
            agents[key]["num_messages"] += 1

        # ── Per-round breakdown ────────────────────────────────────────
        rounds: dict[int, dict] = {}
        for m in messages:
            rn = m.round_number
            if rn not in rounds:
                rounds[rn] = {
                    "round_number": rn,
                    "total_tokens": 0,
                    "total_latency_ms": 0,
                    "num_messages": 0,
                }
            rounds[rn]["total_tokens"] += m.token_usage or 0
            rounds[rn]["total_latency_ms"] += m.latency_ms or 0
            rounds[rn]["num_messages"] += 1

        # Sort rounds: 1, 2, 3, then 0 (chairman) last
        sorted_rounds = sorted(
            rounds.values(),
            key=lambda r: (r["round_number"] == 0, r["round_number"]),
        )

        return {
            "total_tokens": total_tokens,
            "total_latency_ms": total_latency_ms,
            "estimated_cost": round(estimated_cost, 6),
            "per_agent": list(agents.values()),
            "per_round": sorted_rounds,
        }
