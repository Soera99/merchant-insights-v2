from __future__ import annotations

from datetime import date, timedelta
from html import escape

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from shared.theme import BAR_COLOR as BAR

from services.advanced_data import (
    KPI,
    load_dashboard_data,
    load_marketing_data,
    load_consumer_data,
    load_product_data,
    load_operations_data,
)


st.set_page_config(page_title="Klikko Merchant Intelligence", page_icon="K", layout="wide", initial_sidebar_state="collapsed")


# Height (px) of every line / bar chart card. Change this one number to resize all charts.
CHART_HEIGHT = 220
# Space (px) between the top edge of a chart box and its title.
CHART_TITLE_PAD = 25
# A text card that sits in the same row as a chart is never shorter than the chart box (chart height + 2px border).
CARD_HEIGHT = CHART_HEIGHT + 2
# Minimum height (px) of the text cards that share a row with a chart. Each value is the height that row's
# content needs, so nothing is cut off. A row is never shorter than CARD_HEIGHT. Increase a number if you add content.
ROW_H = {
    "voucher": max(CARD_HEIGHT, 262),      # Marketing: Voucher Status Distribution
    "comparison": max(CARD_HEIGHT, 268),   # Marketing: Top/Bottom Campaign + Campaign Timeline
    "behaviour": max(CARD_HEIGHT, 267),     # Consumer: Consumer Behaviour cards
    "merchant": max(CARD_HEIGHT, 221),      # Consumer: Merchant Ranking card
    "selling": max(CARD_HEIGHT, 177),       # Klikko-Hub: Machine Ranking + Revenue Snapshot
}


