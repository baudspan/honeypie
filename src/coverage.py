"""Single source of truth for the coverage objective.

Rules (locked):
- Only `coverage()` computes the objective. Greedy, SA, betweenness and
  exhaustive all call it.
- `build_index()` is the only place the node → path-id map is built.
- `sorted_tiebreak()` is the ONLY tie-breaking rule in the codebase.

Path ids are 0-based indices into the `paths` list, so coverage(`S`) returns
an integer ≤ len(paths).
"""
from __future__ import annotations


def build_index(paths: list[list], eligible: set) -> dict:
    """Return {node: frozenset(path_ids)} for every eligible node.

    Eligible nodes that appear on no path map to frozenset().
    Nodes not in `eligible` are excluded entirely.
    """
    raw: dict = {node: set() for node in eligible}
    for pid, path in enumerate(paths):
        for node in path:
            if node in eligible:
                raw[node].add(pid)
    return {node: frozenset(pids) for node, pids in raw.items()}


def covered_ids(S, index: dict) -> frozenset:
    """Ids of the distinct candidate paths covered by placement S.

    Exposed so GUIs can show *which* paths are covered; coverage() is
    exactly len(covered_ids(...)), so there is still one objective.
    """
    covered: set = set()
    for node in S:
        covered |= index.get(node, frozenset())
    return frozenset(covered)


def coverage(S, index: dict) -> int:
    """Number of distinct candidate paths covered by placement S."""
    return len(covered_ids(S, index))


def sorted_tiebreak(candidates) -> str:
    """Deterministic tie-break: smallest node name (lexicographic)."""
    return min(candidates, key=str)