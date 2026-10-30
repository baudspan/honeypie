"""Interactive Plotly rendering of the benchmark network.

Layouts reuse the project's own ones (src.plots) where they exist so the
dashboard matches the generated PNG figures.
"""
from __future__ import annotations
import re

import networkx as nx
import plotly.graph_objects as go

from src import plots as proj_plots
from ui import theme
from ui.theme import (ALGO_COLORS, EDGE_BASE, HONEYPOT, PATH_HILITE, ROLE_COLORS,
                      SYNTH_EDGE)

LAYOUTS = ["Layered (left → right)", "Spring (as in PNG figures)"]
_IP = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")


# ---------------------------------------------------------------- layouts
def _layered(G: nx.DiGraph, s) -> dict:
    """Layers by longest-path depth if acyclic, else BFS hop distance from s."""
    if nx.is_directed_acyclic_graph(G):
        layers = [list(g) for g in nx.topological_generations(G)]
    else:
        dist = nx.single_source_shortest_path_length(G, s)
        far = max(dist.values(), default=0) + 1
        by = {}
        for n in G.nodes:
            by.setdefault(dist.get(n, far), []).append(n)
        layers = [by[k] for k in sorted(by)]

    ypos = {}
    for li, layer in enumerate(layers):
        layer.sort(key=str)
        if li > 0:   # barycentre ordering against the previous layer reduces crossings
            layer.sort(key=lambda n: (
                sum(ypos[p] for p in G.predecessors(n) if p in ypos) /
                max(1, sum(1 for p in G.predecessors(n) if p in ypos)), str(n)))
        m = len(layer)
        if m == 1:      # zig-zag single-node layers so bypass edges don't hide behind nodes
            ypos[layer[0]] = (0.0, 0.9, -0.9)[li % 3] if len(layers) > 8 else 0.0
        else:
            for i, n in enumerate(layer):
                ypos[n] = (i - (m - 1) / 2.0) * 1.6
    pos = {}
    for li, layer in enumerate(layers):
        for n in layer:
            pos[n] = (float(li) * 1.8, ypos[n])
    return pos


def compute_layout(r, mode: str) -> dict:
    G = r["G"]
    if mode == LAYOUTS[1]:
        return proj_plots._hand_layout_b() if r["benchmark"] == "B" \
            else proj_plots._spring_layout_a(G)
    if r["benchmark"] == "B":
        return proj_plots._hand_layout_b()      # B's hand-tuned layout is already layered
    return _layered(G, r["s"])


def short_label(nodes) -> dict:
    """Compact labels for long IPv4 names ('100.64.36.183' → '36.183')."""
    nodes = list(nodes)
    if not all(_IP.match(str(n)) for n in nodes):
        return {n: str(n) for n in nodes}
    for take in (2, 3):
        lab = {n: ".".join(str(n).split(".")[-take:]) for n in nodes}
        if len(set(lab.values())) == len(lab):
            return lab
    return {n: str(n) for n in nodes}


# ---------------------------------------------------------------- helpers
def node_hover(r, n, extra: dict | None = None) -> str:
    G, idx, bc = r["G"], r["index"], r["bc_values"]
    role = "Source" if n == r["s"] else "Target" if n == r["t"] else \
        "Eligible" if n in set(r["eligible"]) else "Ineligible"
    lines = [f"<b>{n}</b>", f"Role: {role}",
             f"In/Out degree: {G.in_degree(n)}/{G.out_degree(n)}"]
    if n in idx:
        lines.append(f"Paths through node: {len(idx[n])}")
    if n in bc:
        lines.append(f"Betweenness: {bc[n]:.4f}")
    picks = [a for a, res in (("Greedy", r["greedy"]), ("Betweenness", r["betweenness"]),
                              ("SA", r["sa"]), ("Exhaustive", r["exhaustive"]))
             if res is not None and n in res.nodes]
    if picks:
        lines.append("Selected by: " + ", ".join(picks))
    for k, v in (extra or {}).items():
        lines.append(f"{k}: {v}")
    return "<br>".join(lines)


def _edge_style(d, mark_synthetic):
    if mark_synthetic and str(d.get("synthetic", "")).lower() == "true":
        return SYNTH_EDGE
    return EDGE_BASE


def _fmt_w(w):
    return f"{w:g}" if isinstance(w, (int, float)) else str(w)