def inject_css() -> None:
    st.markdown("""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
      :root { --ink:#182230; --muted:#7d8999; --line:#e7ebf1; --blue:#5577d4; --canvas:#f5f7fa; }
      html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
      .stApp { background:var(--canvas); color:var(--ink); }
      .block-container { max-width:1092px; padding:1.25rem 1rem 3rem; }
      #MainMenu, footer, header, [data-testid="stToolbar"] { visibility:hidden; }
      .topbar { display:flex; justify-content:space-between; align-items:flex-end; gap:2rem; margin-bottom:1.15rem; }
      .eyebrow { color:#5570da; font-size:.72rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase; }
      .page-title { margin:.18rem 0 0; font-size:2rem; letter-spacing:-.04em; font-weight:700; }
      .subtitle { color:var(--muted); margin:.3rem 0 0; font-size:.88rem; }
      .live-pill { background:#e9f8ef; color:#138a50; border:1px solid #d4f0df; border-radius:99px; padding:.42rem .72rem; font-size:.74rem; font-weight:700; white-space:nowrap; }
      div[data-baseweb="tab-list"] { gap:.32rem; background:#fff; border:1px solid var(--line); padding:.36rem; border-radius:14px; overflow-x:auto; box-shadow:0 3px 14px rgba(39,57,86,.025); }
      button[data-baseweb="tab"] { border-radius:9px; padding:.62rem .8rem; color:#748094; white-space:nowrap; }
      button[data-baseweb="tab"] p { font-size:.79rem; }
      button[data-baseweb="tab"][aria-selected="true"] { background:#edf2ff; color:#3157cc; }
      div[data-baseweb="tab-highlight"], div[data-baseweb="tab-border"] { display:none; }
      [data-testid="stTabs"] [role="tablist"] { gap:.25rem; background:#fff; border:1px solid var(--line); padding:.32rem; border-radius:14px; box-shadow:0 3px 14px rgba(39,57,86,.025); }
      [data-testid="stTabs"] [role="tab"] { border-radius:9px; padding:.55rem .7rem; white-space:nowrap; }
      [data-testid="stTabs"] [role="tab"][aria-selected="true"] { background:#edf2ff; color:#3157cc; }
      [data-testid="stTabs"] [data-baseweb="tab-highlight"] { display:none; }
      .section-head { margin:1.55rem 0 .65rem; }
      .section-title { font-size:1.02rem; font-weight:700; letter-spacing:-.02em; }
      .kpi-card, .simple-card, .snapshot-card { background:#fff; border:1px solid var(--line); border-radius:16px; box-shadow:0 5px 18px rgba(39,57,86,.03); }
      .kpi-card { min-height:155px; padding:1rem 1rem .85rem; position:relative; overflow:hidden; }
      .kpi-icon { width:28px; height:28px; display:flex; align-items:center; justify-content:center; border-radius:9px; background:#eef3ff; color:#5577d4; font-weight:700; font-size:.7rem; }
      .kpi-delta { position:absolute; right:.85rem; top:1rem; color:#476cc8; background:#edf2ff; border-radius:99px; padding:.2rem .42rem; font-size:.66rem; font-weight:700; }
      .kpi-label { color:#7d8999; font-size:.72rem; margin-top:.65rem; }
      .kpi-value { font-size:1.34rem; font-weight:700; letter-spacing:-.035em; margin-top:.1rem; }
      .comparison { color:#a1a9b5; font-size:.65rem; margin-top:.05rem; }
      .kpi-bottom { display:flex; align-items:flex-end; gap:.55rem; margin-top:.72rem; }
      .target-wrap { flex:1; }.target-label { display:flex; justify-content:space-between; color:#697586; font-size:.62rem; margin-bottom:.25rem; }
      .target-track { height:4px; background:#edf0f4; border-radius:99px; overflow:hidden; }.target-fill { height:100%; background:#5577d4; border-radius:99px; }
      .sparkline { width:55px; height:22px; }
      .simple-card { padding:1rem; display:flex; flex-direction:column; justify-content:center; overflow:hidden; }
      .simple-label { color:#293548; font-size:.72rem; font-weight:700; }
      .simple-metric-row { display:flex; align-items:center; flex-wrap:wrap; gap:.45rem; margin-top:.32rem; }
      .simple-value { color:#111827; font-size:1.34rem; font-weight:700; letter-spacing:-.035em; white-space:nowrap; }
      .simple-delta { color:#0d9c5f; background:#e9faf2; border-radius:99px; padding:.22rem .45rem; font-size:.66rem; font-weight:700; white-space:nowrap; }
      .simple-comparison { color:#98a2b3; font-size:.65rem; margin-top:.42rem; }
      .kpi-row-gap { height:1rem; }
      .active-filter-wrap { margin:.3rem 0 .8rem; padding:.75rem .8rem; background:#f7f9fc; border:1px solid #e8edf4; border-radius:12px; }
      .active-filter-title { color:#667085; font-size:.68rem; font-weight:700; margin-bottom:.45rem; text-transform:uppercase; letter-spacing:.05em; }
      .active-filter-list { display:flex; flex-wrap:wrap; gap:.4rem; }
      .active-filter-chip { display:inline-flex; align-items:center; gap:.28rem; color:#3157a7; background:#eaf0ff; border:1px solid #d9e4ff; border-radius:99px; padding:.26rem .5rem; font-size:.68rem; white-space:nowrap; }
      .active-filter-chip b { color:#263a70; }
      .no-active-filter { color:#98a2b3; font-size:.72rem; }
      div[data-testid="stPlotlyChart"] { background:#fff; border:1px solid var(--line); border-radius:16px; overflow:hidden; box-shadow:0 5px 18px rgba(39,57,86,.03); }
      .snapshot-card { min-height:286px; padding:1rem 1.05rem; }.card-kicker { color:#293548; font-size:.78rem; font-weight:700; margin-bottom:.55rem; }
      .snapshot-row { display:flex; justify-content:space-between; gap:.7rem; padding:.62rem 0; border-top:1px solid #eef1f5; }
      .snap-type { color:#99a2b0; font-size:.61rem; }.snap-name { font-size:.74rem; font-weight:600; margin-top:.08rem; }.snap-value { font-size:.75rem; font-weight:700; text-align:right; align-self:center; white-space:nowrap; }
      .placeholder { margin-top:1rem; background:#fff; border:1px dashed #d6dce5; border-radius:16px; padding:4rem 2rem; text-align:center; color:#7c8797; }.placeholder b { color:#273244; }
      .stDownloadButton button { border-radius:10px; border-color:#dce2ec; font-size:.76rem; }
      [data-testid="stExpander"] { background:#fff; border:1px solid var(--line); border-radius:14px; }
      .section-head.split { display:flex; justify-content:space-between; align-items:baseline; }
      .section-aside { color:#98a2b3; font-size:.7rem; }
      .kpi-icon svg, .fc-icon svg { width:15px; height:15px; stroke:#5577d4; fill:none; stroke-width:2; stroke-linecap:round; stroke-linejoin:round; }
      .pill { color:#476cc8; background:#edf2ff; border-radius:99px; padding:.2rem .45rem; font-size:.66rem; font-weight:700; white-space:nowrap; }
      .mk-card { background:#fff; border:1px solid var(--line); border-radius:16px; box-shadow:0 5px 18px rgba(39,57,86,.03); padding:1rem 1.1rem; box-sizing:border-box; }
      .card-title { color:#182230; font-size:.86rem; font-weight:700; letter-spacing:-.01em; }
      .card-sub { color:#98a2b3; font-size:.68rem; margin-top:.12rem; }
      .fc-card { background:#fff; border:1px solid var(--line); border-radius:16px; box-shadow:0 5px 18px rgba(39,57,86,.03); padding:1rem; min-height:104px; }
      .fc-top { display:flex; justify-content:space-between; align-items:flex-start; }
      .fc-icon { width:28px; height:28px; display:flex; align-items:center; justify-content:center; border-radius:9px; background:#eef3ff; }
      .fc-label { color:#7d8999; font-size:.72rem; margin-top:.7rem; }
      .fc-value { font-size:1.34rem; font-weight:700; letter-spacing:-.035em; margin-top:.1rem; }
      .funnel-card { padding:1.15rem 1.3rem; }
      .funnel-row { display:grid; grid-template-columns:118px 1fr 46px; align-items:center; gap:.8rem; margin:.5rem 0; }
      .funnel-name { color:#667085; font-size:.72rem; }
      .funnel-track { position:relative; height:22px; background:#eef1fb; border-radius:6px; }
      .funnel-fill { height:100%; border-radius:6px; display:flex; align-items:center; padding-left:.5rem; box-sizing:border-box; font-size:.66rem; font-weight:700; white-space:nowrap; }
      .funnel-pct { position:absolute; right:.55rem; top:50%; transform:translateY(-50%); color:#98a2b3; font-size:.62rem; }
      .funnel-drop { color:#98a2b3; font-size:.68rem; text-align:right; }
      .ad-wrap { padding:0; overflow:hidden; }
      .ad-table { width:100%; border-collapse:collapse; font-size:.76rem; }
      .ad-table th { background:#f7f9fc; color:#7d8999; font-weight:600; font-size:.68rem; padding:.8rem 1rem; text-align:right; border-bottom:1px solid var(--line); }
      .ad-table td { padding:.85rem 1rem; text-align:right; color:#344054; }
      .ad-table th:first-child, .ad-table td:first-child { text-align:left; }
      .ad-table td:first-child { font-weight:600; color:#182230; }
      .ad-table tbody tr:nth-child(even) { background:#f9fafc; }
      .ad-table td.strong { font-weight:700; color:#182230; }
      .status-row { margin:.6rem 0; }
      .status-top { display:flex; justify-content:space-between; font-size:.74rem; color:#344054; margin-bottom:.32rem; }
      .status-top b { color:#182230; }
      .status-track { height:6px; background:#eef1f5; border-radius:99px; overflow:hidden; }
      .status-fill { height:100%; border-radius:99px; }
      .cmp-group { color:#7d8999; font-size:.64rem; font-weight:700; letter-spacing:.09em; margin:.15rem 0 .4rem; }
      .cmp-item { display:flex; align-items:baseline; gap:.55rem; font-size:.78rem; }
      .cmp-rank { color:#98a2b3; font-size:.68rem; }
      .cmp-name { font-weight:600; color:#182230; flex:1; }
      .cmp-val { font-weight:700; color:#182230; white-space:nowrap; }
      .cmp-track { height:5px; background:#eef1f5; border-radius:99px; overflow:hidden; margin:.5rem 0 1.4rem; }
      .cmp-track i { display:block; height:100%; background:#5577d4; border-radius:99px; }
      .cmp-track.bottom i { background:#f08a8a; }
      .tl-item { display:flex; gap:.7rem; padding:.55rem 0; position:relative; }
      .tl-item:not(:last-child)::after { content:""; position:absolute; left:4px; top:1.55rem; bottom:-.35rem; width:1px; background:#e7ebf1; }
      .tl-dot { width:9px; height:9px; border-radius:50%; margin-top:.28rem; flex:none; }
      .tl-name { font-size:.76rem; font-weight:600; color:#182230; }
      .tl-date { font-size:.66rem; color:#98a2b3; margin-top:.05rem; }
      .st-key-geo_card { background:#fff; border:1px solid var(--line); border-radius:16px; box-shadow:0 5px 18px rgba(39,57,86,.03); padding:1.05rem 1.15rem 2rem; }
      .st-key-geo_card div[data-testid="stPlotlyChart"] { background:#f1f4fd; border:1px solid #e6ebf7; border-radius:12px; box-shadow:none; }
      .map-foot { display:flex; justify-content:space-between; align-items:center; gap:1rem; flex-wrap:wrap; margin-top:.2rem; color:#7d8999; font-size:.7rem; }
      .map-legend { display:flex; align-items:center; gap:.5rem; }
      .legend-bar { width:140px; height:8px; border-radius:99px; }
      .map-foot b { color:#182230; font-weight:600; }
      [class*="st-key-fbox_"] { background:#fff; border:1px solid var(--line); border-radius:20px; padding:1rem 1.4rem; box-shadow:0 3px 14px rgba(39,57,86,.03); margin-bottom:.5rem; }
      .fb-title { font-size:1.12rem; font-weight:500; color:#182230; white-space:nowrap; }
      .fb-hint { color:#98a2b3; font-size:.8rem; margin-left:.9rem; }
      [class*="st-key-fbox_"] button { border-radius:99px; font-size:.78rem; padding:.3rem 1.15rem; min-height:0; white-space:nowrap; }
      [class*="st-key-fbox_"] button p { font-size:.78rem; }
      [class*="st-key-fbox_"] button[kind="secondary"], [class*="st-key-fbox_"] button[data-testid="stBaseButton-secondary"] { background:#fff; color:#182230; border:1px solid rgb(0,0,0); }
      [class*="st-key-fbox_"] button[kind="secondary"]:hover, [class*="st-key-fbox_"] button[kind="secondary"]:focus, [class*="st-key-fbox_"] button[kind="secondary"]:active, [class*="st-key-fbox_"] button[data-testid="stBaseButton-secondary"]:hover, [class*="st-key-fbox_"] button[data-testid="stBaseButton-secondary"]:focus, [class*="st-key-fbox_"] button[data-testid="stBaseButton-secondary"]:active { border-color:rgb(0,0,0); color:#000; background:#f3f4f7; }
      [class*="st-key-fbox_"] [data-testid="stWidgetLabel"] p, [class*="st-key-fbox_"] label p { font-weight:600; }
      [class*="st-key-fb_right_"] { align-items:flex-end; }
      [class*="st-key-fb_actions_"] { display:flex !important; flex-direction:row !important; flex-wrap:nowrap !important; justify-content:flex-start; align-items:center; gap:1rem !important; }
      [class*="st-key-fb_actions_"] > div { width:auto !important; }
      .fb-pills { display:flex; flex-wrap:wrap; gap:.45rem; align-items:center; }
      .fb-pill { background:#eef0f4; color:#667085; border-radius:99px; padding:.32rem .95rem; font-size:.78rem; white-space:nowrap; }
      .fb-pill b { color:#182230; font-weight:600; }
      .st-key-geo_toggle { align-items:flex-end; }
      .st-key-geo_toggle [data-testid="stButtonGroup"], .st-key-geo_toggle [role="radiogroup"] { background:#f1f3f7; border-radius:10px; padding:.2rem; gap:.2rem; }
      .st-key-geo_toggle button { border:none !important; border-radius:8px !important; background:transparent; color:#667085; font-size:.72rem; padding:.35rem .85rem; min-height:0; box-shadow:none; }
      .st-key-geo_toggle button p { font-size:.72rem; }
      .st-key-geo_toggle button[data-testid$="Active"], .st-key-geo_toggle button[aria-pressed="true"], .st-key-geo_toggle button[aria-checked="true"] { background:#5577d4 !important; color:#fff !important; }
      .st-key-geo_toggle button[data-testid$="Active"] p, .st-key-geo_toggle button[aria-pressed="true"] p, .st-key-geo_toggle button[aria-checked="true"] p { color:#fff; }
      [class*="st-key-fbox_"] [data-baseweb="select"] > div { background:#f3f4f7; border:none; border-radius:10px; }
      .kpi-card.compact { padding:.85rem .8rem .75rem; }
      .kpi-card.compact .kpi-value { font-size:1.15rem; }
      .kpi-card.compact .kpi-delta { right:.6rem; top:.85rem; font-size:.6rem; }
      .kpi-card.compact .kpi-label { min-height:1.9em; }
      .bl-row { display:grid; grid-template-columns:var(--lw,84px) 1fr auto; gap:.6rem; align-items:center; margin:.62rem 0; font-size:.7rem; }
      .bl-l { color:#475467; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
      .bl-track { height:5px; background:#eef1f5; border-radius:99px; overflow:hidden; }
      .bl-track i { display:block; height:100%; border-radius:99px; }
      .bl-v { text-align:right; color:#182230; font-weight:600; white-space:nowrap; }
      .rk-row { display:grid; grid-template-columns:22px minmax(0,1fr) auto; gap:.4rem; align-items:center; margin:.4rem 0; }
      .rk-n { color:#98a2b3; font-size:.68rem; }
      .rk-name { font-size:.74rem; font-weight:600; color:#182230; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
      .rk-track { height:4px; background:#eef1f5; border-radius:99px; overflow:hidden; margin-top:.32rem; }
      .rk-track i { display:block; height:100%; border-radius:99px; }
      .rk-v { text-align:right; font-size:.74rem; font-weight:700; color:#182230; white-space:nowrap; }
      .rk-v em { display:block; font-style:normal; font-weight:600; font-size:.64rem; color:#476cc8; }
      .fc-delta { color:#476cc8; font-size:.7rem; font-weight:600; margin-top:.4rem; }
      .dot { width:10px; height:10px; border-radius:50%; display:inline-block; flex:none; }
      .lc-top { display:flex; align-items:center; gap:.5rem; font-weight:700; font-size:.86rem; }
      .lc-num { font-size:1.45rem; font-weight:700; letter-spacing:-.03em; margin:.7rem 0 .25rem; }
      .lc-meta { display:flex; justify-content:space-between; color:#98a2b3; font-size:.7rem; margin-bottom:.45rem; }
      .lc-meta b { color:#182230; }
      .info-row { display:flex; justify-content:space-between; align-items:flex-start; padding:.85rem 0; font-size:.76rem; color:#667085; }
      .info-row b { color:#182230; display:block; text-align:right; }
      .info-row em { display:block; text-align:right; font-style:normal; color:#476cc8; font-size:.66rem; font-weight:600; }
      .big-num { font-size:1.55rem; font-weight:700; letter-spacing:-.03em; color:#182230; margin-top:.2rem; }
      .delta-blue { color:#476cc8; font-size:.7rem; font-weight:600; }
      .ms-pct { color:#98a2b3; font-size:.66rem; margin-top:.25rem; }
      .status-top .nm { display:inline-flex; align-items:center; gap:.45rem; }
      @media(max-width:900px){ .block-container{padding:1rem}.topbar{align-items:flex-start}.live-pill{display:none}.page-title{font-size:1.65rem}.simple-value,.kpi-value{font-size:1.15rem} }
    </style>
    """, unsafe_allow_html=True)


