from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import KNOWLEDGE_DIR, VECTOR_DIR, get_settings
from src.rag import KnowledgeBase


def main() -> None:
    settings = get_settings()
    kb = KnowledgeBase(KNOWLEDGE_DIR, settings.embedding_model).build()
    manifest = VECTOR_DIR / "manifest.json"
    kb.save_manifest(manifest)
    print(f"Documents: {len(set(chunk.source for chunk in kb.chunks))}")
    print(f"Chunks: {len(kb.chunks)}")
    print(f"Manifest: {manifest}")


if __name__ == "__main__":
    main()
