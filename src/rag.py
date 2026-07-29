from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol

import numpy as np
from pypdf import PdfReader

from src.schemas import RetrievedChunk


class Embedder(Protocol):
    def encode(self, texts: list[str]) -> np.ndarray: ...


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)

    def encode(self, texts: list[str]) -> np.ndarray:
        vectors = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(vectors, dtype="float32")


class HashingEmbedder:
    """Deterministic lightweight fallback used by tests and offline demos."""

    def __init__(self, dimensions: int = 384):
        self.dimensions = dimensions

    def encode(self, texts: list[str]) -> np.ndarray:
        rows: list[np.ndarray] = []
        for text in texts:
            vector = np.zeros(self.dimensions, dtype="float32")
            for token in re.findall(r"[a-zA-Z0-9']+", text.lower()):
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                index = int.from_bytes(digest[:4], "big") % self.dimensions
                sign = 1.0 if digest[4] % 2 == 0 else -1.0
                vector[index] += sign
            norm = np.linalg.norm(vector)
            rows.append(vector / norm if norm else vector)
        return np.vstack(rows)


@dataclass
class RawDocument:
    text: str
    source: str
    grade: int | None
    topic: str | None


@dataclass
class ChunkRecord:
    text: str
    source: str
    grade: int | None
    topic: str | None
    chunk_id: str


class KnowledgeBase:
    def __init__(
        self,
        knowledge_dir: Path,
        embedding_model: str,
        embedder: Embedder | None = None,
    ):
        self.knowledge_dir = Path(knowledge_dir)
        self.embedding_model = embedding_model
        self.embedder = embedder
        self.chunks: list[ChunkRecord] = []
        self.embeddings: np.ndarray | None = None
        self._faiss_index = None

    @staticmethod
    def _infer_grade(path: Path, text: str) -> int | None:
        haystack = f"{path.as_posix()} {text[:300]}".lower()
        if "grade 9" in haystack or "grade9" in haystack:
            return 9
        if "grade 10" in haystack or "grade10" in haystack:
            return 10
        return None

    @staticmethod
    def _infer_topic(path: Path) -> str:
        return path.stem.replace("_", " ").replace("-", " ").title()

    def load_documents(self) -> list[RawDocument]:
        documents: list[RawDocument] = []
        for path in sorted(self.knowledge_dir.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in {".md", ".txt", ".pdf"}:
                continue
            try:
                if path.suffix.lower() == ".pdf":
                    reader = PdfReader(str(path))
                    text = "\n".join(page.extract_text() or "" for page in reader.pages)
                else:
                    text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            text = text.strip()
            if len(text) < 80:
                continue
            documents.append(
                RawDocument(
                    text=text,
                    source=str(path.relative_to(self.knowledge_dir)),
                    grade=self._infer_grade(path, text),
                    topic=self._infer_topic(path),
                )
            )
        return documents

    @staticmethod
    def chunk_text(text: str, chunk_words: int = 320, overlap_words: int = 55) -> list[str]:
        words = text.split()
        if not words:
            return []
        chunks: list[str] = []
        step = max(1, chunk_words - overlap_words)
        for start in range(0, len(words), step):
            piece = words[start : start + chunk_words]
            if len(piece) < 35 and chunks:
                chunks[-1] = chunks[-1] + " " + " ".join(piece)
                break
            chunks.append(" ".join(piece))
            if start + chunk_words >= len(words):
                break
        return chunks

    def build(self) -> "KnowledgeBase":
        documents = self.load_documents()
        chunks: list[ChunkRecord] = []
        for document in documents:
            for index, text in enumerate(self.chunk_text(document.text)):
                chunks.append(
                    ChunkRecord(
                        text=text,
                        source=document.source,
                        grade=document.grade,
                        topic=document.topic,
                        chunk_id=f"{document.source}::chunk-{index}",
                    )
                )
        if not chunks:
            raise RuntimeError(f"No usable knowledge documents found in {self.knowledge_dir}")

        if self.embedder is None:
            try:
                self.embedder = SentenceTransformerEmbedder(self.embedding_model)
            except Exception:
                self.embedder = HashingEmbedder()

        embeddings = self.embedder.encode([chunk.text for chunk in chunks])
        self.chunks = chunks
        self.embeddings = embeddings.astype("float32")

        try:
            import faiss

            index = faiss.IndexFlatIP(self.embeddings.shape[1])
            index.add(self.embeddings)
            self._faiss_index = index
        except Exception:
            self._faiss_index = None
        return self

    def search(self, query: str, top_k: int = 5, grade: int | None = None) -> list[RetrievedChunk]:
        if self.embeddings is None or self.embedder is None:
            self.build()
        assert self.embeddings is not None
        query_vector = self.embedder.encode([query]).astype("float32")
        candidate_count = min(len(self.chunks), max(top_k * 6, 20))

        if self._faiss_index is not None:
            scores, indices = self._faiss_index.search(query_vector, candidate_count)
            pairs = list(zip(indices[0].tolist(), scores[0].tolist()))
        else:
            similarities = self.embeddings @ query_vector[0]
            indices = np.argsort(similarities)[::-1][:candidate_count]
            pairs = [(int(index), float(similarities[index])) for index in indices]

        results: list[RetrievedChunk] = []
        for index, score in pairs:
            if index < 0:
                continue
            chunk = self.chunks[index]
            if grade is not None and chunk.grade not in {grade, None}:
                continue
            results.append(
                RetrievedChunk(
                    text=chunk.text,
                    source=chunk.source,
                    grade=chunk.grade,
                    topic=chunk.topic,
                    score=round(float(score), 4),
                    chunk_id=chunk.chunk_id,
                )
            )
            if len(results) >= top_k:
                break
        return results

    def save_manifest(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "embedding_model": self.embedding_model,
            "document_count": len({chunk.source for chunk in self.chunks}),
            "chunk_count": len(self.chunks),
            "sources": sorted({chunk.source for chunk in self.chunks}),
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def mean_score(chunks: Iterable[RetrievedChunk]) -> float:
    values = [chunk.score for chunk in chunks]
    return sum(values) / len(values) if values else 0.0
