import asyncio

from backend.app.agents.anthropic_agent import AnthropicAgent
from backend.app.agents.google_agent import GoogleAgent
from backend.app.agents.openai_agent import OpenAIAgent

_SYSTEM_PROMPT = "You are a helpful assistant."
_USER_PROMPT = "In one sentence, what is the most important quality of a great cricket captain?"

_TEST_AGENTS = [
    AnthropicAgent(
        agent_id="test-anthropic",
        role="Analytical",
        pseudonym="Agent A",
        model_name="claude-sonnet-4-6",
    ),
    OpenAIAgent(
        agent_id="test-openai",
        role="Analytical",
        pseudonym="Agent B",
        model_name="gpt-4o-mini",
    ),
    GoogleAgent(
        agent_id="test-google",
        role="Analytical",
        pseudonym="Agent C",
        model_name="gemini-2.5-flash",
    ),
]


async def main() -> None:
    print(f"Prompt: {_USER_PROMPT}\n{'─' * 60}")

    for agent in _TEST_AGENTS:
        result = await agent.generate(
            system_prompt=_SYSTEM_PROMPT,
            user_prompt=_USER_PROMPT,
        )
        print(f"\nProvider:    {agent.provider_name} ({agent.model_name})")
        print(f"Content:     {result['content']}")
        print(f"Token usage: {result['token_usage']}")
        print(f"Latency:     {result['latency_ms']} ms")

    print(f"\n{'─' * 60}")


if __name__ == "__main__":
    asyncio.run(main())
