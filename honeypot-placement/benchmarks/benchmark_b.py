"""Benchmark B: the 11-node greedy-failure graph.

All edge weights = 1.0 (equal simulated traversal cost).
Weights represent traversal cost, NOT exploit difficulty or compromise
probability. Dijkstra/Yen minimise total accumulated cost along a route.

    Node A lies on 4 of the 6 paths
    Node B lies on 3 of the 6 paths
    Node C lies on 3 of the 6 paths
    {A, B} and {A, C} cover 5 paths (greedy trap)
    {B, C}         covers 6 paths (optimum)

Eligible honeypot locations: Vc = {"A", "B", "C"} only.
Relay nodes q1, q2, r1..r4 and endpoints s, t are ineligible.
"""
from __future__ import annotations
import networkx as nx


def build() -> tuple[nx.DiGraph, str, str]:
    G = nx.DiGraph()
    G.add_nodes_from(["s", "t", "A", "B", "C",
                      "q1", "q2", "r1", "r2", "r3", "r4"])
    edges = [
        ("s", "A"), ("s", "q1"), ("s", "q2"),
        ("A", "r1"), ("A", "r2"), ("A", "r3"), ("A", "r4"),
        ("r1", "B"), ("r2", "B"),
        ("r3", "C"), ("r4", "C"),
        ("q1", "B"), ("q2", "C"),
        ("B", "t"), ("C", "t"),
    ]
    for u, v in edges:
        G.add_edge(u, v, weight=1)
    return G, "s", "t"


ELIGIBLE = frozenset({"A", "B", "C"})