# ---------------------------------------------------------------- figure
def network_figure(
    r, *, layout=LAYOUTS[0], honeypots=None, honeypot_algo=None,
    highlight_path=None, node_values=None, value_title="Value",
    show_labels=True, show_weights=True, mark_synthetic=False,
    height=560, dim_base=False,
):
    """Build the network figure.

    honeypots      : nodes to draw as gold stars (a placement)
    highlight_path : list of nodes — drawn as a bold highlighted route
    node_values    : {node: float} — colour eligible nodes by this value (heat map)
    mark_synthetic : colour edges whose `synthetic` attr is "true"
    """
    G, s, t = r["G"], r["s"], r["t"]
    eligible = set(r["eligible"])
    pos = compute_layout(r, layout)
    labels = short_label(G.nodes)
    honeypots = set(honeypots or [])
    hp_edges = set(zip(highlight_path[:-1], highlight_path[1:])) if highlight_path else set()
    fig = go.Figure()

    # --- arrows (annotations keep correct pixel-space arrowheads) ---
    anns = []
    for u, v, d in G.edges(data=True):
        hi = (u, v) in hp_edges
        col = PATH_HILITE if hi else _edge_style(d, mark_synthetic)
        anns.append(dict(
            x=pos[v][0], y=pos[v][1], ax=pos[u][0], ay=pos[u][1],
            xref="x", yref="y", axref="x", ayref="y", text="", showarrow=True,
            arrowhead=3, arrowsize=1.0, arrowwidth=3.2 if hi else 1.3,
            arrowcolor=col, standoff=13, startstandoff=13,
            opacity=1.0 if hi else (0.35 if (hp_edges or dim_base) else 0.85)))
    fig.update_layout(annotations=anns)

    # --- edge hover + weight text at the midpoints ---
    mx, my, hov, wtxt = [], [], [], []
    for u, v, d in G.edges(data=True):
        mx.append((pos[u][0] + pos[v][0]) / 2)
        my.append((pos[u][1] + pos[v][1]) / 2)
        h = f"<b>{u} → {v}</b><br>Weight (traversal cost): {_fmt_w(d.get('weight', 1))}"
        if mark_synthetic:
            syn = str(d.get("synthetic", "")).lower() == "true"
            h += "<br>" + ("<b>SYNTHETIC edge</b>" + (f" ({d['note']})" if d.get("note") else "")
                           if syn else "Real observed edge")
        hov.append(h)
        wtxt.append(_fmt_w(d.get("weight", 1)))
    fig.add_trace(go.Scatter(
        x=mx, y=my, mode="text" if show_weights else "markers",
        text=wtxt if show_weights else None, textfont=dict(size=9, color="#94a3b8"),
        marker=dict(size=10, opacity=0), hovertext=hov, hoverinfo="text",
        showlegend=False, name="edges"))

    # legend entries for edge styles
    if mark_synthetic:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", name="Real edge",
                                 line=dict(color=EDGE_BASE, width=2)))
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", name="Synthetic edge",
                                 line=dict(color=SYNTH_EDGE, width=2)))
    if highlight_path:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", name="Selected path",
                                 line=dict(color=PATH_HILITE, width=4)))

    # --- nodes ---
    def label_pos(n):
        return "top center" if pos[n][1] >= 0 else "bottom center"

    if node_values is not None:
        vals = [node_values.get(n) for n in G.nodes if n in node_values]
        vmax = max(vals) if vals else 1.0
        elig = [n for n in G.nodes if n in node_values]
        fig.add_trace(go.Scatter(
            x=[pos[n][0] for n in elig], y=[pos[n][1] for n in elig],
            mode="markers+text" if show_labels else "markers",
            text=[labels[n] for n in elig], textposition=[label_pos(n) for n in elig],
            textfont=dict(size=10, color="#e2e8f0"),
            marker=dict(size=26, color=[node_values[n] for n in elig],
                        colorscale="Viridis", cmin=0, cmax=vmax or 1.0,
                        line=dict(color="#0b1220", width=2),
                        colorbar=dict(title=dict(text=value_title, side="right"),
                                      thickness=12, len=0.7, x=1.0)),
            hovertext=[node_hover(r, n, {value_title: f"{node_values[n]:.4f}"}) for n in elig],
            hoverinfo="text", name="Eligible (heat)", showlegend=False))
        others = [n for n in G.nodes if n not in node_values]
        groups = [("Source", [n for n in others if n == s]),
                  ("Target", [n for n in others if n == t]),
                  ("Ineligible", [n for n in others if n not in (s, t)])]
    else:
        groups = [("Source", [s]), ("Target", [t]),
                  ("Eligible", [n for n in G.nodes if n in eligible]),
                  ("Ineligible", [n for n in G.nodes if n not in eligible and n not in (s, t)])]

    for role, ns in groups:
        if not ns:
            continue
        on_path = [n in (highlight_path or []) for n in ns]
        fig.add_trace(go.Scatter(
            x=[pos[n][0] for n in ns], y=[pos[n][1] for n in ns],
            mode="markers+text" if show_labels else "markers",
            text=[labels[n] for n in ns], textposition=[label_pos(n) for n in ns],
            textfont=dict(size=10, color="#e2e8f0"),
            marker=dict(size=30 if role in ("Source", "Target") else 24,
                        color=ROLE_COLORS[role],
                        line=dict(color=[PATH_HILITE if o else "#0b1220" for o in on_path],
                                  width=[3.5 if o else 2 for o in on_path])),
            hovertext=[node_hover(r, n) for n in ns], hoverinfo="text", name=role,
            customdata=[str(n) for n in ns]))

    # --- honeypot stars on top ---
    if honeypots:
        hp = [n for n in G.nodes if n in honeypots]
        ring = ALGO_COLORS.get(honeypot_algo, "#ffffff")
        fig.add_trace(go.Scatter(
            x=[pos[n][0] for n in hp], y=[pos[n][1] for n in hp],
            mode="markers+text" if show_labels else "markers",
            text=[labels[n] for n in hp], textposition="top center",
            textfont=dict(size=11, color="#fde68a"),
            marker=dict(symbol="star", size=32, color=HONEYPOT,
                        line=dict(color=ring, width=2.5)),
            hovertext=[node_hover(r, n) for n in hp], hoverinfo="text",
            name=f"Honeypot{' · ' + honeypot_algo if honeypot_algo else ''}"))

    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    padx = max(0.6, (max(xs) - min(xs)) * 0.05)
    pady = max(0.9, (max(ys) - min(ys)) * 0.14)
    fig.update_xaxes(visible=False, range=[min(xs) - padx, max(xs) + padx])
    fig.update_yaxes(visible=False, range=[min(ys) - pady, max(ys) + pady])
    theme.style(fig, height=height)
    fig.update_layout(margin=dict(l=0, r=0, t=30, b=0), hovermode="closest",
                      legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0))
    return fig
