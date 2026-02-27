import asyncio

from backend.app.agents.anthropic_agent import AnthropicAgent


async def main() -> None:
    agent = AnthropicAgent(
        agent_id="test-1",
        role="Analytical",
        pseudonym="Agent A",
        model_name="claude-sonnet-4-6",
    )

    result = await agent.generate(
        system_prompt="You are a helpful assistant.",
        user_prompt="In one sentence, what makes Sachin Tendulkar the greatest cricketer?",
    )

    print(f"Content:     {result['content']}")
    print(f"Token usage: {result['token_usage']}")
    print(f"Latency:     {result['latency_ms']} ms")


if __name__ == "__main__":
    asyncio.run(main())
