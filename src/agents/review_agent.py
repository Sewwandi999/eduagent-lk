from __future__ import annotations

from src.agents.base import BaseAgent
from src.config import Settings
from src.llm_clients import ChatClient, LLMUnavailableError
from src.prompts import REVIEW_SYSTEM, review_user
from src.schemas import CurriculumContext, LessonDraft, ReviewReport, TeacherRequest
from src.utils import extract_json


class ReviewAgent(BaseAgent):
    def __init__(self, settings: Settings, client: ChatClient, message_log):
        super().__init__("ReviewAgent", message_log)
        self.settings = settings
        self.client = client

    @staticmethod
    def _fallback_review(request: TeacherRequest, draft: LessonDraft) -> ReviewReport:
        required = ["learning objectives", "exercise", "answer key"]
        lower = draft.markdown.lower()
        missing = [item for item in required if item not in lower]
        timing_present = str(request.duration_minutes) in draft.markdown
        issues = [f"Missing required section: {item}." for item in missing]
        if not timing_present:
            issues.append("The requested total duration is not clearly stated.")
        score = 3 if issues else 4
        return ReviewReport(
            grade_suitability=4,
            grammar_accuracy=4,
            instruction_clarity=score,
            syllabus_alignment=4,
            answer_key_quality=3 if "answer key" not in lower else 4,
            strengths=[
                "The material follows a classroom-ready structure.",
                "The response includes retrieved-source references.",
            ],
            issues=issues,
            revision_required=bool(issues),
            revision_instructions=[f"Add or correct: {item}" for item in missing]
            + (["State and verify the total lesson time."] if not timing_present else []),
            model_used="offline-rule-review",
        )

    def review(
        self,
        request: TeacherRequest,
        context: CurriculumContext,
        draft: LessonDraft,
    ) -> ReviewReport:
        try:
            if self.settings.offline_demo:
                raise LLMUnavailableError("Offline demo enabled")
            response = self.client.complete(
                provider=self.settings.review_provider,
                model=self.settings.review_model,
                messages=[
                    {"role": "system", "content": REVIEW_SYSTEM},
                    {"role": "user", "content": review_user(request, context, draft)},
                ],
                temperature=0.0,
                max_tokens=900,
                json_mode=True,
            )
            payload = extract_json(response.content)
            payload["model_used"] = f"{response.provider}:{response.model}"
            report = ReviewReport(**payload)
        except Exception:
            report = self._fallback_review(request, draft)

        self.send(
            "Orchestrator",
            "critique",
            request.task_id,
            review=report.model_dump(),
            average_score=report.average_score,
        )
        return report
