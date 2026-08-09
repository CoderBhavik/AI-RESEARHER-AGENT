"""
ui_helpers.py
--------------
Pure UI / presentation helpers for the Streamlit AI Research Agent front end.

Nothing in this file talks to Tavily, BeautifulSoup, or any LLM chain
directly — it only shapes data that already came back from
`pipeline.research_agent()` into something nice to render, and renders the
static chrome (theme, header, sidebar, stepper, badges).

Kept separate from app.py so the Streamlit page script stays readable and so
these functions are reusable if the UI ever grows (multi-page app, chat
mode, etc.) — see the "Future Ready" hooks at the bottom of app.py.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

import streamlit as st

# ---------------------------------------------------------------------------
# Pipeline stage definitions — single source of truth for the progress rail,
# used by both the main column stepper and (implicitly) the sidebar diagram.
# ---------------------------------------------------------------------------

STAGES: list[tuple[str, str, str]] = [
    # (stage_key, label, icon)
    ("search", "Searching the Web", "🔎"),
    ("scrape", "Scraping Top Sources", "📄"),
    ("write", "Writing Research Report", "🧠"),
    ("critic", "Reviewing Report", "🧐"),
]
STAGE_KEYS = [s[0] for s in STAGES]


# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------

def inject_custom_css() -> None:
    """Inject the dark, minimal theme. Called once at the top of app.py."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

        :root{
            --bg:            #0A0C10;
            --surface:       #12151C;
            --surface-2:     #171B24;
            --border:        #242A36;
            --text:          #E7E9EE;
            --text-dim:      #99A2B3;
            --accent:        #6C8EFF;
            --accent-dim:    #6C8EFF33;
            --gold:          #F2B84B;
            --green:         #34D399;
            --yellow:        #FBBF24;
            --red:           #F87171;
        }

        html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
        .stApp { background: var(--bg); color: var(--text); }

        h1, h2, h3, h4, .app-title { font-family: 'Space Grotesk', sans-serif; }

        code, .mono { font-family: 'JetBrains Mono', monospace; }

        #MainMenu, footer, header {visibility: hidden;}

        /* ---- Header ------------------------------------------------- */
        .app-header{
            padding: 1.75rem 0 1.25rem 0;
            border-bottom: 1px solid var(--border);
            margin-bottom: 1.75rem;
        }
        .app-title{
            font-size: 2rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            margin: 0;
            display:flex; align-items:center; gap:.6rem;
        }
        .app-subtitle{
            color: var(--text-dim);
            font-size: .98rem;
            margin-top: .35rem;
            max-width: 720px;
        }

        /* ---- Generic card -------------------------------------------- */
        .card{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.4rem 1.5rem;
            box-shadow: 0 8px 24px -12px rgba(0,0,0,0.5);
            margin-bottom: 1.1rem;
        }
        .card-title{
            font-family:'Space Grotesk',sans-serif;
            font-weight:600; font-size:1.05rem;
            margin-bottom: .8rem;
            display:flex; align-items:center; gap:.5rem;
        }

        /* ---- Progress rail (signature element) ------------------------
           A horizontal pipeline rail: each stage is a node on a connecting
           line, since the research process is a genuine ordered sequence
           (search -> scrape -> write -> critique), not a decorative list. */
        .rail{ display:flex; align-items:flex-start; justify-content:space-between;
               position:relative; margin: .5rem 0 1.4rem 0; }
        .rail::before{
            content:""; position:absolute; top:17px; left:5%; right:5%;
            height:2px; background: var(--border); z-index:0;
        }
        .rail-node{ position:relative; z-index:1; display:flex; flex-direction:column;
                    align-items:center; width:25%; text-align:center; gap:.5rem;}
        .rail-dot{ width:34px; height:34px; border-radius:50%; display:flex;
                   align-items:center; justify-content:center; font-size:1rem;
                   background: var(--surface-2); border:2px solid var(--border);
                   transition: all .25s ease; }
        .rail-dot.done{ background: var(--accent); border-color: var(--accent); }
        .rail-dot.active{ border-color: var(--accent); box-shadow: 0 0 0 4px var(--accent-dim);
                           animation: pulse 1.4s ease-in-out infinite; }
        .rail-label{ font-size: .8rem; color: var(--text-dim); line-height:1.2; }
        .rail-label.active, .rail-label.done{ color: var(--text); font-weight:500; }
        @keyframes pulse{
            0%   { box-shadow: 0 0 0 0 var(--accent-dim); }
            70%  { box-shadow: 0 0 0 8px transparent; }
            100% { box-shadow: 0 0 0 0 transparent; }
        }

        /* ---- Score badge ------------------------------------------- */
        .score-badge{
            display:inline-flex; align-items:center; gap:.4rem;
            padding: .35rem .9rem; border-radius: 999px;
            font-weight:600; font-size: 1rem; font-family:'Space Grotesk',sans-serif;
        }
        .score-green{ background:#34D39926; color:#5EEAD4; border:1px solid #34D39955;}
        .score-yellow{ background:#FBBF2426; color:#FBBF24; border:1px solid #FBBF2455;}
        .score-red{ background:#F8717126; color:#FCA5A5; border:1px solid #F8717155;}

        /* ---- Source card --------------------------------------------- */
        .source-card{
            display:block; background: var(--surface-2); border:1px solid var(--border);
            border-radius: 12px; padding: .85rem 1rem; margin-bottom:.6rem;
            text-decoration:none !important; color: var(--text) !important;
            transition: border-color .15s ease, transform .15s ease;
        }
        .source-card:hover{ border-color: var(--accent); transform: translateY(-1px); }
        .source-index{
            display:inline-flex; align-items:center; justify-content:center;
            width:22px; height:22px; border-radius:6px; background:var(--gold);
            color:#1a1400; font-size:.72rem; font-weight:700; margin-right:.5rem;
        }
        .source-title{ font-weight:600; font-size:.92rem; }
        .source-domain{ color: var(--accent); font-size:.78rem; margin-top:.15rem; }
        .source-url{ color: var(--text-dim); font-size:.75rem; font-family:'JetBrains Mono',monospace;
                     word-break:break-all; margin-top:.15rem;}

        /* ---- Misc ------------------------------------------------- */
        .dim{ color: var(--text-dim); font-size:.85rem; }
        .stButton>button{
            border-radius: 12px; font-weight:600; border:1px solid var(--border);
        }
        .stButton>button:not(:disabled):hover{ border-color: var(--accent); color: var(--accent); }
        section[data-testid="stSidebar"]{ background: var(--surface); border-right:1px solid var(--border); }
        .workflow-step{ display:flex; align-items:center; gap:.5rem; padding:.3rem 0; font-size:.88rem;}
        .workflow-arrow{ color: var(--text-dim); text-align:center; line-height:1; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Header / sidebar chrome
# ---------------------------------------------------------------------------

def render_header() -> None:
    st.markdown(
        """
        <div class="app-header">
            <div class="app-title">🔎 AI Research Agent</div>
            <div class="app-subtitle">
                Research any topic using AI-powered web search, scraping, report generation, and review.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> dict:
    """Renders the sidebar (About / workflow / settings / export placeholders)
    and returns the current settings as a dict."""
    with st.sidebar:
        st.markdown("### About")
        st.markdown(
            '<span class="dim">A multi-stage agent that searches the web, '
            "scrapes top sources, drafts a report, and critiques its own "
            "work before handing it to you.</span>",
            unsafe_allow_html=True,
        )

        st.markdown("**Workflow**")
        steps = ["Topic", "Search", "Scrape", "Writer", "Critic"]
        for i, s in enumerate(steps):
            st.markdown(f'<div class="workflow-step">▪ {s}</div>', unsafe_allow_html=True)
            if i < len(steps) - 1:
                st.markdown('<div class="workflow-arrow">↓</div>', unsafe_allow_html=True)

        st.divider()
        st.markdown("### Settings")
        max_results = st.slider("Maximum search results", 1, 10, 5)
        max_pages = st.slider("Maximum pages to scrape", 1, 10, 5)
        model_name = st.text_input("Model name", value="", placeholder="as configured in agents.py")
        temperature = st.slider("Temperature", 0.0, 1.0, 0.3, 0.1)
        st.caption(
            "⚠️ These settings are wired into the UI only for now — see the "
            "integration notes for how to pass them into `tools.py` / "
            "`agents.py` once you're ready."
        )

        st.divider()
        st.markdown("### Export")
        export_placeholder = st.container()

    return {
        "max_results": max_results,
        "max_pages": max_pages,
        "model_name": model_name,
        "temperature": temperature,
        "export_container": export_placeholder,
    }


# ---------------------------------------------------------------------------
# Progress rail
# ---------------------------------------------------------------------------

def render_rail(placeholder, current_stage: str | None, done: bool = False) -> None:
    """Render the horizontal stage rail into `placeholder` (an st.empty()).

    current_stage: one of STAGE_KEYS, or None before anything has started.
    done: True once the whole pipeline has finished (all nodes complete).
    """
    if current_stage is None and not done:
        current_index = -1
    elif done:
        current_index = len(STAGES)
    else:
        current_index = STAGE_KEYS.index(current_stage)

    nodes_html = []
    for i, (_key, label, icon) in enumerate(STAGES):
        if i < current_index or done:
            dot_cls, label_cls, content = "done", "done", "✓"
        elif i == current_index:
            dot_cls, label_cls, content = "active", "active", icon
        else:
            dot_cls, label_cls, content = "", "", icon
        nodes_html.append(
            f'<div class="rail-node">'
            f'<div class="rail-dot {dot_cls}">{content}</div>'
            f'<div class="rail-label {label_cls}">{label}</div>'
            f"</div>"
        )

    placeholder.markdown(f'<div class="rail">{"".join(nodes_html)}</div>', unsafe_allow_html=True)


def progress_fraction(current_stage: str | None, done: bool = False) -> float:
    if done:
        return 1.0
    if current_stage is None:
        return 0.0
    idx = STAGE_KEYS.index(current_stage)
    # each stage counts its start as (idx / n) progress, plus a little for "in-progress"
    return (idx + 0.5) / len(STAGES)


# ---------------------------------------------------------------------------
# Normalizing unknown backend return types
# ---------------------------------------------------------------------------

def to_plain(obj: Any) -> Any:
    """Best-effort conversion of whatever `agents.py` returns (a raw string,
    a LangChain message, a pydantic model, or a plain dict) into a plain
    str/dict/list so the rest of the UI doesn't need to care which one it is.
    """
    if obj is None:
        return ""
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: to_plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_plain(v) for v in obj]
    # pydantic v2
    if hasattr(obj, "model_dump"):
        try:
            return to_plain(obj.model_dump())
        except Exception:
            pass
    # pydantic v1 / some LC objects
    if hasattr(obj, "dict"):
        try:
            return to_plain(obj.dict())
        except Exception:
            pass
    # LangChain AIMessage-like objects
    if hasattr(obj, "content"):
        return to_plain(obj.content)
    return str(obj)


def as_markdown_text(obj: Any) -> str:
    """Render any normalized value as a markdown string for display."""
    plain = to_plain(obj)
    if isinstance(plain, str):
        return plain
    if isinstance(plain, dict):
        # common single-field wrappers
        for key in ("report", "content", "text", "markdown", "output"):
            if key in plain and isinstance(plain[key], str):
                return plain[key]
        return "```json\n" + json.dumps(plain, indent=2, default=str) + "\n```"
    return str(plain)


# ---------------------------------------------------------------------------
# Critic feedback parsing
# ---------------------------------------------------------------------------

@dataclass
class CriticView:
    score: float | None = None
    max_score: int = 10
    strengths: list[str] = field(default_factory=list)
    improvements: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    verdict: str = ""
    raw: str = ""


_LIST_KEY_ALIASES = {
    "strengths": "strengths",
    "areas_for_improvement": "improvements",
    "areas for improvement": "improvements",
    "weaknesses": "improvements",
    "improvements": "improvements",
    "suggestions": "suggestions",
    "recommendations": "suggestions",
}
_SCORE_KEYS = ("score", "overall_score", "rating", "overall_rating")
_VERDICT_KEYS = ("verdict", "conclusion", "summary", "final_verdict")


def _coerce_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip("-• ").strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        # split bullet-ish text into lines
        lines = re.split(r"[\r\n]+", value)
        return [re.sub(r"^[-•*\d.\)]+\s*", "", ln).strip() for ln in lines if ln.strip()]
    return [str(value)]


def _parse_score(text: str) -> float | None:
    m = re.search(r"(\d{1,2}(?:\.\d)?)\s*/\s*10", text)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            return None
    m = re.search(r"score[:\-]?\s*(\d{1,2}(?:\.\d)?)", text, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            return None
    return None


def _parse_markdown_sections(text: str) -> dict[str, str]:
    """Split a markdown-ish string on headers / bold labels into a dict of
    lowercased-label -> body text."""
    sections: dict[str, str] = {}
    # matches "## Strengths", "**Strengths:**", "Strengths:" at line start
    pattern = re.compile(
        r"^(?:#{1,4}\s*|\*\*)?([A-Za-z][A-Za-z /]{2,40}?)(?:\*\*)?\s*:?\s*$",
        re.MULTILINE,
    )
    matches = list(pattern.finditer(text))
    for i, m in enumerate(matches):
        label = m.group(1).strip().lower()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            sections[label] = body
    return sections


def parse_critic_feedback(feedback_obj: Any) -> CriticView:
    """Turn whatever `critic_chain.invoke(...)` returned into a CriticView
    with the fields the UI wants (score, strengths, improvements,
    suggestions, verdict). Falls back gracefully to just showing the raw
    text if the shape can't be recognized."""
    plain = to_plain(feedback_obj)
    view = CriticView()

    if isinstance(plain, dict):
        view.raw = json.dumps(plain, indent=2, default=str)
        for k, v in plain.items():
            key = str(k).strip().lower()
            if key in _SCORE_KEYS:
                view.score = _parse_score(str(v)) if not isinstance(v, (int, float)) else float(v)
            elif key in _LIST_KEY_ALIASES:
                target = _LIST_KEY_ALIASES[key]
                setattr(view, target, _coerce_list(v))
            elif key in _VERDICT_KEYS:
                view.verdict = str(v)
        return view

    # string case
    text = str(plain)
    view.raw = text
    view.score = _parse_score(text)

    sections = _parse_markdown_sections(text)
    for label, body in sections.items():
        if label in _LIST_KEY_ALIASES:
            target = _LIST_KEY_ALIASES[label]
            current = getattr(view, target)
            setattr(view, target, current + _coerce_list(body))
        elif label in _VERDICT_KEYS or "verdict" in label:
            view.verdict = body
        elif "score" in label and view.score is None:
            view.score = _parse_score(body)

    if not (view.strengths or view.improvements or view.suggestions or view.verdict):
        # couldn't find structured sections — treat the whole thing as the verdict
        view.verdict = text

    return view


def score_badge_html(score: float | None, max_score: int = 10) -> str:
    if score is None:
        return '<span class="score-badge" style="background:#ffffff14;color:#99A2B3;border:1px solid #ffffff22;">N/A</span>'
    if score >= max_score * 0.8:
        cls = "score-green"
    elif score >= max_score * 0.5:
        cls = "score-yellow"
    else:
        cls = "score-red"
    score_str = f"{score:g}/{max_score}"
    return f'<span class="score-badge {cls}">⭐ {score_str}</span>'


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

@dataclass
class SourceItem:
    title: str
    url: str
    domain: str


def build_sources(search_result: Any) -> list[SourceItem]:
    plain = to_plain(search_result)
    items: list[SourceItem] = []
    if not isinstance(plain, list):
        return items
    for entry in plain:
        if isinstance(entry, dict):
            url = entry.get("url") or entry.get("link") or ""
            title = entry.get("title") or entry.get("name") or url or "Untitled source"
        else:
            url = str(entry)
            title = url
        domain = urlparse(url).netloc.replace("www.", "") if url else "unknown"
        items.append(SourceItem(title=title, url=url, domain=domain))
    return items


def render_source_card(index: int, source: SourceItem) -> str:
    return (
        f'<a class="source-card" href="{source.url}" target="_blank" rel="noopener noreferrer">'
        f'<div><span class="source-index">{index}</span>'
        f'<span class="source-title">{source.title}</span></div>'
        f'<div class="source-domain">{source.domain}</div>'
        f'<div class="source-url">{source.url}</div>'
        f"</a>"
    )


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def build_export_markdown(topic: str, report_text: str, critic: CriticView, sources: list[SourceItem]) -> str:
    lines = [f"# Research Report: {topic}\n", report_text.strip(), "\n---\n", "## Critic Review\n"]
    if critic.score is not None:
        lines.append(f"**Overall Score:** {critic.score:g}/{critic.max_score}\n")
    if critic.strengths:
        lines.append("**Strengths**\n" + "\n".join(f"- {s}" for s in critic.strengths) + "\n")
    if critic.improvements:
        lines.append("**Areas for Improvement**\n" + "\n".join(f"- {s}" for s in critic.improvements) + "\n")
    if critic.suggestions:
        lines.append("**Suggestions**\n" + "\n".join(f"- {s}" for s in critic.suggestions) + "\n")
    if critic.verdict:
        lines.append(f"**Verdict**\n{critic.verdict}\n")
    if sources:
        lines.append("\n---\n## Sources\n")
        for i, s in enumerate(sources, start=1):
            lines.append(f"{i}. [{s.title}]({s.url}) — {s.domain}")
    return "\n".join(lines)


def build_export_txt(topic: str, report_text: str, critic: CriticView, sources: list[SourceItem]) -> str:
    # Plain-text version: strip the heaviest markdown markers for readability.
    md = build_export_markdown(topic, report_text, critic, sources)
    txt = re.sub(r"[#*_`]", "", md)
    return txt
