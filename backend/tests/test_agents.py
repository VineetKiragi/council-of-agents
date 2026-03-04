"""Unit tests for agent configuration and the BaseAgent interface.

No database or real API calls — uses the mock_agent fixture for generate() tests.
"""

import pytest

from backend.app.agents.agent_config import get_agent_configs


# ---------------------------------------------------------------------------
# AgentConfig
# ---------------------------------------------------------------------------


def test_get_agent_configs_returns_five():
    assert len(get_agent_configs()) == 5


def test_all_configs_have_required_fields():
    required = {"role", "system_prompt", "provider", "model"}
    for config in get_agent_configs():
        missing = required - set(vars(config).keys())
        assert not missing, f"Config {config.role!r} is missing fields: {missing}"


def test_chairman_exists():
    chairmen = [c for c in get_agent_configs() if c.role == "Chairman"]
    assert len(chairmen) == 1


def test_multiple_providers():
    providers = {c.provider for c in get_agent_configs()}
    assert len(providers) >= 2


# ---------------------------------------------------------------------------
# BaseAgent interface (via mock_agent fixture)
# ---------------------------------------------------------------------------


async def test_mock_agent_generate(mock_agent):
    result = await mock_agent.generate(
        system_prompt="You are helpful.",
        user_prompt="Say something.",
    )
    assert "content" in result
    assert "token_usage" in result
    assert "latency_ms" in result
