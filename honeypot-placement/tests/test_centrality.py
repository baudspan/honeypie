"""Tests for src.centrality."""
import pytest
import networkx as nx

from src.centrality import betweenness, betweenness_placement, overlap
from src.models import PlacementResult


def _small_graph():
    G = nx.DiGraph()
    G.add_edge("s", "A", weight=1)
    G.add_edge("A", "t", weight=1)
    G.add_edge("s", "B", weight=1)
    G.add_edge("B", "t", weight=1)
    return G


def test_betweenness_returns_all_eligible():
    G = _small_graph()
    bc = betweenness(G, {"A", "B"})
    assert set(bc.keys()) == {"A", "B"}


def test_betweenness_non_negative():
    G = _small_graph()
    bc = betweenness(G, {"A", "B"})
    for v in bc.values():
        assert v >= 0.0


def test_betweenness_symmetric_graph_equal_values():
    """A and B are structurally identical in this graph."""
    G = _small_graph()
    bc = betweenness(G, {"A", "B"})
    assert abs(bc["A"] - bc["B"]) < 1e-9


def test_betweenness_missing_eligible_gets_zero():
    G = _small_graph()
    bc = betweenness(G, {"A", "Z"})  # Z not in graph
    assert bc["Z"] == 0.0


def test_betweenness_placement_k0_returns_empty():
    idx = {"A": frozenset({0}), "B": frozenset({1})}
    bc = {"A": 0.5, "B": 0.5}
    r = betweenness_placement(bc, idx, n_paths=2, k=0)
    assert r.nodes == frozenset()
    assert r.covered == 0


def test_betweenness_placement_picks_highest():
    idx = {"A": frozenset({0, 1}), "B": frozenset({1, 2}), "C": frozenset({2})}
    bc = {"A": 0.9, "B": 0.5, "C": 0.1}
    r = betweenness_placement(bc, idx, n_paths=3, k=1)
    assert r.nodes == frozenset({"A"})
    assert r.covered == 2


def test_betweenness_placement_deterministic_tiebreak():
    """Equal bc → lexicographically smallest first."""
    idx = {"A": frozenset({0}), "B": frozenset({1}), "C": frozenset({2})}
    bc = {"A": 0.5, "B": 0.5, "C": 0.5}
    r = betweenness_placement(bc, idx, n_paths=3, k=1)
    assert r.nodes == frozenset({"A"})


def test_betweenness_placement_returns_placement_result():
    idx = {"A": frozenset({0})}
    bc = {"A": 1.0}
    r = betweenness_placement(bc, idx, n_paths=1, k=1)
    assert isinstance(r, PlacementResult)
    assert r.total_paths == 1


def test_overlap_basic():
    assert overlap(frozenset({"A", "B"}), frozenset({"B", "C"})) == 1
    assert overlap(frozenset({"A"}), frozenset({"A"})) == 1
    assert overlap(frozenset({"A"}), frozenset({"B"})) == 0