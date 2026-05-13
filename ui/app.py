import streamlit as st
import asyncio
import json
import websockets
import threading
import queue
import os

st.set_page_config(
    page_title="PR Review Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background: #f8f8f6; }
  [data-testid="stMain"] { padding: 2rem 2rem 4rem; }
  .hero { background: white; border: 0.5px solid #e8e8e4; border-radius: 16px;
          padding: 40px 32px; text-align: center; margin-bottom: 16px; }
  .hero h1 { font-size: 26px; font-weight: 600; color: #1a1a1a; margin-bottom: 10px; }
  .hero p  { font-size: 15px; color: #666; max-width: 520px; margin: 0 auto; }
  .how-card { background: white; border: 0.5px solid #e8e8e4; border-radius: 12px;
              padding: 18px; height: 100%; }
  .how-num  { width: 26px; height: 26px; border-radius: 50%; background: #EEEDFE;
              color: #534AB7; font-size: 12px; font-weight: 600;
              display: flex; align-items: center; justify-content: center; margin-bottom: 10px; }
  .agent-row { display: flex; align-items: center; gap: 10px; padding: 9px 0;
               border-bottom: 0.5px solid #f0f0ee; font-size: 14px; }
  .agent-row:last-child { border-bottom: none; }
  .dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }
  .dot-wait    { background: #d0d0cc; }
  .dot-running { background: #7F77DD; }
  .dot-done    { background: #1D9E75; }
  .dot-error   { background: #E24B4A; }
  .metric-card { background: white; border: 0.5px solid #e8e8e4; border-radius: 12px;
                 padding: 18px; text-align: center; }
  .metric-num   { font-size: 28px; font-weight: 600; line-height: 1.1; margin-bottom: 4px; }
  .metric-label { font-size: 12px; color: #888; }
  .rec-banner   { border-radius: 12px; padding: 16px 20px;
                  margin: 0 0 16px; display: flex; gap: 14px; }
  .rec-approve  { background: #E1F5EE; border: 0.5px solid #5DCAA5; }
  .rec-request  { background: #FAECE7; border: 0.5px solid #F0997B; }
  .rec-discuss  { background: #FAEEDA; border: 0.5px solid #EF9F27; }
  .finding { border-left: 3px solid #e0e0e0; padding: 8px 12px;
             margin-bottom: 7px; background: #fafafa; border-radius: 0 6px 6px 0; }
  .finding-critical { border-left-color: #E24B4A; }
  .finding-high     { border-left-color: #D85A30; }
  .finding-medium   { border-left-color: #EF9F27; }
  .finding-low      { border-left-color: #378ADD; }
  .finding-ok       { border-left-color: #1D9E75; }
  .ftitle { font-size: 13px; font-weight: 600; color: #1a1a1a; margin-bottom: 2px; }
  .ffile  { font-size: 11px; color: #999; font-family: monospace; margin-bottom: 3px; }
  .fdesc  { font-size: 12px; color: #555; line-height: 1.5; }
  .sugg-item { display: flex; gap: 8px; margin-bottom: 10px; align-items: flex-start; }
  .sugg-num  { width: 20px; height: 20px; border-radius: 50%; background: #EEEDFE;
               color: #534AB7; font-size: 11px; font-weight: 600;
               display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
  .sugg-text { font-size: 13px; color: #444; line-height: 1.5; padding-top: 1px; }
  .section-head { font-size: 11px; font-weight: 600; color: #999;
                  letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 10px; }
  .ok-pill { display: inline-flex; align-items: center; gap: 4px; font-size: 11px;
             padding: 2px 9px; border-radius: 99px; background: #E1F5EE; color: #0F6E56;
             border: 0.5px solid #5DCAA5; margin-left: 6px; }
  .col-card { background: white; border: 0.5px solid #e8e8e4; border-radius: 12px;
              padding: 16px; height: 100%; }
  .col-title { font-size: 14px; font-weight: 600; color: #1a1a1a;
               margin-bottom: 12px; display: flex; align-items: center; gap: 6px; }
  .summary-strip { background: #EEEDFE; border-radius: 10px; padding: 14px 18px;
                   font-size: 14px; color: #3C3489; line-height: 1.6; margin-bottom: 16px; }
  .pr-meta { font-size: 13px; color: #666; margin-bottom: 16px; }
  .pr-meta strong { color: #1a1a1a; }
  .live-badge { display: inline-flex; align-items: center; gap: 5px; font-size: 12px;
                color: #0F6E56; background: #E1F5EE; padding: 3px 10px;
                border-radius: 99px; border: 0.5px solid #5DCAA5; margin-bottom: 8px; }
  .missing-item { font-size: 12px; color: #555; padding: 4px 0;
                  border-bottom: 0.5px solid #f0f0ee; }
  .missing-item:last-child { border-bottom: none; }
</style>
""", unsafe_allow_html=True)

WS_URL = os.getenv("API_WS_URL", "ws://localhost:8000/review/stream")

AGENTS = [
    ("fetch_pr",      "📥", "Fetch PR from GitHub"),
    ("security",      "🔒", "Security audit"),
    ("logic",         "🧠", "Logic review"),
    ("test_coverage", "🧪", "Test coverage check"),
    ("documentation", "📝", "Documentation check"),
    ("synthesis",     "📋", "Final synthesis"),
]

def run_websocket(pr_url, event_queue):
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

def score_color(score):
    if score >= 80: return "#1D9E75"
    if score >= 60: return "#BA7517"
    return "#A32D2D"

def rec_info(rec):
    return {
        "APPROVE":          ("#E1F5EE", "#5DCAA5", "#0F6E56", "✅", "Looks good to merge",
                             "No significant issues were found. This PR is ready to merge."),
        "REQUEST_CHANGES":  ("#FAECE7", "#F0997B", "#993C1D", "⚠️", "Changes requested before merge",
                             "There are issues that should be addressed before this PR is merged."),
        "NEEDS_DISCUSSION": ("#FAEEDA", "#EF9F27", "#854F0B", "💬", "Needs team discussion",
                             "This PR has tradeoffs or complexity that the team should discuss before merging."),
    }.get(rec, ("#f5f5f5", "#ccc", "#666", "⚪", rec, ""))

def main():
    # ── Header ──
    col_logo, col_badge = st.columns([6, 1])
    with col_logo:
        st.markdown("### 🔍 PR Review Agent")
        st.markdown("<p style='font-size:13px;color:#888;margin-top:-12px;'>Multi-agent code review powered by LangGraph + GPT-4o</p>", unsafe_allow_html=True)
    with col_badge:
        st.markdown("<div style='padding-top:14px;text-align:right;'><span class='live-badge'>● API live</span></div>", unsafe_allow_html=True)

    st.divider()

    # ── Hero ──
    st.markdown("""
    <div class="hero">
      <h1>Get an instant expert review of any pull request</h1>
      <p>Paste a GitHub PR link and five AI agents will check it for security issues,
         logic errors, test coverage gaps, and documentation quality —
         then give you a plain-English report in under 30 seconds.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── How it works ──
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""<div class="how-card"><div class="how-num">1</div>
        <strong style="font-size:13px;">Paste any GitHub PR link</strong>
        <p style="font-size:12px;color:#666;margin-top:6px;line-height:1.5;">
        Works on any public repository. Just copy the URL from your browser.</p></div>""",
        unsafe_allow_html=True)
    with c2:
        st.markdown("""<div class="how-card"><div class="how-num">2</div>
        <strong style="font-size:13px;">Five agents review it live</strong>
        <p style="font-size:12px;color:#666;margin-top:6px;line-height:1.5;">
        Security, logic, test coverage, documentation, and a synthesis agent run in sequence.</p></div>""",
        unsafe_allow_html=True)
    with c3:
        st.markdown("""<div class="how-card"><div class="how-num">3</div>
        <strong style="font-size:13px;">Get a structured report</strong>
        <p style="font-size:12px;color:#666;margin-top:6px;line-height:1.5;">
        A score out of 100, a clear recommendation, and a prioritized list of what to fix.</p></div>""",
        unsafe_allow_html=True)

    st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
    st.divider()

    # ── Input ──
    st.markdown("#### Analyze a pull request")
    col_in, col_btn = st.columns([5, 1])
    with col_in:
        pr_url = st.text_input(
            "GitHub PR URL",
            placeholder="https://github.com/owner/repo/pull/123",
            label_visibility="collapsed",
        )
    with col_btn:
        analyze = st.button("Analyze PR ▶", type="primary", use_container_width=True)

    st.markdown(
        "<p style='font-size:12px;color:#aaa;margin-top:4px;'>"
        "Try it: https://github.com/fastapi/fastapi/pull/15508</p>",
        unsafe_allow_html=True
    )

    if not analyze or not pr_url.strip():
        return

    if "github.com" not in pr_url or "/pull/" not in pr_url:
        st.error("Please enter a valid GitHub PR URL — e.g. https://github.com/owner/repo/pull/123")
        return

    st.divider()

    # ── Progress tracker ──
    st.markdown("#### Live agent progress")

    progress_bar  = st.progress(0)
    agent_slots   = {a[0]: st.empty() for a in AGENTS}
    status_slot   = st.empty()
    results_slot  = st.empty()

    for agent_id, emoji, label in AGENTS:
        agent_slots[agent_id].markdown(
            f"<div class='agent-row'><div class='dot dot-wait'></div>"
            f"<span style='flex:1;'>{emoji} {label}</span>"
            f"<span style='font-size:12px;color:#bbb;'>Waiting</span></div>",
            unsafe_allow_html=True
        )

    eq: queue.Queue = queue.Queue()
    threading.Thread(target=run_websocket, args=(pr_url.strip(), eq), daemon=True).start()

    status_slot.info("🚀 Connecting to agent pipeline...")

    total     = len(AGENTS)
    done      = 0
    final_data = None

    while True:
        try:
            ev = eq.get(timeout=90)
        except queue.Empty:
            status_slot.error("⏱ Timed out. Make sure the API server is running.")
            break

        etype  = ev.get("type")
        agent  = ev.get("agent", "")
        msg    = ev.get("message", "")
        label  = next((l for a, e, l in AGENTS if a == agent), agent)
        emoji  = next((e for a, e, l in AGENTS if a == agent), "⚙️")

        if etype == "agent_start":
            agent_slots[agent].markdown(
                f"<div class='agent-row'><div class='dot dot-running'></div>"
                f"<span style='flex:1;'>{emoji} {label}</span>"
                f"<span style='font-size:12px;color:#7F77DD;'>Running...</span></div>",
                unsafe_allow_html=True
            )

        elif etype == "agent_done":
            done += 1
            progress_bar.progress(done / total)
            data   = ev.get("data", {})
            detail = ""
            if agent == "fetch_pr":
                detail = f"+{data.get('additions',0)} / -{data.get('deletions',0)} lines &nbsp;·&nbsp; {data.get('files',0)} file(s)"
            elif agent == "security":
                c = data.get("count", 0)
                detail = "No issues found ✓" if c == 0 else f"{c} issue(s) found"
            elif agent == "logic":
                c = data.get("count", 0)
                detail = f"{c} issue(s) found"
            elif agent in ("test_coverage", "documentation"):
                detail = f"Score: {data.get('score',0)}/100"
            else:
                detail = msg
            agent_slots[agent].markdown(
                f"<div class='agent-row'><div class='dot dot-done'></div>"
                f"<span style='flex:1;'>{emoji} {label}</span>"
                f"<span style='font-size:12px;color:#1D9E75;'>{detail}</span></div>",
                unsafe_allow_html=True
            )

        elif etype == "complete":
            done = total
            progress_bar.progress(1.0)
            agent_slots["synthesis"].markdown(
                "<div class='agent-row'><div class='dot dot-done'></div>"
                "<span style='flex:1;'>📋 Final synthesis</span>"
                "<span style='font-size:12px;color:#1D9E75;'>Complete</span></div>",
                unsafe_allow_html=True
            )
            status_slot.success("✅ Review complete!")
            final_data = ev.get("data", {})
            break

        elif etype == "error":
            status_slot.error(f"❌ {msg}")
            break

    if not final_data:
        return

    # ── Results ──
    st.divider()
    st.markdown("#### Review report")

    st.markdown(
        f"<div class='pr-meta'>"
        f"<strong>{final_data.get('pr_title','')}</strong><br>"
        f"<span style='font-family:monospace;font-size:12px;'>{final_data.get('repo','')}</span>"
        f" &nbsp;·&nbsp; by <strong>{final_data.get('pr_author','')}</strong>"
        f"</div>",
        unsafe_allow_html=True
    )

    # Score row
    score    = final_data.get("overall_score", 0)
    rec      = final_data.get("recommendation", "")
    test_sc  = final_data.get("test_coverage_score", 0)
    doc_sc   = final_data.get("documentation_score", 0)
    est_time = final_data.get("estimated_review_time_minutes", 0)
    sec_cnt  = len(final_data.get("security_findings", []))
    log_cnt  = len(final_data.get("logic_findings", []))

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    for col, num, color, label in [
        (m1, str(score),    score_color(score), "Overall score"),
        (m2, str(test_sc),  score_color(test_sc), "Test coverage"),
        (m3, str(doc_sc),   score_color(doc_sc), "Documentation"),
        (m4, str(sec_cnt),  "#1D9E75" if sec_cnt == 0 else "#A32D2D", "Security issues"),
        (m5, str(log_cnt),  "#1D9E75" if log_cnt == 0 else "#BA7517", "Logic issues"),
        (m6, f"{est_time}m", "#534AB7", "Est. review time"),
    ]:
        with col:
            st.markdown(
                f"<div class='metric-card'>"
                f"<div class='metric-num' style='color:{color};'>{num}</div>"
                f"<div class='metric-label'>{label}</div></div>",
                unsafe_allow_html=True
            )

    st.markdown("<div style='margin:14px 0;'></div>", unsafe_allow_html=True)

    # Recommendation banner
    bg, border, text_color, icon, title, desc = rec_info(rec)
    st.markdown(
        f"<div class='rec-banner' style='background:{bg};border-color:{border};'>"
        f"<div style='font-size:22px;'>{icon}</div>"
        f"<div><div style='font-size:14px;font-weight:600;color:{text_color};margin-bottom:3px;'>{title}</div>"
        f"<div style='font-size:13px;color:{text_color};opacity:0.85;line-height:1.5;'>{desc}</div></div>"
        f"</div>",
        unsafe_allow_html=True
    )

    # Summary
    summary = final_data.get("summary", "")
    if summary:
        st.markdown(
            f"<div class='summary-strip'>💬 &nbsp;{summary}</div>",
            unsafe_allow_html=True
        )

    # Three columns
    col_sec, col_logic, col_sugg = st.columns(3)

    with col_sec:
        sec_findings = final_data.get("security_findings", [])
        ok = len(sec_findings) == 0
        st.markdown(
            f"<div class='col-title'>🔒 Security"
            f"{'<span class=\"ok-pill\">✓ Clear</span>' if ok else ''}</div>",
            unsafe_allow_html=True
        )
        if ok:
            st.markdown(
                "<div class='finding finding-ok'>"
                "<div class='ftitle'>No security issues found</div>"
                "<div class='fdesc'>All source files passed the security audit.</div></div>",
                unsafe_allow_html=True
            )
        else:
            for f in sec_findings:
                sev = f.get("severity", "low").lower()
                st.markdown(
                    f"<div class='finding finding-{sev}'>"
                    f"<div class='ftitle'>[{sev.upper()}] {f.get('title','')}</div>"
                    f"<div class='ffile'>{f.get('file','')}</div>"
                    f"<div class='fdesc'>{f.get('description','')[:160]}</div></div>",
                    unsafe_allow_html=True
                )
        highlights = final_data.get("security_highlights", [])
        for h in highlights:
            st.markdown(f"<div style='font-size:12px;color:#666;padding:4px 0;'>• {h}</div>", unsafe_allow_html=True)

    with col_logic:
        log_findings = final_data.get("logic_findings", [])
        st.markdown("<div class='col-title'>🧠 Logic issues</div>", unsafe_allow_html=True)
        if not log_findings:
            st.markdown(
                "<div class='finding finding-ok'>"
                "<div class='ftitle'>No logic issues found</div></div>",
                unsafe_allow_html=True
            )
        else:
            for f in log_findings:
                sev = f.get("severity", "low").lower()
                st.markdown(
                    f"<div class='finding finding-{sev}'>"
                    f"<div class='ftitle'>[{sev.upper()}] {f.get('title','')}</div>"
                    f"<div class='ffile'>{f.get('file','')}</div>"
                    f"<div class='fdesc'>{f.get('description','')[:160]}</div></div>",
                    unsafe_allow_html=True
                )

    with col_sugg:
        st.markdown("<div class='col-title'>💡 What to fix first</div>", unsafe_allow_html=True)
        suggestions = final_data.get("top_suggestions", [])
        if suggestions:
            items = "".join([
                f"<div class='sugg-item'>"
                f"<div class='sugg-num'>{i}</div>"
                f"<div class='sugg-text'>{s}</div></div>"
                for i, s in enumerate(suggestions, 1)
            ])
            st.markdown(items, unsafe_allow_html=True)

    # Test + docs detail
    st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
    col_test, col_docs = st.columns(2)

    tc = final_data.get("test_coverage_score", 0)
    dc = final_data.get("documentation_score", 0)

    with col_test:
        with st.expander(f"🧪 Test coverage detail — {tc}/100"):
            missing = final_data.get("missing_test_cases", [])
            if missing:
                st.markdown("**Missing test cases:**")
                for m in missing:
                    st.markdown(f"<div class='missing-item'>· {m}</div>", unsafe_allow_html=True)
            else:
                st.success("No missing test cases identified.")

    with col_docs:
        with st.expander(f"📝 Documentation detail — {dc}/100"):
            missing_ds = final_data.get("missing_docstrings", [])
            missing_th = final_data.get("missing_type_hints", [])
            if missing_ds:
                st.markdown("**Missing docstrings:**")
                for m in missing_ds:
                    st.markdown(f"<div class='missing-item'>· {m}</div>", unsafe_allow_html=True)
            if missing_th:
                st.markdown("**Missing type hints:**")
                for m in missing_th:
                    st.markdown(f"<div class='missing-item'>· {m}</div>", unsafe_allow_html=True)
            if not missing_ds and not missing_th:
                st.success("Documentation looks complete.")

    # Errors (only if any)
    errors = final_data.get("errors", [])
    if errors:
        with st.expander("⚠️ Pipeline warnings"):
            for e in errors:
                st.warning(e)

if __name__ == "__main__":
    main()