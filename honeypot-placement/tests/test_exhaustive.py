"""Tests for src.exhaustive_search."""
import pytest
from src.exhaustive import exhaustive_search
from src.coverage import coverage


def _benchmark_b_index():
    return {
        "A": frozenset({0, 1, 2, 3}),
        "B": frozenset({0, 1, 4}),
        "C": frozenset({2, 3, 5}),
    }


def test_exhaustive_k_equals_zero_returns_empty():
    r = exhaustive_search(_benchmark_b_index(), n_paths=6, k=0)
    assert r.nodes == frozenset()
    assert r.covered == 0


def test_exhaustive_empty_index_returns_empty():
    r = exhaustive_search({}, n_paths=6, k=3)
    assert r.nodes == frozenset()
    assert r.covered == 0


def test_exhaustive_k1_picks_A():
    r = exhaustive_search(_benchmark_b_index(), n_paths=6, k=1)
    assert r.nodes == frozenset({"A"})
    assert r.covered == 4


def test_exhaustive_k2_finds_optimal_B_C():
    r = exhaustive_search(_benchmark_b_index(), n_paths=6, k=2)
    assert r.nodes == frozenset({"B", "C"})
    assert r.covered == 6


def test_exhaustive_k3_covers_all():
    r = exhaustive_search(_benchmark_b_index(), n_paths=6, k=3)
    assert r.covered == 6
    assert r.nodes == frozenset({"A", "B", "C"})


def test_exhaustive_k_exceeds_eligible():
    r = exhaustive_search({"A": frozenset({0}), "B": frozenset({1})}, n_paths=2, k=10)
    assert r.covered == 2
    assert r.nodes == frozenset({"A", "B"})


def test_exhaustive_iteration_count_matches_combination_size():
    # |Vc|=3, k=2 -> C(3,2) = 3 combinations
    r = exhaustive_search(_benchmark_b_index(), n_paths=6, k=2)
    assert r.iterations == 3


def test_exhaustive_matches_coverage_function():
    idx = _benchmark_b_index()
    r = exhaustive_search(idx, n_paths=6, k=2)
    assert r.covered == coverage(r.nodes, idx)


def test_exhaustive_never_worse_than_greedy():
    """Rubric-critical: greedy <= exhaustive on the same instance."""
    from src.greedy import greedy_placement
    idx = _benchmark_b_index()
    g = greedy_placement(idx, n_paths=6, k=2)
    e = exhaustive_search(idx, n_paths=6, k=2)
    assert g.covered <= e.covered
    assert e.covered == 6