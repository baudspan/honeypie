"""Graph construction, loading and input validation.

Only this file (plus candidate_paths, centrality, reachability,
shortest_path) touches NetworkX graph objects.
"""
from __future__ import annotations
import networkx as nx


def load_benchmark(name: str) -> tuple[nx.DiGraph, str, str]:
    """Load a named benchmark graph. Returns (G, s, t)."""
    name = name.upper()
    if name == "A":
        from benchmarks import benchmark_a
        G, s, t = benchmark_a.build()
    elif name == "B":
        from benchmarks import benchmark_b
        G, s, t = benchmark_b.build()
    elif name == "C":
        from benchmarks import benchmark_c
        G, s, t = benchmark_c.build()
    else:
        raise ValueError(f"Unknown benchmark: {name!r} (available: A, B, C)")
    validate_graph(G, s, t)
    return G, s, t


def validate_graph(G: nx.DiGraph, s: str, t: str) -> None:
    """Raise ValueError if the graph violates input assumptions."""
    if not isinstance(G, nx.DiGraph):
        raise ValueError("Graph must be a directed graph (nx.DiGraph).")
    if s not in G:
        raise ValueError(f"Source node {s!r} not in graph.")
    if t not in G:
        raise ValueError(f"Target node {t!r} not in graph.")
    for u, v, data in G.edges(data=True):
        w = data.get("weight", 1)
        if w < 0:
            raise ValueError(f"Negative weight on edge {u}->{v}: {w}")


def define_eligible(G: nx.DiGraph, s: str, t: str, excluded=None) -> set:
    """Eligible honeypot locations: V \\ {s, t}, minus an optional excluded set."""
    excluded = set(excluded or [])
    return set(G.nodes) - {s, t} - excluded