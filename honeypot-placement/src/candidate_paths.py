"""Yen's K-shortest loopless paths via nx.shortest_simple_paths.

Returns up to m candidate attack paths, sorted by cost.
Also reports uncoverable paths and coverage upper bound.
"""
from __future__ import annotations
import networkx as nx


def enumerate_paths(G: nx.DiGraph, s: str, t: str, m: int) -> list[list]:
    """Return up to m shortest loopless s->t paths (cheapest first)."""
    if m <= 0:
        raise ValueError(f"m must be > 0 (got {m}).")
    if s not in G or t not in G:
        raise ValueError(f"s or t not in graph: s={s!r}, t={t!r}")

    paths: list[list] = []
    try:
        for p in nx.shortest_simple_paths(G, s, t, weight="weight"):
            paths.append(list(p))
            if len(paths) >= m:
                break
    except nx.NetworkXNoPath:
        raise ValueError(f"No path from {s!r} to {t!r}.")

    if not paths:
        raise ValueError(f"No paths returned from {s!r} to {t!r}.")
    return paths


def count_uncoverable(paths: list[list], eligible: set) -> int:
    """Paths with no eligible node (can never be covered)."""
    return sum(1 for p in paths if not (set(p) & eligible))


def coverage_upper_bound(paths: list[list], eligible: set) -> int:
    """Max achievable coverage = total paths minus uncoverable ones."""
    return len(paths) - count_uncoverable(paths, eligible)