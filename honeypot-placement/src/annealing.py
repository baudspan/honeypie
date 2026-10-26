"""Simulated Annealing for honeypot placement.

Design rules (locked by the project contract):
- Only returns a PlacementResult; never prints.
- Uses a LOCAL random.Random(seed) — no global random.seed().
- Objective computed ONLY via coverage(S, index) from src.coverage.
- Reported result is best-so-far, initialised at init (usually greedy):
  therefore reported SA coverage >= init coverage ALWAYS.
- Strict improvement is empirical, not guaranteed.

Public API (frozen):
    simulated_annealing(index, n_paths, k, init, T0, alpha, L, iters, seed)
        -> PlacementResult
    simulated_annealing_with_stats(...)  # test-support; adds acceptance stats
"""
from __future__ import annotations
import math
import random
import time

from src.coverage import coverage
from src.models import PlacementResult


def _validate_sa_params(T0, alpha, L, iters):
    if T0 <= 0:
        raise ValueError(f"T0 must be > 0 (got {T0}).")
    if not (0 < alpha < 1):
        raise ValueError(f"alpha must satisfy 0 < alpha < 1 (got {alpha}).")
    if not isinstance(L, int) or L <= 0:
        raise ValueError(f"L must be a positive integer (got {L}).")
    if not isinstance(iters, int) or iters < 0:
        raise ValueError(f"iters must be a non-negative integer (got {iters}).")


def _sa_core(index, n_paths, k, init, T0, alpha, L, iters, seed):
    """Returns (best_nodes, best_cov, iterations_run, attempts, accepts, elapsed_s)."""
    _validate_sa_params(T0, alpha, L, iters)
    t0 = time.perf_counter()

    # --- coverable set: union of all path ids any eligible node can contribute to
    coverable: set = set()
    for pids in index.values():
        coverable |= pids

    # --- early exits ---
    if k <= 0 or not index or k >= len(index) or init.covered >= len(coverable):
        return (init.nodes, init.covered, 0, 0, 0, time.perf_counter() - t0)

    k_eff = min(k, len(index))
    eligible_sorted = sorted(index.keys(), key=str)

    current = set(init.nodes)
    if len(current) < k_eff:
        for node in eligible_sorted:
            if node not in current:
                current.add(node)
                if len(current) >= k_eff:
                    break

    current_cov = coverage(current, index)
    best_cov = init.covered
    best_nodes = init.nodes
    if current_cov > best_cov:
        best_cov = current_cov
        best_nodes = frozenset(current)

    rng = random.Random(seed)
    T = T0
    early_window = min(100, iters)
    early_attempts = 0
    early_accepts = 0
    iterations_run = 0

    for it in range(iters):
        selected = sorted(current, key=str)
        unselected = [n for n in eligible_sorted if n not in current]
        if not unselected:
            break
        out_node = rng.choice(selected)
        in_node = rng.choice(unselected)

        candidate = (current - {out_node}) | {in_node}
        cand_cov = coverage(candidate, index)
        delta = cand_cov - current_cov

        if delta >= 0:
            accept = True
        else:
            accept = rng.random() < math.exp(delta / T)

        if it < early_window:
            early_attempts += 1
            if accept:
                early_accepts += 1

        if accept:
            current = candidate
            current_cov = cand_cov
            if current_cov > best_cov:
                best_cov = current_cov
                best_nodes = frozenset(current)

        if (it + 1) % L == 0:
            T *= alpha

        iterations_run += 1

    return (best_nodes, best_cov, iterations_run,
            early_attempts, early_accepts, time.perf_counter() - t0)


def simulated_annealing(index, n_paths, k, init, T0, alpha, L, iters, seed):
    """Frozen-contract SA. Reports best-so-far, never worse than init."""
    nodes, cov, it_run, _, _, elapsed = _sa_core(
        index, n_paths, k, init, T0, alpha, L, iters, seed
    )
    return PlacementResult(
        nodes=nodes,
        covered=cov,
        total_paths=n_paths,
        runtime_s=elapsed,
        iterations=it_run,
    )


def simulated_annealing_with_stats(index, n_paths, k, init, T0, alpha, L, iters, seed):
    """Same run as simulated_annealing; also returns acceptance-rate stats.

    Used only by tests — the frozen `simulated_annealing` signature is unchanged.
    """
    nodes, cov, it_run, attempts, accepts, elapsed = _sa_core(
        index, n_paths, k, init, T0, alpha, L, iters, seed
    )
    result = PlacementResult(
        nodes=nodes,
        covered=cov,
        total_paths=n_paths,
        runtime_s=elapsed,
        iterations=it_run,
    )
    rate = (accepts / attempts) if attempts else 0.0
    return result, {"early_acceptance_rate": rate,
                    "attempts": attempts,
                    "accepts": accepts}