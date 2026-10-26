"""End-to-end test of Benchmark B.

Asserts BOTH the incidence pattern AND the three-method result:
    greedy k=2 -> 5
    exhaustive k=2 -> 6, nodes = {B, C}
    SA k=2 (init=greedy) -> 6, nodes = {B, C}

Incidence is asserted via coverage counts (order-independent), because
Yen's path order for equal-cost paths depends on NetworkX internals.
"""
import pytest

from benchmarks import benchmark_b
from src.graph_builder import validate_graph
from src.reachability import is_reachable
from src.candidate_paths import (
    enumerate_paths, count_uncoverable, coverage_upper_bound,
)
from src.coverage import build_index, coverage
from src.greedy import greedy_placement
from src.exhaustive import exhaustive_search
from src.annealing import simulated_annealing
import config


@pytest.fixture(scope="module")
def b_setup():
    G, s, t = benchmark_b.build()
    validate_graph(G, s, t)
    assert is_reachable(G, s, t)

    paths = enumerate_paths(G, s, t, m=20)
    eligible = set(benchmark_b.ELIGIBLE)
    index = build_index(paths, eligible)
    return {"G": G, "s": s, "t": t, "paths": paths,
            "eligible": eligible, "index": index}


# ---------- graph shape ----------

def test_benchmark_b_graph_shape(b_setup):
    G = b_setup["G"]
    assert len(G.nodes) == 11
    assert len(G.edges) == 15


def test_benchmark_b_has_exactly_six_paths(b_setup):
    assert len(b_setup["paths"]) == 6


def test_benchmark_b_eligible_is_abc(b_setup):
    assert b_setup["eligible"] == {"A", "B", "C"}


# ---------- incidence (order-independent) ----------

def test_benchmark_b_incidence_singletons(b_setup):
    idx = b_setup["index"]
    assert coverage({"A"}, idx) == 4
    assert coverage({"B"}, idx) == 3
    assert coverage({"C"}, idx) == 3


def test_benchmark_b_incidence_pairs(b_setup):
    idx = b_setup["index"]
    assert coverage({"A", "B"}, idx) == 5
    assert coverage({"A", "C"}, idx) == 5
    assert coverage({"B", "C"}, idx) == 6


def test_benchmark_b_incidence_all_three(b_setup):
    idx = b_setup["index"]
    assert coverage({"A", "B", "C"}, idx) == 6


def test_benchmark_b_no_uncoverable_paths(b_setup):
    paths = b_setup["paths"]
    eligible = b_setup["eligible"]
    assert count_uncoverable(paths, eligible) == 0
    assert coverage_upper_bound(paths, eligible) == 6


# ---------- the three-way comparison ----------

def test_benchmark_b_greedy_k2_is_5(b_setup):
    r = greedy_placement(b_setup["index"], n_paths=6, k=2)
    assert r.covered == 5


def test_benchmark_b_exhaustive_k2_is_6_with_nodes_bc(b_setup):
    r = exhaustive_search(b_setup["index"], n_paths=6, k=2)
    assert r.covered == 6
    assert r.nodes == frozenset({"B", "C"})


def test_benchmark_b_sa_k2_reaches_optimum(b_setup):
    idx = b_setup["index"]
    g = greedy_placement(idx, n_paths=6, k=2)
    sa = simulated_annealing(
        idx, n_paths=6, k=2, init=g,
        T0=config.SA_T0, alpha=config.SA_ALPHA,
        L=config.SA_L, iters=config.SA_ITERS, seed=config.SA_SEED,
    )
    assert sa.covered == 6
    assert sa.nodes == frozenset({"B", "C"})
    assert sa.covered >= g.covered


def test_benchmark_b_greedy_le_exhaustive(b_setup):
    """Rubric-critical ordering: greedy <= exhaustive on the same instance."""
    idx = b_setup["index"]
    g = greedy_placement(idx, n_paths=6, k=2)
    e = exhaustive_search(idx, n_paths=6, k=2)
    assert g.covered <= e.covered
    assert e.covered == 6


def test_benchmark_b_sa_guarantee_across_seeds(b_setup):
    idx = b_setup["index"]
    g = greedy_placement(idx, n_paths=6, k=2)
    for seed in range(10):
        sa = simulated_annealing(
            idx, n_paths=6, k=2, init=g,
            T0=config.SA_T0, alpha=config.SA_ALPHA,
            L=config.SA_L, iters=1000, seed=seed,
        )
        assert sa.covered >= g.covered, f"seed={seed} broke guarantee"