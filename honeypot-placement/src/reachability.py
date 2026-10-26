"""BFS reachability pre-check. Called once, before optimization."""
from __future__ import annotations
import networkx as nx


def is_reachable(G: nx.DiGraph, s: str, t: str) -> bool:
    """True iff t is reachable from s in G (BFS)."""
    if s not in G or t not in G:
        return False
    return t in nx.bfs_tree(G, s)