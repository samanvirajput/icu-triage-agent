import asyncio
from typing import Callable, Dict, List
from .message import A2AMessage


class MessageBus:
    """In-process async message bus. Agents register handlers; bus routes by receiver field."""

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._log: List[A2AMessage] = []

    def register(self, agent_name: str, handler: Callable[[A2AMessage], None]):
        if agent_name not in self._handlers:
            self._handlers[agent_name] = []
        self._handlers[agent_name].append(handler)

    async def publish(self, message: A2AMessage):
        self._log.append(message)
        targets = []

        if message.receiver == "broadcast":
            for name, handlers in self._handlers.items():
                if name != message.sender:
                    targets.extend(handlers)
        else:
            targets = self._handlers.get(message.receiver, [])

        for handler in targets:
            if asyncio.iscoroutinefunction(handler):
                await handler(message)
            else:
                handler(message)

    @property
    def log(self) -> List[A2AMessage]:
        return list(self._log)

    def clear(self):
        self._log.clear()
