import streamlit as st
import asyncio
import json
import websockets
import threading
import queue
import os

st.set_page_config(
    page_title="ReviewAgent — AI Code Review",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
[data-testid="stAppViewContainer"] { background: #f4f3f0; }
[data-testid="stMain"] { padding: 0 !important; }
[data-testid="stMainBlockContainer"] { padding: 0 !important; max-width: 100% !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }
section[data-testid="stSidebar"] { display: none; }
footer { display: none; }
#MainMenu { display: none; }
header[data-testid="stHeader"] { display: none; }

.ra-nav {
    background: #fff;
    border-bottom: 0.5px solid #e5e5e2;
    padding: 0 40px;
    height: 56px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.ra-logo-icon {
    width: 30px; height: 30px;
    background: #1a1a1a; border-radius: 8px;
    display: inline-flex; align-items: center;
    justify-content: center; margin-right: 10px;
    vertical-align: middle;
}
.ra-logo-name {
    font-size: 15px; font-weight: 700;
    color: #1a1a1a; letter-spacing: -0.02em;
    vertical-align: middle;
}
.ra-nav-right { display: flex; align-items: center; gap: 8px; }
.ra-pill {
    font-size: 11px; font-weight: 600;
    padding: 4px 10px; border-radius: 99px; border: 0.5px solid;
}
.ra-pill-green { background: #E1F5EE; color: #0F6E56; border-color: #5DCAA5; }
.ra-pill-gray  { background: #f4f3f0; color: #888;    border-color: #ddd; }

.ra-wrap { max-width: 1080px; margin: 0 auto; padding: 40px 24px 60px; }

.ra-hero { text-align: center; padding: 52px 24px 44px; }
.ra-eyebrow {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 11px; font-weight: 700; letter-spacing: 0.08em;
    text-transform: uppercase; color: #534AB7;
    background: #EEEDFE; padding: 5px 14px;
    border-radius: 99px; margin-bottom: 22px;
}
.ra-h1 {
    font-size: 44px; font-weight: 800; color: #1a1a1a;
    letter-spacing: -0.04em; line-height: 1.1; margin-bottom: 16px;
}
.ra-sub {
    font-size: 18px; color: #777; max-width: 500px;
    margin: 0 auto 36px; line-height: 1.6; font-weight: 400;
}

.ra-how-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 14px; margin-bottom: 36px;
}
.ra-how-card {
    background: #fff; border: 0.5px solid #e8e8e4;
    border-radius: 14px; padding: 20px;
    display: flex; gap: 14px; align-items: flex-start;
}
.ra-how-num {
    width: 30px; height: 30px; border-radius: 9px;
    background: #1a1a1a; color: #fff; font-size: 13px;
    font-weight: 700; display: flex; align-items: center;
    justify-content: center; flex-shrink: 0;
}
.ra-how-title { font-size: 13px; font-weight: 600; color: #1a1a1a; margin-bottom: 4px; }
.ra-how-desc  { font-size: 12px; color: #999; line-height: 1.6; }

.ra-divider {
    display: flex; align-items: center;
    gap: 14px; margin: 28px 0 18px;
}
.ra-divider-line  { flex: 1; height: 0.5px; background: #e8e8e4; }
.ra-divider-label {
    font-size: 11px; font-weight: 700; color: #bbb;
    letter-spacing: 0.08em; text-transform: uppercase; white-space: nowrap;
}

.ra-progress-card {
    background: #fff; border: 0.5px solid #e8e8e4;
    border-radius: 16px; padding: 22px 24px; margin-bottom: 24px;
}
.ra-progress-header {
    display: flex; justify-content: space-between;
    align-items: center; margin-bottom: 16px;
}
.ra-progress-title { font-size: 13px; font-weight: 600; color: #1a1a1a; }
.ra-progress-count { font-size: 12px; color: #aaa; font-weight: 500; }
.ra-pbar-bg {
    height: 3px; background: #f0f0ec;
    border-radius: 99px; margin-bottom: 20px; overflow: hidden;
}
.ra-pbar-fill {
    height: 3px; background: #7F77DD;
    border-radius: 99px; transition: width 0.4s ease;
}
.ra-agent-row {
    display: flex; align-items: center; gap: 12px;
    padding: 10px 0; border-bottom: 0.5px solid #f5f5f2;
}
.ra-agent-row:last-child { border-bottom: none; padding-bottom: 0; }
.ra-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.ra-dot-wait { background: #ddd; }
.ra-dot-run  { background: #7F77DD; }
.ra-dot-done { background: #1D9E75; }
.ra-dot-err  { background: #E24B4A; }
.ra-agent-icon {
    width: 30px; height: 30px; border-radius: 8px;
    display: flex; align-items: center;
    justify-content: center; font-size: 14px; flex-shrink: 0;
}
.ra-icon-wait { background: #f4f3f0; }
.ra-icon-run  { background: #EEEDFE; }
.ra-icon-done { background: #E1F5EE; }
.ra-icon-err  { background: #FCEBEB; }
.ra-agent-name   { font-size: 13px; font-weight: 500; color: #1a1a1a; margin-bottom: 2px; }
.ra-agent-detail { font-size: 11px; color: #bbb; }
.ra-agent-detail-done { color: #1D9E75; }
.ra-agent-detail-run  { color: #7F77DD; }
.ra-badge {
    font-size: 10px; font-weight: 700; padding: 3px 8px;
    border-radius: 99px; letter-spacing: 0.04em; text-transform: uppercase;
}
.ra-badge-wait { background: #f4f3f0; color: #bbb; }
.ra-badge-run  { background: #EEEDFE; color: #534AB7; }
.ra-badge-done { background: #E1F5EE; color: #0F6E56; }
.ra-badge-err  { background: #FCEBEB; color: #A32D2D; }

.ra-score-grid {
    display: grid; grid-template-columns: repeat(6, 1fr);
    gap: 10px; margin-bottom: 18px;
}
.ra-score-card {
    background: #fff; border: 0.5px solid #e8e8e4;
    border-radius: 12px; padding: 16px 10px; text-align: center;
}
.ra-score-num {
    font-size: 28px; font-weight: 800;
    letter-spacing: -0.04em; line-height: 1; margin-bottom: 6px;
}
.ra-score-lbl {
    font-size: 10px; font-weight: 600; color: #bbb;
    text-transform: uppercase; letter-spacing: 0.06em;
}
.c-green  { color: #1D9E75; }
.c-amber  { color: #BA7517; }
.c-red    { color: #E24B4A; }
.c-purple { color: #534AB7; }

.ra-rec-card {
    border-radius: 14px; padding: 18px 22px;
    margin-bottom: 18px; display: flex;
    gap: 14px; align-items: flex-start;
}
.ra-rec-approve  { background: #F0FBF6; border: 1px solid #5DCAA5; }
.ra-rec-request  { background: #FFF8F6; border: 1px solid #F0997B; }
.ra-rec-discuss  { background: #FFFBF2; border: 1px solid #EF9F27; }
.ra-rec-icon {
    width: 38px; height: 38px; border-radius: 10px;
    display: flex; align-items: center;
    justify-content: center; font-size: 20px; flex-shrink: 0;
}
.ra-rec-title-approve { font-size: 15px; font-weight: 700; color: #085041; margin-bottom: 4px; }
.ra-rec-title-request { font-size: 15px; font-weight: 700; color: #712B13; margin-bottom: 4px; }
.ra-rec-title-discuss { font-size: 15px; font-weight: 700; color: #633806; margin-bottom: 4px; }
.ra-rec-desc-approve  { font-size: 13px; color: #0F6E56; line-height: 1.6; }
.ra-rec-desc-request  { font-size: 13px; color: #993C1D; line-height: 1.6; }
.ra-rec-desc-discuss  { font-size: 13px; color: #854F0B; line-height: 1.6; }

.ra-summary {
    background: #EEEDFE; border-radius: 12px;
    padding: 16px 18px; margin-bottom: 20px;
    font-size: 13px; color: #3C3489; line-height: 1.7;
    display: flex; gap: 10px;
}

.ra-cols {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 14px; margin-bottom: 16px;
}
.ra-col-card {
    background: #fff; border: 0.5px solid #e8e8e4;
    border-radius: 14px; padding: 18px;
}
.ra-col-head {
    display: flex; align-items: center;
    justify-content: space-between; margin-bottom: 14px;
}
.ra-col-title {
    font-size: 13px; font-weight: 700; color: #1a1a1a;
    display: flex; align-items: center; gap: 6px;
}
.ra-finding {
    border-left: 3px solid #e0e0e0; padding: 9px 12px;
    margin-bottom: 8px; border-radius: 0 8px 8px 0; background: #fafaf8;
}
.ra-finding:last-child { margin-bottom: 0; }
.ra-f-critical { border-left-color: #E24B4A; }
.ra-f-high     { border-left-color: #D85A30; }
.ra-f-medium   { border-left-color: #EF9F27; }
.ra-f-low      { border-left-color: #378ADD; }
.ra-f-ok       { border-left-color: #1D9E75; }
.ra-f-sev {
    font-size: 9px; font-weight: 800;
    letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 3px;
}
.ra-f-sev-critical { color: #E24B4A; }
.ra-f-sev-high     { color: #D85A30; }
.ra-f-sev-medium   { color: #BA7517; }
.ra-f-sev-low      { color: #185FA5; }
.ra-f-sev-ok       { color: #0F6E56; }
.ra-f-title { font-size: 12px; font-weight: 600; color: #1a1a1a; margin-bottom: 2px; }
.ra-f-file  { font-size: 10px; color: #ccc; font-family: monospace; margin-bottom: 4px; }
.ra-f-desc  { font-size: 11px; color: #888; line-height: 1.5; }

.ra-sugg-item { display: flex; gap: 10px; margin-bottom: 10px; align-items: flex-start; }
.ra-sugg-item:last-child { margin-bottom: 0; }
.ra-sugg-n {
    width: 20px; height: 20px; border-radius: 6px;
    background: #1a1a1a; color: #fff; font-size: 10px;
    font-weight: 700; display: flex; align-items: center;
    justify-content: center; flex-shrink: 0; margin-top: 1px;
}
.ra-sugg-t { font-size: 12px; color: #555; line-height: 1.6; }

.ra-detail-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px; margin-bottom: 24px;
}
.ra-detail-card {
    background: #fff; border: 0.5px solid #e8e8e4;
    border-radius: 14px; padding: 18px;
}
.ra-detail-head {
    display: flex; align-items: center;
    justify-content: space-between; margin-bottom: 14px;
}
.ra-detail-title { font-size: 13px; font-weight: 700; color: #1a1a1a; }
.ra-ring {
    width: 42px; height: 42px; border-radius: 50%;
    border: 3px solid #E1F5EE; display: flex;
    align-items: center; justify-content: center;
    font-size: 12px; font-weight: 800; color: #1D9E75;
}
.ra-ring-amber { border-color: #FAEEDA; color: #BA7517; }
.ra-missing-row {
    display: flex; gap: 10px; align-items: flex-start;
    padding: 7px 0; border-bottom: 0.5px solid #f5f5f2;
    font-size: 12px; color: #666; line-height: 1.5;
}
.ra-missing-row:last-child { border-bottom: none; }
.ra-missing-dot {
    width: 5px; height: 5px; border-radius: 50%;
    background: #EF9F27; flex-shrink: 0; margin-top: 6px;
}

.ra-footer {
    text-align: center; padding: 32px 0 8px;
    font-size: 11px; color: #ccc;
    border-top: 0.5px solid #e8e8e4; margin-top: 8px;
}
.ra-footer a { color: #7F77DD; text-decoration: none; }

.stButton > button {
    background: #1a1a1a !important; color: #fff !important;
    border: none !important; border-radius: 10px !important;
    font-size: 14px !important; font-weight: 600 !important;
    padding: 10px 24px !important; letter-spacing: -0.01em !important;
    height: 44px !important;
}
.stButton > button:hover { background: #333 !important; }
.stTextInput > div > div > input {
    border-radius: 10px !important;
    border: 1.5px solid #e0e0dc !important;
    font-size: 15px !important; height: 44px !important;
    padding: 0 16px !important; background: #fff !important;
}
.stTextInput > div > div > input:focus {
    border-color: #7F77DD !important;
    box-shadow: 0 0 0 3px rgba(127,119,221,0.12) !important;
}

.ra-author-row   { }
.ra-diff-mobile  { display: none; }
.ra-diff-desktop { display: block; }

.ra-diff-card {
    background: #fff; border: 0.5px solid #e8e8e4;
    border-radius: 14px; padding: 18px 20px; margin-bottom: 24px;
}
.ra-diff-card-title {
    font-size: 13px; font-weight: 700; color: #1a1a1a; margin-bottom: 14px;
    padding-bottom: 10px; border-bottom: 0.5px solid #f0f0ec;
}
.ra-diff-link {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 12px; font-weight: 600; color: #534AB7;
    text-decoration: none; padding: 8px 16px;
    border: 0.5px solid #AFA9EC; border-radius: 99px;
    background: #EEEDFE;
}
.ra-diff-link:hover { background: #e0defe; }
.ra-diff-mobile-btn {
    display: flex; align-items: center; justify-content: center; gap: 8px;
    width: 100%; background: #1a1a1a; color: #fff;
    border: none; border-radius: 10px; padding: 13px 20px;
    font-size: 14px; font-weight: 600; cursor: pointer;
    margin-bottom: 24px; text-decoration: none;
}

@media (max-width: 768px) {
    .ra-author-row   { display: none !important; }
    .ra-diff-mobile  { display: block; }
    .ra-diff-desktop { display: none; }
}

@media (max-width: 768px) {
    .ra-nav { padding: 0 16px; }

    .ra-wrap { padding: 20px 14px 40px; }

    .ra-hero { padding: 32px 12px 24px; }
    .ra-h1 { font-size: 28px; letter-spacing: -0.03em; }
    .ra-sub { font-size: 15px; margin-bottom: 24px; }

    .ra-how-grid { grid-template-columns: 1fr; gap: 10px; margin-top: 20px !important; }

    .ra-score-grid { grid-template-columns: repeat(3, 1fr); }
    .ra-score-num  { font-size: 22px; }

    .ra-cols        { grid-template-columns: 1fr; gap: 10px; }
    .ra-col-card    { padding: 14px; }
    .ra-col-head    { margin-bottom: 10px; }
    .ra-col-title   { font-size: 12px; }
    .ra-finding     { padding: 8px 10px; margin-bottom: 6px; overflow: hidden; }
    .ra-f-title     { font-size: 11px; word-break: break-word; overflow-wrap: break-word; }
    .ra-f-file      { word-break: break-all; overflow-wrap: break-word; white-space: normal; }
    .ra-f-desc      { font-size: 10px; word-break: break-word; overflow-wrap: break-word; }
    .ra-sugg-t      { font-size: 11px; word-break: break-word; overflow-wrap: break-word; }
    .ra-detail-grid { grid-template-columns: 1fr; }

    .ra-rec-card { padding: 14px 16px; }

    .ra-progress-card { padding: 16px; }

    /* make Streamlit columns stack on mobile */
    [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
        gap: 8px !important;
    }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        min-width: 0 !important;
        flex: 1 1 auto !important;
    }

    /* hide the spacer columns, let input+button fill the row */
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child,
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child {
        display: none !important;
    }

    .stButton > button { font-size: 13px !important; padding: 10px 14px !important; }
}
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
    if score >= 80: return "c-green"
    if score >= 60: return "c-amber"
    return "c-red"

def agent_html(agent_id, emoji, label, state, detail=""):
    dot_cls   = {"wait":"ra-dot-wait","run":"ra-dot-run","done":"ra-dot-done","err":"ra-dot-err"}.get(state,"ra-dot-wait")
    icon_cls  = {"wait":"ra-icon-wait","run":"ra-icon-run","done":"ra-icon-done","err":"ra-icon-err"}.get(state,"ra-icon-wait")
    badge_cls = {"wait":"ra-badge-wait","run":"ra-badge-run","done":"ra-badge-done","err":"ra-badge-err"}.get(state,"ra-badge-wait")
    badge_lbl = {"wait":"Waiting","run":"Running","done":"Done","err":"Error"}.get(state,"Waiting")
    det_cls   = {"run":"ra-agent-detail-run","done":"ra-agent-detail-done"}.get(state,"")
    return f"""
    <div class="ra-agent-row">
      <div class="ra-dot {dot_cls}"></div>
      <div class="ra-agent-icon {icon_cls}">{emoji}</div>
      <div style="flex:1;">
        <div class="ra-agent-name">{label}</div>
        <div class="ra-agent-detail {det_cls}">{detail or '&nbsp;'}</div>
      </div>
      <span class="ra-badge {badge_cls}">{badge_lbl}</span>
    </div>"""

def rec_html(rec):
    cfg = {
        "APPROVE":          ("ra-rec-approve","✅","#E1F5EE","ra-rec-title-approve","ra-rec-desc-approve",
                             "Looks good to merge",
                             "No significant issues were found. This PR is ready to merge."),
        "REQUEST_CHANGES":  ("ra-rec-request","⚠️","#FAECE7","ra-rec-title-request","ra-rec-desc-request",
                             "Changes requested before merge",
                             "There are issues that should be addressed before this PR is merged."),
        "NEEDS_DISCUSSION": ("ra-rec-discuss","💬","#FAEEDA","ra-rec-title-discuss","ra-rec-desc-discuss",
                             "Needs team discussion",
                             "This PR has tradeoffs that the team should discuss before merging."),
    }.get(rec, ("ra-rec-discuss","💬","#FAEEDA","ra-rec-title-discuss","ra-rec-desc-discuss", rec, ""))
    card_cls, icon, icon_bg, title_cls, desc_cls, title, desc = cfg
    return f"""
    <div class="ra-rec-card {card_cls}">
      <div class="ra-rec-icon" style="background:{icon_bg};">{icon}</div>
      <div>
        <div class="{title_cls}">{title}</div>
        <div class="{desc_cls}">{desc}</div>
      </div>
    </div>"""

def finding_html(findings, kind):
    if not findings:
        return f'<div class="ra-finding ra-f-ok"><div class="ra-f-sev ra-f-sev-ok">ALL CLEAR</div><div class="ra-f-title">No {kind} issues found</div></div>'
    out = ""
    for f in findings:
        sev = f.get("severity", "low").lower()
        out += f"""<div class="ra-finding ra-f-{sev}">
          <div class="ra-f-sev ra-f-sev-{sev}">{sev.upper()}</div>
          <div class="ra-f-title">{f.get('title','')}</div>
          <div class="ra-f-file">{f.get('file','')}</div>
          <div class="ra-f-desc">{f.get('description','')[:160]}</div>
        </div>"""
    return out

def author_card_html(final_data):
    author      = final_data.get('pr_author', '')
    repo        = final_data.get('repo', '')
    pr_title    = final_data.get('pr_title', '')
    pr_num      = final_data.get('pr_number', '')
    additions   = final_data.get('additions', 0)
    deletions   = final_data.get('deletions', 0)
    avatar_url  = f"https://avatars.githubusercontent.com/{author}?s=88"
    gh_pr_url   = f"https://github.com/{repo}/pull/{pr_num}" if pr_num else "#"
    gh_user_url = f"https://github.com/{author}"
    initials    = "".join([w[0].upper() for w in author.replace("-"," ").split()[:2]]) if author else "?"

    return f"""
    <div style="background:#fff;border:0.5px solid #e8e8e4;border-radius:14px;
                padding:20px 22px;margin-bottom:18px;">

      <div style="display:flex;align-items:flex-start;gap:12px;margin-bottom:14px;">
        <span style="font-size:11px;font-weight:700;color:#534AB7;background:#EEEDFE;
                     padding:3px 9px;border-radius:6px;flex-shrink:0;margin-top:2px;">
          #{pr_num}
        </span>
        <span style="font-size:15px;font-weight:700;color:#1a1a1a;
                     line-height:1.4;letter-spacing:-0.01em;">
          {pr_title}
        </span>
      </div>

      <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px;">
        <span style="font-size:11px;padding:3px 9px;border-radius:99px;
                     background:#EEEDFE;color:#534AB7;border:0.5px solid #AFA9EC;">
          {repo}
        </span>
        <span style="font-size:11px;padding:3px 9px;border-radius:99px;
                     background:#fafaf8;color:#666;border:0.5px solid #e8e8e4;">
          +{additions} / −{deletions} lines
        </span>
      </div>

      <div style="height:0.5px;background:#f0f0ec;margin-bottom:14px;"></div>

      <div class="ra-author-row" style="display:flex;align-items:center;gap:12px;">
        <div style="position:relative;flex-shrink:0;">
          <img src="{avatar_url}"
               width="36" height="36"
               style="border-radius:50%;border:2px solid #fff;
                      outline:2px solid #e8e8e4;object-fit:cover;display:block;"
               onerror="this.style.display='none';
                        this.nextElementSibling.style.display='flex';" />
          <div style="display:none;width:36px;height:36px;border-radius:50%;
                      background:#EEEDFE;color:#534AB7;font-size:12px;font-weight:700;
                      align-items:center;justify-content:center;">
            {initials}
          </div>
        </div>

        <div style="flex:1;min-width:0;">
          <div style="font-size:13px;font-weight:600;color:#1a1a1a;
                      margin-bottom:2px;">{author}</div>
          <div style="font-size:11px;color:#aaa;font-family:monospace;">
            github.com/{author}
          </div>
        </div>

        <div style="display:flex;gap:8px;flex-shrink:0;">
          <a href="{gh_user_url}" target="_blank"
             style="font-size:11px;color:#534AB7;text-decoration:none;
                    display:inline-flex;align-items:center;gap:4px;
                    padding:5px 12px;border:0.5px solid #AFA9EC;
                    border-radius:99px;background:#EEEDFE;font-weight:600;">
            View profile ↗
          </a>
          <a href="{gh_pr_url}" target="_blank"
             style="font-size:11px;color:#fff;text-decoration:none;
                    display:inline-flex;align-items:center;gap:4px;
                    padding:5px 12px;border:none;border-radius:99px;
                    background:#1a1a1a;font-weight:600;">
            View PR ↗
          </a>
        </div>
      </div>
    </div>"""

def main():
    st.markdown("""
    <div class="ra-nav">
      <div>
        <div class="ra-logo-icon">🔍</div>
        <span class="ra-logo-name">ReviewAgent</span>
      </div>
      <div class="ra-nav-right">
        <span class="ra-pill ra-pill-green">● API live</span>
        <span class="ra-pill ra-pill-gray">v1.0</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="ra-wrap">', unsafe_allow_html=True)

    st.markdown("""
    <div class="ra-hero">
      <div class="ra-eyebrow">⚡ Powered by GPT-4o + LangGraph</div>
      <h1 class="ra-h1">AI code review<br>in 30 seconds</h1>
      <p class="ra-sub" style="text-align:center;margin-left:auto;margin-right:auto;">
      Paste any GitHub pull request. Five specialist agents check
      security, logic, test coverage, and docs — then deliver a structured report.</p>
    """, unsafe_allow_html=True)

    _, col_input, col_btn, _ = st.columns([2, 3.5, 0.8, 2])
    with col_input:
        pr_url = st.text_input(
            "pr_url",
            placeholder="https://github.com/owner/repo/pull/123",
            label_visibility="collapsed",
        )
    with col_btn:
        analyze = st.button("Analyze PR →", use_container_width=True)

    st.markdown(
        "<p style='font-size:12px;color:#bbb;margin-top:6px;text-align:center;'>"
        "Try: https://github.com/fastapi/fastapi/pull/15508 · Any public GitHub PR works</p>",
        unsafe_allow_html=True
    )

    st.markdown("""
    <div class="ra-how-grid" style="margin-top:32px;">
      <div class="ra-how-card">
        <div class="ra-how-num">1</div>
        <div>
          <div class="ra-how-title">Paste a GitHub PR link</div>
          <div class="ra-how-desc">Any public repository works.
          Just copy the URL from your browser.</div>
        </div>
      </div>
      <div class="ra-how-card">
        <div class="ra-how-num">2</div>
        <div>
          <div class="ra-how-title">Five agents review it live</div>
          <div class="ra-how-desc">Security, logic, tests, docs, and synthesis
          all run and report back in real time.</div>
        </div>
      </div>
      <div class="ra-how-card">
        <div class="ra-how-num">3</div>
        <div>
          <div class="ra-how-title">Get a structured report</div>
          <div class="ra-how-desc">A score out of 100, a merge recommendation,
          and exactly what to fix first.</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if not analyze or not pr_url.strip():
        st.markdown('</div>', unsafe_allow_html=True)
        return

    if "github.com" not in pr_url or "/pull/" not in pr_url:
        st.error("Please enter a valid GitHub PR URL — e.g. https://github.com/owner/repo/pull/123")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    st.markdown("""
    <div class="ra-divider">
      <div class="ra-divider-line"></div>
      <span class="ra-divider-label">Live agent progress</span>
      <div class="ra-divider-line"></div>
    </div>
    """, unsafe_allow_html=True)

    progress_slot = st.empty()
    status_slot   = st.empty()

    agent_states = {a[0]: ("wait", "") for a in AGENTS}
    done_count   = 0
    total        = len(AGENTS)
    final_data   = None

    def render_progress(states):
        rows = ""
        for aid, emoji, label in AGENTS:
            state, detail = states[aid]
            rows += agent_html(aid, emoji, label, state, detail)
        completed = sum(1 for s, _ in states.values() if s == "done")
        pct = int((completed / total) * 100)
        progress_slot.markdown(f"""
        <div class="ra-progress-card">
          <div class="ra-progress-header">
            <span class="ra-progress-title">Analyzing PR</span>
            <span class="ra-progress-count">{completed} of {total} agents complete</span>
          </div>
          <div class="ra-pbar-bg">
            <div class="ra-pbar-fill" style="width:{pct}%;"></div>
          </div>
          {rows}
        </div>
        """, unsafe_allow_html=True)

    render_progress(agent_states)
    status_slot.info("🚀 Connecting to agent pipeline...")

    eq = queue.Queue()
    threading.Thread(
        target=run_websocket, args=(pr_url.strip(), eq), daemon=True
    ).start()

    while True:
        try:
            ev = eq.get(timeout=90)
        except queue.Empty:
            status_slot.error("⏱ Timed out. Make sure the API server is running.")
            break

        etype = ev.get("type")
        agent = ev.get("agent", "")
        msg   = ev.get("message", "")
        data  = ev.get("data", {})

        if etype == "agent_start":
            agent_states[agent] = ("run", "Running...")
            render_progress(agent_states)

        elif etype == "agent_done":
            done_count += 1
            detail = ""
            if agent == "fetch_pr":
                detail = f"+{data.get('additions',0)} / -{data.get('deletions',0)} lines · {data.get('files',0)} file(s)"
            elif agent == "security":
                c = data.get("count", 0)
                detail = "No issues found ✓" if c == 0 else f"{c} issue(s) found"
            elif agent == "logic":
                c = data.get("count", 0)
                detail = f"{c} issue(s) found"
            elif agent in ("test_coverage", "documentation"):
                detail = f"Score: {data.get('score', 0)}/100"
            else:
                detail = msg
            agent_states[agent] = ("done", detail)
            render_progress(agent_states)

        elif etype == "complete":
            agent_states["synthesis"] = ("done", "Complete")
            render_progress(agent_states)
            status_slot.success("✅ Review complete!")
            final_data = ev.get("data", {})
            break

        elif etype == "error":
            status_slot.error(f"❌ {msg}")
            break

    if not final_data:
        st.markdown('</div>', unsafe_allow_html=True)
        return

    st.markdown("""
    <div class="ra-divider">
      <div class="ra-divider-line"></div>
      <span class="ra-divider-label">Review report</span>
      <div class="ra-divider-line"></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(author_card_html(final_data), unsafe_allow_html=True)

    score   = final_data.get("overall_score", 0)
    rec     = final_data.get("recommendation", "")
    test_sc = final_data.get("test_coverage_score", 0)
    doc_sc  = final_data.get("documentation_score", 0)
    est_t   = final_data.get("estimated_review_time_minutes", 0)
    sec_cnt = len(final_data.get("security_findings", []))
    log_cnt = len(final_data.get("logic_findings", []))

    sc    = score_color(score)
    tc    = score_color(test_sc)
    dc    = score_color(doc_sc)
    sec_c = "c-green" if sec_cnt == 0 else "c-red"
    log_c = "c-green" if log_cnt == 0 else "c-amber"

    st.markdown(f"""
    <div class="ra-score-grid">
      <div class="ra-score-card">
        <div class="ra-score-num {sc}">{score}</div>
        <div class="ra-score-lbl">Overall</div>
      </div>
      <div class="ra-score-card">
        <div class="ra-score-num {tc}">{test_sc}</div>
        <div class="ra-score-lbl">Tests</div>
      </div>
      <div class="ra-score-card">
        <div class="ra-score-num {dc}">{doc_sc}</div>
        <div class="ra-score-lbl">Docs</div>
      </div>
      <div class="ra-score-card">
        <div class="ra-score-num {sec_c}"
             style="font-size:{'16px' if sec_cnt==0 else '28px'};
                    {'padding-top:6px;' if sec_cnt==0 else ''}">
          {'None' if sec_cnt == 0 else sec_cnt}
        </div>
        <div class="ra-score-lbl">Security</div>
      </div>
      <div class="ra-score-card">
        <div class="ra-score-num {log_c}">{log_cnt}</div>
        <div class="ra-score-lbl">Logic</div>
      </div>
      <div class="ra-score-card">
        <div class="ra-score-num c-purple">{est_t}m</div>
        <div class="ra-score-lbl">Est. review</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(rec_html(rec), unsafe_allow_html=True)

    summary = final_data.get("summary", "")
    if summary:
        st.markdown(
            f'<div class="ra-summary">'
            f'<span style="font-size:18px;flex-shrink:0;">💬</span>'
            f'<span>{summary}</span></div>',
            unsafe_allow_html=True
        )

    sec_findings = final_data.get("security_findings", [])
    log_findings = final_data.get("logic_findings", [])
    suggestions  = final_data.get("top_suggestions", [])

    sugg_html = "".join([
        f'<div class="ra-sugg-item">'
        f'<div class="ra-sugg-n">{i}</div>'
        f'<div class="ra-sugg-t">{s}</div></div>'
        for i, s in enumerate(suggestions, 1)
    ]) or "<p style='font-size:12px;color:#aaa;'>No suggestions.</p>"

    sec_badge = (
        '<span class="ra-badge ra-badge-done" style="margin-left:6px;">Clear</span>'
        if not sec_findings else
        f'<span class="ra-badge" style="background:#FCEBEB;color:#A32D2D;'
        f'margin-left:6px;">{len(sec_findings)} found</span>'
    )
    log_badge = (
        "" if not log_findings else
        f'<span class="ra-badge" style="background:#FAEEDA;color:#854F0B;'
        f'margin-left:6px;">{len(log_findings)} found</span>'
    )

    st.markdown(f"""
    <div class="ra-cols">
      <div class="ra-col-card">
        <div class="ra-col-head">
          <div class="ra-col-title">Security {sec_badge}</div>
        </div>
        {finding_html(sec_findings, "security")}
      </div>
      <div class="ra-col-card">
        <div class="ra-col-head">
          <div class="ra-col-title">Logic issues {log_badge}</div>
        </div>
        {finding_html(log_findings, "logic")}
      </div>
      <div class="ra-col-card">
        <div class="ra-col-head">
          <div class="ra-col-title">What to fix first</div>
        </div>
        {sugg_html}
      </div>
    </div>
    """, unsafe_allow_html=True)

    import re as _re
    _m = _re.search(r'/pull/(\d+)', pr_url)
    _pr_num = _m.group(1) if _m else ''
    _repo   = final_data.get('repo', '')
    _diff_url = f"https://github.com/{_repo}/pull/{_pr_num}/files" if _pr_num else f"https://github.com/{_repo}"

    st.markdown(f"""
    <div class="ra-diff-desktop">
      <div class="ra-diff-card">
        <div class="ra-diff-card-title">Code Diff</div>
        <p style="font-size:12px;color:#888;margin-bottom:14px;line-height:1.6;">
          View the full file-by-file diff for this pull request on GitHub.
        </p>
        <a href="{_diff_url}" target="_blank" class="ra-diff-link">
          View diff on GitHub ↗
        </a>
      </div>
    </div>
    <div class="ra-diff-mobile">
      <a href="{_diff_url}" target="_blank" class="ra-diff-mobile-btn">
        GitHub Diff View ↗
      </a>
    </div>
    """, unsafe_allow_html=True)

    missing_tests = "".join([
        f'<div class="ra-missing-row">'
        f'<div class="ra-missing-dot"></div><div>{m}</div></div>'
        for m in final_data.get("missing_test_cases", [])
    ]) or (
        '<div class="ra-missing-row">'
        '<div class="ra-missing-dot" style="background:#1D9E75;"></div>'
        '<div>No missing test cases identified</div></div>'
    )

    missing_docs = "".join([
        f'<div class="ra-missing-row">'
        f'<div class="ra-missing-dot" style="background:#BA7517;"></div>'
        f'<div>{m}</div></div>'
        for m in (
            final_data.get("missing_docstrings", []) +
            final_data.get("missing_type_hints", [])
        )
    ]) or (
        '<div class="ra-missing-row">'
        '<div class="ra-missing-dot" style="background:#1D9E75;"></div>'
        '<div>Documentation looks complete</div></div>'
    )

    ring_tc = "ra-ring" if test_sc >= 80 else "ra-ring ra-ring-amber"
    ring_dc = "ra-ring" if doc_sc  >= 80 else "ra-ring ra-ring-amber"

    st.markdown(f"""
    <div class="ra-detail-grid">
      <div class="ra-detail-card">
        <div class="ra-detail-head">
          <div class="ra-detail-title">🧪 Test coverage</div>
          <div class="{ring_tc}">{test_sc}</div>
        </div>
        {missing_tests}
      </div>
      <div class="ra-detail-card">
        <div class="ra-detail-head">
          <div class="ra-detail-title">📝 Documentation</div>
          <div class="{ring_dc}">{doc_sc}</div>
        </div>
        {missing_docs}
      </div>
    </div>
    """, unsafe_allow_html=True)

    errors = final_data.get("errors", [])
    if errors:
        with st.expander("⚠️ Pipeline warnings"):
            for e in errors:
                st.warning(e)

    st.markdown("""
    <div class="ra-footer">
      Built with LangGraph · GPT-4o · FastAPI · Streamlit
      &nbsp;·&nbsp;
      <a href="https://github.com/Satwik-Pamulaparthy/pr-review-agent">View on GitHub</a>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()