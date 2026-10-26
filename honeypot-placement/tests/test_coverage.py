"""Tests for src.coverage: build_index, coverage, sorted_tiebreak."""
import pytest
from src.coverage import build_index, coverage, sorted_tiebreak


def _small_paths():
    # 2 paths: ['a','b'] and ['a','c']
    return [["a", "b"], ["a", "c"]]


def test_build_index_basic():
    idx = build_index(_small_paths(), eligible={"a", "b", "c"})
    assert idx["a"] == frozenset({0, 1})
    assert idx["b"] == frozenset({0})
    assert idx["c"] == frozenset({1})


def test_build_index_excludes_ineligible():
    idx = build_index(_small_paths(), eligible={"a"})
    assert set(idx.keys()) == {"a"}
    assert idx["a"] == frozenset({0, 1})


def test_build_index_includes_isolated_eligible_node():
    idx = build_index(_small_paths(), eligible={"a", "zzz"})
    assert idx["zzz"] == frozenset()


def test_coverage_empty_placement_is_zero():
    idx = build_index(_small_paths(), eligible={"a", "b", "c"})
    assert coverage(set(), idx) == 0


def test_coverage_single_node():
    idx = build_index(_small_paths(), eligible={"a", "b", "c"})
    assert coverage({"a"}, idx) == 2
    assert coverage({"b"}, idx) == 1


def test_coverage_union_dedupes_overlap():
    idx = build_index(_small_paths(), eligible={"a", "b", "c"})
    # {a} covers {0,1}; {b} covers {0}; union {0,1} -> 2
    assert coverage({"a", "b"}, idx) == 2
    # {b, c} covers {0} U {1} -> 2
    assert coverage({"b", "c"}, idx) == 2


def test_coverage_unknown_node_contributes_zero():
    idx = build_index(_small_paths(), eligible={"a"})
    assert coverage({"not_in_index"}, idx) == 0


def test_sorted_tiebreak_deterministic():
    assert sorted_tiebreak(["B", "A", "C"]) == "A"
    assert sorted_tiebreak(["node9", "node10"]) == "node10"


def test_sorted_tiebreak_single():
    assert sorted_tiebreak(["only"]) == "only"