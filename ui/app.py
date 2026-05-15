import streamlit as st
import asyncio
import json
import websockets
import threading
import queue
import os
import re as _re

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
[data-testid="stAppViewContainer"]   { background: #09090b !important; }
[data-testid="stMain"]               { padding: 0 !important; }
[data-testid="stMainBlockContainer"] { padding: 0 !important; max-width: 100% !important; }
.block-container                     { padding: 0 !important; max-width: 100% !important; }
section[data-testid="stSidebar"]     { display: none; }
footer { display: none; }
#MainMenu { display: none; }
header[data-testid="stHeader"] { display: none; }

/* ═══════════════════════════════════════
   ANIMATED BACKGROUND
═══════════════════════════════════════ */
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

/* ═══════════════════════════════════════
   NAV
═══════════════════════════════════════ */
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

/* ═══════════════════════════════════════
   HERO
═══════════════════════════════════════ */
.rv-hero { position: relative; z-index: 5; text-align: center; padding: 80px 24px 0; }
.rv-badge-row {
    display: flex; align-items: center; justify-content: center; gap: 8px;
    margin-bottom: 32px; flex-wrap: wrap;
    animation: fadeInUp 0.5s ease both;
}
.rv-badge {
    display: inline-flex; align-items: center; gap: 5px;
    font-size: 11px; font-weight: 600; letter-spacing: 0.06em;
    padding: 4px 12px; border-radius: 99px;
    border: 1px solid rgba(255,255,255,0.08);
    color: #71717a; background: rgba(255,255,255,0.03);
}
.rv-badge-accent {
    background: rgba(139,92,246,0.12);
    color: #a78bfa; border-color: rgba(139,92,246,0.25);
}
.rv-badge-dot { width: 5px; height: 5px; border-radius: 50%; background: #22c55e; flex-shrink: 0; }
.rv-h1 {
    font-size: 72px; font-weight: 900;
    background: linear-gradient(135deg, #ffffff 0%, #c4b5fd 50%, #93c5fd 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.05em; line-height: 1.03; margin-bottom: 24px;
    animation: fadeInUp 0.5s 0.08s ease both;
}
.rv-h1 em { font-style: normal; color: #a78bfa; -webkit-text-fill-color: #a78bfa; }
.rv-sub {
    font-size: 18px !important; color: #ffffff !important; max-width: 560px;
    margin: 0 auto 36px !important; line-height: 1.7; font-weight: 400;
    text-align: center !important; display: block; width: 100%;
    animation: fadeInUp 0.5s 0.16s ease both;
}
p.rv-sub { text-align: center !important; margin-left: auto !important; margin-right: auto !important; }
.rv-input-row { animation: fadeInUp 0.5s 0.24s ease both; }

/* Match input height to button */
.rv-input-row .stButton > button {
    height: 52px !important;
}

/* Stats pills row */
.rv-stat-pills {
    display: flex; align-items: center; justify-content: center;
    flex-wrap: wrap; gap: 8px; margin-top: 20px; margin-bottom: 16px;
    animation: fadeInUp 0.5s 0.32s ease both;
}
.rv-stat-pill {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 12px; font-weight: 500; color: #52525b;
    padding: 6px 14px; border-radius: 99px;
    border: 1px solid rgba(255,255,255,0.06);
    background: rgba(255,255,255,0.02);
}
.rv-stat-pill-icon { font-size: 13px; }
.rv-stat-pill-sep  { width: 1px; height: 14px; background: rgba(255,255,255,0.07); margin: 0 4px; }

/* Product preview card */
.rv-preview-wrap {
    max-width: 740px; margin: 44px auto 0;
    position: relative; z-index: 5;
    animation: fadeInUp 0.6s 0.4s ease both;
}
.rv-preview-glow {
    position: absolute; top: -60px; left: 50%; transform: translateX(-50%);
    width: 500px; height: 200px;
    background: radial-gradient(ellipse, rgba(139,92,246,0.18) 0%, transparent 70%);
    pointer-events: none;
}
.rv-preview-card {
    background: rgba(255,255,255,0.025);
    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 20px; overflow: hidden;
    box-shadow: 0 32px 80px rgba(0,0,0,0.5), 0 0 0 1px rgba(139,92,246,0.08);
}
.rv-pc-bar {
    display: flex; align-items: center; gap: 7px;
    padding: 12px 18px; border-bottom: 1px solid rgba(255,255,255,0.06);
    background: rgba(255,255,255,0.015);
}
.rv-pc-dot { width: 10px; height: 10px; border-radius: 50%; }
.rv-pc-title {
    font-size: 12px; color: #52525b; font-weight: 500;
    margin-left: 6px; flex: 1; text-align: center; letter-spacing: 0.01em;
}
.rv-pc-body { padding: 20px 22px; display: flex; gap: 20px; align-items: flex-start; }
.rv-pc-left { flex: 0 0 120px; display: flex; flex-direction: column; align-items: center; gap: 12px; }
.rv-pc-right { flex: 1; min-width: 0; }
.rv-pc-score-label {
    font-size: 10px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
    color: #52525b; text-align: center;
}
.rv-pc-rec {
    display: inline-flex; align-items: center; gap: 5px;
    font-size: 11px; font-weight: 700; padding: 4px 10px;
    border-radius: 8px; background: rgba(34,197,94,0.12);
    color: #4ade80; border: 1px solid rgba(34,197,94,0.22);
}
.rv-pc-meta { font-size: 11px; color: #3f3f46; margin-bottom: 12px; }
.rv-pc-meta strong { color: #71717a; }
.rv-pc-finding {
    display: flex; align-items: flex-start; gap: 8px;
    padding: 8px 10px; border-radius: 8px; margin-bottom: 6px;
    background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05);
}
.rv-pc-finding:last-child { margin-bottom: 0; }
.rv-pc-f-bar { width: 3px; border-radius: 2px; align-self: stretch; flex-shrink: 0; min-height: 32px; }
.rv-pc-f-title { font-size: 11px; font-weight: 600; color: #a1a1aa; margin-bottom: 2px; }
.rv-pc-f-desc  { font-size: 10px; color: #52525b; line-height: 1.5; }
.rv-pc-f-badge {
    font-size: 9px; font-weight: 700; padding: 2px 6px; border-radius: 4px;
    border: 1px solid; letter-spacing: 0.04em; text-transform: uppercase;
    margin-left: auto; flex-shrink: 0; white-space: nowrap;
    align-self: flex-start;
}

/* Demo link row */
.rv-demo-row {
    display: flex; align-items: center; justify-content: center;
    gap: 16px; margin-top: 14px; margin-bottom: 0;
    animation: fadeInUp 0.5s 0.32s ease both;
}
.rv-btn-demo {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 12px; font-weight: 500; color: #3f3f46;
    text-decoration: none; padding: 7px 16px;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 8px; background: rgba(255,255,255,0.02);
    transition: color 0.2s, border-color 0.2s, background 0.2s;
}
.rv-btn-demo:hover { color: #71717a; border-color: rgba(255,255,255,0.11); background: rgba(255,255,255,0.04); }

/* ═══════════════════════════════════════
   FEATURE GRID
═══════════════════════════════════════ */
.rv-feature-header {
    text-align: center; margin-bottom: 28px;
}
.rv-feature-header-label {
    font-size: 10px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase;
    color: #3f3f46; margin-bottom: 10px;
}
.rv-feature-header-title {
    font-size: 26px; font-weight: 800; color: #e4e4e7;
    letter-spacing: -0.03em; line-height: 1.2;
}
.rv-feature-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 12px; margin-bottom: 16px;
}
.rv-feature-card {
    background: rgba(255,255,255,0.02);
    backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px; padding: 20px;
    transition: border-color 0.2s, background 0.2s, transform 0.2s;
}
.rv-feature-card:hover {
    border-color: rgba(139,92,246,0.22);
    background: rgba(139,92,246,0.03);
    transform: translateY(-2px);
}
.rv-fc-icon {
    font-size: 22px; margin-bottom: 12px; display: block;
    filter: drop-shadow(0 0 8px rgba(139,92,246,0.35));
}
.rv-fc-title { font-size: 13px; font-weight: 700; color: #e4e4e7; margin-bottom: 6px; }
.rv-fc-desc  { font-size: 12px; color: #3f3f46; line-height: 1.65; }
.rv-fc-tags  { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 12px; }
.rv-fc-tag   {
    font-size: 10px; font-weight: 500; color: #52525b;
    background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.07);
    padding: 2px 7px; border-radius: 4px;
}

/* ═══════════════════════════════════════
   HOW IT WORKS
═══════════════════════════════════════ */
.rv-steps-header { text-align: center; margin-bottom: 24px; }
.rv-steps-title {
    font-size: 22px; font-weight: 800; color: #e4e4e7;
    letter-spacing: -0.03em;
}
.rv-how-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 12px; margin-bottom: 40px;
    position: relative;
}
.rv-how-card {
    background: rgba(255,255,255,0.02);
    backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px; padding: 22px 20px;
    transition: border-color 0.2s, background 0.2s;
    position: relative; overflow: hidden;
}
.rv-how-card::before {
    content: attr(data-n);
    position: absolute; top: -4px; right: 14px;
    font-size: 56px; font-weight: 900; color: rgba(255,255,255,0.025);
    letter-spacing: -0.04em; line-height: 1; pointer-events: none;
}
.rv-how-card:hover { border-color: rgba(139,92,246,0.25); background: rgba(139,92,246,0.04); }
.rv-how-ico {
    width: 38px; height: 38px; border-radius: 11px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; margin-bottom: 14px;
    background: rgba(139,92,246,0.1); border: 1px solid rgba(139,92,246,0.2);
}
.rv-how-title { font-size: 13px; font-weight: 700; color: #e4e4e7; margin-bottom: 6px; }
.rv-how-desc  { font-size: 12px; color: #3f3f46; line-height: 1.65; }

/* ═══════════════════════════════════════
   WRAP + DIVIDER
═══════════════════════════════════════ */
.rv-wrap { max-width: 1080px; margin: 0 auto; padding: 0 24px 60px; position: relative; z-index: 5; }
.rv-divider { display: flex; align-items: center; gap: 14px; margin: 32px 0 20px; }
.rv-divider-line  { flex: 1; height: 1px; background: rgba(255,255,255,0.06); }
.rv-divider-label {
    font-size: 10px; font-weight: 700; color: #3f3f46;
    letter-spacing: 0.1em; text-transform: uppercase; white-space: nowrap;
}

/* ═══════════════════════════════════════
   AGENT PROGRESS (unchanged classes)
═══════════════════════════════════════ */
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
.ra-badge      { font-size: 10px; font-weight: 700; padding: 3px 8px; border-radius: 6px; letter-spacing: 0.04em; text-transform: uppercase; border: 1px solid; }
.ra-badge-wait { background: rgba(255,255,255,0.04); color: #3f3f46; border-color: rgba(255,255,255,0.06); }
.ra-badge-run  { background: rgba(139,92,246,0.15); color: #a78bfa; border-color: rgba(139,92,246,0.25); }
.ra-badge-done { background: rgba(34,197,94,0.1);   color: #4ade80; border-color: rgba(34,197,94,0.2); }
.ra-badge-err  { background: rgba(239,68,68,0.1);   color: #f87171; border-color: rgba(239,68,68,0.2); }

/* ═══════════════════════════════════════
   DASHBOARD SECTION CARDS
═══════════════════════════════════════ */
.rv-section {
    background: rgba(255,255,255,0.025);
    backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px; margin-bottom: 12px;
    transition: border-color 0.2s, box-shadow 0.2s;
    overflow: visible;
}
.rv-section:hover { border-color: rgba(255,255,255,0.11); box-shadow: 0 4px 24px rgba(0,0,0,0.3); }

.rv-section details > summary {
    cursor: pointer; list-style: none; user-select: none;
    padding: 16px 20px;
    display: flex; align-items: center; justify-content: space-between;
    border-bottom: 1px solid transparent;
    transition: background 0.15s;
}
.rv-section details > summary::-webkit-details-marker { display: none; }
.rv-section details > summary::marker { display: none; }
.rv-section details[open] > summary { border-bottom-color: rgba(255,255,255,0.06); background: rgba(255,255,255,0.01); }
.rv-section details > summary:hover  { background: rgba(255,255,255,0.02); }

.rv-sh-left    { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.rv-sh-icon    {
    width: 30px; height: 30px; border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 14px; flex-shrink: 0; border: 1px solid;
}
.rv-sh-title   { font-size: 13px; font-weight: 600; color: #e4e4e7; }
.rv-sh-meta    { font-size: 11px; color: #52525b; }
.rv-sh-chevron { color: #52525b; font-size: 18px; transition: transform 0.25s ease; flex-shrink: 0; margin-left: 8px; }
.rv-section details[open] .rv-sh-chevron { transform: rotate(90deg); }
.rv-sb { padding: 20px; }

/* Severity badge system */
.rv-sev {
    display: inline-flex; align-items: center; gap: 4px;
    font-size: 10px; font-weight: 700; padding: 3px 8px;
    border-radius: 6px; letter-spacing: 0.05em; text-transform: uppercase; border: 1px solid;
}
.rv-sev-critical { background: rgba(239,68,68,0.14);  color: #f87171; border-color: rgba(239,68,68,0.25); }
.rv-sev-high     { background: rgba(249,115,22,0.14); color: #fb923c; border-color: rgba(249,115,22,0.25); }
.rv-sev-medium   { background: rgba(234,179,8,0.14);  color: #facc15; border-color: rgba(234,179,8,0.25); }
.rv-sev-low      { background: rgba(59,130,246,0.14); color: #60a5fa; border-color: rgba(59,130,246,0.25); }
.rv-sev-ok       { background: rgba(34,197,94,0.12);  color: #4ade80; border-color: rgba(34,197,94,0.22); }
.rv-sev-warn     { background: rgba(234,179,8,0.14);  color: #facc15; border-color: rgba(234,179,8,0.25); }
.rv-sev-info     { background: rgba(59,130,246,0.14); color: #60a5fa; border-color: rgba(59,130,246,0.25); }

/* ═══════════════════════════════════════
   1. REPOSITORY OVERVIEW
═══════════════════════════════════════ */
.rv-repo-header { display: flex; align-items: center; gap: 14px; padding: 20px; }
.rv-repo-avatar { flex-shrink: 0; }
.rv-repo-name   { font-size: 16px; font-weight: 700; color: #f4f4f5; letter-spacing: -0.02em; margin-bottom: 4px; }
.rv-repo-sub    { font-size: 12px; color: #52525b; font-family: monospace; }
.rv-repo-chips  { display: flex; gap: 6px; flex-wrap: wrap; margin-left: auto; align-items: center; }
.rv-chip {
    font-size: 11px; padding: 4px 10px; border-radius: 99px; font-weight: 500;
    border: 1px solid;
}
.rv-chip-purple { background: rgba(139,92,246,0.1); color: #a78bfa; border-color: rgba(139,92,246,0.22); }
.rv-chip-zinc   { background: rgba(255,255,255,0.04); color: #71717a; border-color: rgba(255,255,255,0.08); }
.rv-chip-green  { background: rgba(34,197,94,0.1); color: #4ade80; border-color: rgba(34,197,94,0.2); }
.rv-chip-red    { background: rgba(239,68,68,0.1); color: #f87171; border-color: rgba(239,68,68,0.2); }

.rv-stat-strip { display: flex; border-top: 1px solid rgba(255,255,255,0.06); }
.rv-stat { flex: 1; padding: 14px 16px; border-right: 1px solid rgba(255,255,255,0.06); text-align: center; }
.rv-stat:last-child { border-right: none; }
.rv-stat-val { font-size: 20px; font-weight: 700; color: #f4f4f5; letter-spacing: -0.03em; display: block; margin-bottom: 3px; }
.rv-stat-lbl { font-size: 10px; color: #3f3f46; font-weight: 600; text-transform: uppercase; letter-spacing: 0.07em; }
.rv-stat-add { color: #4ade80 !important; }
.rv-stat-del { color: #f87171 !important; }

/* ═══════════════════════════════════════
   2. CODE QUALITY SCORE
═══════════════════════════════════════ */
.rv-quality-body { display: flex; gap: 28px; align-items: center; }
.rv-ring-wrap    { flex-shrink: 0; }
.rv-metrics-list { flex: 1; display: flex; flex-direction: column; gap: 13px; }
.rv-metric-row   { display: flex; align-items: center; gap: 12px; }
.rv-metric-lbl   { font-size: 12px; color: #71717a; font-weight: 500; width: 88px; flex-shrink: 0; }
.rv-metric-bar-bg { flex: 1; height: 5px; background: rgba(255,255,255,0.06); border-radius: 99px; overflow: hidden; }
.rv-metric-bar   { height: 5px; border-radius: 99px; transition: width 0.7s cubic-bezier(.4,0,.2,1); }
.rv-bar-green    { background: linear-gradient(90deg,#22c55e,#4ade80); }
.rv-bar-amber    { background: linear-gradient(90deg,#d97706,#fbbf24); }
.rv-bar-red      { background: linear-gradient(90deg,#dc2626,#f87171); }
.rv-bar-purple   { background: linear-gradient(90deg,#8b5cf6,#a78bfa); }
.rv-metric-val   { font-size: 12px; font-weight: 700; color: #a1a1aa; width: 26px; text-align: right; flex-shrink: 0; }

/* ═══════════════════════════════════════
   3. RISK ANALYSIS
═══════════════════════════════════════ */
.rv-risk-band {
    display: flex; align-items: center; gap: 16px;
    padding: 16px 18px; border-radius: 12px; margin-bottom: 16px;
}
.rv-risk-critical { background: rgba(239,68,68,0.07);  border: 1px solid rgba(239,68,68,0.18); }
.rv-risk-high     { background: rgba(249,115,22,0.07); border: 1px solid rgba(249,115,22,0.18); }
.rv-risk-medium   { background: rgba(59,130,246,0.07); border: 1px solid rgba(59,130,246,0.18); }
.rv-risk-low      { background: rgba(34,197,94,0.07);  border: 1px solid rgba(34,197,94,0.18); }
.rv-risk-label    { font-size: 17px; font-weight: 700; margin-bottom: 3px; }
.rv-risk-desc     { font-size: 12px; opacity: 0.75; line-height: 1.5; }
.rv-risk-icon     { font-size: 26px; flex-shrink: 0; }

.rv-rec-row { display: flex; gap: 10px; align-items: center; padding: 12px 14px; border-radius: 10px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); }
.rv-rec-icon { font-size: 20px; flex-shrink: 0; }
.rv-rec-title { font-size: 14px; font-weight: 600; margin-bottom: 2px; }
.rv-rec-sub   { font-size: 12px; opacity: 0.65; }

/* ═══════════════════════════════════════
   4. PULL REQUEST SUMMARY
═══════════════════════════════════════ */
.rv-summary-text { font-size: 14px; color: #a1a1aa; line-height: 1.85; padding: 2px 0; }
.rv-ai-label {
    display: inline-flex; align-items: center; gap: 5px;
    font-size: 10px; font-weight: 700; letter-spacing: 0.07em;
    text-transform: uppercase; color: #a78bfa;
    background: rgba(139,92,246,0.1); padding: 3px 9px;
    border-radius: 99px; border: 1px solid rgba(139,92,246,0.22);
    margin-bottom: 14px; display: block; width: fit-content;
}

/* ═══════════════════════════════════════
   5 & 6. FINDINGS (Security + Logic)
═══════════════════════════════════════ */
.rv-finding {
    display: flex; gap: 0; align-items: stretch;
    border-radius: 10px; overflow: hidden;
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.07);
    margin-bottom: 10px; transition: border-color 0.2s, background 0.15s;
}
.rv-finding:last-child { margin-bottom: 0; }
.rv-finding:hover { border-color: rgba(255,255,255,0.12); background: rgba(255,255,255,0.035); }
.rv-finding-bar  { width: 3px; flex-shrink: 0; }
.rv-finding-body { padding: 13px 14px; flex: 1; min-width: 0; }
.rv-finding-top  { display: flex; align-items: center; gap: 8px; margin-bottom: 5px; flex-wrap: wrap; }
.rv-finding-title { font-size: 13px; font-weight: 600; color: #e4e4e7; }
.rv-finding-file  { font-size: 10px; color: #3f3f46; font-family: monospace; margin-bottom: 6px; word-break: break-all; }
.rv-finding-desc  { font-size: 12px; color: #71717a; line-height: 1.6; word-break: break-word; overflow-wrap: break-word; }
.rv-bar-critical { background: #f87171; }
.rv-bar-high     { background: #fb923c; }
.rv-bar-medium   { background: #facc15; }
.rv-bar-low      { background: #60a5fa; }
.rv-bar-ok       { background: #4ade80; }

.rv-allclear {
    display: flex; align-items: center; gap: 10px;
    padding: 14px 16px; border-radius: 10px;
    background: rgba(34,197,94,0.06); border: 1px solid rgba(34,197,94,0.16);
    font-size: 13px; color: #4ade80; font-weight: 500;
}

/* ═══════════════════════════════════════
   7. SUGGESTED FIXES
═══════════════════════════════════════ */
.rv-fix {
    display: flex; gap: 13px; align-items: flex-start;
    padding: 13px 14px; border-radius: 10px;
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.07);
    margin-bottom: 10px; transition: border-color 0.2s;
}
.rv-fix:last-child { margin-bottom: 0; }
.rv-fix:hover { border-color: rgba(139,92,246,0.22); }
.rv-fix-num {
    width: 22px; height: 22px; border-radius: 7px;
    background: rgba(139,92,246,0.15); color: #a78bfa;
    font-size: 10px; font-weight: 800;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; margin-top: 1px;
}
.rv-fix-text { font-size: 13px; color: #a1a1aa; line-height: 1.65; word-break: break-word; }

/* ═══════════════════════════════════════
   8. COMPLEXITY METRICS
═══════════════════════════════════════ */
.rv-complexity-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.rv-complexity-card {
    padding: 18px; border-radius: 12px;
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.07);
}
.rv-cx-head  { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.rv-cx-title { font-size: 13px; font-weight: 600; color: #a1a1aa; }
.rv-cx-ring  {
    width: 40px; height: 40px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 11px; font-weight: 800; border: 2px solid;
}
.rv-cx-ring-green { border-color: rgba(34,197,94,0.35);  color: #4ade80; }
.rv-cx-ring-amber { border-color: rgba(251,191,36,0.35); color: #fbbf24; }
.rv-cx-item {
    display: flex; gap: 9px; align-items: flex-start;
    padding: 7px 0; border-bottom: 1px solid rgba(255,255,255,0.04);
    font-size: 12px; color: #52525b; line-height: 1.5;
}
.rv-cx-item:last-child { border-bottom: none; }
.rv-cx-dot { width: 5px; height: 5px; border-radius: 50%; flex-shrink: 0; margin-top: 5px; }

/* Diff link */
.rv-diff-card {
    background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px; padding: 18px 20px; margin-bottom: 24px;
}
.rv-diff-title { font-size: 13px; font-weight: 600; color: #a1a1aa; margin-bottom: 10px; }
.rv-diff-link {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 12px; font-weight: 600; color: #a78bfa;
    text-decoration: none; padding: 8px 16px;
    border: 1px solid rgba(139,92,246,0.3); border-radius: 99px;
    background: rgba(139,92,246,0.1); transition: background 0.2s;
}
.rv-diff-link:hover { background: rgba(139,92,246,0.18); }
.rv-diff-mobile-btn {
    display: flex; align-items: center; justify-content: center; gap: 8px;
    width: 100%; background: linear-gradient(135deg,#8b5cf6,#3b82f6);
    color: #fff; border: none; border-radius: 10px; padding: 13px 20px;
    font-size: 14px; font-weight: 600; cursor: pointer;
    margin-bottom: 24px; text-decoration: none;
}
.rv-diff-mobile  { display: none; }
.rv-diff-desktop { display: block; }

/* Footer */
.rv-footer {
    text-align: center; padding: 32px 0 8px;
    font-size: 11px; color: #27272a;
    border-top: 1px solid rgba(255,255,255,0.05); margin-top: 8px;
}
.rv-footer a { color: #52525b; text-decoration: none; }
.rv-footer a:hover { color: #a78bfa; }

/* ═══════════════════════════════════════
   STREAMLIT OVERRIDES
═══════════════════════════════════════ */
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
    font-size: 14px !important; height: 52px !important;
    padding: 0 16px !important;
    background: rgba(255,255,255,0.92) !important;
    color: #000000 !important;
    caret-color: #000000 !important;
}
.stTextInput > div { padding-bottom: 0 !important; }
.stTextInput { margin-bottom: 0 !important; }
.stTextInput > div > div > input::placeholder { color: #71717a !important; }
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

/* ═══════════════════════════════════════
   ANIMATIONS
═══════════════════════════════════════ */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(18px); }
    to   { opacity: 1; transform: translateY(0);    }
}

/* ═══════════════════════════════════════
   CONNECTING SPINNER
═══════════════════════════════════════ */
.rv-connecting {
    display: flex; align-items: center; gap: 12px;
    padding: 14px 20px; border-radius: 12px;
    background: rgba(139,92,246,0.08);
    border: 1px solid rgba(139,92,246,0.2);
    color: #a78bfa; font-size: 14px; font-weight: 500;
    margin-bottom: 8px;
}
.rv-spinner {
    width: 18px; height: 18px; border-radius: 50%; flex-shrink: 0;
    border: 2px solid rgba(139,92,246,0.25);
    border-top-color: #a78bfa;
    animation: spin 0.75s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ═══════════════════════════════════════
   INFO TOOLTIP
═══════════════════════════════════════ */
.rv-info-btn {
    display: inline-flex; align-items: center; justify-content: center;
    width: 16px; height: 16px; border-radius: 50%;
    background: rgba(139,92,246,0.15); border: 1px solid rgba(139,92,246,0.3);
    color: #a78bfa; font-size: 10px; font-weight: 700;
    cursor: default; flex-shrink: 0; line-height: 1;
    position: relative; vertical-align: middle;
}
.rv-info-btn .rv-tooltip {
    display: none; position: absolute; top: calc(100% + 8px); left: 50%;
    transform: translateX(-50%);
    background: #18181b; border: 1px solid rgba(255,255,255,0.1);
    border-radius: 10px; padding: 10px 12px; width: 220px;
    font-size: 11px; color: #a1a1aa; line-height: 1.6;
    box-shadow: 0 8px 24px rgba(0,0,0,0.5); z-index: 999;
    pointer-events: none; text-align: left; font-weight: 400;
}
.rv-info-btn:hover .rv-tooltip { display: block; }

/* ═══════════════════════════════════════
   MOBILE
═══════════════════════════════════════ */
@media (max-width: 768px) {
    .rv-nav   { padding: 0 16px; }
    .rv-h1    { font-size: 38px; }
    .rv-sub   { font-size: 15px; margin-bottom: 24px; }
    .rv-hero  { padding: 52px 16px 0; }
    .rv-preview-wrap { margin-top: 28px; }
    .rv-pc-body { flex-direction: column; gap: 14px; }
    .rv-pc-left { flex: none; flex-direction: row; justify-content: center; align-items: center; width: 100%; }
    .rv-feature-grid { grid-template-columns: 1fr 1fr; }
    .rv-stat-pills { gap: 6px; }
    .rv-stat-strip { flex-wrap: wrap; }
    .rv-stat  { min-width: 50%; border-bottom: 1px solid rgba(255,255,255,0.06); }
    .rv-quality-body  { flex-direction: column; align-items: center; }
    .rv-complexity-grid { grid-template-columns: 1fr; }
    .rv-repo-chips { display: none; }
    .rv-diff-mobile  { display: block; }
    .rv-diff-desktop { display: none; }

    [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 8px !important; }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { min-width: 0 !important; flex: 1 1 auto !important; }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child,
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child { display: none !important; }
    .stButton > button { font-size: 13px !important; height: 48px !important; }
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
WS_URL = os.getenv("API_WS_URL", "ws://localhost:8000/review/stream")

AGENTS = [
    ("fetch_pr",      "📥", "Fetch PR from GitHub"),
    ("security",      "🔒", "Security audit"),
    ("logic",         "🧠", "Logic review"),
    ("test_coverage", "🧪", "Test coverage check"),
    ("documentation", "📝", "Documentation check"),
    ("synthesis",     "📋", "Final synthesis"),
]

# ─────────────────────────────────────────────────────────────────────────────
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

def score_color_class(score):
    if score >= 80: return "c-green",  "#22c55e", "rv-bar-green"
    if score >= 60: return "c-amber",  "#fbbf24", "rv-bar-amber"
    return           "c-red",   "#f87171", "rv-bar-red"

def get_risk(score, sec_cnt, log_cnt):
    if sec_cnt >= 3 or score < 50:
        return ("CRITICAL", "rv-risk-critical", "🔴", "#f87171",
                "Critical risk — multiple security issues require immediate attention before merging.")
    if sec_cnt > 0 or score < 65:
        return ("HIGH", "rv-risk-high", "🟠", "#fb923c",
                "High risk — security issues found. Review carefully before merging.")
    if log_cnt > 2 or score < 80:
        return ("MEDIUM", "rv-risk-medium", "🔵", "#60a5fa",
                "Medium risk — some logic issues to address. Consider requesting changes.")
    return ("LOW", "rv-risk-low", "🟢", "#4ade80",
            "Low risk — minor issues only. This PR looks good to merge.")

def sev_bar_class(sev):
    return {"critical":"rv-bar-critical","high":"rv-bar-high",
            "medium":"rv-bar-medium","low":"rv-bar-low"}.get(sev,"rv-bar-low")

def sev_badge_class(sev):
    return {"critical":"rv-sev-critical","high":"rv-sev-high",
            "medium":"rv-sev-medium","low":"rv-sev-low"}.get(sev,"rv-sev-low")

# ─────────────────────────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────────────────────────
def section_html(icon, icon_bg, icon_border, title, badge_html, body_html, open_by_default=True):
    open_attr = "open" if open_by_default else ""
    return f"""
    <div class="rv-section">
      <details {open_attr}>
        <summary>
          <div class="rv-sh-left">
            <span class="rv-sh-icon" style="background:{icon_bg};border-color:{icon_border};">{icon}</span>
            <span class="rv-sh-title">{title}</span>
            {badge_html}
          </div>
          <span class="rv-sh-chevron">›</span>
        </summary>
        <div class="rv-sb">{body_html}</div>
      </details>
    </div>"""

# ─────────────────────────────────────────────────────────────────────────────
def repo_overview_html(final_data, pr_url):
    author    = final_data.get('pr_author', '')
    repo      = final_data.get('repo', '')
    pr_title  = final_data.get('pr_title', '')
    pr_num    = final_data.get('pr_number', '')
    additions = final_data.get('additions', 0)
    deletions = final_data.get('deletions', 0)
    est_t     = final_data.get('estimated_review_time_minutes', 0)
    avatar_url= f"https://avatars.githubusercontent.com/{author}?s=88"
    gh_pr_url = f"https://github.com/{repo}/pull/{pr_num}" if pr_num else "#"
    gh_user   = f"https://github.com/{author}"
    initials  = "".join([w[0].upper() for w in author.replace("-"," ").split()[:2]]) if author else "?"

    m = _re.search(r'/pull/(\d+)', pr_url)
    parsed_num = m.group(1) if m else pr_num

    body = f"""
    <div class="rv-repo-header">
      <div class="rv-repo-avatar">
        <img src="{avatar_url}" width="40" height="40"
             style="border-radius:50%;border:2px solid rgba(255,255,255,0.1);object-fit:cover;display:block;"
             onerror="this.style.display='none';this.nextElementSibling.style.display='flex';" />
        <div style="display:none;width:40px;height:40px;border-radius:50%;
                    background:rgba(139,92,246,0.2);color:#a78bfa;font-size:13px;font-weight:700;
                    align-items:center;justify-content:center;">{initials}</div>
      </div>
      <div>
        <div class="rv-repo-name">{pr_title}</div>
        <div class="rv-repo-sub">
          <a href="{gh_user}" target="_blank" style="color:#52525b;text-decoration:none;">{author}</a>
          &nbsp;·&nbsp; {repo}
        </div>
      </div>
      <div class="rv-repo-chips">
        <span class="rv-chip rv-chip-purple">#{parsed_num}</span>
        <a href="{gh_pr_url}" target="_blank"
           style="font-size:11px;color:#fff;text-decoration:none;
                  padding:5px 12px;border-radius:99px;
                  background:linear-gradient(135deg,#8b5cf6,#3b82f6);font-weight:600;">
          View PR ↗
        </a>
      </div>
    </div>
    <div class="rv-stat-strip">
      <div class="rv-stat"><span class="rv-stat-val rv-stat-add">+{additions}</span><span class="rv-stat-lbl">Additions</span></div>
      <div class="rv-stat"><span class="rv-stat-val rv-stat-del">−{deletions}</span><span class="rv-stat-lbl">Deletions</span></div>
      <div class="rv-stat"><span class="rv-stat-val" style="color:#a78bfa;">{est_t}m</span><span class="rv-stat-lbl">Est. Review</span></div>
      <div class="rv-stat">
        <a href="{gh_user}" target="_blank"
           style="font-size:11px;color:#a78bfa;text-decoration:none;font-weight:600;">
          @{author} ↗
        </a>
        <span class="rv-stat-lbl" style="margin-top:4px;">Author</span>
      </div>
    </div>"""

    badge = f'<span class="rv-chip rv-chip-zinc" style="font-size:10px;">{repo}</span>'
    return section_html("📁", "rgba(139,92,246,0.12)", "rgba(139,92,246,0.25)",
                        "Repository Overview", badge, body, open_by_default=True)

# ─────────────────────────────────────────────────────────────────────────────
def quality_score_html(score, test_sc, doc_sc, sec_cnt, log_cnt, est_t):
    circ = 326.73
    filled = (score / 100) * circ
    sc_cls, sc_color, _ = score_color_class(score)
    tc_cls, tc_color, tc_bar = score_color_class(test_sc)
    dc_cls, dc_color, dc_bar = score_color_class(doc_sc)
    sec_bar = "rv-bar-green" if sec_cnt == 0 else "rv-bar-red"
    log_bar = "rv-bar-green" if log_cnt == 0 else "rv-bar-amber"
    sec_pct = 100 if sec_cnt == 0 else max(0, 100 - sec_cnt * 20)
    log_pct = 100 if log_cnt == 0 else max(0, 100 - log_cnt * 15)

    ring_svg = f"""
    <svg width="130" height="130" viewBox="0 0 130 130">
      <defs>
        <linearGradient id="rgrad" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#8b5cf6"/>
          <stop offset="100%" stop-color="#3b82f6"/>
        </linearGradient>
      </defs>
      <circle cx="65" cy="65" r="52" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="9"/>
      <circle cx="65" cy="65" r="52" fill="none" stroke="url(#rgrad)" stroke-width="9"
              stroke-dasharray="{filled:.1f} {circ:.1f}"
              stroke-linecap="round" transform="rotate(-90 65 65)"/>
      <text x="65" y="58" text-anchor="middle" font-size="28" font-weight="900"
            fill="{sc_color}" font-family="Inter,sans-serif">{score}</text>
      <text x="65" y="76" text-anchor="middle" font-size="11" fill="#52525b"
            font-family="Inter,sans-serif" font-weight="600">out of 100</text>
    </svg>"""

    def metric(label, val, bar_cls, pct, numeric_pct=None):
        color_pct = numeric_pct if numeric_pct is not None else pct
        color = score_color_class(color_pct)[1] if color_pct > 10 else '#f87171'
        return f"""
        <div class="rv-metric-row">
          <span class="rv-metric-lbl">{label}</span>
          <div class="rv-metric-bar-bg"><div class="rv-metric-bar {bar_cls}" style="width:{pct}%;"></div></div>
          <span class="rv-metric-val" style="color:{color};">{val}</span>
        </div>"""

    sec_label = "✓ None" if sec_cnt == 0 else f"{sec_cnt} issue{'s' if sec_cnt != 1 else ''}"
    log_label = "✓ None" if log_cnt == 0 else f"{log_cnt} issue{'s' if log_cnt != 1 else ''}"

    body = f"""
    <div class="rv-quality-body">
      <div class="rv-ring-wrap">{ring_svg}</div>
      <div class="rv-metrics-list">
        {metric("Overall", score, _, score)}
        {metric("Tests", test_sc, tc_bar, test_sc)}
        {metric("Docs", doc_sc, dc_bar, doc_sc)}
        {metric("Security", sec_label, sec_bar, sec_pct, sec_pct)}
        {metric("Logic", log_label, log_bar, log_pct, log_pct)}
        {metric("Est. Review", f"{est_t}m", "rv-bar-purple", min(100, est_t * 8), min(100, est_t * 8))}
      </div>
    </div>"""

    sc_label = "Excellent" if score >= 85 else "Good" if score >= 70 else "Fair" if score >= 55 else "Poor"
    badge = f'<span class="rv-sev rv-sev-{"ok" if score>=80 else "warn" if score>=60 else "critical"}">{sc_label}</span>'
    qs_title = """Code Quality Score <span class="rv-info-btn" style="vertical-align:middle;">i<span class="rv-tooltip">
        <strong style="color:#e4e4e7;">Code Quality Score</strong><br>
        An overall 0–100 score combining security, logic correctness, test coverage, and documentation quality.
        80+ is excellent. Below 60 indicates significant issues that should be addressed before merging.
    </span></span>"""
    return section_html("📊", "rgba(59,130,246,0.12)", "rgba(59,130,246,0.25)",
                        qs_title, badge, body, open_by_default=True)

# ─────────────────────────────────────────────────────────────────────────────
def risk_analysis_html(rec, score, sec_cnt, log_cnt):
    risk_lbl, risk_cls, risk_icon, risk_color, risk_desc = get_risk(score, sec_cnt, log_cnt)

    rec_cfg = {
        "APPROVE":          ("✅", "#4ade80",  "Approved — looks good to merge",
                             "No blocking issues found. Ready to merge."),
        "REQUEST_CHANGES":  ("⚠️", "#f87171",  "Changes requested before merge",
                             "Issues were found that should be resolved first."),
        "NEEDS_DISCUSSION": ("💬", "#fbbf24", "Needs team discussion",
                             "Tradeoffs exist that the team should align on."),
    }.get(rec, ("💬", "#fbbf24", rec, ""))
    rec_icon, rec_color, rec_title, rec_sub = rec_cfg

    body = f"""
    <div class="rv-risk-band {risk_cls}">
      <span class="rv-risk-icon">{risk_icon}</span>
      <div>
        <div class="rv-risk-label" style="color:{risk_color};">{risk_lbl} RISK</div>
        <div class="rv-risk-desc" style="color:{risk_color};">{risk_desc}</div>
      </div>
    </div>
    <div class="rv-rec-row">
      <span class="rv-rec-icon">{rec_icon}</span>
      <div>
        <div class="rv-rec-title" style="color:{rec_color};">{rec_title}</div>
        <div class="rv-rec-sub" style="color:{rec_color};">{rec_sub}</div>
      </div>
    </div>"""

    badge = f'<span class="rv-sev rv-sev-{"critical" if risk_lbl=="CRITICAL" else "warn" if risk_lbl in ("HIGH","MEDIUM") else "ok"}">{risk_lbl}</span>'
    return section_html("⚡", "rgba(234,179,8,0.12)", "rgba(234,179,8,0.25)",
                        "Risk Analysis", badge, body, open_by_default=True)

# ─────────────────────────────────────────────────────────────────────────────
def pr_summary_html(summary):
    if not summary:
        summary = "No summary available."
    body = f"""
    <div class="rv-ai-label">✦ AI Generated</div>
    <div class="rv-summary-text">{summary}</div>"""
    return section_html("💬", "rgba(139,92,246,0.12)", "rgba(139,92,246,0.25)",
                        "Pull Request Summary", "", body, open_by_default=True)

# ─────────────────────────────────────────────────────────────────────────────
def security_section_html(findings):
    count = len(findings)
    if not findings:
        body = '<div class="rv-allclear">✅&nbsp; No security issues found — this PR passes the security audit.</div>'
    else:
        items = ""
        for f in findings:
            sev = f.get("severity", "low").lower()
            items += f"""
            <div class="rv-finding">
              <div class="rv-finding-bar {sev_bar_class(sev)}"></div>
              <div class="rv-finding-body">
                <div class="rv-finding-top">
                  <span class="rv-sev {sev_badge_class(sev)}">{sev}</span>
                  <span class="rv-finding-title">{f.get('title','')}</span>
                </div>
                <div class="rv-finding-file">{f.get('file','')}</div>
                <div class="rv-finding-desc">{f.get('description','')[:200]}</div>
              </div>
            </div>"""
        body = items

    badge = (
        '<span class="rv-sev rv-sev-ok">Clear</span>' if count == 0 else
        f'<span class="rv-sev rv-sev-critical">{count} found</span>'
    )
    return section_html("🔒", "rgba(239,68,68,0.1)", "rgba(239,68,68,0.22)",
                        "Security Findings", badge, body, open_by_default=True)

# ─────────────────────────────────────────────────────────────────────────────
def logic_section_html(findings):
    count = len(findings)
    if not findings:
        body = '<div class="rv-allclear">✅&nbsp; No logic issues flagged — code logic looks sound.</div>'
    else:
        items = ""
        for f in findings:
            sev = f.get("severity", "medium").lower()
            items += f"""
            <div class="rv-finding">
              <div class="rv-finding-bar {sev_bar_class(sev)}"></div>
              <div class="rv-finding-body">
                <div class="rv-finding-top">
                  <span class="rv-sev {sev_badge_class(sev)}">{sev}</span>
                  <span class="rv-finding-title">{f.get('title','')}</span>
                </div>
                <div class="rv-finding-file">{f.get('file','')}</div>
                <div class="rv-finding-desc">{f.get('description','')[:200]}</div>
              </div>
            </div>"""
        body = items

    badge = (
        "" if count == 0 else
        f'<span class="rv-sev rv-sev-warn">{count} issues</span>'
    )
    return section_html("🧠", "rgba(59,130,246,0.1)", "rgba(59,130,246,0.22)",
                        "AI Reviewer Comments", badge, body, open_by_default=count > 0)

# ─────────────────────────────────────────────────────────────────────────────
def suggestions_section_html(suggestions):
    if not suggestions:
        body = '<div class="rv-allclear">✅&nbsp; No specific fixes to suggest.</div>'
    else:
        items = "".join([
            f'<div class="rv-fix"><div class="rv-fix-num">{i}</div><div class="rv-fix-text">{s}</div></div>'
            for i, s in enumerate(suggestions, 1)
        ])
        body = items
    badge = f'<span class="rv-sev rv-sev-info">{len(suggestions)} suggestions</span>' if suggestions else ""
    return section_html("💡", "rgba(139,92,246,0.1)", "rgba(139,92,246,0.22)",
                        "Suggested Fixes", badge, body, open_by_default=True)

# ─────────────────────────────────────────────────────────────────────────────
def complexity_section_html(test_sc, doc_sc, missing_tests, missing_docs):
    tc_ring = "rv-cx-ring-green" if test_sc >= 80 else "rv-cx-ring-amber"
    dc_ring = "rv-cx-ring-green" if doc_sc  >= 80 else "rv-cx-ring-amber"

    def items_html(items, dot_color):
        if not items:
            return f'<div class="rv-cx-item"><div class="rv-cx-dot" style="background:#4ade80;"></div>Looks complete</div>'
        return "".join([
            f'<div class="rv-cx-item"><div class="rv-cx-dot" style="background:{dot_color};"></div><div>{m}</div></div>'
            for m in items
        ])

    body = f"""
    <div class="rv-complexity-grid">
      <div class="rv-complexity-card">
        <div class="rv-cx-head">
          <span class="rv-cx-title" style="display:flex;align-items:center;gap:6px;">
            🧪 Test Coverage
            <span class="rv-info-btn">i
              <span class="rv-tooltip">
                <strong style="color:#e4e4e7;">Test Coverage Score</strong><br>
                Rates 0–100 how well the PR's new code is covered by tests.
                Checks for missing unit tests, untested functions, and coverage gaps introduced by this PR.
              </span>
            </span>
          </span>
          <div class="rv-cx-ring {tc_ring}">{test_sc}</div>
        </div>
        {items_html(missing_tests, "#fbbf24")}
      </div>
      <div class="rv-complexity-card">
        <div class="rv-cx-head">
          <span class="rv-cx-title" style="display:flex;align-items:center;gap:6px;">
            📝 Documentation
            <span class="rv-info-btn">i
              <span class="rv-tooltip">
                <strong style="color:#e4e4e7;">Documentation Score</strong><br>
                Rates 0–100 how well the changed code is documented.
                Checks for missing docstrings, type hints, and inline comments on complex logic.
              </span>
            </span>
          </span>
          <div class="rv-cx-ring {dc_ring}">{doc_sc}</div>
        </div>
        {items_html(missing_docs, "#fb923c")}
      </div>
    </div>"""

    avg = (test_sc + doc_sc) // 2
    badge = f'<span class="rv-sev rv-sev-{"ok" if avg>=80 else "warn" if avg>=60 else "critical"}">avg {avg}</span>'
    return section_html("🔬", "rgba(34,197,94,0.1)", "rgba(34,197,94,0.22)",
                        "Complexity Metrics", badge, body, open_by_default=True)

# ─────────────────────────────────────────────────────────────────────────────
def main():
    # ── Background + Nav ──────────────────────────────────────────────────────
    st.markdown("""
    <div class="rv-bg">
      <div class="rv-blob rv-blob-1"></div>
      <div class="rv-blob rv-blob-2"></div>
      <div class="rv-blob rv-blob-3"></div>
      <div class="rv-particle" style="left:7%;  width:2px;height:2px;animation-duration:20s;animation-delay:0s;"></div>
      <div class="rv-particle" style="left:14%; width:1px;height:1px;animation-duration:26s;animation-delay:-8s;"></div>
      <div class="rv-particle" style="left:22%; width:2px;height:2px;animation-duration:18s;animation-delay:-3s;"></div>
      <div class="rv-particle" style="left:35%; width:1px;height:1px;animation-duration:30s;animation-delay:-12s;"></div>
      <div class="rv-particle" style="left:50%; width:2px;height:2px;animation-duration:22s;animation-delay:-6s;"></div>
      <div class="rv-particle" style="left:63%; width:1px;height:1px;animation-duration:24s;animation-delay:-2s;"></div>
      <div class="rv-particle" style="left:74%; width:2px;height:2px;animation-duration:19s;animation-delay:-9s;"></div>
      <div class="rv-particle" style="left:82%; width:1px;height:1px;animation-duration:28s;animation-delay:-14s;"></div>
      <div class="rv-particle" style="left:91%; width:2px;height:2px;animation-duration:21s;animation-delay:-4s;"></div>
      <div class="rv-code-line" style="left:4%;  animation-duration:32s;animation-delay:0s;">const review = await revora.analyze(pr);</div>
      <div class="rv-code-line" style="left:24%; animation-duration:38s;animation-delay:-12s;">if (security.critical.length > 0) reject(pr);</div>
      <div class="rv-code-line" style="left:55%; animation-duration:28s;animation-delay:-6s;">score: 94/100 — approved ✓</div>
      <div class="rv-code-line" style="left:72%; animation-duration:35s;animation-delay:-20s;">diff --git a/src/auth.py b/src/auth.py</div>
      <div class="rv-code-line" style="left:42%; animation-duration:42s;animation-delay:-9s;">+ const hash = await bcrypt.hash(password, 12);</div>
      <div class="rv-code-line" style="left:85%; animation-duration:30s;animation-delay:-3s;">logic_issues: 2, suggestions: [...]</div>
    </div>

    <nav class="rv-nav">
      <div class="rv-nav-logo">
        <svg width="26" height="26" viewBox="0 0 28 28" fill="none">
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

    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="rv-hero">
      <div class="rv-badge-row">
        <span class="rv-badge rv-badge-accent">⚡ GPT-4o &nbsp;·&nbsp; LangGraph</span>
        <span class="rv-badge"><span class="rv-badge-dot"></span>&nbsp;API Live</span>
        <span class="rv-badge">Free &amp; Open Source</span>
      </div>
      <h1 class="rv-h1">Great code doesn't review <em>itself.</em></h1>
      <p class="rv-sub" style="text-align:center;margin-left:auto;margin-right:auto;">
        Paste a GitHub PR link. Five AI agents analyze security, logic,
        test coverage, and documentation — full report in seconds.
      </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Input ─────────────────────────────────────────────────────────────────
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

    if analyze:
        st.markdown("""
        <div id="rv-progress-anchor"></div>
        <script>
          (function() {
            var el = document.getElementById('rv-progress-anchor');
            if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
          })();
        </script>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="rv-stat-pills">
      <span class="rv-stat-pill"><span class="rv-stat-pill-icon">🔒</span>Security audit</span>
      <span class="rv-stat-pill-sep"></span>
      <span class="rv-stat-pill"><span class="rv-stat-pill-icon">🧠</span>Logic review</span>
      <span class="rv-stat-pill-sep"></span>
      <span class="rv-stat-pill"><span class="rv-stat-pill-icon">🧪</span>Test coverage</span>
      <span class="rv-stat-pill-sep"></span>
      <span class="rv-stat-pill"><span class="rv-stat-pill-icon">📝</span>Documentation</span>
      <span class="rv-stat-pill-sep"></span>
      <span class="rv-stat-pill"><span class="rv-stat-pill-icon">⚡</span>~30 seconds</span>
    </div>

    <div class="rv-preview-wrap">
      <div class="rv-preview-glow"></div>
      <div class="rv-preview-card">
        <div class="rv-pc-bar">
          <div class="rv-pc-dot" style="background:#ef4444;"></div>
          <div class="rv-pc-dot" style="background:#fbbf24;"></div>
          <div class="rv-pc-dot" style="background:#22c55e;"></div>
          <span class="rv-pc-title">Revora — AI Review Report</span>
        </div>
        <div class="rv-pc-body">
          <div class="rv-pc-left">
            <svg width="100" height="100" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="7"/>
              <circle cx="50" cy="50" r="40" fill="none" stroke="url(#pg)" stroke-width="7"
                      stroke-dasharray="213 251" stroke-linecap="round" transform="rotate(-90 50 50)"/>
              <defs>
                <linearGradient id="pg" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stop-color="#8b5cf6"/>
                  <stop offset="100%" stop-color="#3b82f6"/>
                </linearGradient>
              </defs>
              <text x="50" y="45" text-anchor="middle" font-size="22" font-weight="900"
                    fill="#f4f4f5" font-family="Inter,sans-serif">85</text>
              <text x="50" y="59" text-anchor="middle" font-size="9" fill="#52525b"
                    font-family="Inter,sans-serif" font-weight="600">out of 100</text>
            </svg>
            <div class="rv-pc-score-label">Quality Score</div>
            <div class="rv-pc-rec">✓ Approved</div>
          </div>
          <div class="rv-pc-right">
            <div class="rv-pc-meta"><strong>fastapi/fastapi</strong> · PR #1234 · 3 files · +87 −12</div>
            <div class="rv-pc-finding">
              <div class="rv-pc-f-bar" style="background:#f87171;"></div>
              <div style="flex:1;min-width:0;">
                <div class="rv-pc-f-title">Unsanitized user input in query builder</div>
                <div class="rv-pc-f-desc">SQL injection risk — use parameterized queries</div>
              </div>
              <div class="rv-pc-f-badge" style="background:rgba(239,68,68,0.14);color:#f87171;border-color:rgba(239,68,68,0.25);">HIGH</div>
            </div>
            <div class="rv-pc-finding">
              <div class="rv-pc-f-bar" style="background:#facc15;"></div>
              <div style="flex:1;min-width:0;">
                <div class="rv-pc-f-title">Missing edge case in pagination logic</div>
                <div class="rv-pc-f-desc">Off-by-one error when page count equals limit</div>
              </div>
              <div class="rv-pc-f-badge" style="background:rgba(234,179,8,0.14);color:#facc15;border-color:rgba(234,179,8,0.25);">MED</div>
            </div>
            <div class="rv-pc-finding">
              <div class="rv-pc-f-bar" style="background:#60a5fa;"></div>
              <div style="flex:1;min-width:0;">
                <div class="rv-pc-f-title">No unit tests for new auth helper</div>
                <div class="rv-pc-f-desc">3 functions added, 0 tests — coverage gap</div>
              </div>
              <div class="rv-pc-f-badge" style="background:rgba(59,130,246,0.14);color:#60a5fa;border-color:rgba(59,130,246,0.25);">LOW</div>
            </div>
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Feature grid + How it works ───────────────────────────────────────────
    st.markdown('<div class="rv-wrap" style="margin-top:60px;">', unsafe_allow_html=True)
    st.markdown("""
    <div class="rv-feature-header">
      <div class="rv-feature-header-label">What Revora checks</div>
      <div class="rv-feature-header-title">Four specialist AI agents</div>
    </div>
    <div class="rv-feature-grid">
      <div class="rv-feature-card">
        <span class="rv-fc-icon">🔒</span>
        <div class="rv-fc-title">Security Audit</div>
        <div class="rv-fc-desc">Scans for vulnerabilities before they reach production.</div>
        <div class="rv-fc-tags">
          <span class="rv-fc-tag">SQL injection</span>
          <span class="rv-fc-tag">XSS</span>
          <span class="rv-fc-tag">Secrets</span>
          <span class="rv-fc-tag">Auth flaws</span>
        </div>
      </div>
      <div class="rv-feature-card">
        <span class="rv-fc-icon">🧠</span>
        <div class="rv-fc-title">Logic Review</div>
        <div class="rv-fc-desc">Catches bugs, race conditions, and incorrect assumptions.</div>
        <div class="rv-fc-tags">
          <span class="rv-fc-tag">Edge cases</span>
          <span class="rv-fc-tag">Off-by-one</span>
          <span class="rv-fc-tag">Null checks</span>
        </div>
      </div>
      <div class="rv-feature-card">
        <span class="rv-fc-icon">🧪</span>
        <div class="rv-fc-title">Test Coverage</div>
        <div class="rv-fc-desc">Identifies untested code paths and missing test cases.</div>
        <div class="rv-fc-tags">
          <span class="rv-fc-tag">Coverage gaps</span>
          <span class="rv-fc-tag">Missing mocks</span>
          <span class="rv-fc-tag">Assertions</span>
        </div>
      </div>
      <div class="rv-feature-card">
        <span class="rv-fc-icon">📝</span>
        <div class="rv-fc-title">Documentation</div>
        <div class="rv-fc-desc">Flags missing docstrings, type hints, and inline comments.</div>
        <div class="rv-fc-tags">
          <span class="rv-fc-tag">Docstrings</span>
          <span class="rv-fc-tag">Type hints</span>
          <span class="rv-fc-tag">README</span>
        </div>
      </div>
    </div>

    <div class="rv-steps-header" style="margin-top:40px;">
      <div class="rv-steps-title">How it works</div>
    </div>
    <div class="rv-how-grid">
      <div class="rv-how-card" data-n="1">
        <div class="rv-how-ico">🔗</div>
        <div class="rv-how-title">Paste any GitHub PR</div>
        <div class="rv-how-desc">Works with any public repo. Just copy the URL from your browser tab.</div>
      </div>
      <div class="rv-how-card" data-n="2">
        <div class="rv-how-ico">⚡</div>
        <div class="rv-how-title">Agents run in parallel</div>
        <div class="rv-how-desc">Watch five AI agents stream their findings back live in real time.</div>
      </div>
      <div class="rv-how-card" data-n="3">
        <div class="rv-how-ico">📊</div>
        <div class="rv-how-title">Get a full report</div>
        <div class="rv-how-desc">Score, recommendation, severity-ranked findings, and top fixes.</div>
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

    # ── Agent progress ────────────────────────────────────────────────────────
    st.markdown("""
    <div class="rv-divider">
      <div class="rv-divider-line"></div>
      <span class="rv-divider-label">Live agent progress</span>
      <div class="rv-divider-line"></div>
    </div>
    """, unsafe_allow_html=True)

    progress_slot = st.empty()
    status_slot   = st.empty()
    agent_states  = {a[0]: ("wait", "") for a in AGENTS}
    done_count    = 0
    total         = len(AGENTS)
    final_data    = None

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
          <div class="ra-pbar-bg"><div class="ra-pbar-fill" style="width:{pct}%;"></div></div>
          {rows}
        </div>
        """, unsafe_allow_html=True)

    render_progress(agent_states)
    status_slot.markdown("""
    <div class="rv-connecting">
      <div class="rv-spinner"></div>
      Connecting to agent pipeline...
    </div>
    """, unsafe_allow_html=True)

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

    # ── Dashboard ─────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="rv-divider">
      <div class="rv-divider-line"></div>
      <span class="rv-divider-label">Review dashboard</span>
      <div class="rv-divider-line"></div>
    </div>
    """, unsafe_allow_html=True)

    score    = final_data.get("overall_score", 0)
    rec      = final_data.get("recommendation", "")
    test_sc  = final_data.get("test_coverage_score", 0)
    doc_sc   = final_data.get("documentation_score", 0)
    est_t    = final_data.get("estimated_review_time_minutes", 0)
    sec_findings = final_data.get("security_findings", [])
    log_findings = final_data.get("logic_findings", [])
    suggestions  = final_data.get("top_suggestions", [])
    summary      = final_data.get("summary", "")
    missing_tests= final_data.get("missing_test_cases", [])
    missing_docs = final_data.get("missing_docstrings", []) + final_data.get("missing_type_hints", [])
    sec_cnt = len(sec_findings)
    log_cnt = len(log_findings)

    # 1. Repository Overview
    st.markdown(repo_overview_html(final_data, pr_url), unsafe_allow_html=True)

    # 2 & 3. Quality Score + Risk side by side on desktop
    col_q, col_r = st.columns([3, 2])
    with col_q:
        st.markdown(quality_score_html(score, test_sc, doc_sc, sec_cnt, log_cnt, est_t), unsafe_allow_html=True)
    with col_r:
        st.markdown(risk_analysis_html(rec, score, sec_cnt, log_cnt), unsafe_allow_html=True)

    # 4. PR Summary
    st.markdown(pr_summary_html(summary), unsafe_allow_html=True)

    # 5. Security Findings
    st.markdown(security_section_html(sec_findings), unsafe_allow_html=True)

    # 6. Suggested Fixes
    st.markdown(suggestions_section_html(suggestions), unsafe_allow_html=True)

    # 8. Complexity Metrics
    st.markdown(complexity_section_html(test_sc, doc_sc, missing_tests, missing_docs), unsafe_allow_html=True)

    # Diff link
    m = _re.search(r'/pull/(\d+)', pr_url)
    pr_num   = m.group(1) if m else ''
    repo     = final_data.get('repo', '')
    diff_url = f"https://github.com/{repo}/pull/{pr_num}/files" if pr_num else f"https://github.com/{repo}"

    st.markdown(f"""
    <div class="rv-diff-desktop">
      <div class="rv-diff-card">
        <div class="rv-diff-title">Code Diff</div>
        <p style="font-size:12px;color:#52525b;margin-bottom:14px;line-height:1.6;">
          View the complete file-by-file diff for this pull request on GitHub.
        </p>
        <a href="{diff_url}" target="_blank" class="rv-diff-link">View diff on GitHub ↗</a>
      </div>
    </div>
    <div class="rv-diff-mobile">
      <a href="{diff_url}" target="_blank" class="rv-diff-mobile-btn">GitHub Diff View ↗</a>
    </div>
    """, unsafe_allow_html=True)

    errors = final_data.get("errors", [])
    if errors:
        with st.expander("⚠️ Pipeline warnings"):
            for e in errors:
                st.warning(e)

    st.markdown("""
    <div class="rv-footer">
      Built with LangGraph · GPT-4o · FastAPI · Streamlit &nbsp;·&nbsp;
      <a href="https://github.com/Satwik-Pamulaparthy/pr-review-agent">View on GitHub</a>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
