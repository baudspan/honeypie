"""Budget sensitivity: run all methods for k = 0..K on one benchmark.

Fixed graph, fixed m. Reports coverage per (method, k) and runtime.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.experiments import run_experiment


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--benchmark", "-b", required=True)
    p.add_argument("--m", type=int, required=True)
    p.add_argument("--kmax", type=int, default=5)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    if args.benchmark.upper() not in ("A", "B", "C"):
        raise SystemExit(f"--benchmark must be A, B, or C (got {args.benchmark})")
    if args.kmax < 0:
        raise SystemExit(f"--kmax must be >= 0 (got {args.kmax})")
    if args.m <= 0:
        raise SystemExit(f"--m must be > 0 (got {args.m})")

    print(f"Budget sweep on Benchmark {args.benchmark} "
          f"(m={args.m}, seed={args.seed})")
    print()
    print(f"  {'k':>2}  {'greedy':>6}  {'btwn':>4}  {'SA':>4}  {'optimum':>7}  "
          f"{'greedy ms':>9}  {'SA ms':>7}")
    print("  " + "-" * 60)

    for k in range(args.kmax + 1):
        r = run_experiment(args.benchmark, k=k, m=args.m, seed=args.seed)
        g = r["greedy"].covered
        btwn = r["betweenness"].covered
        sa = r["sa"].covered
        ex = r["exhaustive"].covered if r["exhaustive"] else None
        print(f"  {k:>2}  {g:>6}  {btwn:>4}  {sa:>4}  "
              f"{(ex if ex is not None else 'n/a'):>7}  "
              f"{r['greedy'].runtime_s * 1000:>9.3f}  "
              f"{r['sa'].runtime_s * 1000:>7.3f}")


if __name__ == "__main__":
    main()