def section(title: str, aside: str = "") -> None:
    if aside:
        st.markdown(f'<div class="section-head split"><div class="section-title">{title}</div><div class="section-aside">{aside}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="section-head"><div class="section-title">{title}</div></div>', unsafe_allow_html=True)


ICONS = {
    "activity": '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
    "check-circle": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
    "users": '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "eye": '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "gift": '<polyline points="20 12 20 22 4 22 4 12"/><rect x="2" y="7" width="20" height="5"/><line x1="12" y1="22" x2="12" y2="7"/><path d="M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7z"/><path d="M12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7z"/>',
    "check-square": '<polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>',
    "trending-up": '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>',
    "zap": '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    "user-plus": '<path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/>',
    "repeat": '<polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/>',
    "dollar": '<line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
    "bar-chart": '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',
    "cart": '<circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/>',
    "package": '<line x1="16.5" y1="9.4" x2="7.5" y2="4.21"/><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/>',
    "clipboard": '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/>',
    "megaphone": '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/>',
    "alert-triangle": '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    "alert-circle": '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>',
    "flask": '<path d="M9 3h6"/><path d="M10 3v6L4.5 19a1.5 1.5 0 0 0 1.3 2h12.4a1.5 1.5 0 0 0 1.3-2L14 9V3"/>',
    "gauge": '<path d="M12 14l4-4"/><path d="M3.34 19a10 10 0 1 1 17.32 0"/>',
    "monitor": '<rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>',
    "arrow-up-right": '<line x1="7" y1="17" x2="17" y2="7"/><polyline points="7 7 17 7 17 17"/>',
    "cpu": '<rect x="4" y="4" width="16" height="16" rx="2" ry="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/>',
    "percent": '<line x1="19" y1="5" x2="5" y2="19"/><circle cx="6.5" cy="6.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/>',
    "tag": '<path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/>',
    "credit-card": '<rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/>',
}


