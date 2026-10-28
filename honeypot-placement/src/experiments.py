"""Experiment runner for Benchmarks A and B.

Runs the full pipeline and returns a structured dict.
PRINTS NOTHING. Only report.py is allowed to print.

Pipeline:
  1. Load benchmark, validate
  2. BFS reachability
  3. Dijkstra min-cost route
  4. Yen's K-shortest paths (up to m)
  5. Build coverage index over eligible set Vc
  6. Greedy placement
  7. SA placement (init=greedy, best-so-far)
  8. Exhaustive placement (guarded by feasibility check)
  9. Return everything as a dict
"""
from __future__ import annotations
from math import comb
from src.centrality import betweenness, betweenness_placement

from benchmarks import benchmark_b
from src.graph_builder import load_benchmark, define_eligible
from src.reachability import is_reachable
from src.shortest_path import min_cost_path
from src.candidate_paths import (
    enumerate_paths, count_uncoverable, coverage_upper_bound,
)
from src.coverage import build_index, coverage
from src.greedy import greedy_placement
from src.exhaustive import exhaustive_search
from src.annealing import simulated_annealing
import config


# Exhaustive becomes too slow above this many combinations.
EXHAUSTIVE_COMBO_CAP = 100_000



def _n_combinations(n: int, k: int) -> int:
    """Number of k-subsets of an n-set. C(n, 0) == 1 (the empty placement)."""
    if k < 0:
        raise ValueError(f"k must be >= 0 (got {k}).")
    if n <= 0:
        return 1 if k == 0 else 0
    return comb(n, min(k, n))


def run_experiment(benchmark_name, k, m, seed=config.SA_SEED):
    """Run the full pipeline on one benchmark and return a structured dict.

    Raises ValueError if the target is not reachable.
    """
    if k < 0:
        raise ValueError(f"k must be >= 0 (got {k}).")
    if m <= 0:
        raise ValueError(f"m must be > 0 (got {m}).")
    name = benchmark_name.upper()
    G, s, t = load_benchmark(name)

    if not is_reachable(G, s, t):
        raise ValueError(f"Target {t!r} not reachable from {s!r} in benchmark {name}")

    min_path, min_cost = min_cost_path(G, s, t)
    paths = enumerate_paths(G, s, t, m=m)

    # Cross-check: Dijkstra cost must equal Yen's first-path cost
    yen_first = paths[0]
    yen_cost = sum(
        G[yen_first[i]][yen_first[i + 1]].get("weight", 1)
        for i in range(len(yen_first) - 1)
    )
    if abs(min_cost - yen_cost) > 1e-6:
        raise RuntimeError(
            f"Dijkstra cost {min_cost} != Yen first-path cost {yen_cost}. "
            f"Path identity may differ (equal-cost ties) but cost must agree."
        )

    # Benchmark B has a curated eligible set; A uses default V \ {s, t}
    if name == "B":
        eligible = set(benchmark_b.ELIGIBLE)
    elif name == "C":
        from benchmarks import benchmark_c
        eligible = benchmark_c.eligible(G, s, t)
    else:
        eligible = define_eligible(G, s, t)

    n_paths = len(paths)
    n_uncoverable = count_uncoverable(paths, eligible)
    upper_bound = coverage_upper_bound(paths, eligible)

    index = build_index(paths, eligible)
    bc = betweenness(G, eligible)
    greedy = greedy_placement(index, n_paths=n_paths, k=k)
    sa = simulated_annealing(
        index, n_paths=n_paths, k=k, init=greedy,
        T0=config.SA_T0, alpha=config.SA_ALPHA,
        L=config.SA_L, iters=config.SA_ITERS, seed=seed,
    )
    betweenness_res = betweenness_placement(bc, index, n_paths=n_paths, k=k)
    n_combos = _n_combinations(len(eligible), k)
    exhaustive = None
    if 0 < n_combos <= EXHAUSTIVE_COMBO_CAP:      # C(n,0)=1 still runs
        exhaustive = exhaustive_search(index, n_paths=n_paths, k=k)
    result = {
        "benchmark": name,
        "s": s,
        "t": t,
        "graph_nodes": len(G.nodes),
        "graph_edges": len(G.edges),
        "reachable": True,
        "min_cost_path": min_path,
        "min_cost": min_cost,
        "n_paths": n_paths,
        "n_uncoverable": n_uncoverable,
        "coverage_upper_bound": upper_bound,
        "eligible_size": len(eligible),
        "eligible": sorted(eligible, key=str),
        "k": k,
        "m": m,
        "betweenness": betweenness_res,
        "bc_values": bc,
        "greedy": greedy,
        "sa": sa,
        "exhaustive": exhaustive,
        "n_combinations": n_combos,
        "sa_params": {
            "T0": config.SA_T0,
            "alpha": config.SA_ALPHA,
            "L": config.SA_L,
            "iters": config.SA_ITERS,
            "seed": seed,
        },
    }

    if name == "B":
        result["incidence"] = {
            "A":   coverage({"A"}, index) if "A" in eligible else None,
            "B":   coverage({"B"}, index) if "B" in eligible else None,
            "C":   coverage({"C"}, index) if "C" in eligible else None,
            "B,C": coverage({"B", "C"}, index) if {"B", "C"} <= eligible else None,
        }

    return result