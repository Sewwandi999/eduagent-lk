from __future__ import annotations

from src.schemas import AgentMessage


class BaseAgent:
    def __init__(self, name: str, message_log: list[AgentMessage]):
        self.name = name
        self.message_log = message_log

    def send(self, receiver: str, performative: str, task_id: str, **payload) -> AgentMessage:
        message = AgentMessage(
            sender=self.name,
            receiver=receiver,
            performative=performative,
            task_id=task_id,
            payload=payload,
        )
        self.message_log.append(message)
        return message
