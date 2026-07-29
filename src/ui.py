from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Iterable

import streamlit as st

from src.config import Settings
from src.schemas import AgentMessage, ReviewReport, TeacherRequest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STYLE_PATH = PROJECT_ROOT / "assets" / "styles.css"


def inject_styles() -> None:
    """Load the local design system into the Streamlit application."""
    if STYLE_PATH.exists():
        st.markdown(f"<style>{STYLE_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def render_brand() -> None:
    st.markdown(
        """
        <div class="brand-lockup">
            <div class="brand-mark">E</div>
            <div>
                <div class="brand-name">EduAgent LK</div>
                <div class="brand-subtitle">Teacher workspace</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(settings: Settings, document_count: int) -> None:
    with st.sidebar:
        render_brand()
        st.markdown(
            """
            <div class="sidebar-intro">
                Plan lessons, create assessments and review teaching material with a coordinated AI agent team.
            </div>
            """,
            unsafe_allow_html=True,
        )

        api_ready = settings.offline_demo or (
            settings.has_fast_key and settings.has_reasoning_key
        )
        status_class = "status-ready" if api_ready else "status-warning"
        status_label = "Demo mode active" if settings.offline_demo else (
            "AI services ready" if api_ready else "API key required"
        )
        status_icon = "●"
        st.markdown(
            f"""
            <div class="sidebar-section-label">SYSTEM STATUS</div>
            <div class="system-status {status_class}">
                <span>{status_icon}</span>
                <span>{html.escape(status_label)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="sidebar-stat-grid">
                <div class="sidebar-stat"><strong>{document_count}</strong><span>Knowledge docs</span></div>
                <div class="sidebar-stat"><strong>4</strong><span>AI agents</span></div>
                <div class="sidebar-stat"><strong>5</strong><span>Design patterns</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("Model configuration", expanded=False):
            st.caption("Fast routing and review")
            st.code(f"{settings.fast_provider}:{settings.fast_model}", language=None)
            st.caption("Lesson generation")
            st.code(
                f"{settings.reasoning_provider}:{settings.reasoning_model}",
                language=None,
            )
            st.caption("Embeddings")
            st.code(settings.embedding_model, language=None)

        st.markdown('<div class="sidebar-section-label">AGENT WORKFLOW</div>', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="mini-flow">
                <div><span>01</span><p><b>Route</b><small>Understand the request</small></p></div>
                <div><span>02</span><p><b>Retrieve</b><small>Search curriculum knowledge</small></p></div>
                <div><span>03</span><p><b>Plan</b><small>Create teaching material</small></p></div>
                <div><span>04</span><p><b>Review</b><small>Check and improve quality</small></p></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="sidebar-footer">
                <span>IT41043 · Agentic AI</span>
                <small>Built for Sri Lankan Grade 9–10 English education</small>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_hero(document_count: int) -> None:
    st.markdown(
        f"""
        <section class="hero-panel">
            <div class="hero-copy">
                <div class="eyebrow"><span></span> AI-POWERED TEACHING WORKSPACE</div>
                <h1>Design better English lessons<br><em>in minutes, not hours.</em></h1>
                <p>Generate curriculum-grounded lesson plans, worksheets, quizzes and revision papers for Sri Lankan Grade 9 and 10 classrooms.</p>
                <div class="hero-tags">
                    <span>✓ Curriculum-grounded</span>
                    <span>✓ Multi-agent review</span>
                    <span>✓ Ready to download</span>
                </div>
            </div>
            <div class="hero-visual" aria-hidden="true">
                <div class="orbit orbit-one"></div>
                <div class="orbit orbit-two"></div>
                <div class="agent-core">AI</div>
                <div class="floating-card card-route"><b>Router</b><small>Intent detected</small></div>
                <div class="floating-card card-rag"><b>RAG</b><small>{document_count} sources</small></div>
                <div class="floating-card card-review"><b>Review</b><small>Quality checked</small></div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_section_heading(kicker: str, title: str, description: str) -> None:
    st.markdown(
        f"""
        <div class="section-heading">
            <div class="section-kicker">{html.escape(kicker)}</div>
            <h2>{html.escape(title)}</h2>
            <p>{html.escape(description)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_workflow_preview() -> None:
    st.markdown(
        """
        <div class="workflow-card">
            <div class="workflow-card-head">
                <div>
                    <span class="card-kicker">WHAT HAPPENS NEXT</span>
                    <h3>Your AI teaching team</h3>
                </div>
                <div class="live-pill"><span></span> Ready</div>
            </div>
            <div class="workflow-step active">
                <div class="step-icon">01</div>
                <div><b>Router Agent</b><p>Classifies your output type and task complexity.</p></div>
            </div>
            <div class="workflow-line"></div>
            <div class="workflow-step">
                <div class="step-icon">02</div>
                <div><b>Curriculum Agent</b><p>Finds grade-specific guidance from the knowledge base.</p></div>
            </div>
            <div class="workflow-line"></div>
            <div class="workflow-step">
                <div class="step-icon">03</div>
                <div><b>Lesson Planning Agent</b><p>Builds objectives, activities, assessment and answers.</p></div>
            </div>
            <div class="workflow-line"></div>
            <div class="workflow-step">
                <div class="step-icon">04</div>
                <div><b>Review Agent</b><p>Scores quality and requests a revision when needed.</p></div>
            </div>
            <div class="workflow-note">Every run includes an auditable structured message trace.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_result_header(request: TeacherRequest, title: str, score: float, revision: int) -> None:
    escaped_title = html.escape(title)
    score_class = "score-high" if score >= 4 else "score-mid" if score >= 3 else "score-low"
    st.markdown(
        f"""
        <div class="result-header">
            <div class="result-title-wrap">
                <div class="success-check">✓</div>
                <div>
                    <span class="result-eyebrow">GENERATION COMPLETE</span>
                    <h2>{escaped_title}</h2>
                    <div class="result-chips">
                        <span>Grade {request.grade}</span>
                        <span>{html.escape(request.output_type.value)}</span>
                        <span>{request.duration_minutes} minutes</span>
                        <span>{html.escape(request.student_level.value)}</span>
                    </div>
                </div>
            </div>
            <div class="result-score {score_class}">
                <strong>{score:.1f}</strong><span>/ 5 quality</span><small>{revision} revision{'' if revision == 1 else 's'}</small>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_review_cards(report: ReviewReport) -> None:
    metrics = [
        ("Grade fit", report.grade_suitability, "Target level"),
        ("Grammar", report.grammar_accuracy, "Language accuracy"),
        ("Clarity", report.instruction_clarity, "Teacher directions"),
        ("Alignment", report.syllabus_alignment, "Curriculum match"),
        ("Answer key", report.answer_key_quality, "Assessment support"),
    ]
    cards = []
    for label, value, note in metrics:
        tone = "excellent" if value >= 4 else "average" if value == 3 else "attention"
        cards.append(
            f"""
            <div class="quality-card {tone}">
                <div class="quality-top"><span>{html.escape(label)}</span><strong>{value}/5</strong></div>
                <div class="quality-track"><i style="width:{value * 20}%"></i></div>
                <small>{html.escape(note)}</small>
            </div>
            """
        )
    st.markdown(f'<div class="quality-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def render_message_timeline(messages: Iterable[AgentMessage]) -> None:
    for index, message in enumerate(messages, start=1):
        payload_preview = json.dumps(message.payload, ensure_ascii=False, indent=2)
        with st.expander(
            f"{index:02d}  {message.sender}  →  {message.receiver}   ·   {message.performative.title()}",
            expanded=False,
        ):
            st.caption(f"Timestamp: {message.timestamp}  |  Task: {message.task_id}")
            st.code(payload_preview, language="json")


def safe_filename(value: str) -> str:
    cleaned = "".join(character.lower() if character.isalnum() else "_" for character in value)
    return "_".join(filter(None, cleaned.split("_"))) or "teaching_material"
