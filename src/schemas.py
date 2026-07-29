from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class OutputType(str, Enum):
    LESSON_PLAN = "Lesson Plan"
    WORKSHEET = "Worksheet"
    QUIZ = "Quiz"
    REVISION_PAPER = "Revision Paper"


class StudentLevel(str, Enum):
    SUPPORT_NEEDED = "Needs Support"
    AVERAGE = "Average"
    ADVANCED = "Advanced"
    MIXED = "Mixed Ability"


class TeacherRequest(BaseModel):
    grade: Literal[9, 10]
    topic: str = Field(min_length=2, max_length=120)
    duration_minutes: int = Field(ge=20, le=120)
    student_level: StudentLevel
    output_type: OutputType
    extra_instructions: str = Field(default="", max_length=800)
    task_id: str = Field(default_factory=lambda: str(uuid4()))


class AgentMessage(BaseModel):
    sender: str
    receiver: str
    performative: Literal[
        "request", "inform", "result", "critique", "revise", "error", "observation"
    ]
    task_id: str
    payload: dict[str, Any]
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )


class RouteDecision(BaseModel):
    route: Literal["lesson_plan", "worksheet", "quiz", "revision_paper"]
    requires_rag: bool = True
    complexity: Literal["simple", "standard", "complex"] = "standard"
    reason: str


class RetrievedChunk(BaseModel):
    text: str
    source: str
    grade: int | None = None
    topic: str | None = None
    score: float
    chunk_id: str


class CurriculumContext(BaseModel):
    query: str
    chunks: list[RetrievedChunk]
    retrieval_notes: str
    sufficient: bool


class LessonDraft(BaseModel):
    title: str
    markdown: str
    sections: list[str]
    model_used: str
    revision_number: int = 0


class ReviewReport(BaseModel):
    grade_suitability: int = Field(ge=1, le=5)
    grammar_accuracy: int = Field(ge=1, le=5)
    instruction_clarity: int = Field(ge=1, le=5)
    syllabus_alignment: int = Field(ge=1, le=5)
    answer_key_quality: int = Field(ge=1, le=5)
    strengths: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
    revision_required: bool
    revision_instructions: list[str] = Field(default_factory=list)
    model_used: str

    @property
    def average_score(self) -> float:
        values = [
            self.grade_suitability,
            self.grammar_accuracy,
            self.instruction_clarity,
            self.syllabus_alignment,
            self.answer_key_quality,
        ]
        return round(sum(values) / len(values), 2)


class WorkflowResult(BaseModel):
    request: TeacherRequest
    route: RouteDecision
    curriculum: CurriculumContext
    draft: LessonDraft
    review: ReviewReport
    messages: list[AgentMessage]
