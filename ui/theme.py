"""Colours, CSS and Plotly styling shared by every tab."""
from __future__ import annotations
import streamlit as st

# One colour per algorithm, used identically in every chart / network view.
ALGO_ORDER = ["Greedy", "Betweenness", "SA", "Exhaustive"]
ALGO_COLORS = {
    "Greedy": "#38bdf8",       # sky
    "Betweenness": "#fb923c",  # orange
    "SA": "#c084fc",           # violet
    "Exhaustive": "#2dd4bf",   # teal
}
ALGO_LONG = {
    "Greedy": "Greedy",
    "Betweenness": "Betweenness (top-k)",
    "SA": "Simulated Annealing",
    "Exhaustive": "Exhaustive",
}

ROLE_COLORS = {
    "Source": "#a3e635",
    "Target": "#f43f5e",
    "Eligible": "#3b82f6",
    "Ineligible": "#64748b",
}
HONEYPOT = "#facc15"
PATH_HILITE = "#fb7185"
SYNTH_EDGE = "#f472b6"
EDGE_BASE = "#475569"
GOOD = "#34d399"
BAD = "#f87171"
MUTED = "#94a3b8"

CSS = """
<style>
:root { --accent:#22d3ee; --panel:#111a2e; --panel2:#0f172a; --line:#1e293b; }
.block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1500px; }
h1, h2, h3 { letter-spacing: -0.01em; }
h1 { font-weight: 700; }
/* metric cards */
div[data-testid="stMetric"] {
  background: linear-gradient(180deg, #111a2e 0%, #0e1627 100%);
  border: 1px solid var(--line); border-left: 3px solid var(--accent);
  border-radius: 10px; padding: 0.8rem 1rem;
}
div[data-testid="stMetricLabel"] p { color:#94a3b8; font-size:0.78rem;
  text-transform:uppercase; letter-spacing:0.06em; }
div[data-testid="stMetricValue"] { font-size: 1.55rem; font-weight: 650; }
/* sidebar */
section[data-testid="stSidebar"] { border-right: 1px solid var(--line); }
.brand { font-weight:800; font-size:1.15rem; letter-spacing:0.08em; color:#e2e8f0; }
.brand span { color: var(--accent); }
.brand-sub { color:#64748b; font-size:0.72rem; letter-spacing:0.12em;
  text-transform:uppercase; margin-bottom:0.8rem; }
.runcard { background: var(--panel); border:1px solid var(--line);
  border-radius:10px; padding:0.7rem 0.85rem; font-size:0.82rem; line-height:1.55; }
.runcard b { color:#e2e8f0; } .runcard .k { color:#94a3b8; }
/* tags & callouts */
.tag { display:inline-block; padding:0.12rem 0.55rem; border-radius:999px;
  font-size:0.74rem; font-weight:600; border:1px solid; margin-right:0.3rem; }
.callout { background:#0f1c33; border:1px solid #1d3557; border-left:3px solid var(--accent);
  border-radius:8px; padding:0.7rem 0.95rem; margin:0.4rem 0 0.8rem 0; font-size:0.92rem; }
.callout.warn { border-left-color:#fbbf24; background:#211a0b; border-color:#4a3a10; }
.callout.good { border-left-color:#34d399; background:#0b2119; border-color:#14532d; }
.sub { color:#94a3b8; margin-top:-0.6rem; margin-bottom:1rem; }
.nodechip { display:inline-block; background:#0f172a; border:1px solid #334155;
  border-radius:6px; padding:0.05rem 0.5rem; margin:0.1rem 0.2rem 0.1rem 0;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size:0.82rem; }
.stTabs [data-baseweb="tab"] { height: 2.4rem; }
div[data-testid="stExpander"] { border:1px solid var(--line); border-radius:10px; }
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def header(title: str, subtitle: str | None = None):
    st.markdown(f"# {title}")
    if subtitle:
        st.markdown(f'<div class="sub">{subtitle}</div>', unsafe_allow_html=True)


def callout(text: str, kind: str = "info"):
    cls = {"info": "", "warn": " warn", "good": " good"}[kind]
    st.markdown(f'<div class="callout{cls}">{text}</div>', unsafe_allow_html=True)


def tag(text: str, color: str) -> str:
    return (f'<span class="tag" style="color:{color};border-color:{color};'
            f'background:{color}1a">{text}</span>')


def chips(nodes) -> str:
    items = sorted(nodes, key=str)
    if not items:
        return '<span class="sub">(none)</span>'
    return "".join(f'<span class="nodechip">{n}</span>' for n in items)


def style(fig, height: int | None = None, legend: bool = True, title: str | None = None):
    """Apply the dark cyber look to any Plotly figure."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, -apple-system, Segoe UI, sans-serif",
                  color="#cbd5e1", size=12),
        margin=dict(l=10, r=10, t=48 if title else 30, b=56 if legend else 10),
        showlegend=legend,
        legend=dict(bgcolor="rgba(15,23,42,0.7)", bordercolor="#1e293b", borderwidth=1,
                    orientation="h", yanchor="top", y=-0.14, xanchor="left", x=0),
        hoverlabel=dict(bgcolor="#0f172a", bordercolor="#334155", font_size=12),
    )
    if title:
        fig.update_layout(title=dict(text=title, font=dict(size=14, color="#e2e8f0"),
                                     x=0, xanchor="left"))
    if height:
        fig.update_layout(height=height)
    fig.update_xaxes(gridcolor="#1e293b", zerolinecolor="#1e293b", linecolor="#334155")
    fig.update_yaxes(gridcolor="#1e293b", zerolinecolor="#1e293b", linecolor="#334155")
    return fig
