import streamlit as st
import asyncio
import json
import websockets
import threading
import queue
import os

st.set_page_config(
    page_title="Revora — AI PR Reviews",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
[data-testid="stAppViewContainer"] { background: #09090b !important; }
[data-testid="stMain"]             { padding: 0 !important; }
[data-testid="stMainBlockContainer"]{ padding: 0 !important; max-width: 100% !important; }
.block-container                   { padding: 0 !important; max-width: 100% !important; }
section[data-testid="stSidebar"]   { display: none; }
footer { display: none; }
#MainMenu { display: none; }
header[data-testid="stHeader"] { display: none; }

/* ── Animated background ── */
.rv-bg {
    position: fixed; top: 0; left: 0;
    width: 100%; height: 100%;
    overflow: hidden; pointer-events: none; z-index: 0;
    background: #09090b;
}
.rv-blob {
    position: absolute; border-radius: 50%;
    filter: blur(100px); pointer-events: none;
    animation: blobDrift ease-in-out infinite;
}
.rv-blob-1 {
    width: 700px; height: 700px;
    background: radial-gradient(circle, rgba(139,92,246,0.22), transparent 70%);
    top: -220px; left: -160px; animation-duration: 14s;
}
.rv-blob-2 {
    width: 600px; height: 600px;
    background: radial-gradient(circle, rgba(59,130,246,0.18), transparent 70%);
    top: -80px; right: -160px; animation-duration: 18s; animation-direction: reverse;
}
.rv-blob-3 {
    width: 500px; height: 500px;
    background: radial-gradient(circle, rgba(139,92,246,0.14), transparent 70%);
    bottom: 5%; left: 28%; animation-duration: 11s; animation-delay: -5s;
}
@keyframes blobDrift {
    0%, 100% { transform: translate(0,    0);    }
    33%       { transform: translate(40px,-30px); }
    66%       { transform: translate(-28px,22px); }
}

.rv-particle {
    position: absolute; border-radius: 50%;
    background: rgba(139,92,246,0.45);
    animation: particleRise linear infinite;
    pointer-events: none;
}
@keyframes particleRise {
    0%   { transform: translateY(100vh); opacity: 0; }
    6%   { opacity: 1; }
    94%  { opacity: 0.5; }
    100% { transform: translateY(-8vh);  opacity: 0; }
}

.rv-code-line {
    position: absolute;
    font-family: 'Fira Code', 'JetBrains Mono', monospace;
    font-size: 11px; color: rgba(139,92,246,0.14);
    animation: codeRise linear infinite;
    pointer-events: none; white-space: nowrap;
}
@keyframes codeRise {
    0%   { transform: translateY(105vh); opacity: 0; }
    8%   { opacity: 1; }
    92%  { opacity: 0.7; }
    100% { transform: translateY(-6vh);  opacity: 0; }
}

/* ── Nav ── */
.rv-nav {
    position: relative; z-index: 10;
    background: rgba(9,9,11,0.75);
    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    border-bottom: 1px solid rgba(255,255,255,0.06);
    padding: 0 40px; height: 60px;
    display: flex; align-items: center; justify-content: space-between;
}
.rv-nav-logo {
    display: flex; align-items: center; gap: 10px;
    font-size: 17px; font-weight: 800; letter-spacing: -0.03em;
    background: linear-gradient(135deg, #fff 0%, #c4b5fd 50%, #93c5fd 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}
.rv-nav-right { display: flex; align-items: center; gap: 8px; }
.rv-pill {
    font-size: 11px; font-weight: 600;
    padding: 4px 10px; border-radius: 99px; border: 1px solid;
}
.rv-pill-green { background: rgba(34,197,94,0.1);   color: #4ade80; border-color: rgba(34,197,94,0.25); }
.rv-pill-gray  { background: rgba(255,255,255,0.04); color: #52525b; border-color: rgba(255,255,255,0.08); }

/* ── Hero ── */
.rv-hero {
    position: relative; z-index: 5;
    text-align: center; padding: 88px 24px 16px;
}
.rv-eyebrow {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 11px; font-weight: 700; letter-spacing: 0.1em;
    text-transform: uppercase; color: #a78bfa;
    background: rgba(139,92,246,0.1); padding: 5px 14px;
    border-radius: 99px; margin-bottom: 28px;
    border: 1px solid rgba(139,92,246,0.22);
    animation: fadeInUp 0.6s ease both;
}
.rv-h1 {
    font-size: 62px; font-weight: 900;
    background: linear-gradient(135deg, #ffffff 0%, #c4b5fd 45%, #93c5fd 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.045em; line-height: 1.06; margin-bottom: 22px;
    animation: fadeInUp 0.6s 0.1s ease both;
}
.rv-sub {
    font-size: 17px; color: #52525b; max-width: 580px;
    margin: 0 auto 40px; line-height: 1.75; font-weight: 400;
    animation: fadeInUp 0.6s 0.2s ease both;
}
.rv-input-row { animation: fadeInUp 0.6s 0.3s ease both; }
.rv-demo-row  {
    display: flex; align-items: center; justify-content: center;
    gap: 16px; margin-top: 14px; margin-bottom: 44px;
    animation: fadeInUp 0.6s 0.4s ease both;
}
.rv-btn-demo {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 13px; font-weight: 500; color: #52525b;
    text-decoration: none; padding: 9px 18px;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px; background: rgba(255,255,255,0.03);
    transition: color 0.2s, border-color 0.2s, background 0.2s;
}
.rv-btn-demo:hover { color: #a1a1aa; border-color: rgba(255,255,255,0.13); background: rgba(255,255,255,0.06); }

/* Trust strip */
.rv-trust {
    display: flex; align-items: center; justify-content: center;
    flex-wrap: wrap; gap: 10px; margin-bottom: 64px;
    font-size: 12px; color: #3f3f46;
    animation: fadeInUp 0.6s 0.5s ease both;
}
.rv-trust-dot  { width: 3px; height: 3px; border-radius: 50%; background: #3f3f46; }
.rv-trust-hi   { color: #71717a; font-weight: 500; }

/* How-it-works */
.rv-how-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 14px; margin-bottom: 40px;
}
.rv-how-card {
    background: rgba(255,255,255,0.02);
    backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px; padding: 22px;
    display: flex; gap: 16px; align-items: flex-start;
    transition: border-color 0.2s, background 0.2s;
}
.rv-how-card:hover { border-color: rgba(139,92,246,0.25); background: rgba(139,92,246,0.04); }
.rv-how-num {
    width: 32px; height: 32px; border-radius: 10px;
    background: linear-gradient(135deg,#8b5cf6,#3b82f6);
    color: #fff; font-size: 13px; font-weight: 700;
    display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.rv-how-title { font-size: 13px; font-weight: 600; color: #e4e4e7; margin-bottom: 5px; }
.rv-how-desc  { font-size: 12px; color: #52525b; line-height: 1.65; }

/* ── Wrap ── */
.rv-wrap { max-width: 1080px; margin: 0 auto; padding: 0 24px 60px; position: relative; z-index: 5; }

/* ── Divider ── */
.ra-divider { display: flex; align-items: center; gap: 14px; margin: 28px 0 18px; }
.ra-divider-line  { flex: 1; height: 1px; background: rgba(255,255,255,0.06); }
.ra-divider-label {
    font-size: 11px; font-weight: 700; color: #3f3f46;
    letter-spacing: 0.08em; text-transform: uppercase; white-space: nowrap;
}

/* ── Progress card ── */
.ra-progress-card {
    background: rgba(255,255,255,0.02);
    backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px; padding: 22px 24px; margin-bottom: 24px;
}
.ra-progress-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.ra-progress-title  { font-size: 13px; font-weight: 600; color: #a1a1aa; }
.ra-progress-count  { font-size: 12px; color: #52525b; font-weight: 500; }
.ra-pbar-bg   { height: 2px; background: rgba(255,255,255,0.06); border-radius: 99px; margin-bottom: 20px; overflow: hidden; }
.ra-pbar-fill { height: 2px; background: linear-gradient(90deg,#8b5cf6,#3b82f6); border-radius: 99px; transition: width 0.4s ease; }

.ra-agent-row { display: flex; align-items: center; gap: 12px; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.04); }
.ra-agent-row:last-child { border-bottom: none; padding-bottom: 0; }
.ra-dot      { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.ra-dot-wait { background: #27272a; }
.ra-dot-run  { background: #8b5cf6; box-shadow: 0 0 8px rgba(139,92,246,0.6); }
.ra-dot-done { background: #22c55e; }
.ra-dot-err  { background: #ef4444; }
.ra-agent-icon { width: 30px; height: 30px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 14px; flex-shrink: 0; }
.ra-icon-wait { background: rgba(255,255,255,0.04); }
.ra-icon-run  { background: rgba(139,92,246,0.15); }
.ra-icon-done { background: rgba(34,197,94,0.1); }
.ra-icon-err  { background: rgba(239,68,68,0.1); }
.ra-agent-name        { font-size: 13px; font-weight: 500; color: #a1a1aa; margin-bottom: 2px; }
.ra-agent-detail      { font-size: 11px; color: #3f3f46; }
.ra-agent-detail-done { color: #4ade80; }
.ra-agent-detail-run  { color: #a78bfa; }
.ra-badge      { font-size: 10px; font-weight: 700; padding: 3px 8px; border-radius: 99px; letter-spacing: 0.04em; text-transform: uppercase; }
.ra-badge-wait { background: rgba(255,255,255,0.04); color: #3f3f46; }
.ra-badge-run  { background: rgba(139,92,246,0.15); color: #a78bfa; }
.ra-badge-done { background: rgba(34,197,94,0.1);   color: #4ade80; }
.ra-badge-err  { background: rgba(239,68,68,0.1);   color: #f87171; }

/* ── Score grid ── */
.ra-score-grid {
    display: grid; grid-template-columns: repeat(6, 1fr);
    gap: 10px; margin-bottom: 18px;
}
.ra-score-card {
    background: rgba(255,255,255,0.02);
    backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px; padding: 18px 10px; text-align: center;
    transition: border-color 0.2s, background 0.2s;
}
.ra-score-card:hover { background: rgba(255,255,255,0.04); border-color: rgba(255,255,255,0.12); }
.ra-score-num { font-size: 28px; font-weight: 800; letter-spacing: -0.04em; line-height: 1; margin-bottom: 6px; }
.ra-score-lbl { font-size: 10px; font-weight: 600; color: #3f3f46; text-transform: uppercase; letter-spacing: 0.06em; }
.c-green  { color: #4ade80; }
.c-amber  { color: #fbbf24; }
.c-red    { color: #f87171; }
.c-purple { color: #a78bfa; }

/* ── Recommendation ── */
.ra-rec-card { border-radius: 14px; padding: 18px 22px; margin-bottom: 18px; display: flex; gap: 14px; align-items: flex-start; }
.ra-rec-approve { background: rgba(34,197,94,0.06);  border: 1px solid rgba(34,197,94,0.2); }
.ra-rec-request { background: rgba(239,68,68,0.06);  border: 1px solid rgba(239,68,68,0.2); }
.ra-rec-discuss { background: rgba(251,191,36,0.06); border: 1px solid rgba(251,191,36,0.2); }
.ra-rec-icon { width: 38px; height: 38px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0; }
.ra-rec-title-approve { font-size: 15px; font-weight: 700; color: #4ade80;  margin-bottom: 4px; }
.ra-rec-title-request { font-size: 15px; font-weight: 700; color: #f87171;  margin-bottom: 4px; }
.ra-rec-title-discuss { font-size: 15px; font-weight: 700; color: #fbbf24;  margin-bottom: 4px; }
.ra-rec-desc-approve  { font-size: 13px; color: #86efac; line-height: 1.6; }
.ra-rec-desc-request  { font-size: 13px; color: #fca5a5; line-height: 1.6; }
.ra-rec-desc-discuss  { font-size: 13px; color: #fde68a; line-height: 1.6; }

/* ── Summary ── */
.ra-summary {
    background: rgba(139,92,246,0.08); border: 1px solid rgba(139,92,246,0.18);
    border-radius: 12px; padding: 16px 18px; margin-bottom: 20px;
    font-size: 13px; color: #c4b5fd; line-height: 1.75;
    display: flex; gap: 10px;
}

/* ── 3-col findings ── */
.ra-cols { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 14px; margin-bottom: 16px; }
.ra-col-card {
    background: rgba(255,255,255,0.02);
    backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px; padding: 18px;
    transition: border-color 0.2s;
}
.ra-col-card:hover { border-color: rgba(255,255,255,0.12); }
.ra-col-head  { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.ra-col-title { font-size: 13px; font-weight: 700; color: #a1a1aa; display: flex; align-items: center; gap: 6px; }

/* ── Findings ── */
.ra-finding {
    border-left: 2px solid rgba(255,255,255,0.08); padding: 9px 12px;
    margin-bottom: 8px; border-radius: 0 8px 8px 0;
    background: rgba(255,255,255,0.02); overflow: hidden;
}
.ra-finding:last-child { margin-bottom: 0; }
.ra-f-critical { border-left-color: #f87171; }
.ra-f-high     { border-left-color: #fb923c; }
.ra-f-medium   { border-left-color: #fbbf24; }
.ra-f-low      { border-left-color: #60a5fa; }
.ra-f-ok       { border-left-color: #4ade80; }
.ra-f-sev          { font-size: 9px; font-weight: 800; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 3px; }
.ra-f-sev-critical { color: #f87171; }
.ra-f-sev-high     { color: #fb923c; }
.ra-f-sev-medium   { color: #fbbf24; }
.ra-f-sev-low      { color: #60a5fa; }
.ra-f-sev-ok       { color: #4ade80; }
.ra-f-title { font-size: 12px; font-weight: 600; color: #a1a1aa; margin-bottom: 2px; word-break: break-word; overflow-wrap: break-word; }
.ra-f-file  { font-size: 10px; color: #3f3f46; font-family: monospace; margin-bottom: 4px; word-break: break-all; overflow-wrap: break-word; white-space: normal; }
.ra-f-desc  { font-size: 11px; color: #52525b; line-height: 1.5; word-break: break-word; overflow-wrap: break-word; }

/* ── Suggestions ── */
.ra-sugg-item { display: flex; gap: 10px; margin-bottom: 10px; align-items: flex-start; }
.ra-sugg-item:last-child { margin-bottom: 0; }
.ra-sugg-n {
    width: 20px; height: 20px; border-radius: 6px;
    background: rgba(139,92,246,0.18); color: #a78bfa; font-size: 10px;
    font-weight: 700; display: flex; align-items: center;
    justify-content: center; flex-shrink: 0; margin-top: 1px;
}
.ra-sugg-t { font-size: 12px; color: #71717a; line-height: 1.65; word-break: break-word; overflow-wrap: break-word; }

/* ── Detail grid ── */
.ra-detail-grid { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 14px; margin-bottom: 24px; }
.ra-detail-card {
    background: rgba(255,255,255,0.02);
    backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px; padding: 18px;
}
.ra-detail-head  { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.ra-detail-title { font-size: 13px; font-weight: 700; color: #a1a1aa; }
.ra-ring {
    width: 42px; height: 42px; border-radius: 50%;
    border: 2px solid rgba(34,197,94,0.3); display: flex;
    align-items: center; justify-content: center;
    font-size: 12px; font-weight: 800; color: #4ade80;
}
.ra-ring-amber { border-color: rgba(251,191,36,0.3); color: #fbbf24; }
.ra-missing-row {
    display: flex; gap: 10px; align-items: flex-start;
    padding: 7px 0; border-bottom: 1px solid rgba(255,255,255,0.04);
    font-size: 12px; color: #52525b; line-height: 1.5;
}
.ra-missing-row:last-child { border-bottom: none; }
.ra-missing-dot { width: 5px; height: 5px; border-radius: 50%; background: #fbbf24; flex-shrink: 0; margin-top: 6px; }

/* ── Diff section ── */
.ra-author-row   { }
.ra-diff-mobile  { display: none; }
.ra-diff-desktop { display: block; }
.ra-diff-card {
    background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px; padding: 18px 20px; margin-bottom: 24px;
}
.ra-diff-card-title {
    font-size: 13px; font-weight: 700; color: #a1a1aa; margin-bottom: 14px;
    padding-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.06);
}
.ra-diff-link {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 12px; font-weight: 600; color: #a78bfa;
    text-decoration: none; padding: 8px 16px;
    border: 1px solid rgba(139,92,246,0.3); border-radius: 99px;
    background: rgba(139,92,246,0.1);
    transition: background 0.2s;
}
.ra-diff-link:hover { background: rgba(139,92,246,0.18); }
.ra-diff-mobile-btn {
    display: flex; align-items: center; justify-content: center; gap: 8px;
    width: 100%; background: linear-gradient(135deg,#8b5cf6,#3b82f6);
    color: #fff; border: none; border-radius: 10px; padding: 13px 20px;
    font-size: 14px; font-weight: 600; cursor: pointer;
    margin-bottom: 24px; text-decoration: none;
}

/* ── Footer ── */
.ra-footer {
    text-align: center; padding: 32px 0 8px;
    font-size: 11px; color: #27272a;
    border-top: 1px solid rgba(255,255,255,0.05); margin-top: 8px;
}
.ra-footer a { color: #52525b; text-decoration: none; }
.ra-footer a:hover { color: #a78bfa; }

/* ── Streamlit overrides ── */
.stButton > button {
    background: linear-gradient(135deg,#8b5cf6,#3b82f6) !important;
    color: #fff !important; border: none !important;
    border-radius: 10px !important; font-size: 14px !important;
    font-weight: 600 !important; height: 52px !important;
    padding: 0 24px !important; letter-spacing: -0.01em !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.82 !important; }
.stTextInput > div > div > input {
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    font-size: 15px !important; height: 52px !important;
    padding: 0 20px !important;
    background: rgba(255,255,255,0.04) !important;
    color: #fafafa !important;
}
.stTextInput > div > div > input::placeholder { color: #3f3f46 !important; }
.stTextInput > div > div > input:focus {
    border-color: rgba(139,92,246,0.6) !important;
    box-shadow: 0 0 0 3px rgba(139,92,246,0.12) !important;
}
[data-testid="stAlert"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important; color: #71717a !important;
}
.stExpander {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 12px !important;
}

/* ── Entrance animations ── */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(18px); }
    to   { opacity: 1; transform: translateY(0);    }
}

/* ── Mobile ── */
@media (max-width: 768px) {
    .rv-nav  { padding: 0 16px; }
    .rv-h1   { font-size: 34px; }
    .rv-sub  { font-size: 15px; margin-bottom: 24px; }
    .rv-hero { padding: 56px 16px 12px; }

    .ra-score-grid  { grid-template-columns: repeat(3,1fr); }
    .ra-score-num   { font-size: 22px; }
    .ra-cols        { grid-template-columns: 1fr; gap: 10px; }
    .ra-col-card    { padding: 14px; }
    .ra-col-head    { margin-bottom: 10px; }
    .ra-col-title   { font-size: 12px; }
    .ra-finding     { padding: 8px 10px; margin-bottom: 6px; overflow: hidden; }
    .ra-f-title     { font-size: 11px; }
    .ra-f-desc      { font-size: 10px; }
    .ra-sugg-t      { font-size: 11px; }
    .ra-detail-grid { grid-template-columns: 1fr; }
    .ra-rec-card    { padding: 14px 16px; }
    .ra-progress-card { padding: 16px; }

    .ra-author-row   { display: none !important; }
    .ra-diff-mobile  { display: block; }
    .ra-diff-desktop { display: none; }

    [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 8px !important; }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { min-width: 0 !important; flex: 1 1 auto !important; }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child,
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child { display: none !important; }
    .stButton > button { font-size: 13px !important; padding: 10px 14px !important; height: 48px !important; }
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
        "APPROVE":          ("ra-rec-approve","✅","rgba(34,197,94,0.1)",  "ra-rec-title-approve","ra-rec-desc-approve",
                             "Looks good to merge",
                             "No significant issues were found. This PR is ready to merge."),
        "REQUEST_CHANGES":  ("ra-rec-request","⚠️","rgba(239,68,68,0.1)",  "ra-rec-title-request","ra-rec-desc-request",
                             "Changes requested before merge",
                             "There are issues that should be addressed before this PR is merged."),
        "NEEDS_DISCUSSION": ("ra-rec-discuss","💬","rgba(251,191,36,0.1)","ra-rec-title-discuss","ra-rec-desc-discuss",
                             "Needs team discussion",
                             "This PR has tradeoffs that the team should discuss before merging."),
    }.get(rec, ("ra-rec-discuss","💬","rgba(251,191,36,0.1)","ra-rec-title-discuss","ra-rec-desc-discuss", rec, ""))
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
    author     = final_data.get('pr_author', '')
    repo       = final_data.get('repo', '')
    pr_title   = final_data.get('pr_title', '')
    pr_num     = final_data.get('pr_number', '')
    additions  = final_data.get('additions', 0)
    deletions  = final_data.get('deletions', 0)
    avatar_url = f"https://avatars.githubusercontent.com/{author}?s=88"
    gh_pr_url  = f"https://github.com/{repo}/pull/{pr_num}" if pr_num else "#"
    gh_user_url= f"https://github.com/{author}"
    initials   = "".join([w[0].upper() for w in author.replace("-"," ").split()[:2]]) if author else "?"

    return f"""
    <div style="background:rgba(255,255,255,0.02);backdrop-filter:blur(12px);
                border:1px solid rgba(255,255,255,0.07);border-radius:16px;
                padding:20px 22px;margin-bottom:18px;">

      <div style="display:flex;align-items:flex-start;gap:12px;margin-bottom:14px;">
        <span style="font-size:11px;font-weight:700;color:#a78bfa;
                     background:rgba(139,92,246,0.12);padding:3px 9px;
                     border-radius:6px;flex-shrink:0;margin-top:2px;
                     border:1px solid rgba(139,92,246,0.25);">
          #{pr_num}
        </span>
        <span style="font-size:15px;font-weight:700;color:#f4f4f5;
                     line-height:1.4;letter-spacing:-0.01em;">
          {pr_title}
        </span>
      </div>

      <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px;">
        <span style="font-size:11px;padding:3px 9px;border-radius:99px;
                     background:rgba(139,92,246,0.1);color:#a78bfa;
                     border:1px solid rgba(139,92,246,0.2);">
          {repo}
        </span>
        <span style="font-size:11px;padding:3px 9px;border-radius:99px;
                     background:rgba(255,255,255,0.04);color:#71717a;
                     border:1px solid rgba(255,255,255,0.07);">
          +{additions} / −{deletions} lines
        </span>
      </div>

      <div style="height:1px;background:rgba(255,255,255,0.06);margin-bottom:14px;"></div>

      <div class="ra-author-row" style="display:flex;align-items:center;gap:12px;">
        <div style="position:relative;flex-shrink:0;">
          <img src="{avatar_url}" width="36" height="36"
               style="border-radius:50%;border:2px solid rgba(255,255,255,0.1);
                      object-fit:cover;display:block;"
               onerror="this.style.display='none';this.nextElementSibling.style.display='flex';" />
          <div style="display:none;width:36px;height:36px;border-radius:50%;
                      background:rgba(139,92,246,0.2);color:#a78bfa;font-size:12px;font-weight:700;
                      align-items:center;justify-content:center;">
            {initials}
          </div>
        </div>
        <div style="flex:1;min-width:0;">
          <div style="font-size:13px;font-weight:600;color:#e4e4e7;margin-bottom:2px;">{author}</div>
          <div style="font-size:11px;color:#52525b;font-family:monospace;">github.com/{author}</div>
        </div>
        <div style="display:flex;gap:8px;flex-shrink:0;">
          <a href="{gh_user_url}" target="_blank"
             style="font-size:11px;color:#a78bfa;text-decoration:none;
                    display:inline-flex;align-items:center;gap:4px;
                    padding:5px 12px;border:1px solid rgba(139,92,246,0.3);
                    border-radius:99px;background:rgba(139,92,246,0.1);font-weight:600;">
            View profile ↗
          </a>
          <a href="{gh_pr_url}" target="_blank"
             style="font-size:11px;color:#fff;text-decoration:none;
                    display:inline-flex;align-items:center;gap:4px;
                    padding:5px 12px;border:none;border-radius:99px;
                    background:linear-gradient(135deg,#8b5cf6,#3b82f6);font-weight:600;">
            View PR ↗
          </a>
        </div>
      </div>
    </div>"""


def main():
    # ── Animated background + Nav ─────────────────────────────────────────────
    st.markdown("""
    <div class="rv-bg">
      <div class="rv-blob rv-blob-1"></div>
      <div class="rv-blob rv-blob-2"></div>
      <div class="rv-blob rv-blob-3"></div>
      <!-- Particles -->
      <div class="rv-particle" style="left:7%;  width:2px;height:2px;animation-duration:20s;animation-delay:0s;"></div>
      <div class="rv-particle" style="left:14%; width:1px;height:1px;animation-duration:26s;animation-delay:-8s;"></div>
      <div class="rv-particle" style="left:22%; width:2px;height:2px;animation-duration:18s;animation-delay:-3s;"></div>
      <div class="rv-particle" style="left:35%; width:1px;height:1px;animation-duration:30s;animation-delay:-12s;"></div>
      <div class="rv-particle" style="left:50%; width:2px;height:2px;animation-duration:22s;animation-delay:-6s;"></div>
      <div class="rv-particle" style="left:63%; width:1px;height:1px;animation-duration:24s;animation-delay:-2s;"></div>
      <div class="rv-particle" style="left:74%; width:2px;height:2px;animation-duration:19s;animation-delay:-9s;"></div>
      <div class="rv-particle" style="left:82%; width:1px;height:1px;animation-duration:28s;animation-delay:-14s;"></div>
      <div class="rv-particle" style="left:91%; width:2px;height:2px;animation-duration:21s;animation-delay:-4s;"></div>
      <!-- Floating code lines -->
      <div class="rv-code-line" style="left:4%;  animation-duration:32s;animation-delay:0s;">const review = await revora.analyze(pr);</div>
      <div class="rv-code-line" style="left:24%; animation-duration:38s;animation-delay:-12s;">if (security.critical.length > 0) reject(pr);</div>
      <div class="rv-code-line" style="left:55%; animation-duration:28s;animation-delay:-6s;">score: 94/100 — approved ✓</div>
      <div class="rv-code-line" style="left:72%; animation-duration:35s;animation-delay:-20s;">diff --git a/src/auth.py b/src/auth.py</div>
      <div class="rv-code-line" style="left:42%; animation-duration:42s;animation-delay:-9s;">+ const hash = await bcrypt.hash(password, 12);</div>
      <div class="rv-code-line" style="left:85%; animation-duration:30s;animation-delay:-3s;">logic_issues: 2, suggestions: [...]</div>
    </div>

    <nav class="rv-nav">
      <div class="rv-nav-logo">
        <svg width="26" height="26" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="navgl" x1="0" y1="0" x2="28" y2="28" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stop-color="#c4b5fd"/>
              <stop offset="100%" stop-color="#93c5fd"/>
            </linearGradient>
          </defs>
          <circle cx="11" cy="11" r="9" stroke="url(#navgl)" stroke-width="1.9" fill="none"/>
          <path d="M8 2.8C5.5 5.5 5.5 16.5 8 19.2"  stroke="url(#navgl)" stroke-width="1.9" fill="none" stroke-linecap="round"/>
          <path d="M14 2.8C16.5 5.5 16.5 16.5 14 19.2" stroke="url(#navgl)" stroke-width="1.9" fill="none" stroke-linecap="round"/>
          <path d="M2.5 8.5Q11 11 19.5 8.5"  stroke="url(#navgl)" stroke-width="1.9" fill="none" stroke-linecap="round"/>
          <line x1="2" y1="11" x2="20" y2="11" stroke="url(#navgl)" stroke-width="1.9" stroke-linecap="round"/>
          <path d="M2.5 13.5Q11 11 19.5 13.5" stroke="url(#navgl)" stroke-width="1.9" fill="none" stroke-linecap="round"/>
          <circle cx="20" cy="20" r="4.5" stroke="url(#navgl)" stroke-width="1.9" fill="none"/>
          <line x1="23.2" y1="23.2" x2="26.5" y2="26.5" stroke="url(#navgl)" stroke-width="1.9" stroke-linecap="round"/>
        </svg>
        Revora
      </div>
      <div class="rv-nav-right">
        <span class="rv-pill rv-pill-green">● API live</span>
        <span class="rv-pill rv-pill-gray">v1.0</span>
      </div>
    </nav>
    """, unsafe_allow_html=True)

    # ── Hero text ─────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="rv-hero">
      <div class="rv-eyebrow">⚡ Powered by GPT-4o &nbsp;·&nbsp; LangGraph</div>
      <h1 class="rv-h1">AI-powered Pull Request<br>Reviews in Seconds</h1>
      <p class="rv-sub">
        Catch bugs, improve readability, enforce best practices,<br>
        and generate intelligent review comments automatically.
      </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Input + button ────────────────────────────────────────────────────────
    st.markdown('<div class="rv-input-row">', unsafe_allow_html=True)
    _, col_input, col_btn, _ = st.columns([2, 3.5, 0.8, 2])
    with col_input:
        pr_url = st.text_input(
            "pr_url",
            placeholder="https://github.com/owner/repo/pull/123",
            label_visibility="collapsed",
        )
    with col_btn:
        analyze = st.button("Analyze →", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Demo link + trust strip ───────────────────────────────────────────────
    st.markdown("""
    <div class="rv-demo-row">
      <a href="https://github.com/fastapi/fastapi/pull/13474" target="_blank" class="rv-btn-demo">
        View Demo PR ↗
      </a>
    </div>
    <div class="rv-trust">
      <span class="rv-trust-hi">Built for developers</span>
      <div class="rv-trust-dot"></div>
      <span>students</span>
      <div class="rv-trust-dot"></div>
      <span>engineering teams</span>
    </div>
    """, unsafe_allow_html=True)

    # ── How it works ──────────────────────────────────────────────────────────
    st.markdown('<div class="rv-wrap">', unsafe_allow_html=True)

    st.markdown("""
    <div class="rv-how-grid">
      <div class="rv-how-card">
        <div class="rv-how-num">1</div>
        <div>
          <div class="rv-how-title">Paste a GitHub PR link</div>
          <div class="rv-how-desc">Any public repository. Copy the URL from your browser and paste it above.</div>
        </div>
      </div>
      <div class="rv-how-card">
        <div class="rv-how-num">2</div>
        <div>
          <div class="rv-how-title">Five agents review it live</div>
          <div class="rv-how-desc">Security, logic, tests, docs, and synthesis all run and stream back in real time.</div>
        </div>
      </div>
      <div class="rv-how-card">
        <div class="rv-how-num">3</div>
        <div>
          <div class="rv-how-title">Get a structured report</div>
          <div class="rv-how-desc">A score out of 100, a merge recommendation, and exactly what to fix first.</div>
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
    threading.Thread(target=run_websocket, args=(pr_url.strip(), eq), daemon=True).start()

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
    ]) or "<p style='font-size:12px;color:#3f3f46;'>No suggestions.</p>"

    sec_badge = (
        '<span class="ra-badge ra-badge-done" style="margin-left:6px;">Clear</span>'
        if not sec_findings else
        f'<span class="ra-badge" style="background:rgba(239,68,68,0.12);color:#f87171;'
        f'margin-left:6px;">{len(sec_findings)} found</span>'
    )
    log_badge = (
        "" if not log_findings else
        f'<span class="ra-badge" style="background:rgba(251,191,36,0.12);color:#fbbf24;'
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
    _pr_num   = _m.group(1) if _m else ''
    _repo     = final_data.get('repo', '')
    _diff_url = f"https://github.com/{_repo}/pull/{_pr_num}/files" if _pr_num else f"https://github.com/{_repo}"

    st.markdown(f"""
    <div class="ra-diff-desktop">
      <div class="ra-diff-card">
        <div class="ra-diff-card-title">Code Diff</div>
        <p style="font-size:12px;color:#52525b;margin-bottom:14px;line-height:1.6;">
          View the full file-by-file diff for this pull request on GitHub.
        </p>
        <a href="{_diff_url}" target="_blank" class="ra-diff-link">View diff on GitHub ↗</a>
      </div>
    </div>
    <div class="ra-diff-mobile">
      <a href="{_diff_url}" target="_blank" class="ra-diff-mobile-btn">GitHub Diff View ↗</a>
    </div>
    """, unsafe_allow_html=True)

    missing_tests = "".join([
        f'<div class="ra-missing-row">'
        f'<div class="ra-missing-dot"></div><div>{m}</div></div>'
        for m in final_data.get("missing_test_cases", [])
    ]) or (
        '<div class="ra-missing-row">'
        '<div class="ra-missing-dot" style="background:#4ade80;"></div>'
        '<div>No missing test cases identified</div></div>'
    )

    missing_docs = "".join([
        f'<div class="ra-missing-row">'
        f'<div class="ra-missing-dot" style="background:#fbbf24;"></div>'
        f'<div>{m}</div></div>'
        for m in (
            final_data.get("missing_docstrings", []) +
            final_data.get("missing_type_hints", [])
        )
    ]) or (
        '<div class="ra-missing-row">'
        '<div class="ra-missing-dot" style="background:#4ade80;"></div>'
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
