"""Manual integration test for the Google Gemini agent adapter.

Run from project root:
    python -m pytest backend/tests/test_google_agent.py -s -v

Or run directly:
    python -m backend.tests.test_google_agent
"""

import asyncio

from backend.app.agents.google_agent import GoogleAgent

_SYSTEM_PROMPT = "You are a helpful assistant."
_USER_PROMPT = (
    "In 3-4 sentences, explain why Sachin Tendulkar is considered one of the greatest "
    "ODI cricketers. Include specific statistics."
)

_AGENT = GoogleAgent(
    agent_id="test-google",
    role="Analytical",
    pseudonym="Agent C",
    model_name="gemini-2.5-flash",
)


async def main() -> None:
    print(f"Prompt: {_USER_PROMPT}\n{'─' * 60}")

    result = await _AGENT.generate(
        system_prompt=_SYSTEM_PROMPT,
        user_prompt=_USER_PROMPT,
    )

    print(f"\nContent:\n{result['content']}")
    print(f"\nToken usage: {result['token_usage']}")
    print(f"Latency:     {result['latency_ms']} ms")
    print(f"\n{'─' * 60}")


if __name__ == "__main__":
    asyncio.run(main())
