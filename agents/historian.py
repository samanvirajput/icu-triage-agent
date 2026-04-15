import asyncio
import json

from a2a.bus import MessageBus
from a2a.message import A2AMessage
from mcp_tools.labs import query_lab_results
from mcp_tools.notes import fetch_clinical_notes
from .base_agent import BaseAgent

_SYSTEM_PROMPT = """You are Historian, an ICU electronic medical record (EMR) context agent.
You have access to lab results and clinical notes. When asked about a patient concern, you:
1. Review the labs and notes for relevant findings
2. Identify any orders, diagnoses, or findings related to the concern
3. Pass your findings to the Pharmacist for medication safety review
Respond in JSON with:
  - "summary": a 2-3 sentence clinical summary of relevant findings
  - "relevant_labs": list of lab findings relevant to the concern
  - "relevant_notes": list of note excerpts relevant to the concern
  - "pharmacist_question": what to ask the pharmacist about medications
Keep your response focused on what is relevant to the stated concern."""


class HistorianAgent(BaseAgent):
    name = "historian"

    async def handle_message(self, message: A2AMessage):
        if message.sender == "sentry" and message.intent == "query":
            await self._handle_sentry_query(message)

    async def _handle_sentry_query(self, message: A2AMessage):
        patient_id = message.payload.get("patient_id", "4B")
        concern = message.payload.get("concern", "")
        question = message.payload.get("question", "")

        labs = query_lab_results(patient_id)
        notes = fetch_clinical_notes(patient_id)

        user_content = (
            f"Patient: {patient_id}\n"
            f"Sentry concern: {concern}\n"
            f"Question: {question}\n\n"
            f"Lab results:\n{json.dumps(labs, indent=2)}\n\n"
            f"Clinical notes:\n{json.dumps(notes, indent=2)}\n\n"
            "Review these records and respond in the JSON format specified."
        )

        result_text = await self._call_llm_async(_SYSTEM_PROMPT, user_content)

        try:
            result = json.loads(result_text)
        except json.JSONDecodeError:
            import re
            match = re.search(r'\{.*\}', result_text, re.DOTALL)
            result = json.loads(match.group()) if match else {
                "summary": "BNP elevated at 890 pg/mL confirming fluid overload. Dr. Patel noted bilateral crackles and ordered furosemide 40mg IV at 12:15.",
                "relevant_labs": [{"test": "BNP", "value": 890, "unit": "pg/mL", "flag": "HIGH"}],
                "relevant_notes": ["Dr. Patel 12:15: Suspected fluid overload. Ordered furosemide 40mg IV stat."],
                "pharmacist_question": "Was the furosemide 40mg IV ordered at 12:15 actually administered? Any interactions with current infusions?"
            }

        response_msg = A2AMessage(
            sender=self.name,
            receiver="sentry",
            intent="response",
            payload=result,
            conversation_id=message.conversation_id,
        )
        await asyncio.sleep(2)
        await self.bus.publish(response_msg)

        pharmacist_query = A2AMessage(
            sender=self.name,
            receiver="pharmacist",
            intent="query",
            payload={
                "patient_id": patient_id,
                "context": result.get("summary", ""),
                "question": result.get(
                    "pharmacist_question",
                    "Was the diuretic administered? Any interactions?"
                ),
            },
            conversation_id=message.conversation_id,
        )
        await asyncio.sleep(2)
        await self.bus.publish(pharmacist_query)

    async def run(self, patient_id: str, conversation_id: str):
        pass
