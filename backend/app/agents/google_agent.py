import time

import google.api_core.exceptions
import google.generativeai as genai
from google.generativeai import types

from backend.app.agents.base import BaseAgent
from backend.app.config import settings


class GoogleAgent(BaseAgent):
    def __init__(self, agent_id: str, role: str, pseudonym: str, model_name: str) -> None:
        super().__init__(
            agent_id=agent_id,
            role=role,
            pseudonym=pseudonym,
            provider_name="google",
            model_name=model_name,
        )
        genai.configure(api_key=settings.GOOGLE_API_KEY)

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2048,
    ) -> dict[str, str | int | None]:
        start_ms = time.monotonic() * 1000

        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_prompt,
                generation_config=types.GenerationConfig(max_output_tokens=max_tokens),
            )

            response = await model.generate_content_async(user_prompt)

            latency_ms = int(time.monotonic() * 1000 - start_ms)
            # Join all text parts explicitly — response.text raises on multi-part responses
            # (e.g. Gemini 2.5 Flash thinking tokens produce a separate part before the answer)
            content = "".join(
                part.text
                for part in response.candidates[0].content.parts
                if hasattr(part, "text") and part.text
            )
            usage = response.usage_metadata
            token_usage = usage.total_token_count if usage else None

            return {
                "content": content,
                "token_usage": token_usage,
                "latency_ms": latency_ms,
            }

        except google.api_core.exceptions.GoogleAPIError as exc:
            return {
                "content": f"[Google API error: {exc}]",
                "token_usage": None,
                "latency_ms": None,
            }
