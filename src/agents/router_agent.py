from __future__ import annotations

from src.agents.base import BaseAgent
from src.config import Settings
from src.llm_clients import ChatClient, LLMUnavailableError
from src.prompts import ROUTER_SYSTEM, router_user
from src.schemas import RouteDecision, TeacherRequest
from src.utils import extract_json


class RouterAgent(BaseAgent):
    def __init__(self, settings: Settings, client: ChatClient, message_log):
        super().__init__("RouterAgent", message_log)
        self.settings = settings
        self.client = client

    def route(self, request: TeacherRequest) -> RouteDecision:
        try:
            if self.settings.offline_demo:
                raise LLMUnavailableError("Offline demo enabled")
            response = self.client.complete(
                provider=self.settings.fast_provider,
                model=self.settings.fast_model,
                messages=[
                    {"role": "system", "content": ROUTER_SYSTEM},
                    {"role": "user", "content": router_user(request)},
                ],
                temperature=0.0,
                max_tokens=300,
                json_mode=True,
            )
            decision = RouteDecision(**extract_json(response.content))
        except Exception:
            route_map = {
                "Lesson Plan": "lesson_plan",
                "Worksheet": "worksheet",
                "Quiz": "quiz",
                "Revision Paper": "revision_paper",
            }
            complexity = "complex" if request.output_type.value == "Revision Paper" else "standard"
            decision = RouteDecision(
                route=route_map[request.output_type.value],
                requires_rag=True,
                complexity=complexity,
                reason="Deterministic fallback based on the selected output type.",
            )
        self.send("Orchestrator", "result", request.task_id, route=decision.model_dump())
        return decision
