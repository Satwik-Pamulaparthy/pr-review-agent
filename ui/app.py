import streamlit as st
import asyncio
import json
import websockets
import threading
import queue
import time

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="PR Review Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Styling ───────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #666;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    .score-box {
        text-align: center;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
    }
    .score-number {
        font-size: 3rem;
        font-weight: 700;
        line-height: 1;
    }
    .score-label {
        font-size: 0.85rem;
        color: #888;
        margin-top: 0.3rem;
    }
    .recommendation-approve    { color: #22c55e; }
    .recommendation-request    { color: #ef4444; }
    .recommendation-discussion { color: #f59e0b; }
    .agent-row {
        display: flex;
        align-items: center;
        padding: 0.6rem 0;
        border-bottom: 1px solid #f0f0f0;
        font-size: 0.95rem;
    }
    .finding-card {
        background: #fafafa;
        border-left: 4px solid #e0e0e0;
        padding: 0.8rem 1rem;
        margin-bottom: 0.6rem;
        border-radius: 0 8px 8px 0;
    }
    .severity-critical { border-left-color: #dc2626 !important; }
    .severity-high     { border-left-color: #ea580c !important; }
    .severity-medium   { border-left-color: #ca8a04 !important; }
    .severity-low      { border-left-color: #2563eb !important; }
</style>
""", unsafe_allow_html=True)


# ── Constants ─────────────────────────────────────────────────────────────────

AGENTS = [
    ("fetch_pr",      "📥", "Fetch PR"),
    ("security",      "🔒", "Security Audit"),
    ("logic",         "🧠", "Logic Review"),
    ("test_coverage", "🧪", "Test Coverage"),
    ("documentation", "📝", "Documentation"),
    ("synthesis",     "📋", "Final Synthesis"),
]

WS_URL = "ws://localhost:8000/review/stream"


# ── WebSocket runner (runs in a background thread) ────────────────────────────

def run_websocket(pr_url: str, event_queue: queue.Queue):
    """
    Runs in a background thread.
    Connects to the WebSocket, receives events, puts them in the queue.
    """
    async def _connect():
        try:
            async with websockets.connect(WS_URL) as ws:
                await ws.send(json.dumps({"pr_url": pr_url}))
                async for message in ws:
                    event = json.loads(message)
                    event_queue.put(event)
                    if event.get("type") in ("complete", "error"):
                        break
        except Exception as e:
            event_queue.put({"type": "error", "message": str(e)})

    asyncio.run(_connect())


# ── Score color helper ────────────────────────────────────────────────────────

def score_color(score: int) -> str:
    if score >= 80:
        return "#22c55e"
    elif score >= 60:
        return "#f59e0b"
    else:
        return "#ef4444"


def recommendation_color(rec: str) -> str:
    return {
        "APPROVE":          "#22c55e",
        "REQUEST_CHANGES":  "#ef4444",
        "NEEDS_DISCUSSION": "#f59e0b",
    }.get(rec, "#888")


def recommendation_emoji(rec: str) -> str:
    return {
        "APPROVE":          "✅",
        "REQUEST_CHANGES":  "🔴",
        "NEEDS_DISCUSSION": "🟡",
    }.get(rec, "⚪")


def severity_color(severity: str) -> str:
    return {
        "critical": "#dc2626",
        "high":     "#ea580c",
        "medium":   "#ca8a04",
        "low":      "#2563eb",
    }.get(severity.lower(), "#888")


# ── Main UI ───────────────────────────────────────────────────────────────────

def main():
    # Header
    st.markdown('<div class="main-header">🤖 PR Review Agent</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Multi-agent code review powered by LangGraph + GPT-4o</div>',
        unsafe_allow_html=True,
    )

    # Input row
    col_input, col_button = st.columns([5, 1])
    with col_input:
        pr_url = st.text_input(
            label="GitHub PR URL",
            placeholder="https://github.com/owner/repo/pull/123",
            label_visibility="collapsed",
        )
    with col_button:
        analyze = st.button("Analyze PR", type="primary", use_container_width=True)

    st.divider()

    # Only run when button is clicked and URL is provided
    if not analyze or not pr_url.strip():
        # Show placeholder instructions
        st.markdown("#### How it works")
        cols = st.columns(3)
        with cols[0]:
            st.markdown("**1. Paste a GitHub PR URL**")
            st.markdown("Any public GitHub pull request")
        with cols[1]:
            st.markdown("**2. Watch agents run live**")
            st.markdown("Security → Logic → Tests → Docs → Synthesis")
        with cols[2]:
            st.markdown("**3. Get a structured review**")
            st.markdown("Score, recommendation, and prioritized suggestions")
        return

    # Validate URL
    if "github.com" not in pr_url or "/pull/" not in pr_url:
        st.error("Please enter a valid GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)")
        return

    # ── Live progress section ─────────────────────────────────────────────────

    st.markdown("### 🔄 Agent Progress")
    progress_bar = st.progress(0)

    # Create a placeholder row for each agent
    agent_placeholders = {}
    for agent_id, emoji, label in AGENTS:
        agent_placeholders[agent_id] = st.empty()
        agent_placeholders[agent_id].markdown(
            f"⬜ **{emoji} {label}** — waiting..."
        )

    status_placeholder = st.empty()
    results_placeholder = st.empty()

    # ── Start background WebSocket thread ─────────────────────────────────────

    event_queue: queue.Queue = queue.Queue()
    thread = threading.Thread(
        target=run_websocket,
        args=(pr_url.strip(), event_queue),
        daemon=True,
    )
    thread.start()

    # ── Process events as they arrive ─────────────────────────────────────────

    agent_status  = {a[0]: "waiting" for a in AGENTS}
    total_agents  = len(AGENTS)
    completed     = 0
    final_data    = None

    status_placeholder.info("🚀 Connecting to agent pipeline...")

    while True:
        try:
            event = event_queue.get(timeout=60)
        except queue.Empty:
            status_placeholder.error("Timed out waiting for agents. Is the API server running?")
            break

        event_type = event.get("type")
        agent      = event.get("agent", "")
        message    = event.get("message", "")

        if event_type == "start":
            status_placeholder.info(f"🚀 {message}")

        elif event_type == "agent_start":
            agent_status[agent] = "running"
            # Find the label for this agent
            label = next((l for a, e, l in AGENTS if a == agent), agent)
            emoji = next((e for a, e, l in AGENTS if a == agent), "⚙️")
            agent_placeholders[agent].markdown(
                f"🔄 **{emoji} {label}** — running..."
            )

        elif event_type == "agent_done":
            agent_status[agent] = "done"
            completed += 1
            progress_bar.progress(completed / total_agents)
            label = next((l for a, e, l in AGENTS if a == agent), agent)
            emoji = next((e for a, e, l in AGENTS if a == agent), "⚙️")
            data  = event.get("data", {})

            # Build a result summary string for this agent
            detail = ""
            if agent == "fetch_pr":
                detail = f"+{data.get('additions', 0)} / -{data.get('deletions', 0)} lines, {data.get('files', 0)} file(s)"
            elif agent == "security":
                count  = data.get("count", 0)
                detail = f"{count} issue(s) found" if count else "no issues found ✓"
            elif agent == "logic":
                count  = data.get("count", 0)
                detail = f"{count} issue(s) found"
            elif agent in ("test_coverage", "documentation"):
                detail = f"score: {data.get('score', 0)}/100"
            elif agent == "synthesis":
                detail = message

            agent_placeholders[agent].markdown(
                f"✅ **{emoji} {label}** — {detail}"
            )

        elif event_type == "complete":
            completed = total_agents
            progress_bar.progress(1.0)
            agent_status["synthesis"] = "done"
            agent_placeholders["synthesis"].markdown(
                f"✅ **📋 Final Synthesis** — complete"
            )
            final_data = event.get("data", {})
            status_placeholder.success("✅ Review complete!")
            break

        elif event_type == "error":
            status_placeholder.error(f"❌ Error: {message}")
            break

    # ── Render final results ──────────────────────────────────────────────────

    if not final_data:
        return

    st.divider()
    st.markdown("### 📊 Review Report")

    # PR metadata
    st.markdown(f"**{final_data.get('pr_title', '')}**")
    st.markdown(
        f"`{final_data.get('repo', '')}` · "
        f"by **{final_data.get('pr_author', '')}**"
    )

    st.markdown("")

    # Score cards row
    score     = final_data.get("overall_score", 0)
    rec       = final_data.get("recommendation", "")
    test_sc   = final_data.get("test_coverage_score", 0)
    doc_sc    = final_data.get("documentation_score", 0)
    est_time  = final_data.get("estimated_review_time_minutes", 0)

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.markdown(
            f'<div class="score-box">'
            f'<div class="score-number" style="color:{score_color(score)}">{score}</div>'
            f'<div class="score-label">Overall Score</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c2:
        rec_color = recommendation_color(rec)
        rec_emoji = recommendation_emoji(rec)
        st.markdown(
            f'<div class="score-box">'
            f'<div class="score-number" style="color:{rec_color};font-size:2rem">{rec_emoji}</div>'
            f'<div class="score-label">{rec.replace("_", " ")}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="score-box">'
            f'<div class="score-number" style="color:{score_color(test_sc)}">{test_sc}</div>'
            f'<div class="score-label">Test Coverage</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f'<div class="score-box">'
            f'<div class="score-number" style="color:{score_color(doc_sc)}">{doc_sc}</div>'
            f'<div class="score-label">Documentation</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c5:
        st.markdown(
            f'<div class="score-box">'
            f'<div class="score-number" style="color:#6366f1">{est_time}</div>'
            f'<div class="score-label">Est. Review (min)</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("")

    # Summary
    st.info(f"**Summary:** {final_data.get('summary', '')}")

    # Three columns: Security, Logic, Suggestions
    col_sec, col_logic, col_sugg = st.columns(3)

    with col_sec:
        st.markdown("#### 🔒 Security")
        findings = final_data.get("security_findings", [])
        if findings:
            for f in findings:
                sev   = f.get("severity", "low")
                color = severity_color(sev)
                st.markdown(
                    f'<div class="finding-card severity-{sev}">'
                    f'<strong style="color:{color}">[{sev.upper()}]</strong> {f.get("title", "")}<br>'
                    f'<small>{f.get("file", "")}</small><br>'
                    f'<small>{f.get("description", "")[:150]}...</small>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.success("No security issues found ✓")

        highlights = final_data.get("security_highlights", [])
        if highlights:
            for h in highlights:
                st.markdown(f"• {h}")

    with col_logic:
        st.markdown("#### 🧠 Logic")
        findings = final_data.get("logic_findings", [])
        if findings:
            for f in findings:
                sev   = f.get("severity", "low")
                color = severity_color(sev)
                st.markdown(
                    f'<div class="finding-card severity-{sev}">'
                    f'<strong style="color:{color}">[{sev.upper()}]</strong> {f.get("title", "")}<br>'
                    f'<small>{f.get("file", "")}</small><br>'
                    f'<small>{f.get("description", "")[:150]}...</small>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.success("No logic issues found ✓")

        highlights = final_data.get("logic_highlights", [])
        if highlights:
            for h in highlights:
                st.markdown(f"• {h}")

    with col_sugg:
        st.markdown("#### 💡 Top Suggestions")
        suggestions = final_data.get("top_suggestions", [])
        for i, s in enumerate(suggestions, 1):
            st.markdown(
                f'<div class="finding-card">'
                f'<strong>#{i}</strong> {s}'
                f'</div>',
                unsafe_allow_html=True,
            )

    # Errors (shown only if any)
    errors = final_data.get("errors", [])
    if errors:
        st.warning(f"⚠️ Errors during analysis: {errors}")


if __name__ == "__main__":
    main()