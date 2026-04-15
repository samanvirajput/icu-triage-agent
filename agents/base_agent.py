import asyncio
import json
import os
import re
from abc import ABC, abstractmethod
from openai import OpenAI

from a2a.bus import MessageBus
from a2a.message import A2AMessage


def _escape_control_chars(s: str) -> str:
    """Escape literal control characters inside JSON string values.

    LLMs frequently emit multi-line strings with bare newlines, which are
    invalid JSON.  This walks the raw text char-by-char, tracks whether we
    are inside a JSON string, and replaces any control character (< 0x20)
    found there with its proper escape sequence.
    """
    result = []
    in_string = False
    escape_next = False
    for char in s:
        if escape_next:
            result.append(char)
            escape_next = False
        elif char == "\\":
            result.append(char)
            escape_next = True
        elif char == '"':
            result.append(char)
            in_string = not in_string
        elif in_string and ord(char) < 0x20:
            if char == "\n":
                result.append("\\n")
            elif char == "\r":
                result.append("\\r")
            elif char == "\t":
                result.append("\\t")
            else:
                result.append(f"\\u{ord(char):04x}")
        else:
            result.append(char)
    return "".join(result)


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

    def _parse_json(self, text: str) -> dict | None:
        """Robustly parse a JSON dict from raw LLM output.

        Tries in order:
        1. Direct json.loads (fast path — works when LLM is well-behaved)
        2. Extract the first {...} block, then json.loads
        3. Same block after escaping bare control characters inside strings
        Returns None if all three attempts fail.
        """
        # 1. Direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 2. Extract {...} block
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return None
        extracted = match.group()

        try:
            return json.loads(extracted)
        except json.JSONDecodeError:
            pass

        # 3. Fix bare control characters inside strings, then retry
        try:
            return json.loads(_escape_control_chars(extracted))
        except json.JSONDecodeError:
            return None

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
