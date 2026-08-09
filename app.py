"""
app.py
------
Streamlit front end for the AI Research Agent.

This file owns presentation only. The one call into the research backend is
`pipeline.research_agent(topic, on_progress=...)` — everything else here is
about laying that result (and the live stage updates) out on screen.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import re as _re
import time
import traceback

import streamlit as st

import ui_helpers as ui
from pipeline import research_agent  # <-- the one backend entry point the UI calls

# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="AI Research Agent",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

ui.inject_custom_css()

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

st.session_state.setdefault("is_running", False)
st.session_state.setdefault("result", None)          # raw state dict from research_agent
st.session_state.setdefault("error", None)
st.session_state.setdefault("elapsed", None)
st.session_state.setdefault("topic", "")

# ---------------------------------------------------------------------------
# Sidebar (About / workflow / settings / export slot)
# ---------------------------------------------------------------------------

settings = ui.render_sidebar()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

ui.render_header()

# ---------------------------------------------------------------------------
# Input section
# ---------------------------------------------------------------------------

with st.container():
    topic = st.text_input(
        "Research topic",
        placeholder="Enter a research topic...",
        label_visibility="collapsed",
        key="topic_input",
    )
    st.markdown(
        '<span class="dim">Try: Quantum Computing · Artificial General Intelligence · '
        "Impact of War on Stock Market</span>",
        unsafe_allow_html=True,
    )
    st.write("")
    run_clicked = st.button(
        "🔬 Research",
        use_container_width=True,
        type="primary",
        disabled=st.session_state.is_running,
    )

st.write("")

# ---------------------------------------------------------------------------
# Progress + pipeline execution
# ---------------------------------------------------------------------------
# Placeholders declared once so the callback can update them *during* the
# (synchronous) research_agent() call — Streamlit flushes each placeholder
# update to the browser as it happens, which is what gives the "live"
# timeline feel without needing threads or async.

rail_slot = st.empty()
bar_slot = st.empty()
status_slot = st.empty()

if run_clicked:
    if not topic or not topic.strip():
        st.warning("Enter a topic before starting research.")
    else:
        st.session_state.is_running = True
        st.session_state.result = None
        st.session_state.error = None
        st.session_state.topic = topic.strip()

        progress_bar = bar_slot.progress(0.0)
        ui.render_rail(rail_slot, current_stage=None)

        def on_progress(stage: str) -> None:
            """Callback passed into pipeline.research_agent — updates the
            rail + progress bar live as each stage begins."""
            if stage == "done":
                ui.render_rail(rail_slot, current_stage=None, done=True)
                progress_bar.progress(1.0)
                status_slot.markdown('<span class="dim">Finalizing...</span>', unsafe_allow_html=True)
                return
            ui.render_rail(rail_slot, current_stage=stage)
            progress_bar.progress(ui.progress_fraction(stage))
            label = dict((k, l) for k, l, _ in ui.STAGES)[stage]
            status_slot.markdown(f'<span class="dim">{label}...</span>', unsafe_allow_html=True)

        start = time.time()
        try:
            with st.spinner("Running the research pipeline..."):
                state = research_agent(topic.strip(), on_progress=on_progress)
            st.session_state.result = state
            status_slot.empty()
            st.success("Research complete.")
        except Exception as exc:  # noqa: BLE001 - surface any backend error to the user
            st.session_state.error = str(exc)
            st.session_state.error_trace = traceback.format_exc()
            status_slot.empty()
            ui.render_rail(rail_slot, current_stage=None)
            bar_slot.empty()
        finally:
            st.session_state.elapsed = time.time() - start
            st.session_state.is_running = False
            st.rerun()

elif st.session_state.result is not None:
    # Re-render the completed rail after a rerun (e.g. triggered by a
    # download button click) so the timeline doesn't disappear.
    ui.render_rail(rail_slot, current_stage=None, done=True)
    bar_slot.progress(1.0)

# ---------------------------------------------------------------------------
# Error state
# ---------------------------------------------------------------------------

if st.session_state.error:
    st.error(f"Research failed: {st.session_state.error}")
    with st.expander("Show technical details"):
        st.code(st.session_state.get("error_trace", ""), language="text")

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

if st.session_state.result is not None:
    state = st.session_state.result
    topic_done = st.session_state.topic

    if st.session_state.elapsed is not None:
        st.caption(f"⏱ Completed in {st.session_state.elapsed:.1f}s")

    report_text = ui.as_markdown_text(state.get("Report"))
    critic = ui.parse_critic_feedback(state.get("Feedback"))
    sources = ui.build_sources(state.get("search_result"))

    report_col, side_col = st.columns([2, 1], gap="large")

    # ---- Report ------------------------------------------------------
    with report_col:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f'<div class="card-title">📝 Research Report — {topic_done}</div>', unsafe_allow_html=True)

        # Split on top-level markdown headings so long sections can collapse.
        parts = _re.split(r"(?m)^(##?\s+.+)$", report_text)
        if len(parts) <= 1:
            st.markdown(report_text)
        else:
            intro = parts[0].strip()
            if intro:
                st.markdown(intro)
            first = True
            for i in range(1, len(parts), 2):
                heading = parts[i].lstrip("# ").strip()
                body = parts[i + 1] if i + 1 < len(parts) else ""
                with st.expander(heading, expanded=first):
                    st.markdown(body)
                first = False
        st.markdown("</div>", unsafe_allow_html=True)

    # ---- Critic --------------------------------------------------------
    with side_col:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">🧐 Critic Review</div>', unsafe_allow_html=True)
        st.markdown(ui.score_badge_html(critic.score, critic.max_score), unsafe_allow_html=True)
        st.write("")

        if critic.strengths:
            st.markdown("**Strengths**")
            for s in critic.strengths:
                st.markdown(f"- {s}")
        if critic.improvements:
            st.markdown("**Areas for Improvement**")
            for s in critic.improvements:
                st.markdown(f"- {s}")
        if critic.suggestions:
            st.markdown("**Suggestions**")
            for s in critic.suggestions:
                st.markdown(f"- {s}")
        if critic.verdict:
            st.markdown("**Verdict**")
            st.markdown(critic.verdict)

        if not (critic.strengths or critic.improvements or critic.suggestions or critic.verdict):
            st.markdown(critic.raw or "_No critic output returned._")

        st.markdown("</div>", unsafe_allow_html=True)

    # ---- Sources -----------------------------------------------------
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div class="card-title">🔗 Sources ({len(sources)})</div>', unsafe_allow_html=True)
    if sources:
        cols = st.columns(2)
        for i, s in enumerate(sources, start=1):
            with cols[(i - 1) % 2]:
                st.markdown(ui.render_source_card(i, s), unsafe_allow_html=True)
    else:
        st.markdown('<span class="dim">No sources returned.</span>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ---- Export (sidebar slot) ----------------------------------------
    md_export = ui.build_export_markdown(topic_done, report_text, critic, sources)
    txt_export = ui.build_export_txt(topic_done, report_text, critic, sources)

    with settings["export_container"]:
        st.download_button(
            "⬇ Download Markdown",
            data=md_export,
            file_name=f"{topic_done.replace(' ', '_')}_report.md",
            mime="text/markdown",
            use_container_width=True,
        )
        st.download_button(
            "⬇ Download TXT",
            data=txt_export,
            file_name=f"{topic_done.replace(' ', '_')}_report.txt",
            mime="text/plain",
            use_container_width=True,
        )
        if st.button("⬇ Download PDF", use_container_width=True, disabled=True):
            pass
        st.caption("PDF export is a placeholder — wire up a renderer (e.g. weasyprint) when ready.")

else:
    st.markdown(
        '<div class="card"><span class="dim">Enter a topic above and click '
        '<b>Research</b> to get started. The live progress timeline and '
        "results will appear here.</span></div>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Future-ready hooks (intentionally unused placeholders — see README notes):
#   - Chat history:            st.session_state["history"] = [...]
#   - Multi-agent visualization: extend ui.render_rail() with per-agent detail
#   - Streaming responses:     swap research_agent() for a generator/yield version
#   - Multiple LLM support:    settings["model_name"] already collected above
#   - RAG / citation viewer:   ui.build_sources() already isolates source data
#   - Research history:        persist st.session_state["result"] snapshots
#   - User auth:                gate this script behind st.experimental_user / SSO
# ---------------------------------------------------------------------------
