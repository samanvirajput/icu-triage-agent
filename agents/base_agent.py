import asyncio
import os
from abc import ABC, abstractmethod
from openai import OpenAI

from a2a.bus import MessageBus
from a2a.message import A2AMessage


class BaseAgent(ABC):
    """Abstract base class for all ICU triage agents."""

    name: str = "base"

    def __init__(self, bus: MessageBus):
        self.bus = bus
        self._client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("GROQ_API_KEY"),
        )
        self._model = "llama-3.3-70b-versatile"
        bus.register(self.name, self.handle_message)

    def _call_llm(self, system_prompt: str, user_content: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()

    async def _call_llm_async(self, system_prompt: str, user_content: str) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._call_llm, system_prompt, user_content
        )

    @abstractmethod
    async def handle_message(self, message: A2AMessage):
        """Handle an incoming A2A message."""

    @abstractmethod
    async def run(self, patient_id: str, conversation_id: str):
        """Entry point — kick off this agent's primary task."""
