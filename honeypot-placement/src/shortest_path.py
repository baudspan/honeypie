"""Dijkstra minimum-cost path.

Cross-check against Yen's first path: compare total COST, not path identity.
Equal-cost ties can legitimately return different paths.
"""
from __future__ import annotations
import networkx as nx


def min_cost_path(G: nx.DiGraph, s: str, t: str) -> tuple[list, float]:
    """Return (path, cost) for the minimum-cost s->t route."""
    try:
        path = nx.dijkstra_path(G, s, t, weight="weight")
        cost = nx.dijkstra_path_length(G, s, t, weight="weight")
    except nx.NetworkXNoPath:
        raise ValueError(f"No path from {s!r} to {t!r}.")
    return list(path), float(cost)