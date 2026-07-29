from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_DIR = PROJECT_ROOT / "data" / "knowledge_base"
VECTOR_DIR = PROJECT_ROOT / "data" / "vector_store"


def _secret_or_env(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value:
        return value
    try:
        import streamlit as st

        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return default


@dataclass(frozen=True)
class Settings:
    groq_api_key: str
    openrouter_api_key: str
    fast_provider: str
    fast_model: str
    reasoning_provider: str
    reasoning_model: str
    review_provider: str
    review_model: str
    embedding_model: str
    top_k: int
    max_revision_loops: int
    offline_demo: bool

    @property
    def has_fast_key(self) -> bool:
        return bool(
            self.groq_api_key if self.fast_provider == "groq" else self.openrouter_api_key
        )

    @property
    def has_reasoning_key(self) -> bool:
        return bool(
            self.groq_api_key
            if self.reasoning_provider == "groq"
            else self.openrouter_api_key
        )


def get_settings() -> Settings:
    return Settings(
        groq_api_key=_secret_or_env("GROQ_API_KEY"),
        openrouter_api_key=_secret_or_env("OPENROUTER_API_KEY"),
        fast_provider=_secret_or_env("FAST_PROVIDER", "groq").lower(),
        fast_model=_secret_or_env("FAST_MODEL", "llama-3.1-8b-instant"),
        reasoning_provider=_secret_or_env("REASONING_PROVIDER", "groq").lower(),
        reasoning_model=_secret_or_env("REASONING_MODEL", "openai/gpt-oss-120b"),
        review_provider=_secret_or_env("REVIEW_PROVIDER", "groq").lower(),
        review_model=_secret_or_env("REVIEW_MODEL", "llama-3.1-8b-instant"),
        embedding_model=_secret_or_env(
            "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        ),
        top_k=int(_secret_or_env("TOP_K", "5")),
        max_revision_loops=int(_secret_or_env("MAX_REVISION_LOOPS", "1")),
        offline_demo=_secret_or_env("OFFLINE_DEMO", "false").lower() in {"1", "true", "yes"},
    )
