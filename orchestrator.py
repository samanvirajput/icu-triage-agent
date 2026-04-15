import asyncio
import uuid
from typing import Callable

from a2a.bus import MessageBus
from a2a.message import A2AMessage
from agents.sentry import SentryAgent
from agents.historian import HistorianAgent
from agents.pharmacist import PharmacistAgent


class Orchestrator:
    """Manages agent lifecycle and the shared message bus."""

    def __init__(self, on_message: Callable[[A2AMessage], None] | None = None):
        self.bus = MessageBus()
        self._on_message = on_message

        if on_message:
            for agent_name in ["sentry", "historian", "pharmacist", "broadcast"]:
                self.bus.register(agent_name, self._intercept_message)

        self.sentry = SentryAgent(self.bus)
        self.historian = HistorianAgent(self.bus)
        self.pharmacist = PharmacistAgent(self.bus)

        self._clinical_brief: dict | None = None
        self.bus.register("broadcast", self._capture_brief)

    async def _intercept_message(self, message: A2AMessage):
        if self._on_message:
            self._on_message(message)

    async def _capture_brief(self, message: A2AMessage):
        if message.intent == "clinical_brief":
            self._clinical_brief = message.payload

    async def run_triage(self, patient_id: str = "4B") -> dict:
        self.bus.clear()
        self._clinical_brief = None
        conversation_id = str(uuid.uuid4())[:8]

        await self.sentry.run(patient_id, conversation_id)

        timeout = 60
        elapsed = 0
        while self._clinical_brief is None and elapsed < timeout:
            await asyncio.sleep(0.5)
            elapsed += 0.5

        return {
            "messages": [m.to_dict() for m in self.bus.log],
            "clinical_brief": self._clinical_brief,
        }
