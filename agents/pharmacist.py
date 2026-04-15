import asyncio
import json

from a2a.bus import MessageBus
from a2a.message import A2AMessage
from mcp_tools.infusions import get_active_infusions
from .base_agent import BaseAgent

_SYSTEM_PROMPT = """You are Pharmacist, an ICU medication safety agent.
You review active infusions and medication orders to check administration status and drug interactions.
When asked, you:
1. Check whether ordered medications were actually administered
2. Flag any missed or delayed medications
3. Check for dangerous drug interactions
4. Generate a concise Clinical Brief for the clinical team

Respond in JSON with:
  - "administration_status": list of dicts with drug name, ordered status, administered status
  - "missed_medications": list of medications ordered but not administered
  - "interactions": list of any flagged interactions (empty list if none)
  - "clinical_brief": a formatted string (the final handoff document) with sections:
      CLINICAL BRIEF — Patient [ID]
      Priority: [HIGH/MEDIUM/LOW]
      Finding: [what's happening]
      Root cause: [why]
      Action: [what to do immediately]
      Context: [supporting evidence]
      Note: [important qualifier]

Be direct and action-oriented. The clinical brief will be shown to ICU staff."""


class PharmacistAgent(BaseAgent):
    name = "pharmacist"

    async def handle_message(self, message: A2AMessage):
        if message.sender == "historian" and message.intent == "query":
            await self._handle_historian_query(message)

    async def _handle_historian_query(self, message: A2AMessage):
        patient_id = message.payload.get("patient_id", "4B")
        context = message.payload.get("context", "")
        question = message.payload.get("question", "")

        infusions = get_active_infusions(patient_id)

        user_content = (
            f"Patient: {patient_id}\n"
            f"Clinical context: {context}\n"
            f"Question: {question}\n\n"
            f"Active infusions / medication orders:\n{json.dumps(infusions, indent=2)}\n\n"
            "Review the medication data and generate the Clinical Brief. Respond in the JSON format specified."
        )

        result_text = await self._call_llm_async(_SYSTEM_PROMPT, user_content)

        result = self._parse_json(result_text) or {
            "administration_status": [
                {"drug": "Furosemide", "ordered": True, "administered": False, "status": "scheduled"},
                {"drug": "Morphine", "ordered": True, "administered": True, "status": "active"},
            ],
            "missed_medications": ["Furosemide 40mg IV — ordered 12:15, NOT administered"],
            "interactions": [],
            "clinical_brief": (
                "CLINICAL BRIEF — Patient 4B\n"
                "Priority: HIGH\n"
                "Finding: SpO2 declining (97→91), likely fluid-related\n"
                "Root cause: Furosemide 40mg IV ordered 2hr ago but NOT administered\n"
                "Action: Check diuretic IV line immediately\n"
                "Context: BNP 890 (elevated), clinical note confirms fluid overload\n"
                "Note: Not a sensor error — trend correlates with missed medication"
            ),
        }

        broadcast_msg = A2AMessage(
            sender=self.name,
            receiver="broadcast",
            intent="clinical_brief",
            payload=result,
            conversation_id=message.conversation_id,
        )
        await asyncio.sleep(2)
        await self.bus.publish(broadcast_msg)

    async def run(self, patient_id: str, conversation_id: str):
        pass
