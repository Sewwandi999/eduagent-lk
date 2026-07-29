from pathlib import Path

from src.rag import HashingEmbedder, KnowledgeBase


def test_grade_filtered_retrieval(tmp_path: Path):
    (tmp_path / "grade9").mkdir()
    (tmp_path / "grade10").mkdir()
    (tmp_path / "grade9" / "reported_speech.md").write_text(
        "# Grade 9 Reported Speech\nReported speech transforms direct statements and changes pronouns and tense. " * 5,
        encoding="utf-8",
    )
    (tmp_path / "grade10" / "formal_letter.md").write_text(
        "# Grade 10 Formal Letter\nFormal letters use addresses, salutations, paragraphs and a formal closing. " * 5,
        encoding="utf-8",
    )
    kb = KnowledgeBase(tmp_path, "test", embedder=HashingEmbedder()).build()
    results = kb.search("reported speech tense changes", top_k=2, grade=9)
    assert results
    assert all(item.grade in {9, None} for item in results)
    assert "reported" in results[0].text.lower()
