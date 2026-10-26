"""Greedy marginal coverage — the primary baseline placement method.

At each step, add the eligible node that covers the most currently
uncovered paths. Stop early if no node adds coverage. Ties broken by
sorted_tiebreak (smallest node name).
"""
from __future__ import annotations
import time

from src.coverage import sorted_tiebreak
from src.models import PlacementResult


def greedy_placement(index: dict, n_paths: int, k: int) -> PlacementResult:
    t0 = time.perf_counter()

    if k <= 0 or not index:
        return PlacementResult(
            nodes=frozenset(),
            covered=0,
            total_paths=n_paths,
            runtime_s=time.perf_counter() - t0,
        )

    selected: list = []
    covered_ids: set = set()

    while len(selected) < k:
        best_gain = 0
        best_node = None
        for node, pids in index.items():
            if node in selected:
                continue
            gain = len(pids - covered_ids)
            if gain > best_gain:
                best_gain = gain
                best_node = node
            elif gain == best_gain and gain > 0:
                best_node = sorted_tiebreak([best_node, node])
        if best_gain == 0:
            break
        selected.append(best_node)
        covered_ids |= index[best_node]

    return PlacementResult(
        nodes=frozenset(selected),
        covered=len(covered_ids),
        total_paths=n_paths,
        runtime_s=time.perf_counter() - t0,
    )