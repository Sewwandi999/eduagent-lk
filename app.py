from __future__ import annotations

import json

import streamlit as st
from pydantic import ValidationError

from src.config import KNOWLEDGE_DIR, get_settings
from src.exporters import build_docx_bytes, build_pdf_bytes
from src.orchestrator import EduAgentOrchestrator
from src.rag import KnowledgeBase
from src.schemas import OutputType, StudentLevel, TeacherRequest, WorkflowResult
from src.ui import (
    inject_styles,
    render_hero,
    render_message_timeline,
    render_result_header,
    render_review_cards,
    render_section_heading,
    render_sidebar,
    render_workflow_preview,
    safe_filename,
)

st.set_page_config(
    page_title="EduAgent LK · AI Teaching Workspace",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "EduAgent LK is an agentic AI teaching assistant for Sri Lankan Grade 9–10 English teachers."
    },
)

inject_styles()


@st.cache_resource(show_spinner=False)
def load_knowledge_base(embedding_model: str) -> KnowledgeBase:
    return KnowledgeBase(KNOWLEDGE_DIR, embedding_model).build()


def message_rows(result: WorkflowResult) -> list[dict[str, str | int]]:
    rows: list[dict[str, str | int]] = []
    for index, message in enumerate(result.messages, start=1):
        payload = json.dumps(message.payload, ensure_ascii=False)
        rows.append(
            {
                "#": index,
                "Sender": message.sender,
                "Receiver": message.receiver,
                "Type": message.performative,
                "Payload preview": payload[:220] + ("..." if len(payload) > 220 else ""),
            }
        )
    return rows


def render_empty_state() -> None:
    st.markdown(
        """
        <div class="empty-state">
            <div class="empty-icon">✦</div>
            <strong>Your generated teaching material will appear here.</strong><br>
            Configure the class, enter a topic and let the agent team do the rest.
        </div>
        """,
        unsafe_allow_html=True,
    )


settings = get_settings()
document_count = len(list(KNOWLEDGE_DIR.rglob("*.md")))
render_sidebar(settings, document_count)
render_hero(document_count)

try:
    knowledge_base = load_knowledge_base(settings.embedding_model)
except Exception as exc:
    st.error(
        "The curriculum knowledge base could not be prepared. Check the embedding model "
        f"and project files, then restart the app. Technical detail: {exc}"
    )
    st.stop()

render_section_heading(
    "CREATE MATERIAL",
    "Build your classroom resource",
    "Set the class context once. The agents will retrieve, plan, review and improve the result.",
)

form_column, workflow_column = st.columns([1.55, 0.75], gap="large")

with form_column:
    with st.form("teacher_request", clear_on_submit=False):
        row_one_left, row_one_right = st.columns(2, gap="medium")
        with row_one_left:
            grade = st.selectbox(
                "Grade",
                options=[9, 10],
                help="Retrieval is filtered to grade-relevant knowledge documents.",
            )
        with row_one_right:
            student_level = st.selectbox(
                "Student ability",
                options=[item.value for item in StudentLevel],
                index=1,
                help="Used to adjust vocabulary, scaffolding and activity difficulty.",
            )

        topic = st.text_input(
            "English lesson topic",
            value="Reported Speech",
            placeholder="Example: Reported Speech, WH Questions, Passive Voice",
            max_chars=120,
        )

        row_two_left, row_two_right = st.columns(2, gap="medium")
        with row_two_left:
            output_type = st.selectbox(
                "Resource type",
                options=[item.value for item in OutputType],
            )
        with row_two_right:
            duration = st.slider(
                "Lesson duration",
                min_value=20,
                max_value=120,
                value=45,
                step=5,
                format="%d min",
            )

        extra = st.text_area(
            "Teaching preferences",
            placeholder=(
                "Example: Use simple local examples, include a five-minute pair activity, "
                "and add differentiated questions for weaker students."
            ),
            height=105,
            max_chars=800,
        )

        st.caption(
            "Tip: Give one or two concrete preferences. The Review Agent will check the final material automatically."
        )
        submitted = st.form_submit_button(
            "✨  Generate teaching material",
            type="primary",
            use_container_width=True,
        )

with workflow_column:
    render_workflow_preview()

if submitted:
    if len(topic.strip()) < 2:
        st.warning("Enter an English lesson topic before generating material.")
    else:
        try:
            request = TeacherRequest(
                grade=grade,
                topic=topic.strip(),
                duration_minutes=duration,
                student_level=StudentLevel(student_level),
                output_type=OutputType(output_type),
                extra_instructions=extra.strip(),
            )
        except ValidationError as exc:
            st.error(f"Please check the lesson settings: {exc}")
        else:
            orchestrator = EduAgentOrchestrator(settings, knowledge_base)
            with st.status("Preparing the agent workspace…", expanded=True) as status:
                progress_bar = st.progress(0)
                activity = st.empty()

                def update_progress(stage: str, detail: str, percent: int) -> None:
                    status.update(label=stage, state="running", expanded=True)
                    progress_bar.progress(max(0, min(percent, 100)))
                    activity.caption(detail)

                try:
                    result = orchestrator.run(request, progress_callback=update_progress)
                except Exception as exc:
                    status.update(label="Generation could not be completed", state="error", expanded=True)
                    st.error(
                        "The agent workflow encountered an error. Confirm your API settings or enable "
                        f"OFFLINE_DEMO, then try again. Technical detail: {exc}"
                    )
                else:
                    progress_bar.progress(100)
                    activity.caption("All agents completed the task and the result is ready.")
                    status.update(label="Teaching material ready", state="complete", expanded=False)
                    st.session_state["last_result"] = result.model_dump(mode="json")
                    st.toast("Teaching material generated and quality checked.", icon="✅")

