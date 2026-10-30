"""Greedy marginal coverage — the primary baseline placement method.

At each step, add the eligible node that covers the most currently
uncovered paths. Stop early if no node adds coverage. Ties broken by
sorted_tiebreak (smallest node name).
"""
from __future__ import annotations
import time

from src.coverage import sorted_tiebreak
from src.models import PlacementResult


def _greedy_core(index: dict, k: int, trace: list | None = None):
    """Selection loop shared by greedy_placement and the traced variant.

    If `trace` is a list, one dict per step is appended:
      {"step", "node", "gain", "cumulative", "candidate_gains"}
    where candidate_gains maps every not-yet-selected node to its marginal gain
    at that step. Returns (selected_nodes_in_order, covered_ids).
    """
    selected: list = []
    covered_ids: set = set()

    while len(selected) < k:
        best_gain = 0
        best_node = None
        cand_gains = {}
        for node, pids in index.items():
            if node in selected:
                continue
            gain = len(pids - covered_ids)
            cand_gains[node] = gain
            if gain > best_gain:
                best_gain = gain
                best_node = node
            elif gain == best_gain and gain > 0:
                best_node = sorted_tiebreak([best_node, node])
        if best_gain == 0:
            break
        selected.append(best_node)
        covered_ids |= index[best_node]
        if trace is not None:
            trace.append({
                "step": len(selected),
                "node": best_node,
                "gain": best_gain,
                "cumulative": len(covered_ids),
                "candidate_gains": cand_gains,
            })
    return selected, covered_ids


def _empty_result(n_paths, t0):
    return PlacementResult(
        nodes=frozenset(),
        covered=0,
        total_paths=n_paths,
        runtime_s=time.perf_counter() - t0,
    )


def greedy_placement(index: dict, n_paths: int, k: int) -> PlacementResult:
    t0 = time.perf_counter()
    if k <= 0 or not index:
        return _empty_result(n_paths, t0)
    selected, covered_ids = _greedy_core(index, k)
    return PlacementResult(
        nodes=frozenset(selected),
        covered=len(covered_ids),
        total_paths=n_paths,
        runtime_s=time.perf_counter() - t0,
    )


def greedy_placement_with_trace(index: dict, n_paths: int, k: int):
    """Same result as greedy_placement, plus the per-step selection trace.

    Returns (PlacementResult, list[dict]). Used by dashboards to show
    selection order and marginal coverage; greedy_placement is unchanged.
    """
    t0 = time.perf_counter()
    trace: list = []
    if k <= 0 or not index:
        return _empty_result(n_paths, t0), trace
    selected, covered_ids = _greedy_core(index, k, trace)
    return PlacementResult(
        nodes=frozenset(selected),
        covered=len(covered_ids),
        total_paths=n_paths,
        runtime_s=time.perf_counter() - t0,
    ), trace
