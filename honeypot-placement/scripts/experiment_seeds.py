"""Multi-seed stability experiment: SA across N random seeds on one benchmark.

Fixed graph, fixed k, fixed m — only the SA seed varies. Reports mean,
best, worst, std, and how often SA reaches the exhaustive optimum.
"""
from __future__ import annotations
import argparse
import statistics
import sys
from pathlib import Path

# Make `import src.*` work when invoked as `python scripts/foo.py`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.experiments import run_experiment


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--benchmark", "-b", required=True)
    p.add_argument("--k", type=int, required=True)
    p.add_argument("--m", type=int, required=True)
    p.add_argument("--seeds", type=int, default=30)
    args = p.parse_args()

    if args.benchmark.upper() not in ("A", "B", "C"):
        raise SystemExit(f"--benchmark must be A, B, or C (got {args.benchmark})")
    if args.seeds < 1:
        raise SystemExit(f"--seeds must be >= 1 (got {args.seeds})")
    if args.k < 0:
        raise SystemExit(f"--k must be >= 0 (got {args.k})")
    if args.m <= 0:
        raise SystemExit(f"--m must be > 0 (got {args.m})")

    sa_coverages = []
    sa_runtimes = []
    greedy_cov = None
    opt_cov = None

    print(f"Running {args.seeds} SA seeds on Benchmark {args.benchmark} "
          f"(k={args.k}, m={args.m})...")
    print()
    print(f"  {'seed':>4}  {'greedy':>6}  {'SA':>4}  {'optimum':>7}  "
          f"{'SA runtime (ms)':>15}")
    print("  " + "-" * 46)

    for seed in range(args.seeds):
        r = run_experiment(args.benchmark, k=args.k, m=args.m, seed=seed)
        g = r["greedy"].covered
        sa = r["sa"].covered
        ex = r["exhaustive"].covered if r["exhaustive"] else None
        greedy_cov = g
        if ex is not None:
            opt_cov = ex
        sa_coverages.append(sa)
        sa_runtimes.append(r["sa"].runtime_s * 1000)
        print(f"  {seed:>4}  {g:>6}  {sa:>4}  "
              f"{(ex if ex is not None else 'n/a'):>7}  "
              f"{r['sa'].runtime_s * 1000:>15.3f}")

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Greedy coverage        : {greedy_cov}")
    print(f"  Exact optimum          : {opt_cov if opt_cov is not None else 'n/a'}")
    print(f"  SA best                : {max(sa_coverages)}")
    print(f"  SA worst               : {min(sa_coverages)}")
    print(f"  SA mean                : {statistics.mean(sa_coverages):.3f}")
    print(f"  SA std dev             : {statistics.pstdev(sa_coverages):.4f}")
    print(f"  SA mean runtime (ms)   : {statistics.mean(sa_runtimes):.3f}")

    if opt_cov is not None:
        hits = sum(1 for c in sa_coverages if c == opt_cov)
        print(f"  SA reached optimum     : {hits}/{args.seeds} "
              f"({100 * hits / args.seeds:.1f}%)")

    beats = sum(1 for c in sa_coverages if c > greedy_cov)
    ties = sum(1 for c in sa_coverages if c == greedy_cov)
    print(f"  SA strictly beat greedy: {beats}/{args.seeds}")
    print(f"  SA tied greedy         : {ties}/{args.seeds}")


if __name__ == "__main__":
    main()