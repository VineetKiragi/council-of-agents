from abc import ABC, abstractmethod


class BaseAgent(ABC):
    def __init__(
        self,
        agent_id: str,
        role: str,
        pseudonym: str,
        provider_name: str,
        model_name: str,
    ) -> None:
        self.agent_id = agent_id
        self.role = role
        self.pseudonym = pseudonym
        self.provider_name = provider_name
        self.model_name = model_name

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, str | int | None]:
        """Call the LLM and return the response.

        Returns:
            {
                "content": str,
                "token_usage": int | None,
                "latency_ms": int | None,
            }
        """

    def get_info(self) -> dict[str, str]:
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "pseudonym": self.pseudonym,
            "provider_name": self.provider_name,
            "model_name": self.model_name,
        }