def icon_svg(name: str) -> str:
    return f'<svg viewBox="0 0 24 24">{ICONS[name]}</svg>' if name in ICONS else ""


def compact(n: float) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return f"{n:.0f}"


def sparkline_svg(values: tuple[int, ...]) -> str:
    width, height, pad = 55, 22, 2
    low, high = min(values), max(values)
    span = max(high - low, 1)
    points = " ".join(f"{pad + i * (width - 2 * pad) / (len(values) - 1):.1f},{height - pad - (v - low) * (height - 2 * pad) / span:.1f}" for i, v in enumerate(values))
    return f'<svg class="sparkline" viewBox="0 0 {width} {height}"><polyline points="{points}" fill="none" stroke="#5577d4" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def render_kpi(kpi: KPI, compact: bool = False) -> None:
    initials = icon_svg(kpi.icon) or "".join(part[0] for part in kpi.label.split()[:2]).upper()
    st.markdown(f"""<div class="kpi-card{" compact" if compact else ""}"><div class="kpi-icon">{initials}</div><div class="kpi-delta">{kpi.delta}</div>
      <div class="kpi-label">{kpi.label}</div><div class="kpi-value">{kpi.value}</div><div class="comparison">{kpi.comparison}</div>
      <div class="kpi-bottom"><div class="target-wrap"><div class="target-label"><span>Target</span><b>{kpi.target}%</b></div>
      <div class="target-track"><div class="target-fill" style="width:{kpi.target}%"></div></div></div>{sparkline_svg(kpi.trend)}</div></div>""", unsafe_allow_html=True)


def render_simple_card(label: str, value: str, delta: str, comparison: str) -> None:
    st.markdown(f"""<div class="simple-card"><div class="simple-label">{label}</div>
      <div class="simple-metric-row"><div class="simple-value">{value}</div><div class="simple-delta">↑ {delta}</div></div>
      <div class="simple-comparison">{comparison}</div></div>""", unsafe_allow_html=True)


