from pathlib import Path

from src.config import Settings
from src.orchestrator import EduAgentOrchestrator
from src.rag import HashingEmbedder, KnowledgeBase
from src.schemas import OutputType, StudentLevel, TeacherRequest


def test_offline_workflow(tmp_path: Path):
    grade_dir = tmp_path / "grade9"
    grade_dir.mkdir()
    (grade_dir / "reported_speech.md").write_text(
        "# Grade 9 Reported Speech\nUse direct and reported speech examples, tense changes, pronouns, classroom practice, differentiation and assessment. " * 10,
        encoding="utf-8",
    )
    kb = KnowledgeBase(tmp_path, "test", embedder=HashingEmbedder()).build()
    settings = Settings(
        groq_api_key="",
        openrouter_api_key="",
        fast_provider="groq",
        fast_model="llama-3.1-8b-instant",
        reasoning_provider="groq",
        reasoning_model="openai/gpt-oss-120b",
        review_provider="groq",
        review_model="llama-3.1-8b-instant",
        embedding_model="test",
        top_k=3,
        max_revision_loops=1,
        offline_demo=True,
    )
    request = TeacherRequest(
        grade=9,
        topic="Reported Speech",
        duration_minutes=45,
        student_level=StudentLevel.AVERAGE,
        output_type=OutputType.LESSON_PLAN,
    )
    result = EduAgentOrchestrator(settings, kb).run(request)
    assert "Answer Key" in result.draft.markdown
    assert result.messages
    assert result.review.average_score >= 3
