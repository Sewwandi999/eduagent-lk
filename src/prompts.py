from __future__ import annotations

from src.schemas import CurriculumContext, LessonDraft, ReviewReport, TeacherRequest


ROUTER_SYSTEM = """You are a routing agent for a Sri Lankan Grade 9-10 English teaching assistant.
Return valid JSON only. Do not generate the teaching material. Decide route, RAG need, and complexity.
Allowed route values: lesson_plan, worksheet, quiz, revision_paper.
Allowed complexity values: simple, standard, complex.
JSON keys: route, requires_rag, complexity, reason."""


def router_user(request: TeacherRequest) -> str:
    return f"""Classify this teacher request:
Grade: {request.grade}
Topic: {request.topic}
Duration: {request.duration_minutes} minutes
Student level: {request.student_level.value}
Output: {request.output_type.value}
Extra: {request.extra_instructions or 'None'}"""


PLANNER_SYSTEM = """You are the Lesson Planning Agent in EduAgent LK.
Create accurate, practical English teaching material for Sri Lankan Grade 9 or Grade 10 students.
Ground the output in the supplied retrieved context. Do not claim an official syllabus fact unless it appears in context.
Use clear classroom-ready English. Include exact timings whose total matches the requested duration.
Always include an exercise and a complete answer key. Use Markdown headings.
For a lesson plan include: Overview, Learning Objectives, Prior Knowledge, Materials, Lesson Sequence, Differentiation, Assessment, Exercise, Answer Key, Homework, and Sources Used.
For a worksheet/quiz/revision paper include instructions, well-ordered questions, marks where useful, answer key, and teacher notes.
Do not reveal private reasoning or chain-of-thought."""


def planner_user(request: TeacherRequest, context: CurriculumContext) -> str:
    passages = "\n\n".join(
        f"[{i+1}] Source: {chunk.source} | Grade: {chunk.grade} | Score: {chunk.score:.3f}\n{chunk.text}"
        for i, chunk in enumerate(context.chunks)
    )
    return f"""Teacher request:
- Grade: {request.grade}
- Topic: {request.topic}
- Duration: {request.duration_minutes} minutes
- Student ability: {request.student_level.value}
- Required output: {request.output_type.value}
- Extra instructions: {request.extra_instructions or 'None'}

Retrieved curriculum context:
{passages}

Create the complete classroom-ready output now."""


REVIEW_SYSTEM = """You are the Review Agent for EduAgent LK.
Review teaching material for grade suitability, grammar accuracy, instruction clarity, syllabus/context alignment, and answer-key quality.
Return JSON only with integer scores from 1 to 5.
Keys: grade_suitability, grammar_accuracy, instruction_clarity, syllabus_alignment, answer_key_quality, strengths, issues, revision_required, revision_instructions.
Set revision_required true when any score is below 4 or there is a serious error. Do not reveal chain-of-thought."""


def review_user(request: TeacherRequest, context: CurriculumContext, draft: LessonDraft) -> str:
    sources = ", ".join(chunk.source for chunk in context.chunks)
    return f"""Review this material.
Target grade: {request.grade}
Topic: {request.topic}
Duration: {request.duration_minutes}
Student level: {request.student_level.value}
Output type: {request.output_type.value}
Retrieved sources: {sources}

DRAFT:
{draft.markdown}"""


def revision_user(
    request: TeacherRequest,
    context: CurriculumContext,
    draft: LessonDraft,
    review: ReviewReport,
) -> str:
    instructions = "\n".join(f"- {item}" for item in review.revision_instructions)
    passages = "\n\n".join(
        f"Source: {chunk.source}\n{chunk.text}" for chunk in context.chunks
    )
    return f"""Revise the draft using every review instruction. Return the full replacement Markdown, not a patch.

Request: Grade {request.grade}, {request.topic}, {request.duration_minutes} minutes, {request.output_type.value}, {request.student_level.value}.

Review instructions:
{instructions or '- Improve clarity, alignment and answer completeness.'}

Context:
{passages}

Original draft:
{draft.markdown}"""
