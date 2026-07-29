from __future__ import annotations

from collections.abc import Callable

from src.agents.curriculum_agent import CurriculumAgent
from src.agents.lesson_planner_agent import LessonPlanningAgent
from src.agents.review_agent import ReviewAgent
from src.agents.router_agent import RouterAgent
from src.config import Settings
from src.llm_clients import ChatClient
from src.rag import KnowledgeBase
from src.schemas import AgentMessage, TeacherRequest, WorkflowResult


class EduAgentOrchestrator:
    """Orchestrator-worker workflow with routing, RAG tool use and reflection."""

    def __init__(self, settings: Settings, knowledge_base: KnowledgeBase):
        self.settings = settings
        self.messages: list[AgentMessage] = []
        client = ChatClient(settings)
        self.router = RouterAgent(settings, client, self.messages)
        self.curriculum = CurriculumAgent(knowledge_base, settings.top_k, self.messages)
        self.planner = LessonPlanningAgent(settings, client, self.messages)
        self.reviewer = ReviewAgent(settings, client, self.messages)

    def run(
        self,
        request: TeacherRequest,
        progress_callback: Callable[[str, str, int], None] | None = None,
    ) -> WorkflowResult:
        self.messages.clear()

        def progress(stage: str, detail: str, percent: int) -> None:
            if progress_callback is not None:
                progress_callback(stage, detail, percent)

        progress("Understanding your request", "The orchestrator is preparing the task for the Router Agent.", 8)
        self.messages.append(
            AgentMessage(
                sender="TeacherUI",
                receiver="Orchestrator",
                performative="request",
                task_id=request.task_id,
                payload=request.model_dump(mode="json"),
            )
        )
        self.messages.append(
            AgentMessage(
                sender="Orchestrator",
                receiver="RouterAgent",
                performative="request",
                task_id=request.task_id,
                payload={"request": request.model_dump(mode="json")},
            )
        )
        route = self.router.route(request)
        progress("Request routed", f"Route: {route.route.replace('_', ' ').title()} · Complexity: {route.complexity}.", 22)
        self.messages.append(
            AgentMessage(
                sender="Orchestrator",
                receiver="CurriculumAgent",
                performative="request",
                task_id=request.task_id,
                payload={"route": route.model_dump()},
            )
        )
        progress("Searching curriculum knowledge", "The Curriculum Agent is retrieving grade-specific teaching guidance.", 35)
        curriculum = self.curriculum.retrieve(request)
        progress("Curriculum context ready", f"Retrieved {len(curriculum.chunks)} relevant knowledge chunks.", 50)
        progress("Creating teaching material", "The Lesson Planning Agent is designing objectives, activities and assessment.", 62)
        draft = self.planner.create(request, curriculum)
        progress("Reviewing the first draft", "The Review Agent is checking grade fit, grammar, clarity and syllabus alignment.", 78)
        review = self.reviewer.review(request, curriculum, draft)

        loops = 0
        while review.revision_required and loops < self.settings.max_revision_loops:
            progress("Improving the draft", "The planner is applying the reviewer's revision instructions.", 86)
            self.messages.append(
                AgentMessage(
                    sender="Orchestrator",
                    receiver="LessonPlanningAgent",
                    performative="revise",
                    task_id=request.task_id,
                    payload={"revision_instructions": review.revision_instructions},
                )
            )
            draft = self.planner.revise(request, curriculum, draft, review)
            review = self.reviewer.review(request, curriculum, draft)
            loops += 1
            progress("Revision reviewed", f"Quality score after revision: {review.average_score}/5.", 94)

        self.messages.append(
            AgentMessage(
                sender="Orchestrator",
                receiver="TeacherUI",
                performative="result",
                task_id=request.task_id,
                payload={
                    "revision_count": draft.revision_number,
                    "quality_score": review.average_score,
                },
            )
        )
        progress("Finalising your resource", "The orchestrator is packaging the material, sources and audit trace.", 98)
        return WorkflowResult(
            request=request,
            route=route,
            curriculum=curriculum,
            draft=draft,
            review=review,
            messages=list(self.messages),
        )
