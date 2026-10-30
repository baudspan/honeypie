"""Tests for the additive backend hooks used by the Streamlit dashboard.

They must not change any existing result: every new code path is compared
against the original frozen-contract functions.
"""
import pytest

import config
from src.annealing import simulated_annealing, simulated_annealing_with_history
from src.coverage import build_index, coverage, covered_ids
from src.experiments import run_experiment
from src.greedy import greedy_placement, greedy_placement_with_trace


@pytest.mark.parametrize("name,k,m", [("A", 3, 20), ("B", 2, 20), ("C", 2, 100), ("C", 4, 30)])
def test_run_experiment_unchanged_and_extended(name, k, m):
    r = run_experiment(name, k, m, 42)
    idx, n = r["index"], r["n_paths"]
    g = greedy_placement(idx, n, k)
    assert (r["greedy"].nodes, r["greedy"].covered) == (g.nodes, g.covered)
    sa = simulated_annealing(idx, n, k, g, config.SA_T0, config.SA_ALPHA,
                             config.SA_L, config.SA_ITERS, 42)
    assert (r["sa"].nodes, r["sa"].covered, r["sa"].iterations) == (sa.nodes, sa.covered, sa.iterations)
    # additive keys
    for key in ("G", "paths", "index", "greedy_trace", "sa_history", "exhaustive_cap"):
        assert key in r
    assert len(r["paths"]) == n


def test_greedy_trace_matches_placement():
    r = run_experiment("B", 2, 20, 42)
    res, trace = greedy_placement_with_trace(r["index"], r["n_paths"], 2)
    assert res.nodes == r["greedy"].nodes and res.covered == r["greedy"].covered
    assert [t["node"] for t in trace] and trace[-1]["cumulative"] == res.covered
    assert sum(t["gain"] for t in trace) == res.covered
    assert all(t["gain"] > 0 for t in trace)


def test_sa_history_shape_and_best_monotone():
    r = run_experiment("B", 2, 20, 42)
    hist = r["sa_history"]
    assert len(hist) == r["sa"].iterations == config.SA_ITERS
    bests = [h["best"] for h in hist]
    assert bests == sorted(bests)
    assert bests[-1] == r["sa"].covered
    assert hist[0]["T"] == config.SA_T0
    assert hist[config.SA_L]["T"] == pytest.approx(config.SA_T0 * config.SA_ALPHA)


def test_sa_history_empty_on_early_exit():
    r = run_experiment("C", 2, 100, 42)   # greedy already covers everything
    assert r["sa"].iterations == 0 and r["sa_history"] == []


def test_history_does_not_change_sa_result():
    r = run_experiment("B", 2, 20, 7)
    g = r["greedy"]
    a = simulated_annealing(r["index"], r["n_paths"], 2, g, 1.5, 0.99, 10, 3000, 7)
    b, _ = simulated_annealing_with_history(r["index"], r["n_paths"], 2, g, 1.5, 0.99, 10, 3000, 7)
    assert (a.nodes, a.covered, a.iterations) == (b.nodes, b.covered, b.iterations)


def test_sa_params_override_and_validation():
    r = run_experiment("B", 2, 20, 42, sa_params={"iters": 50, "T0": 2.0})
    assert r["sa_params"]["iters"] == 50 and r["sa_params"]["T0"] == 2.0
    assert r["sa_params"]["alpha"] == config.SA_ALPHA
    assert r["sa"].iterations <= 50
    with pytest.raises(ValueError):
        run_experiment("B", 2, 20, 42, sa_params={"bogus": 1})
    with pytest.raises(ValueError):
        run_experiment("B", 2, 20, 42, sa_params={"alpha": 1.5})


def test_covered_ids_consistent_with_coverage():
    r = run_experiment("A", 3, 20, 42)
    for res in (r["greedy"], r["betweenness"], r["sa"], r["exhaustive"]):
        ids = covered_ids(res.nodes, r["index"])
        assert len(ids) == coverage(res.nodes, r["index"]) == res.covered
        assert all(0 <= i < r["n_paths"] for i in ids)
    assert covered_ids([], r["index"]) == frozenset()


def test_visualize_generate_figures(tmp_path):
    from visualize import generate_figures
    out = generate_figures("B", out_dir=str(tmp_path))
    for f in out["files"].values():
        assert (tmp_path / f.split("/")[-1]).exists() or __import__("os").path.exists(f)
