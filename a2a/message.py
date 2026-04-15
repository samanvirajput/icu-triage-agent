from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class A2AMessage:
    sender: str           # "sentry", "historian", "pharmacist"
    receiver: str         # target agent name or "broadcast"
    intent: str           # "alert", "query", "response", "clinical_brief"
    payload: dict         # flexible content
    timestamp: datetime = field(default_factory=datetime.now)
    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> dict:
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "intent": self.intent,
            "payload": self.payload,
            "timestamp": self.timestamp.strftime("%H:%M:%S"),
            "conversation_id": self.conversation_id,
        }
