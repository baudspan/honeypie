"""Generate visualizations for the honeypot placement pipeline.

Runs the full pipeline (src.experiments.run_experiment), then writes three
figures per benchmark:
  benchmark_X_network.png     — topology
  benchmark_X_paths.png       — candidate paths (small multiples)
  benchmark_X_comparison.png  — greedy/betweenness/SA/exhaustive placements

Output directory defaults to `results/` (created if missing).
`generate_figures()` is print-free so GUIs can call it; the CLI prints.
"""
from __future__ import annotations
import argparse
import os

from src.experiments import run_experiment
import src.plots as plots
import config

# name -> (plot layout, default k, default m)
BENCHMARKS = {
    "A": ("spring", 3, 20),
    "B": ("b", 2, 20),
    "C": ("spring", 2, 100),
}
MAX_PATH_PANELS = 24      # small-multiples figure gets unreadable beyond this


def generate_figures(name, k=None, m=None, seed=config.SA_SEED,
                     out_dir="results", sa_params=None, result=None):
    """Write the three figures for one benchmark. Returns a dict with the
    output file paths and the experiment result. Prints nothing.

    result: optionally reuse an already-computed run_experiment() dict.
    """
    name = name.upper()
    if name not in BENCHMARKS:
        raise ValueError(f"Unknown benchmark: {name}")
    layout, default_k, default_m = BENCHMARKS[name]
    k = default_k if k is None else k
    m = default_m if m is None else m

    r = result if result is not None else run_experiment(
        name, k, m, seed, sa_params=sa_params)
    G, s, t = r["G"], r["s"], r["t"]
    eligible = set(r["eligible"])
    paths = r["paths"]

    results = {"Greedy": r["greedy"], "Betweenness": r["betweenness"],
               "SA": r["sa"]}
    if r["exhaustive"] is not None:
        results["Exhaustive"] = r["exhaustive"]

    os.makedirs(out_dir, exist_ok=True)
    prefix = os.path.join(out_dir, f"benchmark_{name.lower()}")
    files = {
        "network": f"{prefix}_network.png",
        "paths": f"{prefix}_paths.png",
        "comparison": f"{prefix}_comparison.png",
    }
    plots.plot_network(G, s, t, eligible, files["network"], layout=layout)
    plots.plot_paths(G, s, t, eligible, paths[:MAX_PATH_PANELS], files["paths"],
                     layout=layout, n_total=len(paths))
    plots.plot_comparison(G, s, t, eligible, paths, results,
                          files["comparison"], layout=layout,
                          benchmark_name=name)
    return {"files": files, "result": r, "k": k, "m": m}


def run_benchmark(name, k, m, seed, out_dir):
    out = generate_figures(name, k, m, seed, out_dir)
    r = out["result"]
    exh = r["exhaustive"].covered if r["exhaustive"] is not None else "skipped"
    print(f"[{r['benchmark']}] k={out['k']}, m={out['m']}")
    print(f"  greedy={r['greedy'].covered}  betweenness={r['betweenness'].covered}  "
          f"SA={r['sa'].covered}  exhaustive={exh}")
    prefix = os.path.join(out_dir, f"benchmark_{r['benchmark'].lower()}")
    print(f"  figures -> {prefix}_{{network,paths,comparison}}.png")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--benchmark", choices=["A", "B", "C", "all"], default="all")
    p.add_argument("--k", type=int, default=None,
                   help="Honeypot budget (default: A=3, B=2, C=2).")
    p.add_argument("--m", type=int, default=None,
                   help="Max candidate paths (default: A=20, B=20, C=100).")
    p.add_argument("--seed", type=int, default=config.SA_SEED)
    p.add_argument("--out", default="results")
    args = p.parse_args()

    names = ["A", "B", "C"] if args.benchmark == "all" else [args.benchmark]
    for n in names:
        run_benchmark(n, args.k, args.m, args.seed, args.out)


if __name__ == "__main__":
    main()
