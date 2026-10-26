"""Exhaustive enumeration of all k-subsets of eligible nodes.

Only feasible on small instances. Because coverage is monotone in S
(adding a node never reduces coverage), the optimal placement of size ≤ k
is always achievable at size exactly min(k, |eligible|), so we only need
to enumerate that size.

Tie-break: among optimal placements, return the lexicographically smallest
(the first one found while iterating combinations in sorted-node order).
"""
from __future__ import annotations
import time
from itertools import combinations

from src.coverage import coverage
from src.models import PlacementResult


def exhaustive_search(index: dict, n_paths: int, k: int) -> PlacementResult:
    t0 = time.perf_counter()

    nodes = sorted(index.keys(), key=str)
    k_eff = min(k, len(nodes))

    if k_eff <= 0:
        return PlacementResult(
            nodes=frozenset(),
            covered=0,
            total_paths=n_paths,
            runtime_s=time.perf_counter() - t0,
        )

    best_nodes = None
    best_covered = -1
    iterations = 0

    for combo in combinations(nodes, k_eff):
        iterations += 1
        cov = coverage(combo, index)
        if cov > best_covered:
            best_covered = cov
            best_nodes = combo

    return PlacementResult(
        nodes=frozenset(best_nodes),
        covered=best_covered,
        total_paths=n_paths,
        runtime_s=time.perf_counter() - t0,
        iterations=iterations,
    )