import time

import openai

from backend.app.agents.base import BaseAgent
from backend.app.config import settings


class OpenAIAgent(BaseAgent):
    def __init__(self, agent_id: str, role: str, pseudonym: str, model_name: str) -> None:
        super().__init__(
            agent_id=agent_id,
            role=role,
            pseudonym=pseudonym,
            provider_name="openai",
            model_name=model_name,
        )
        self._client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, str | int | None]:
        start_ms = time.monotonic() * 1000

        try:
            response = await self._client.chat.completions.create(
                model=self.model_name,
                max_tokens=1024,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )

            latency_ms = int(time.monotonic() * 1000 - start_ms)
            content = response.choices[0].message.content
            token_usage = response.usage.prompt_tokens + response.usage.completion_tokens

            return {
                "content": content,
                "token_usage": token_usage,
                "latency_ms": latency_ms,
            }

        except openai.APIError as exc:
            return {
                "content": f"[OpenAI API error: {exc}]",
                "token_usage": None,
                "latency_ms": None,
            }
