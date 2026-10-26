"""Visualization module — produces matplotlib figures for the pipeline.

Three figure types:
  plot_network    — base graph with node roles + weights
  plot_paths      — one panel per candidate attack path (small multiples)
  plot_comparison — 2x2 grid: each method's honeypot placement

All figures save to disk. This module does NOT print.
"""
from __future__ import annotations
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


NODE_COLORS = {
    "source":     "#2ecc71",
    "target":     "#e74c3c",
    "eligible":   "#3498db",
    "ineligible": "#95a5a6",
}
HONEYPOT_COLOR = "#f1c40f"
COVERED_EDGE   = "#27ae60"
UNCOVERED_EDGE = "#d5d8dc"


# ---------- layout ----------

def _hand_layout_b() -> dict:
    """Hand-tuned layout for the 11-node Benchmark B (greedy-trap graph)."""
    return {
        "s":  (-0.2, 0.0),
        "A":  (1.0, 1.6),
        "q1": (1.0, 0.0),
        "q2": (1.0, -1.6),
        "r1": (2.0, 2.4),
        "r2": (2.0, 1.6),
        "r3": (2.0, -1.6),
        "r4": (2.0, -2.4),
        "B":  (3.0, 0.8),
        "C":  (3.0, -0.8),
        "t":  (4.2, 0.0),
    }


def _spring_layout_a(G, seed=42):
    return nx.spring_layout(G, seed=seed, k=1.2, iterations=120)


# ---------- helpers ----------

def _node_roles(G, s, t, eligible):
    return {
        n: ("source" if n == s else
            "target" if n == t else
            "eligible" if n in eligible else
            "ineligible")
        for n in G.nodes
    }


def _path_edges(path):
    return set(zip(path[:-1], path[1:]))


def _covered_edges(paths, honeypots):
    edges = set()
    for p in paths:
        if set(p) & honeypots:
            edges |= _path_edges(p)
    return edges


def _uncovered_edges(paths, honeypots):
    edges = set()
    for p in paths:
        if not (set(p) & honeypots):
            edges |= _path_edges(p)
    return edges


# ---------- primitives ----------

def _draw_edges(ax, G, pos, edgelist=None, color="#7f8c8d", width=1.4, alpha=1.0):
    elist = list(G.edges()) if edgelist is None else list(edgelist)
    if not elist:
        return
    nx.draw_networkx_edges(
        G, pos, edgelist=elist, ax=ax,
        edge_color=color, width=width, alpha=alpha,
        arrows=True, arrowsize=12, min_target_margin=18,
    )


def _draw_nodes(ax, G, pos, s, t, eligible, honeypots=None):
    roles = _node_roles(G, s, t, eligible)
    for role, color in NODE_COLORS.items():
        nodes = [n for n, r in roles.items() if r == role]
        if not nodes:
            continue
        size = 900 if role in ("source", "target") else 700
        nx.draw_networkx_nodes(
            G, pos, nodelist=nodes, ax=ax,
            node_color=color, node_size=size,
            edgecolors="black", linewidths=1.5,
        )
    if honeypots:
        nx.draw_networkx_nodes(
            G, pos, nodelist=list(honeypots), ax=ax,
            node_color=HONEYPOT_COLOR, node_size=1150,
            edgecolors="black", linewidths=2.5, node_shape="*",
        )
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=10,
                            font_color="white", font_weight="bold")


# ---------- public figure builders ----------

