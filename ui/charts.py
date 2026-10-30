"""Reusable Plotly charts (all take backend-derived DataFrames)."""
from __future__ import annotations
import math
import plotly.graph_objects as go

from ui import theme
from ui.theme import ALGO_COLORS


def algo_bar(df, col, title, *, ytitle=None, log=False, fmt="{:g}", hline=None,
             hline_label=None, height=320):
    """One bar per algorithm in the shared algorithm colours (skips missing values)."""
    d = df.dropna(subset=[col])
    fig = go.Figure(go.Bar(
        x=d["Algorithm"], y=d[col],
        marker=dict(color=[ALGO_COLORS[a] for a in d["Algorithm"]],
                    line=dict(color="#0b1220", width=1)),
        text=[fmt.format(v) for v in d[col]], textposition="outside",
        cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>" + (ytitle or col) + ": %{y:,.4g}<extra></extra>"))
    if hline is not None:
        fig.add_hline(y=hline, line=dict(color="#facc15", dash="dot", width=1.5))
    theme.style(fig, height=height, legend=False, title=title)
    fig.update_yaxes(title=ytitle, type="log" if log else "linear")
    if log and len(d):
        lo = math.floor(math.log10(max(d[col].min(), 1e-9)))
        hi = math.ceil(math.log10(max(d[col].max(), 1e-9)))
        hi = max(hi, lo + 1)
        ticks = [10.0 ** e for e in range(lo, hi + 1)]
        fig.update_yaxes(tickvals=ticks, ticktext=[f"{t:g}" for t in ticks],
                         range=[lo - 0.15, math.log10(d[col].max()) + 0.35], minor=dict(showgrid=False))
    if not log:
        top = max([hline or 0] + list(d[col])) if len(d) else 1
        fig.update_yaxes(range=[0, top * 1.22 if top else 1])
    return fig


def cov_runtime_scatter(df, height=380):
    d = df.dropna(subset=["Coverage", "Runtime (ms)"])
    fig = go.Figure()
    for _, row in d.iterrows():
        fig.add_trace(go.Scatter(
            x=[max(row["Runtime (ms)"], 1e-4)], y=[row["Coverage %"]],
            mode="markers+text", name=row["Algorithm"], text=[row["Algorithm"]],
            textposition="top center",
            marker=dict(size=22, color=ALGO_COLORS[row["Algorithm"]],
                        line=dict(color="#0b1220", width=2)),
            hovertemplate=(f"<b>{row['Algorithm']}</b><br>Runtime: {row['Runtime (ms)']:.3f} ms"
                           f"<br>Coverage: {row['Coverage %']:.1f}% ({int(row['Coverage'])} paths)"
                           "<extra></extra>")))
    theme.style(fig, height=height, legend=False, title="Coverage vs runtime")
    fig.update_xaxes(title="Runtime (ms, log scale)", type="log")
    lo = min(d["Coverage %"].min(), 100) if len(d) else 0
    fig.update_yaxes(title="Coverage (%)", range=[max(0, lo - 12), 106])
    return fig


def overlap_heatmap(mat, height=360):
    fig = go.Figure(go.Heatmap(
        z=mat.values, x=list(mat.columns), y=list(mat.index),
        colorscale=[[0, "#0f172a"], [1, "#22d3ee"]], zmin=0,
        text=mat.values, texttemplate="%{text}", showscale=False,
        hovertemplate="%{y} ∩ %{x}: %{z} shared honeypot(s)<extra></extra>"))
    theme.style(fig, height=height, legend=False, title="Shared honeypots between algorithms")
    fig.update_yaxes(autorange="reversed")
    return fig
