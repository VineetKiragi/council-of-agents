from backend.app.agents.agent_config import AgentConfig, get_agent_configs
from backend.app.agents.anthropic_agent import AnthropicAgent
from backend.app.agents.base import BaseAgent
from backend.app.agents.google_agent import GoogleAgent
from backend.app.agents.openai_agent import OpenAIAgent

_PSEUDONYMS = ["Agent A", "Agent B", "Agent C", "Agent D", "Agent E"]


def create_agent(config: AgentConfig, pseudonym: str) -> BaseAgent:
    agent_id = f"agent-{config.role.lower().replace(' ', '-')}"

    if config.provider == "anthropic":
        return AnthropicAgent(
            agent_id=agent_id,
            role=config.role,
            pseudonym=pseudonym,
            model_name=config.model,
        )
    if config.provider == "openai":
        return OpenAIAgent(
            agent_id=agent_id,
            role=config.role,
            pseudonym=pseudonym,
            model_name=config.model,
        )
    if config.provider == "google":
        return GoogleAgent(
            agent_id=agent_id,
            role=config.role,
            pseudonym=pseudonym,
            model_name=config.model,
        )

    raise ValueError(f"Unknown provider: {config.provider!r}")


def create_all_agents() -> list[BaseAgent]:
    configs = get_agent_configs()
    return [
        create_agent(config, pseudonym)
        for config, pseudonym in zip(configs, _PSEUDONYMS)
    ]
