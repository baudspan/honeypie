"""Edge cases and graph-layer tests (Steps 1–7 build order).

Covers: input validation, reachability, Dijkstra, Yen's path enumeration.
Once test_benchmark_b.py exists (Step 3), it asserts the 6-path incidence
directly, so happy-path enumeration is tested there rather than here.
"""
import pytest
import networkx as nx

from src.graph_builder import load_benchmark, validate_graph, define_eligible
from src.reachability import is_reachable
from src.shortest_path import min_cost_path
from src.candidate_paths import (
    enumerate_paths, count_uncoverable, coverage_upper_bound,
)


# ---------- graph_builder ----------

def test_load_benchmark_a():
    G, s, t = load_benchmark("A")
    assert s in G and t in G
    assert len(G.nodes) == 15
    assert len(G.edges) == 25


def test_define_eligible_excludes_s_t():
    G, s, t = load_benchmark("A")
    eligible = define_eligible(G, s, t)
    assert s not in eligible
    assert t not in eligible
    assert len(eligible) == len(G.nodes) - 2


def test_validate_rejects_negative_weight():
    G = nx.DiGraph()
    G.add_edge("a", "b", weight=-1)
    with pytest.raises(ValueError):
        validate_graph(G, "a", "b")


def test_unknown_benchmark_raises():
    with pytest.raises(ValueError):
        load_benchmark("ZZZ")


# ---------- reachability ----------

def test_reachable():
    G = nx.DiGraph()
    G.add_edges_from([("a", "b"), ("b", "c")])
    assert is_reachable(G, "a", "c") is True


def test_unreachable_disconnected():
    G = nx.DiGraph()
    G.add_edges_from([("a", "b"), ("c", "d")])
    assert is_reachable(G, "a", "d") is False


def test_reachable_missing_node_returns_false():
    G = nx.DiGraph()
    G.add_edge("a", "b")
    assert is_reachable(G, "a", "zzz") is False


# ---------- shortest_path (Dijkstra) ----------

def test_dijkstra_picks_cheaper_indirect_route():
    G = nx.DiGraph()
    G.add_edge("a", "c", weight=10)
    G.add_edge("a", "b", weight=1)
    G.add_edge("b", "c", weight=1)
    path, cost = min_cost_path(G, "a", "c")
    assert path == ["a", "b", "c"]
    assert cost == 2


def test_dijkstra_equal_cost_tie_returns_valid_cost():
    # Tie can return different paths — we lock on COST, not path identity.
    G = nx.DiGraph()
    G.add_edge("a", "c", weight=5)
    G.add_edge("a", "b", weight=2)
    G.add_edge("b", "c", weight=3)
    _, cost = min_cost_path(G, "a", "c")
    assert cost == 5


def test_dijkstra_no_path_raises():
    G = nx.DiGraph()
    G.add_edge("a", "b")
    with pytest.raises(ValueError):
        min_cost_path(G, "a", "c")


# ---------- candidate_paths (Yen) ----------

def _two_paths_graph():
    G = nx.DiGraph()
    G.add_edge("s", "a", weight=1)
    G.add_edge("s", "b", weight=2)
    G.add_edge("a", "t", weight=1)
    G.add_edge("b", "t", weight=1)
    return G


def test_paths_capped_at_m():
    paths = enumerate_paths(_two_paths_graph(), "s", "t", m=1)
    assert len(paths) == 1


def test_paths_returns_all_when_m_exceeds_available():
    paths = enumerate_paths(_two_paths_graph(), "s", "t", m=10)
    assert len(paths) == 2


def test_paths_sorted_by_cost():
    paths = enumerate_paths(_two_paths_graph(), "s", "t", m=10)
    # s->a->t cost 2 precedes s->b->t cost 3
    assert paths[0] == ["s", "a", "t"]


def test_paths_m_zero_raises():
    with pytest.raises(ValueError):
        enumerate_paths(_two_paths_graph(), "s", "t", m=0)


def test_paths_no_route_raises():
    G = nx.DiGraph()
    G.add_edge("s", "x")
    with pytest.raises(ValueError):
        enumerate_paths(G, "s", "t", m=5)


def test_uncoverable_and_upper_bound():
    paths = enumerate_paths(_two_paths_graph(), "s", "t", m=10)
    eligible = {"a"}  # 'b' ineligible -> s->b->t uncoverable
    assert count_uncoverable(paths, eligible) == 1
    assert coverage_upper_bound(paths, eligible) == 1

def test_validate_rejects_nan_weight():
    import math
    G = nx.DiGraph()
    G.add_edge("a", "b", weight=float("nan"))
    with pytest.raises(ValueError, match="Non-finite"):
        validate_graph(G, "a", "b")


def test_validate_rejects_infinite_weight():
    G = nx.DiGraph()
    G.add_edge("a", "b", weight=float("inf"))
    with pytest.raises(ValueError, match="Non-finite"):
        validate_graph(G, "a", "b")


def test_validate_rejects_non_numeric_weight():
    G = nx.DiGraph()
    G.add_edge("a", "b", weight="heavy")
    with pytest.raises(ValueError, match="Non-numeric"):
        validate_graph(G, "a", "b")


def test_validate_accepts_zero_weight():
    # Zero-weight edges are allowed (means "free traverse").
    G = nx.DiGraph()
    G.add_edge("a", "b", weight=0)
    validate_graph(G, "a", "b")   # must not raise