if "last_result" in st.session_state:
    result = WorkflowResult(**st.session_state["last_result"])
    render_result_header(
        result.request,
        result.draft.title,
        result.review.average_score,
        result.draft.revision_number,
    )

    material_tab, review_tab, sources_tab, trace_tab = st.tabs(
        ["📘  Teaching material", "✓  Quality review", "⌕  RAG sources", "⇄  Agent trace"]
    )

    with material_tab:
        export_name = (
            f"grade_{result.request.grade}_{safe_filename(result.request.topic)}_"
            f"{safe_filename(result.request.output_type.value)}"
        )

        try:
            pdf_bytes = build_pdf_bytes(result)
            docx_bytes = build_docx_bytes(result)
        except Exception as exc:
            st.error(f"The downloadable documents could not be created: {exc}")
        else:
            pdf_column, docx_column = st.columns(2, gap="small")
            with pdf_column:
                st.download_button(
                    "↓  Download PDF",
                    data=pdf_bytes,
                    file_name=f"{export_name}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True,
                )
            with docx_column:
                st.download_button(
                    "↓  Download Word document",
                    data=docx_bytes,
                    file_name=f"{export_name}.docx",
                    mime=(
                        "application/vnd.openxmlformats-officedocument."
                        "wordprocessingml.document"
                    ),
                    use_container_width=True,
                )
            st.caption(
                "Both files include the lesson title, class details, formatted sections, "
                "questions, answer key and page-ready styling."
            )

        with st.expander("Developer exports (optional)", expanded=False):
            markdown_column, json_column = st.columns(2, gap="small")
            with markdown_column:
                st.download_button(
                    "Download Markdown",
                    data=result.draft.markdown,
                    file_name=f"{export_name}.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
            with json_column:
                st.download_button(
                    "Download complete run JSON",
                    data=json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False),
                    file_name=f"eduagent_{safe_filename(result.request.topic)}_run.json",
                    mime="application/json",
                    use_container_width=True,
                )

        with st.container(border=True):
            st.markdown(result.draft.markdown)

        st.caption(
            f"Generated by {result.draft.model_used} · Revision cycle {result.draft.revision_number}"
        )

    with review_tab:
        summary_left, summary_right = st.columns([0.72, 0.28], gap="large")
        with summary_left:
            st.subheader("Quality dimensions")
            st.caption("Each dimension is scored by the Review Agent from 1 to 5.")
        with summary_right:
            st.metric("Overall score", f"{result.review.average_score:.1f} / 5")

        render_review_cards(result.review)

        strengths_column, issues_column = st.columns(2, gap="large")
        with strengths_column:
            with st.container(border=True):
                st.subheader("What works well")
                if result.review.strengths:
                    for strength in result.review.strengths:
                        st.markdown(f"✅ &nbsp; {strength}")
                else:
                    st.write("No strengths were returned by the review model.")

        with issues_column:
            with st.container(border=True):
                st.subheader("Review notes")
                if result.review.issues:
                    for issue in result.review.issues:
                        st.markdown(f"⚠️ &nbsp; {issue}")
                else:
                    st.success("No major issues were identified.")

        if result.review.revision_instructions:
            with st.expander("Revision instructions used by the planner", expanded=False):
                for instruction in result.review.revision_instructions:
                    st.markdown(f"- {instruction}")

        st.caption(f"Reviewed by {result.review.model_used}")

    with sources_tab:
        metric_one, metric_two, metric_three = st.columns(3)
        metric_one.metric("Retrieved chunks", len(result.curriculum.chunks))
        metric_two.metric(
            "Best relevance",
            f"{max((chunk.score for chunk in result.curriculum.chunks), default=0):.3f}",
        )
        metric_three.metric("Context sufficient", "Yes" if result.curriculum.sufficient else "Review")

        with st.container(border=True):
            st.markdown("#### Retrieval summary")
            st.write(result.curriculum.retrieval_notes)
            st.caption(f"Search query: {result.curriculum.query}")

        for index, chunk in enumerate(result.curriculum.chunks, start=1):
            source_name = chunk.source.replace("\\", "/").split("/")[-1]
            with st.expander(
                f"{index:02d} · {source_name} · relevance {chunk.score:.3f}",
                expanded=index == 1,
            ):
                source_meta_left, source_meta_right = st.columns(2)
                source_meta_left.caption(f"Grade: {chunk.grade or 'General'}")
                source_meta_right.caption(f"Chunk ID: {chunk.chunk_id}")
                st.write(chunk.text)

    with trace_tab:
        trace_summary_left, trace_summary_right = st.columns([0.72, 0.28], gap="large")
        with trace_summary_left:
            st.subheader("Structured agent communication")
            st.caption(
                "Open any message to inspect the exact sender, receiver, performative and JSON payload."
            )
        with trace_summary_right:
            st.metric("Messages exchanged", len(result.messages))

        view_mode = st.radio(
            "Trace view",
            options=["Timeline", "Table"],
            horizontal=True,
            label_visibility="collapsed",
        )
        if view_mode == "Timeline":
            render_message_timeline(result.messages)
        else:
            st.dataframe(message_rows(result), use_container_width=True, hide_index=True)
else:
    render_empty_state()

st.markdown(
    "<div class='app-footer'>EduAgent LK · Agentic AI Teaching Assistant · Horizon Campus IT41043</div>",
    unsafe_allow_html=True,
)
