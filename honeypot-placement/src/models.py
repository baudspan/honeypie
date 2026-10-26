"""Shared return type for every placement method.

Frozen contract — do not alter:
    PlacementResult(nodes, covered, total_paths, runtime_s, iterations=0)
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class PlacementResult:
    nodes: frozenset      # which eligible nodes were selected
    covered: int          # number of distinct candidate paths covered
    total_paths: int      # |P| — total candidate paths for computing %
    runtime_s: float      # wall-clock seconds spent inside the method
    iterations: int = 0   # 0 for methods that do not iterate (greedy, baseline)