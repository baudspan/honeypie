"""Tests for src.greedy.

Uses a synthetic index matching the Benchmark-B incidence pattern:
    A -> {0,1,2,3}   (4 paths)
    B -> {0,1,4}
    C -> {2,3,5}
So greedy at k=2 must give 5 (A then B by tie-break),
while the optimum is 6 via {B, C}.
"""
import pytest
from src.greedy import greedy_placement
from src.coverage import coverage


def _benchmark_b_index():
    return {
        "A": frozenset({0, 1, 2, 3}),
        "B": frozenset({0, 1, 4}),
        "C": frozenset({2, 3, 5}),
    }


def test_greedy_k_equals_zero_returns_empty():
    r = greedy_placement(_benchmark_b_index(), n_paths=6, k=0)
    assert r.nodes == frozenset()
    assert r.covered == 0
    assert r.total_paths == 6


def test_greedy_empty_index_returns_empty():
    r = greedy_placement({}, n_paths=6, k=3)
    assert r.nodes == frozenset()
    assert r.covered == 0


def test_greedy_k1_picks_A():
    r = greedy_placement(_benchmark_b_index(), n_paths=6, k=1)
    assert r.nodes == frozenset({"A"})
    assert r.covered == 4


def test_greedy_k2_reaches_5_not_6():
    r = greedy_placement(_benchmark_b_index(), n_paths=6, k=2)
    assert r.covered == 5
    assert r.nodes == frozenset({"A", "B"})  # B wins tie-break vs C


def test_greedy_k3_covers_all():
    r = greedy_placement(_benchmark_b_index(), n_paths=6, k=3)
    assert r.covered == 6
    assert r.nodes == frozenset({"A", "B", "C"})


def test_greedy_stops_early_when_no_gain():
    # Only A contributes; k=3 requested but only A useful
    index = {"A": frozenset({0, 1}), "Z": frozenset()}
    r = greedy_placement(index, n_paths=2, k=3)
    assert r.nodes == frozenset({"A"})
    assert r.covered == 2


def test_greedy_k_exceeds_eligible_selects_all():
    index = {"A": frozenset({0}), "B": frozenset({1})}
    r = greedy_placement(index, n_paths=2, k=10)
    assert r.nodes == frozenset({"A", "B"})
    assert r.covered == 2


def test_greedy_negative_k_returns_empty():
    r = greedy_placement(_benchmark_b_index(), n_paths=6, k=-1)
    assert r.nodes == frozenset()
    assert r.covered == 0


def test_greedy_matches_coverage_function():
    """Sanity: r.covered must equal coverage(r.nodes, index)."""
    idx = _benchmark_b_index()
    r = greedy_placement(idx, n_paths=6, k=2)
    assert r.covered == coverage(r.nodes, idx)