def plot_network(G, s, t, eligible, out_path, layout="spring"):
    """Figure 1 — base network topology with role coloring."""
    pos = _hand_layout_b() if layout == "b" else _spring_layout_a(G)
    fig, ax = plt.subplots(figsize=(11, 7))
    _draw_edges(ax, G, pos)
    nx.draw_networkx_edge_labels(
        G, pos, edge_labels=nx.get_edge_attributes(G, "weight"),
        ax=ax, font_size=7, font_color="#555555",
    )
    _draw_nodes(ax, G, pos, s, t, eligible)

    legend = [
        Line2D([0], [0], marker="o", color="w", markersize=13,
               markerfacecolor=NODE_COLORS["source"], label="Source (s)"),
        Line2D([0], [0], marker="o", color="w", markersize=13,
               markerfacecolor=NODE_COLORS["target"], label="Target (t)"),
        Line2D([0], [0], marker="o", color="w", markersize=13,
               markerfacecolor=NODE_COLORS["eligible"], label="Eligible (Vc)"),
        Line2D([0], [0], marker="o", color="w", markersize=13,
               markerfacecolor=NODE_COLORS["ineligible"], label="Ineligible"),
    ]
    ax.legend(handles=legend, loc="upper left", framealpha=0.9, fontsize=9)
    ax.set_title(f"Network Topology — {len(G.nodes)} nodes, {len(G.edges)} edges",
                 fontsize=13, fontweight="bold")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_paths(G, s, t, eligible, paths, out_path, layout="b"):
    """Figure 2 — small multiples, one panel per candidate path."""
    pos = _hand_layout_b() if layout == "b" else _spring_layout_a(G)
    n = len(paths)
    cols = 3 if n >= 3 else n
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 4 * rows))
    axes = [axes] if rows * cols == 1 else list(axes.flatten())

    for i, p in enumerate(paths):
        ax = axes[i]
        _draw_edges(ax, G, pos, color="#dddddd", width=1.0, alpha=0.5)
        nx.draw_networkx_edges(
            G, pos, edgelist=list(zip(p[:-1], p[1:])), ax=ax,
            edge_color="#e67e22", width=3.0,
            arrows=True, arrowsize=16, min_target_margin=18,
        )
        _draw_nodes(ax, G, pos, s, t, eligible)
        ax.set_title(f"p{i+1}:  {' → '.join(p)}", fontsize=10)
        ax.axis("off")

    for j in range(n, len(axes)):
        axes[j].axis("off")

    fig.suptitle(f"Candidate Attack Paths (Yen's K-shortest, K={n})",
                 fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_comparison(G, s, t, eligible, paths, results, out_path,layout="b", benchmark_name="?"):
    """Figure 3 — 2x2 grid: each method's placement + covered-path highlighting.

    results: dict {name: PlacementResult}
      covered edges (green)   = edges of paths hit by >=1 honeypot
      uncovered edges (light) = edges of paths hit by 0 honeypots
      honeypot nodes (star)   = the method's selected placement
    """
    pos = _hand_layout_b() if layout == "b" else _spring_layout_a(G)
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    axes = axes.flatten()

    for ax, (name, r) in zip(axes, results.items()):
        cov = _covered_edges(paths, r.nodes)
        uncov = _uncovered_edges(paths, r.nodes)
        _draw_edges(ax, G, pos, edgelist=list(uncov),
                    color=UNCOVERED_EDGE, width=1.0, alpha=0.5)
        _draw_edges(ax, G, pos, edgelist=list(cov),
                    color=COVERED_EDGE, width=2.6)
        _draw_nodes(ax, G, pos, s, t, eligible, honeypots=r.nodes)
        title = f"{name}:  {r.covered}/{r.total_paths} paths covered"
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.axis("off")

    legend = [
        Line2D([0], [0], color=COVERED_EDGE, lw=3,
               label="Covered path"),
        Line2D([0], [0], color=UNCOVERED_EDGE, lw=3,
               label="Uncovered path"),
        Line2D([0], [0], marker="*", color="w", markersize=18,
               markerfacecolor=HONEYPOT_COLOR,
               markeredgecolor="black", label="Honeypot"),
    ]
    fig.legend(handles=legend, loc="lower center",
               ncol=3, framealpha=0.95, fontsize=11,
               bbox_to_anchor=(0.5, -0.02))
    fig.suptitle(f"Honeypot Placement Comparison  (Benchmark {benchmark_name})",
                 fontsize=15, fontweight="bold")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)