"""Betweenness centrality analysis + top-k baseline placement.

This is on the allowed NetworkX-touching list (rule 4). Betweenness values
are computed ONCE from the graph; the placement function then takes only
`index` for coverage evaluation — matching the contract for all other
placement methods.

The ranking is by betweenness descending; ties broken by sorted node name
(same rule as coverage.sorted_tiebreak, applied inline).
"""
from __future__ import annotations
import time

import networkx as nx

from src.coverage import coverage
from src.models import PlacementResult


def betweenness(G: nx.DiGraph, eligible: set) -> dict:
    """Weighted betweenness centrality, restricted to eligible nodes.

    Returns {node: float} for every node in `eligible`.
    Nodes not on any path return 0.0.
    """
    bc_all = nx.betweenness_centrality(G, weight="weight", normalized=True)
    return {n: float(bc_all.get(n, 0.0)) for n in eligible}


def betweenness_placement(bc: dict, index: dict, n_paths: int, k: int) -> PlacementResult:
    """Top-k eligible nodes by betweenness, evaluated with shared coverage."""
    t0 = time.perf_counter()

    k_eff = min(k, len(bc))
    if k_eff <= 0:
        return PlacementResult(
            nodes=frozenset(),
            covered=0,
            total_paths=n_paths,
            runtime_s=time.perf_counter() - t0,
        )

    # Descending bc; tie-break by node name (same rule as sorted_tiebreak)
    ranked = sorted(bc.keys(), key=lambda n: (-bc[n], str(n)))
    top = ranked[:k_eff]

    return PlacementResult(
        nodes=frozenset(top),
        covered=coverage(top, index),
        total_paths=n_paths,
        runtime_s=time.perf_counter() - t0,
    )


def overlap(a: frozenset, b: frozenset) -> int:
    """Size of set intersection — used for Experiment F."""
    return len(set(a) & set(b))