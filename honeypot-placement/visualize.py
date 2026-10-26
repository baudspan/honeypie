"""Generate visualizations for the honeypot placement pipeline.

Runs the full pipeline, then writes three figures per benchmark:
  benchmark_X_network.png     — topology
  benchmark_X_paths.png       — candidate paths (small multiples)
  benchmark_X_comparison.png  — 2x2 greedy/betweenness/SA/exhaustive

Output directory defaults to `results/` (created if missing).
"""
from __future__ import annotations
import argparse
import os

from benchmarks import benchmark_a, benchmark_b
from src.graph_builder import define_eligible
from src.candidate_paths import enumerate_paths
from src.coverage import build_index
from src.greedy import greedy_placement
from src.exhaustive import exhaustive_search
from src.annealing import simulated_annealing
from src.centrality import betweenness, betweenness_placement
import src.plots as plots
import config


def run_benchmark(name, k, m, seed, out_dir):
    name = name.upper()
    if name == "A":
        G, s, t = benchmark_a.build()
        eligible = define_eligible(G, s, t)
        layout = "spring"
        default_k = 3
    elif name == "B":
        G, s, t = benchmark_b.build()
        eligible = set(benchmark_b.ELIGIBLE)
        layout = "b"
        default_k = 2
    else:
        raise ValueError(f"Unknown benchmark: {name}")

    k = k if k is not None else default_k
    paths = enumerate_paths(G, s, t, m=m)
    index = build_index(paths, eligible)

    greedy = greedy_placement(index, n_paths=len(paths), k=k)
    bc_values = betweenness(G, eligible)
    btwn = betweenness_placement(bc_values, index, n_paths=len(paths), k=k)
    sa = simulated_annealing(
        index, n_paths=len(paths), k=k, init=greedy,
        T0=config.SA_T0, alpha=config.SA_ALPHA,
        L=config.SA_L, iters=config.SA_ITERS, seed=seed,
    )
    exhaustive = exhaustive_search(index, n_paths=len(paths), k=k)

    prefix = os.path.join(out_dir, f"benchmark_{name.lower()}")
    plots.plot_network(G, s, t, eligible, f"{prefix}_network.png", layout=layout)
    plots.plot_paths(G, s, t, eligible, paths, f"{prefix}_paths.png", layout=layout)
    plots.plot_comparison(
        G, s, t, eligible, paths,
        {"Greedy": greedy, "Betweenness": btwn,
         "SA": sa, "Exhaustive": exhaustive},
        f"{prefix}_comparison.png", layout=layout,
        benchmark_name=name,
    )

    print(f"[{name}] k={k}, m={m}")
    print(f"  greedy={greedy.covered}  betweenness={btwn.covered}  "
          f"SA={sa.covered}  exhaustive={exhaustive.covered}")
    print(f"  figures -> {prefix}_{{network,paths,comparison}}.png")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--benchmark", choices=["A", "B", "all"], default="all")
    p.add_argument("--k", type=int, default=None,
                   help="Honeypot budget (default: A=3, B=2).")
    p.add_argument("--m", type=int, default=20)
    p.add_argument("--seed", type=int, default=config.SA_SEED)
    p.add_argument("--out", default="results")
    args = p.parse_args()

    os.makedirs(args.out, exist_ok=True)

    if args.benchmark in ("A", "all"):
        run_benchmark("A", args.k, args.m, args.seed, args.out)
    if args.benchmark in ("B", "all"):
        run_benchmark("B", args.k, args.m, args.seed, args.out)


if __name__ == "__main__":
    main()