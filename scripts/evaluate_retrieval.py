from __future__ import annotations

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import KNOWLEDGE_DIR, get_settings
from src.rag import KnowledgeBase


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    queries = json.loads((root / "data" / "evaluation_queries.json").read_text(encoding="utf-8"))
    settings = get_settings()
    kb = KnowledgeBase(KNOWLEDGE_DIR, settings.embedding_model).build()
    results = []

    for item in queries:
        chunks = kb.search(item["query"], top_k=5, grade=item["grade"])
        combined = " ".join(chunk.text.lower() for chunk in chunks)
        hits = [term for term in item["expected_terms"] if term.lower() in combined]
        relevant = len(hits) >= max(1, len(item["expected_terms"]) - 1)
        results.append(
            {
                "query": item["query"],
                "grade": item["grade"],
                "top_sources": [chunk.source for chunk in chunks],
                "mean_score": round(sum(c.score for c in chunks) / max(len(chunks), 1), 4),
                "matched_terms": hits,
                "relevant": relevant,
                "comment": (
                    "Relevant: the retrieved text contains most expected concepts."
                    if relevant
                    else "Needs improvement: add or re-chunk documents for this topic."
                ),
            }
        )

    output = root / "data" / "retrieval_evaluation_results.json"
    output.write_text(json.dumps(results, indent=2), encoding="utf-8")
    for row in results:
        print(f"[{ 'PASS' if row['relevant'] else 'REVIEW' }] {row['query']} -> {row['mean_score']}")
    print(f"Saved: {output}")


if __name__ == "__main__":
    main()