def trend_chart(title: str, subtitle: str, x: list[str], y: list[float], color: str, kind: str = "line", height: int = CHART_HEIGHT, unit: str = "", ticks: list[str] | None = None) -> go.Figure:
    fig = go.Figure()
    if kind == "bar":
        fig.add_bar(x=x, y=y, marker_color=color, marker_line_width=0, opacity=.9, hovertemplate="%{x}: %{y:,}" + unit + "<extra></extra>")
    else:
        rgb = tuple(int(color.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
        fig.add_scatter(x=x, y=y, mode="lines+markers", line=dict(color=color, width=2.2, shape="spline"), marker=dict(size=5, color=color, line=dict(color="white", width=1)), fill="tozeroy", fillcolor=f"rgba({rgb[0]},{rgb[1]},{rgb[2]},0.10)", hovertemplate="%{x}: %{y:,}" + unit + "<extra></extra>")
    fig.update_layout(title=dict(text=f"<b>{title}</b><br><span style='font-size:11px;color:#98a2b3'>{subtitle}</span>", x=.045, xref="container", y=1, yref="container", yanchor="top", pad=dict(t=CHART_TITLE_PAD)), height=height, margin=dict(l=30, r=25, t=CHART_TITLE_PAD + 52, b=30), paper_bgcolor="white", plot_bgcolor="white", font=dict(family="DM Sans", color="#344054"), showlegend=False, dragmode=False, xaxis=dict(showgrid=False, zeroline=False, fixedrange=True, tickfont=dict(size=10, color="#98a2b3")), yaxis=dict(showgrid=True, gridcolor="#eef1f5", zeroline=False, fixedrange=True, showticklabels=False), hoverlabel=dict(bgcolor="white", font_color="#182230"), bargap=.42)
    if ticks:
        fig.update_xaxes(tickmode="array", tickvals=ticks, ticktext=ticks)
    return fig


def render_snapshot(kicker: str, rows: list[tuple[str, str, str]]) -> None:
    content = "".join(f'<div class="snapshot-row"><div><div class="snap-type">{kind}</div><div class="snap-name">{name}</div></div><div class="snap-value">{value}</div></div>' for kind, name, value in rows)
    st.markdown(f'<div class="snapshot-card"><div class="card-kicker">{kicker}</div>{content}</div>', unsafe_allow_html=True)


MAP_CONFIG = {
    "Revenue": ("revenue", "Revenue", "Rp %{customdata[1]:,.0f}M", "#5577d4"),
    "Consumer": ("consumers", "Consumers", "%{customdata[1]:,.0f}", "#8b6bd8"),
    "Voucher": ("vouchers", "Vouchers", "%{customdata[1]:,.0f}", "#2f9b78"),
}
MAP_BG = "#f1f4fd"


def map_chart(frame: pd.DataFrame, metric: str) -> go.Figure:
    field, label, value_template, color = MAP_CONFIG[metric]
    values = frame[field]
    sizes = 10 + 34 * (values - values.min()) / max(values.max() - values.min(), 1)
    custom = pd.concat([frame["province"], values], axis=1).to_numpy()
    fig = go.Figure(go.Scattergeo(lon=frame["lon"], lat=frame["lat"], mode="markers+text", text=frame["province"].str.replace(" ", "<br>"), textposition="top center", textfont=dict(size=8, color="#667085"), marker=dict(size=sizes, color=values, colorscale=[[0, "#dbe5ff"], [1, color]], opacity=.88, line=dict(color="white", width=1), showscale=False), customdata=custom, hovertemplate=f"<b>%{{customdata[0]}}</b><br>{label}: {value_template}<extra></extra>"))
    fig.update_geos(scope="asia", projection_type="mercator", showland=True, landcolor="#e7ecf9", showocean=True, oceancolor=MAP_BG, showcountries=True, countrycolor="#d5dcee", showcoastlines=False, lataxis_range=[-12, 7], lonaxis_range=[94, 143], bgcolor=MAP_BG)
    fig.update_layout(height=400, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor=MAP_BG, geo=dict(center=dict(lat=-2.5, lon=118)), font=dict(family="DM Sans"), dragmode=False)
    return fig


def geo_card(frame: pd.DataFrame) -> None:
    """Heatmap card: title, metric toggle, map, legend and summary all live inside one box."""
    metric = st.session_state.get("map_metric") or "Revenue"
    field, _, _, color = MAP_CONFIG[metric]
    options = list(MAP_CONFIG)
    with st.container(key="geo_card"):
        head_left, head_right = st.columns([3, 2], gap="small")
        with head_left:
            st.markdown(f'<div class="card-title">Geographic Distribution by {metric}</div><div class="card-sub">Color by: <b>{metric}</b></div>', unsafe_allow_html=True)
        with head_right:
            with st.container(key="geo_toggle"):
                if hasattr(st, "segmented_control"):
                    st.segmented_control("Map metric", options, default="Revenue", key="map_metric", label_visibility="collapsed")
                else:
                    st.radio("Map metric", options, horizontal=True, key="map_metric", label_visibility="collapsed")
        st.plotly_chart(map_chart(frame, metric), width="stretch", config={"displayModeBar": False, "scrollZoom": False})
        leader = frame.sort_values(field, ascending=False).iloc[0]["province"]
        st.markdown(
            f'<div class="map-foot"><div class="map-legend"><span>Low</span><div class="legend-bar" style="background:linear-gradient(90deg,#dbe5ff,{color})"></div><span>High</span></div>'
            f'<div>Leading province: <b>{escape(str(leader))}</b> &nbsp;·&nbsp; Coverage: <b>{len(frame)} provinces</b></div></div>',
            unsafe_allow_html=True,
        )


FILTERS = {
    "Business Owner": ["All business owners", "Klikko Group", "Partner Network"],
    "Brand": ["All brands", "Brand A", "Brand B", "Brand C"],
    "Merchant": ["All merchants", "Guardian", "Klik Indomaret", "Outlet Network"],
    "Campaign": ["All campaigns", "Campaign Merdeka", "Klikko Payday", "Weekend Deal"],
    "Program Type": ["All program types", "Voucher", "Sampling", "Retail Media"],
    "Machine": ["All machines", "Vending BSD 01", "Kiosk JKT 041", "Kiosk SBY 018"],
    "Province": ["All provinces", "DKI Jakarta", "West Java", "East Java", "Bali"],
    "City": ["All cities", "Jakarta", "Bandung", "Surabaya", "Denpasar"],
    "Category": ["All categories", "Beverages", "Snacks", "Health & Beauty"],
    "Product": ["All products", "Iced Latte 250ml", "Matcha Cloud", "Caramel Macchiato"],
    "Consumer Segment": ["All consumer segments", "New", "Active", "Returning", "At risk"],
    "Gender": ["All genders", "Female", "Male", "Prefer not to say"],
    "Age Group": ["All age groups", "13–17", "18–24", "25–34", "35–50", "50+"],
}


def open_filter_editor(tab: str) -> None:
    applied = st.session_state.get("applied_filters", {})
    for name, options in FILTERS.items():
        st.session_state[f"{tab}_draft_{name}"] = applied.get(name, options[0])
    st.session_state["filter_editing_tab"] = tab


def apply_filters(tab: str) -> None:
    chosen = {name: st.session_state.get(f"{tab}_draft_{name}", options[0]) for name, options in FILTERS.items()}
    st.session_state["applied_filters"] = {n: v for n, v in chosen.items() if v != FILTERS[n][0]}
    st.session_state["filter_editing_tab"] = None


def cancel_filters() -> None:
    st.session_state["filter_editing_tab"] = None


def clear_filters() -> None:
    st.session_state["applied_filters"] = {}


def h_container(key: str):
    """Horizontal wrapping row; uses the native option when this Streamlit version has it, CSS otherwise."""
    try:
        return st.container(key=key, horizontal=True)
    except TypeError:
        return st.container(key=key)


def filter_bar(tab: str) -> None:
    """Filter panel shared by every tab. Applied filters live in session state, so they follow the user across tabs."""
    applied = st.session_state.get("applied_filters", {})
    editing = st.session_state.get("filter_editing_tab") == tab
    title = '<span class="fb-title">Filters :</span>'
    with st.container(key=f"fbox_{tab}"):
        if editing:
            left, right = st.columns([6, 1.3], vertical_alignment="center")
            hint = "Choose filters, then click Apply Filter" if applied else "No filters applied - showing all data"
            left.markdown(f'{title}<span class="fb-hint">{hint}</span>', unsafe_allow_html=True)
            with right:
                with st.container(key=f"fb_right_{tab}"):
                    st.button("Add Filter", key=f"fb_add_{tab}", type="primary", disabled=True)
            names = list(FILTERS)
            for start in range(0, len(names), 4):
                columns = st.columns(4, gap="medium")
                for column, name in zip(columns, names[start:start + 4]):
                    with column:
                        st.selectbox(name, FILTERS[name], key=f"{tab}_draft_{name}")
            with h_container(f"fb_actions_{tab}"):
                st.button("Apply Filter", key=f"fb_apply_{tab}", type="primary", on_click=apply_filters, args=(tab,))
                st.button("Cancel", key=f"fb_cancel_{tab}", on_click=cancel_filters)
        elif applied:
            title_col, pills_col, action_col = st.columns([1, 6.3, 1.9], vertical_alignment="center")
            title_col.markdown(title, unsafe_allow_html=True)
            pills = "".join(f'<span class="fb-pill">{escape(name)}: <b>{escape(value)}</b></span>' for name, value in applied.items())
            pills_col.markdown(f'<div class="fb-pills">{pills}</div>', unsafe_allow_html=True)
            with action_col:
                with st.container(key=f"fb_right_{tab}"):
                    st.button("Add Filter", key=f"fb_add_{tab}", type="primary", on_click=open_filter_editor, args=(tab,))
                    st.button("Clear All Filter", key=f"fb_clear_{tab}", on_click=clear_filters)
        else:
            left, right = st.columns([6, 1.3], vertical_alignment="center")
            left.markdown(f'{title}<span class="fb-hint">No filters applied - showing all data</span>', unsafe_allow_html=True)
            with right:
                with st.container(key=f"fb_right_{tab}"):
                    st.button("Add Filter", key=f"fb_add_{tab}", type="primary", on_click=open_filter_editor, args=(tab,))


def executive_overview(data: dict) -> None:
    filter_bar("exec")
    section("Executive KPI Cards")
    for start in (0, 5):
        cols = st.columns(5, gap="medium")
        for col, kpi in zip(cols, data["kpis"][start:start + 5]):
            with col:
                if start == 0:
                    render_kpi(kpi)
                else:
                    render_simple_card(kpi.label, kpi.value, kpi.delta, kpi.comparison)
        if start == 0:
            st.markdown('<div class="kpi-row-gap"></div>', unsafe_allow_html=True)

    section("Business Growth Trend")
    charts = [("Revenue Trend", "Last 12 Months", data["revenue"], "#5577d4", "line"), ("Consumer Trend", "Last 12 Months", data["consumer"], "#8467d7", "line"), ("Campaign Trend", "Last 12 Months", data["campaign"], "#5577d4", "bar"), ("Voucher Redemption Trend", "Last 12 Months", data["redemption"], "#2f9b78", "line")]
    for pair_start in (0, 2):
        cols = st.columns(2, gap="large")
        for col, item in zip(cols, charts[pair_start:pair_start + 2]):
            with col: st.plotly_chart(trend_chart(item[0], item[1], data["months"], item[2], item[3], item[4]), width="stretch", config={"displayModeBar": False, "scrollZoom": False, "doubleClick": False})

    section("Business Snapshot")
    snapshots = [
        ("Ranked performance", [("TOP CAMPAIGN", "Campaign Merdeka", "Rp 840M"), ("TOP PRODUCT", "Iced Latte 250ml", "9,820"), ("TOP MERCHANT", "Guardian BSD Central", "Rp 420M"), ("TOP MACHINE", "Vending BSD Central 01", "Rp 180M"), ("TOP PROVINCE", "DKI Jakarta", "Rp 1.2B")]),
        ("Attention required", [("BOTTOM CAMPAIGN", "Bakery Weekday Deal", "Rp 12M"), ("BOTTOM PRODUCT", "Expired Bakery Item", "284"), ("BOTTOM MERCHANT", "Outlet Cikini", "Rp 8M"), ("LOWEST ROI", "Morning Snack Trial", "0.7x"), ("LOWEST REDEMPTION", "Weekend Bundle", "18.2%")]),
        ("Key operating signals", [("ACTIVE USERS", "Last 30 days", "48,291"), ("CAMPAIGN SUCCESS", "Above ROI threshold", "76.4%"), ("MERCHANT COVERAGE", "Active locations", "1,284"), ("AVG SESSION", "Merchant portal", "08m 42s"), ("AVG CAMPAIGN ROI", "Revenue per cost", "3.8x")]),
    ]
    cols = st.columns(3, gap="large")
    for col, (kicker, rows) in zip(cols, snapshots):
        with col: render_snapshot(kicker, rows)

    section("Indonesia Business Heatmap")
    geo_card(data["geography"])

    section("Forecast Summary — Next 30 Days")
    forecasts = [("Revenue Forecast", "Rp 1.4B", "+9.2% expected", "#5577d4"), ("Consumer Forecast", "+28,400", "+7.8% expected", "#8467d7"), ("Redemption Forecast", "88,400", "+14.0% expected", "#2f9b78"), ("Campaign Completion", "84%", "+4.0pp expected", "#3578c8")]
    cols = st.columns(4, gap="large")
    for col, (label, value, note, accent) in zip(cols, forecasts):
        with col: render_simple_card(label, value, note.replace(" expected", ""), "vs. current 30-day run rate")


def render_forecast_card(label: str, value: str, delta: str, icon: str) -> None:
    st.markdown(f'<div class="fc-card"><div class="fc-top"><div class="fc-icon">{icon_svg(icon)}</div><div class="pill">{delta}</div></div><div class="fc-label">{label}</div><div class="fc-value">{value}</div></div>', unsafe_allow_html=True)


def funnel_card(steps: list[tuple[str, int]]) -> None:
    top = steps[0][1]
    shades = ["#6f83c9", "#a2b0e2", "#b4c0e8", "#bfc9ec", "#c7d0ef", "#cfd7f1", "#d6ddf3", "#dde3f5"]
    rows = []
    for i, (name, value) in enumerate(steps):
        share = value / top * 100
        drop = "" if i == 0 else f"-{(1 - value / steps[i - 1][1]) * 100:.0f}%"
        text = "#ffffff" if i == 0 else "#33415c"
        pct = f"{share:.0f}%" if share >= 10 else f"{share:.1f}%"
        rows.append(f'<div class="funnel-row"><div class="funnel-name">{escape(name)}</div><div class="funnel-track"><div class="funnel-fill" style="width:{max(share, 5):.1f}%;background:{shades[min(i, len(shades) - 1)]};color:{text}">{compact(value)}</div><div class="funnel-pct" style="{"color:rgba(255,255,255,.8)" if i == 0 else ""}">{pct}</div></div><div class="funnel-drop">{drop}</div></div>')
    st.markdown(f'<div class="mk-card funnel-card">{"".join(rows)}</div>', unsafe_allow_html=True)


def ad_table(rows: list[tuple[str, ...]]) -> None:
    head = "".join(f"<th>{h}</th>" for h in ("Ad Types", "Reach", "Engagement", "CTR", "Completion", "Conversion"))
    body = "".join("<tr>" + f"<td>{escape(r[0])}</td><td>{r[1]}</td><td>{r[2]}</td><td class=\"strong\">{r[3]}</td><td>{r[4]}</td><td class=\"strong\">{r[5]}</td>" + "</tr>" for r in rows)
    st.markdown(f'<div class="mk-card ad-wrap"><table class="ad-table"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>', unsafe_allow_html=True)


def status_card(items: list[tuple[str, int, str]]) -> None:
    issued = items[0][1]
    rows = "".join(f'<div class="status-row"><div class="status-top"><span>{escape(n)}</span><b>{compact(v)}</b></div><div class="status-track"><div class="status-fill" style="width:{v / issued * 100:.1f}%;background:{c}"></div></div></div>' for n, v, c in items)
    st.markdown(f'<div class="mk-card" style="min-height:{ROW_H["voucher"]}px"><div class="card-title">Voucher Status Distribution</div><div class="card-sub">Current snapshot</div><div style="margin-top:.6rem">{rows}</div></div>', unsafe_allow_html=True)


def compare_card(top: tuple, bottom: tuple) -> None:
    st.markdown(
        f'<div class="mk-card" style="min-height:{ROW_H["comparison"]}px"><div class="cmp-group">TOP CAMPAIGN</div>'
        f'<div class="cmp-item"><span class="cmp-rank">#1</span><span class="cmp-name">{escape(top[0])}</span><span class="cmp-val">{top[1]}</span></div>'
        f'<div class="cmp-track"><i style="width:{top[2]}%"></i></div>'
        f'<div class="cmp-group">BOTTOM CAMPAIGN</div>'
        f'<div class="cmp-item"><span class="cmp-rank">#1</span><span class="cmp-name">{escape(bottom[0])}</span><span class="cmp-val">{bottom[1]}</span></div>'
        f'<div class="cmp-track bottom"><i style="width:{bottom[2]}%"></i></div></div>',
        unsafe_allow_html=True,
    )


def timeline_card(items: list[tuple[str, str, str]]) -> None:
    rows = "".join(f'<div class="tl-item"><div class="tl-dot" style="background:{c}"></div><div><div class="tl-name">{escape(n)}</div><div class="tl-date">{d}</div></div></div>' for n, d, c in items)
    st.markdown(f'<div class="mk-card" style="min-height:{ROW_H["comparison"]}px"><div class="card-title">Campaign Timeline</div><div class="card-sub">Execution plan overview</div><div style="margin-top:.7rem">{rows}</div></div>', unsafe_allow_html=True)


def marketing_overview(data: dict, months: list[str]) -> None:
    filter_bar("mkt")
    section("Campaign KPI", "Real-time data")
    for start in (0, 5):
        cols = st.columns(5, gap="medium")
        for col, kpi in zip(cols, data["kpis"][start:start + 5]):
            with col: render_kpi(kpi)
        if start == 0:
            st.markdown('<div class="kpi-row-gap"></div>', unsafe_allow_html=True)

    section("Campaign Funnel")
    funnel_card(data["funnel"])

    section("Advertisement Performance")
    ad_table(data["ads"])

    section("Voucher Intelligence")
    left, right = st.columns(2, gap="large")
    with left:
        st.plotly_chart(trend_chart("Voucher Lifecycle Trend", "Last 12 months", months, data["lifecycle"], "#2f9b78"), width="stretch", config={"displayModeBar": False, "scrollZoom": False, "doubleClick": False})
    with right:
        status_card(data["status"])

    section("Campaign Comparison")
    a, b, c = st.columns(3, gap="large")
    with a: compare_card(data["top"], data["bottom"])
    with b: timeline_card(data["timeline"])
    with c:
        st.plotly_chart(trend_chart("Campaign Trend", "ROI vs Trend", months, data["roi"], "#5577d4", "bar", unit="×"), width="stretch", config={"displayModeBar": False, "scrollZoom": False, "doubleClick": False})

    section("Campaign Forecast — Next 30 Days")
    cols = st.columns(4, gap="large")
    for col, item in zip(cols, data["forecast"]):
        with col: render_forecast_card(*item)


TREND_CONFIG = {"displayModeBar": False, "scrollZoom": False, "doubleClick": False}
TICKS = ["Jan", "Mar", "May", "Jul", "Sep", "Nov", "Dec"]
BLUE, PURPLE, GREEN = "#5577d4", "#8467d7", "#2f9b78"



# ---------------------------------------------------------------- shared helpers
def mk(inner: str, h: int | None = None) -> None:
    style = f' style="min-height:{h}px"' if h else ""
    st.markdown(f'<div class="mk-card"{style}>{inner}</div>', unsafe_allow_html=True)


def head(title: str, sub: str = "") -> str:
    return f'<div class="card-title">{escape(title)}</div>' + (f'<div class="card-sub">{escape(sub)}</div>' if sub else "")


def kicker(text: str) -> str:
    return f'<div class="cmp-group">{escape(text)}</div>'


def bar_rows(rows: list[tuple[str, float, str, str]], label_w: int = 84) -> str:
    """rows: (label, bar width %, value text, colour)"""
    return "".join(
        f'<div class="bl-row" style="--lw:{label_w}px"><span class="bl-l">{escape(label)}</span><div class="bl-track"><i style="width:{max(width, 3):.0f}%;background:{color}"></i></div><span class="bl-v">{escape(value)}</span></div>'
        for label, width, value, color in rows
    )


def stat_rows(rows: list[tuple[str, float, str, str]]) -> str:
    """Progress rows with the label and value on top of the bar."""
    return "".join(
        f'<div class="status-row"><div class="status-top"><span>{escape(label)}</span><b>{escape(value)}</b></div><div class="status-track"><div class="status-fill" style="width:{width:.0f}%;background:{color}"></div></div></div>'
        for label, width, value, color in rows
    )


def rank_rows(rows: list[tuple], bars: bool = True) -> str:
    """rows: (name, value, bar width %, optional delta, optional colour)"""
    out = []
    for i, row in enumerate(rows, 1):
        name, value, width = row[0], row[1], row[2]
        delta = row[3] if len(row) > 3 else ""
        color = row[4] if len(row) > 4 else BAR
        bar = f'<div class="rk-track"><i style="width:{width:.0f}%;background:{color}"></i></div>' if bars else ""
        extra = f"<em>{escape(delta)}</em>" if delta else ""
        out.append(f'<div class="rk-row"><span class="rk-n">#{i}</span><div><div class="rk-name">{escape(name)}</div>{bar}</div><span class="rk-v">{escape(value)}{extra}</span></div>')
    return "".join(out)


def info_rows(rows: list[tuple[str, str, str]]) -> str:
    return "".join(f'<div class="info-row"><span>{escape(label)}</span><span><b>{escape(value)}</b><em>{escape(delta)}</em></span></div>' for label, value, delta in rows)


def chart(fig) -> None:
    st.plotly_chart(fig, width="stretch", config=TREND_CONFIG)


def scaled(rows: list[tuple[str, float, str]], color: str = BAR) -> list[tuple[str, float, str, str]]:
    """Turn (label, number, text) into bar rows whose widths are relative to the largest value."""
    top = max(value for _, value, _ in rows)
    return [(label, value / top * 100, text, color) for label, value, text in rows]




def kpi_row(kpis: list[KPI], compact: bool = False) -> None:
    cols = st.columns(len(kpis), gap="small" if compact else "medium")
    for col, kpi in zip(cols, kpis):
        with col: render_kpi(kpi, compact)


def forecast_row(items: list[tuple[str, str, str, str]]) -> None:
    cols = st.columns(len(items), gap="large" if len(items) <= 4 else "medium")
    for col, item in zip(cols, items):
        with col: render_forecast_card(*item)


def simple_metric_card(label: str, value: str, delta: str, icon: str) -> None:
    st.markdown(f'<div class="fc-card"><div class="fc-top"><div class="fc-icon">{icon_svg(icon)}</div></div><div class="fc-label">{escape(label)}</div><div class="fc-value">{value}</div><div class="fc-delta">{delta}</div></div>', unsafe_allow_html=True)


# ---------------------------------------------------------------- Consumer & Merchant Intelligence


def profile_card(title: str, sub: str, rows: list[tuple[str, float]], label_w: int = 96) -> None:
    mk(head(title, sub) + f'<div style="margin-top:.7rem">{bar_rows([(label, value, f"{value}%", BAR) for label, value in rows], label_w)}</div>', 215)


def consumer_overview(data: dict, months: list[str]) -> None:
    filter_bar("con")
    section("Consumer KPI", "Real-time data")
    kpi_row(data["kpis"], compact=True)

    section("Consumer Profile")
    cols = st.columns(3, gap="large")
    with cols[0]: mk(head("Gender Distribution", "Consumer breakdown") + f'<div style="margin-top:.6rem">{stat_rows(data["gender"])}</div>', 215)
    with cols[1]: profile_card("Age Group", "Consumer by age", data["age"], 48)
    with cols[2]: profile_card("Generation", "Generational split", data["generation"], 72)
    st.markdown('<div class="kpi-row-gap"></div>', unsafe_allow_html=True)
    cols = st.columns(3, gap="large")
    with cols[0]: profile_card("Occupation", "By profession", data["occupation"], 88)
    with cols[1]: profile_card("Income Bracket", "Income segments", data["income"], 100)
    with cols[2]: profile_card("Loyalty Tier", "Member status", data["loyalty"], 72)

    section("Consumer Behaviour")
    a, b, c = st.columns(3, gap="large")
    with a: mk(kicker("FAVORITE PRODUCT") + rank_rows(data["fav_product"]) + kicker("FAVORITE MERCHANT") + rank_rows(data["fav_merchant"]), ROW_H["behaviour"])
    with b: chart(trend_chart("Purchase Frequency", "Last 12 months", months, data["frequency"], BLUE, ticks=TICKS))
    with c: mk(kicker("FAVORITE CATEGORY") + rank_rows(data["fav_category"]) + kicker("PREFERRED PURCHASE TIME") + bar_rows([(label, value, f"{value}%", BAR) for label, value in data["purchase_time"]], 92), ROW_H["behaviour"])

    section("Merchant Performance")
    left, right = st.columns([2, 3], gap="large")
    with left:
        mk(kicker("MERCHANT RANKING") + rank_rows([(n, v, 0, d) for n, v, d in data["merchants"]], bars=False) + kicker("AVERAGE BASKET VALUE") + '<div class="big-num">Rp 48K</div><div class="delta-blue">+4.2% vs last period</div>', ROW_H["merchant"])
    with right:
        chart(trend_chart("Merchant Trend", "Performance over time", months, data["merchant_trend"], BLUE, "bar", ticks=TICKS))

    section("Consumer Journey")
    funnel_card(data["journey"])

    section("Prediction — Next 30 Days")
    forecast_row(data["forecast"])


# ---------------------------------------------------------------- Product & Sales Intelligence


def product_overview(data: dict, months: list[str]) -> None:
    filter_bar("prod")
    section("Sales KPI", "Real-time data")
    kpi_row(data["sales_kpis"], compact=True)
    section("Product KPI", "Real-time data")
    kpi_row(data["product_kpis"], compact=True)

    section("Product Analysis")
    cols = st.columns(5, gap="medium")
    for col, (title, rows) in zip(cols, data["analysis"]):
        with col: mk(head(title, "Top performers") + f'<div style="margin-top:.7rem">{bar_rows(scaled(rows), 78)}</div>', 175)

    section("Product Lifecycle")
    cols = st.columns(4, gap="medium")
    for col, (name, count, pct, color) in zip(cols, data["lifecycle"]):
        with col:
            mk(f'<div class="lc-top"><i class="dot" style="background:{color}"></i>{escape(name)}</div><div class="lc-num">{count}</div><div class="lc-meta"><span>products</span><b>{pct}%</b></div><div class="status-track"><div class="status-fill" style="width:{pct}%;background:{color}"></div></div>')

    section("Product Ranking")
    cols = st.columns(5, gap="medium")
    for col, (title, rows, color) in zip(cols, data["ranking"]):
        with col: mk(kicker(title) + rank_rows([(n, v, w, "", color) for n, v, w in rows]), 185)

    section("Performance Trends")
    left, right = st.columns(2, gap="large")
    with left: chart(trend_chart("Revenue Trend", "Last 12 months", months, data["revenue_trend"], BLUE, ticks=TICKS))
    with right: chart(trend_chart("Product Sales Trend", "Last 12 months", months, data["sales_trend"], BLUE, "bar", ticks=TICKS))

    section("Forecast — Next 30 Days")
    forecast_row(data["forecast"])


# ---------------------------------------------------------------- Klikko-Hub & Operational Intelligence


def operations_overview(data: dict, months: list[str]) -> None:
    filter_bar("ops")
    section("Machine KPI", "Real-time data")
    kpi_row(data["kpis"], compact=True)

    section("Selling Performance")
    a, b, c = st.columns(3, gap="large")
    with a: mk(head("Machine Ranking", "Top 3 by revenue") + f'<div style="margin-top:.6rem">{rank_rows(data["ranking"])}</div>', ROW_H["selling"])
    with b: chart(trend_chart("Sales Trend", "Last 12 months", months, data["sales_trend"], BLUE, ticks=TICKS))
    with c: mk(kicker("REVENUE SNAPSHOT") + stat_rows(data["snapshot"]), ROW_H["selling"])

    section("Sampling Performance")
    cols = st.columns(5, gap="medium")
    for col, item in zip(cols, data["sampling"]):
        with col: simple_metric_card(*item)

    section("Retail Media Performance")
    cols = st.columns(3, gap="large")
    for col, (title, rows) in zip(cols, data["media"]):
        with col: mk(head(title, "Current metrics") + f'<div style="margin-top:.5rem">{info_rows(rows)}</div>', 200)

    section("Machine Performance")
    a, b, c = st.columns(3, gap="large")
    with a: mk(head("Revenue by Machine", "Top performers") + f'<div style="margin-top:.6rem">{rank_rows(data["machine_revenue"])}</div><div class="delta-blue" style="margin-top:.9rem">+18.4% Growth</div>', 290)
    with b:
        rows = "".join(
            f'<div class="status-row"><div class="status-top"><span class="nm"><i class="dot" style="background:{color}"></i>{escape(name)}</span><b>{count}</b></div><div class="status-track"><div class="status-fill" style="width:{pct}%;background:{color}"></div></div><div class="ms-pct">{pct}%</div></div>'
            for name, count, pct, color in data["status"]
        )
        mk(head("Machine Status", "Current state") + f'<div style="margin-top:.6rem">{rows}</div>', 290)
    with c: mk(head("Regional Distribution", "By machines & revenue") + f'<div style="margin-top:.7rem">{bar_rows(scaled([(n, v, str(v)) for n, v in data["regions"]]), 84)}</div>', 290)

    section("Operational Forecast — Next 30 Days")
    forecast_row(data["forecast"])


inject_css()
data = load_dashboard_data()
updated = date.today() - timedelta(days=1)
st.markdown(f'<div class="topbar"><div><div class="eyebrow">Klikko Intelligence</div><div class="page-title">Merchant Dashboard</div><div class="subtitle">Executive performance across revenue, customers, campaigns, vouchers, and operations · Updated {updated:%d %b %Y}</div></div><div class="live-pill">● &nbsp; Demo data connected</div></div>', unsafe_allow_html=True)

tab_names = ["Executive Overview", "Marketing & Campaign Intelligence", "Consumer & Merchant Intelligence", "Product & Sales Intelligence", "Klikko-Hub & Operational Intelligence"]
tabs = st.tabs(tab_names)
with tabs[0]: executive_overview(data)
with tabs[1]: marketing_overview(load_marketing_data(), data["months"])
with tabs[2]: consumer_overview(load_consumer_data(), data["months"])
with tabs[3]: product_overview(load_product_data(), data["months"])
with tabs[4]: operations_overview(load_operations_data(), data["months"])
