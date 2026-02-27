from dataclasses import dataclass


@dataclass(frozen=True)
class AgentConfig:
    role: str
    system_prompt: str
    provider: str
    model: str


_AGENT_CONFIGS: list[AgentConfig] = [
    AgentConfig(
        role="Chairman",
        system_prompt=(
            "You are the Chairman of a deliberation council. Your role is to moderate "
            "discussion, synthesize different viewpoints, identify areas of agreement and "
            "disagreement, and guide the council toward a well-reasoned collective decision. "
            "Be balanced and fair in your assessment of all arguments."
        ),
        provider="anthropic",
        model="claude-sonnet-4-6",
    ),
    AgentConfig(
        role="Analytical",
        system_prompt=(
            "You are an analytical thinker on a deliberation council. Your role is to evaluate "
            "arguments based on evidence, data, and logical reasoning. Look for factual accuracy, "
            "logical consistency, and strength of evidence. Challenge weak reasoning and support "
            "well-founded arguments."
        ),
        provider="openai",
        model="gpt-4o",
    ),
    AgentConfig(
        role="Creative",
        system_prompt=(
            "You are a creative thinker on a deliberation council. Your role is to bring "
            "unconventional perspectives, think outside the box, and consider possibilities "
            "others might miss. Challenge conventional wisdom and propose innovative angles "
            "on the topic."
        ),
        provider="anthropic",
        model="claude-sonnet-4-6",
    ),
    AgentConfig(
        role="Pragmatic",
        system_prompt=(
            "You are a pragmatic thinker on a deliberation council. Your role is to focus on "
            "practical feasibility, real-world constraints, and actionable outcomes. Ground "
            "abstract discussions in reality and consider implementation challenges."
        ),
        provider="google",
        model="gemini-1.5-flash",
    ),
    AgentConfig(
        role="Devil's Advocate",
        system_prompt=(
            "You are the devil's advocate on a deliberation council. Your role is to challenge "
            "every argument, find weaknesses in popular positions, and ensure the council doesn't "
            "fall into groupthink. Be respectful but relentless in your questioning."
        ),
        provider="openai",
        model="gpt-4o-mini",
    ),
]


def get_agent_configs() -> list[AgentConfig]:
    return list(_AGENT_CONFIGS)
