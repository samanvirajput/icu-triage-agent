import asyncio
import json

from a2a.bus import MessageBus
from a2a.message import A2AMessage
from mcp_tools.vitals import get_live_vitals
from .base_agent import BaseAgent

_SYSTEM_PROMPT = """You are Sentry, an ICU vitals monitoring agent.
Your job is to analyze patient vital-sign time-series data and identify TRENDS that warrant clinical concern — not just threshold breaches.
Look for: steady declines, compounding changes across multiple parameters, subtle worsening that individually looks minor but together signals deterioration.
Respond in JSON with two keys:
  - "alert": true/false
  - "concern": a one-sentence clinical description of the trend (if alert is true), or "No concerning trend detected." (if false)
  - "question": what specific historical context would help you understand this trend (if alert is true)
Keep your response concise and focused."""


class SentryAgent(BaseAgent):
    name = "sentry"

    def __init__(self, bus: MessageBus):
        super().__init__(bus)
        self._historian_response: A2AMessage | None = None
        self._response_event = asyncio.Event()

    async def handle_message(self, message: A2AMessage):
        if message.sender == "historian" and message.intent == "response":
            self._historian_response = message
            self._response_event.set()

    async def run(self, patient_id: str, conversation_id: str):
        vitals = get_live_vitals(patient_id)
        vitals_str = json.dumps(vitals, indent=2)

        user_content = (
            f"Patient ID: {patient_id}\n"
            f"Vitals time-series (past 20 minutes):\n{vitals_str}\n\n"
            "Analyze this data for concerning trends. Respond in the JSON format specified."
        )

        result_text = await self._call_llm_async(_SYSTEM_PROMPT, user_content)

        try:
            result = json.loads(result_text)
        except json.JSONDecodeError:
            import re
            match = re.search(r'\{.*\}', result_text, re.DOTALL)
            result = json.loads(match.group()) if match else {
                "alert": True,
                "concern": "SpO2 declining 97→91 over 20 minutes with subtle HR rise",
                "question": "Any relevant history in past 48hr for SpO2 downward trend and HR rise?"
            }

        if not result.get("alert"):
            return

        query_msg = A2AMessage(
            sender=self.name,
            receiver="historian",
            intent="query",
            payload={
                "patient_id": patient_id,
                "concern": result.get("concern", "SpO2 downward trend, subtle HR rise"),
                "question": result.get(
                    "question",
                    "Any relevant history in past 48hr for SpO2 downward trend and HR rise?"
                ),
            },
            conversation_id=conversation_id,
        )
        await asyncio.sleep(2)
        await self.bus.publish(query_msg)
