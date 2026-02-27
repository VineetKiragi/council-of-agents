import time

import anthropic

from backend.app.agents.base import BaseAgent
from backend.app.config import settings


class AnthropicAgent(BaseAgent):
    def __init__(self, agent_id: str, role: str, pseudonym: str, model_name: str) -> None:
        super().__init__(
            agent_id=agent_id,
            role=role,
            pseudonym=pseudonym,
            provider_name="anthropic",
            model_name=model_name,
        )
        self._client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, str | int | None]:
        start_ms = time.monotonic() * 1000

        try:
            response = await self._client.messages.create(
                model=self.model_name,
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            latency_ms = int(time.monotonic() * 1000 - start_ms)
            content = response.content[0].text
            token_usage = response.usage.input_tokens + response.usage.output_tokens

            return {
                "content": content,
                "token_usage": token_usage,
                "latency_ms": latency_ms,
            }

        except anthropic.APIError as exc:
            return {
                "content": f"[Anthropic API error: {exc}]",
                "token_usage": None,
                "latency_ms": None,
            }
