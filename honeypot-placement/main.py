"""CLI entry point for the honeypot placement optimizer.

Wires: benchmark loader -> experiment runner -> console report.
No computation lives here; only argparse and dispatch.
"""
from __future__ import annotations
import argparse
import sys

import config
from src.experiments import run_experiment
from src import report


def _parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="main.py",
        description="Attack Path Analysis & Honeypot Placement Optimization",
    )
    p.add_argument("--benchmark", "-b", choices=["A", "B", "C", "a", "b", "c"], default="B",
                help="Benchmark (A=corporate, B=greedy-trap, C=real Precinct6 hybrid).")
    p.add_argument("--k", type=int, default=config.DEFAULT_K,
                   help=f"Honeypot budget (default {config.DEFAULT_K}).")
    p.add_argument("--m", type=int, default=config.DEFAULT_M,
                   help=f"Max candidate paths (default {config.DEFAULT_M}).")
    p.add_argument("--seed", type=int, default=config.SA_SEED,
                   help=f"SA random seed (default {config.SA_SEED}).")
    return p.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)
    try:
        result = run_experiment(args.benchmark, args.k, args.m, args.seed)
    except (ValueError, RuntimeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    report.print_experiment(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())