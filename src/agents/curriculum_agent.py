from __future__ import annotations

from src.agents.base import BaseAgent
from src.rag import KnowledgeBase, mean_score
from src.schemas import CurriculumContext, TeacherRequest


class CurriculumAgent(BaseAgent):
    def __init__(self, knowledge_base: KnowledgeBase, top_k: int, message_log):
        super().__init__("CurriculumAgent", message_log)
        self.knowledge_base = knowledge_base
        self.top_k = top_k

    def retrieve(self, request: TeacherRequest) -> CurriculumContext:
        query = (
            f"Sri Lanka Grade {request.grade} English {request.topic} "
            f"learning outcomes teaching activities assessment {request.student_level.value}"
        )
        self.send("RAGTool", "request", request.task_id, query=query, grade=request.grade)
        chunks = self.knowledge_base.search(query, top_k=self.top_k, grade=request.grade)
        score = mean_score(chunks)
        self.send(
            "Orchestrator",
            "observation",
            request.task_id,
            retrieved_chunks=len(chunks),
            mean_similarity=round(score, 4),
            sources=[chunk.source for chunk in chunks],
        )

        if len(chunks) < min(3, self.top_k) or score < 0.12:
            retry_query = f"Grade {request.grade} {request.topic} grammar examples exercises classroom"
            self.send("RAGTool", "request", request.task_id, query=retry_query, retry=True)
            retry_chunks = self.knowledge_base.search(
                retry_query, top_k=self.top_k, grade=request.grade
            )
            by_id = {chunk.chunk_id: chunk for chunk in chunks + retry_chunks}
            chunks = sorted(by_id.values(), key=lambda item: item.score, reverse=True)[: self.top_k]
            query = f"{query} | retry: {retry_query}"
            score = mean_score(chunks)

        context = CurriculumContext(
            query=query,
            chunks=chunks,
            retrieval_notes=(
                f"Retrieved {len(chunks)} chunks. Mean similarity: {score:.3f}. "
                "The planner must ground claims in these passages and label sources."
            ),
            sufficient=len(chunks) >= 3,
        )
        self.send(
            "LessonPlanningAgent",
            "inform",
            request.task_id,
            curriculum=context.model_dump(),
        )
        return context
