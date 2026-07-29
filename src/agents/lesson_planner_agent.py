from __future__ import annotations

import re

from src.agents.base import BaseAgent
from src.config import Settings
from src.llm_clients import ChatClient, LLMUnavailableError
from src.prompts import PLANNER_SYSTEM, planner_user, revision_user
from src.schemas import CurriculumContext, LessonDraft, ReviewReport, TeacherRequest


class LessonPlanningAgent(BaseAgent):
    def __init__(self, settings: Settings, client: ChatClient, message_log):
        super().__init__("LessonPlanningAgent", message_log)
        self.settings = settings
        self.client = client

    @staticmethod
    def _sections(markdown: str) -> list[str]:
        return [match.strip() for match in re.findall(r"^##\s+(.+)$", markdown, flags=re.MULTILINE)]

    def _offline_draft(self, request: TeacherRequest, context: CurriculumContext) -> str:
        warmup = max(5, round(request.duration_minutes * 0.12))
        teaching = max(10, round(request.duration_minutes * 0.34))
        practice = max(8, round(request.duration_minutes * 0.28))
        assessment = request.duration_minutes - warmup - teaching - practice
        source_lines = "\n".join(
            f"- `{chunk.source}` — {chunk.topic or 'Curriculum note'}"
            for chunk in context.chunks
        )
        return f"""# Grade {request.grade} English: {request.topic}

## Overview
A {request.duration_minutes}-minute {request.output_type.value.lower()} for {request.student_level.value.lower()} Grade {request.grade} learners. The material uses retrieved curriculum notes and includes guided practice, independent work, and feedback.

## Learning Objectives
By the end of the session, students should be able to:
1. identify the main form and purpose of **{request.topic}**;
2. use the target language accurately in short examples;
3. apply the target language in a classroom task;
4. check and correct common errors.

## Prior Knowledge
Students should understand basic sentence structure, subjects, verbs, and punctuation.

## Materials
Board, markers, student notebooks, and printed question sheet.

## Lesson Sequence
### 1. Warm-up — {warmup} minutes
Write two short example sentences on the board. Ask students what changes between them and collect answers without correcting immediately.

### 2. Guided explanation — {teaching} minutes
Explain the form, meaning, and use of {request.topic}. Model three examples. Highlight word order, verb changes, punctuation, and common mistakes. Use one familiar Sri Lankan classroom situation in the examples.

### 3. Pair practice — {practice} minutes
Students work in pairs to complete six items. They compare answers and explain one correction to another pair.

### 4. Assessment and feedback — {assessment} minutes
Use an exit ticket with three items. Review one strong answer and one common error.

## Differentiation
- **Needs support:** provide sentence frames and a word bank.
- **Average:** complete the core task and explain one answer.
- **Advanced:** write two original examples and justify the grammar choice.

## Exercise
1. Rewrite or complete a sentence using {request.topic}.
2. Correct one grammatical error in a supplied sentence.
3. Choose the best answer from three options.
4. Join or transform two short sentences.
5. Write one original example about school life.
6. Explain why your answer to Question 3 is correct.

## Answer Key
1. Accept any grammatically correct response that uses the target form.
2. The corrected sentence must use the correct verb form, word order, and punctuation.
3. Award the mark for the option that follows the rule explained during guided teaching.
4. Accept a complete sentence with accurate linking or transformation.
5. Award for relevance and grammatical accuracy.
6. The explanation should name the rule and connect it to the selected answer.

## Homework
Write five original sentences using {request.topic}. Underline the target language and label the rule used in each sentence.

## Teacher Quality Check
Confirm that the examples match Grade {request.grade}, timings total {request.duration_minutes} minutes, instructions use simple verbs, and every closed question has a clear answer.

## Sources Used
{source_lines}
"""

    def create(self, request: TeacherRequest, context: CurriculumContext) -> LessonDraft:
        model_label = "offline-template"
        try:
            if self.settings.offline_demo:
                raise LLMUnavailableError("Offline demo enabled")
            response = self.client.complete(
                provider=self.settings.reasoning_provider,
                model=self.settings.reasoning_model,
                messages=[
                    {"role": "system", "content": PLANNER_SYSTEM},
                    {"role": "user", "content": planner_user(request, context)},
                ],
                temperature=0.25,
                max_tokens=4500,
            )
            markdown = response.content.strip()
            model_label = f"{response.provider}:{response.model}"
        except Exception:
            markdown = self._offline_draft(request, context)

        draft = LessonDraft(
            title=f"Grade {request.grade} {request.topic} — {request.output_type.value}",
            markdown=markdown,
            sections=self._sections(markdown),
            model_used=model_label,
        )
        self.send("ReviewAgent", "result", request.task_id, draft=draft.model_dump())
        return draft

    def revise(
        self,
        request: TeacherRequest,
        context: CurriculumContext,
        draft: LessonDraft,
        review: ReviewReport,
    ) -> LessonDraft:
        self.send(
            "LessonPlanningAgent",
            "revise",
            request.task_id,
            instructions=review.revision_instructions,
        )
        try:
            if self.settings.offline_demo:
                raise LLMUnavailableError("Offline demo enabled")
            response = self.client.complete(
                provider=self.settings.reasoning_provider,
                model=self.settings.reasoning_model,
                messages=[
                    {"role": "system", "content": PLANNER_SYSTEM},
                    {
                        "role": "user",
                        "content": revision_user(request, context, draft, review),
                    },
                ],
                temperature=0.2,
                max_tokens=4500,
            )
            markdown = response.content.strip()
            model_label = f"{response.provider}:{response.model}"
        except Exception:
            improvements = "\n".join(f"- {item}" for item in review.revision_instructions)
            markdown = (
                draft.markdown
                + "\n\n## Revision Notes Applied\n"
                + (improvements or "- Reviewed for clarity and completeness.")
            )
            model_label = "offline-template"
        return LessonDraft(
            title=draft.title,
            markdown=markdown,
            sections=self._sections(markdown),
            model_used=model_label,
            revision_number=draft.revision_number + 1,
        )
