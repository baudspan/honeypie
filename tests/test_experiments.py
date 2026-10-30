"""Smoke tests for the experiment runner and reporter."""
import pytest
from src.experiments import run_experiment


def test_run_experiment_b_end_to_end():
    r = run_experiment("B", k=2, m=20, seed=42)
    assert r["benchmark"] == "B"
    assert r["greedy"].covered == 5
    assert r["sa"].covered == 6
    assert r["exhaustive"] is not None
    assert r["exhaustive"].covered == 6
    assert r["sa"].covered >= r["greedy"].covered
    assert r["n_uncoverable"] == 0
    assert r["coverage_upper_bound"] == 6
    assert r["incidence"]["B,C"] == 6


def test_run_experiment_a_end_to_end():
    r = run_experiment("A", k=3, m=20, seed=42)
    assert r["benchmark"] == "A"
    assert r["reachable"] is True
    assert r["greedy"].covered > 0
    assert r["sa"].covered >= r["greedy"].covered
    assert r["exhaustive"] is not None
    # Exhaustive is the true optimum: SA cannot beat it
    assert r["exhaustive"].covered >= r["sa"].covered

def test_run_experiment_c_loads_real_graph():
    """Smoke test: Benchmark C on real Precinct6 hybrid graph."""
    r = run_experiment("C", k=2, m=20, seed=42)
    assert r["benchmark"] == "C"
    assert r["graph_nodes"] == 17
    assert r["reachable"] is True
    assert r["n_paths"] == 20            # capped by m
    assert r["greedy"].covered >= 1
    assert r["sa"].covered >= r["greedy"].covered    # frozen guarantee
    assert r["exhaustive"] is not None
    assert r["exhaustive"].covered >= r["sa"].covered  # optimum is upper bound


def test_unknown_benchmark_raises():
    with pytest.raises(ValueError):
        run_experiment("ZZZ", k=2, m=10)


def test_sa_params_recorded():
    r = run_experiment("B", k=2, m=20, seed=7)
    assert r["sa_params"]["T0"] == 1.5
    assert r["sa_params"]["seed"] == 7


def test_report_produces_output_without_crash(capsys):
    from src import report
    r = run_experiment("B", k=2, m=20, seed=42)
    report.print_experiment(r)
    out = capsys.readouterr().out
    assert "Benchmark B" in out
    assert "Greedy" in out and "SA" in out and "Exhaustive" in out
    assert "SA IMPROVED on greedy" in out  # B must show improvement


def test_cli_b_returns_zero(capsys):
    from main import main
    rc = main(["--benchmark", "B", "--k", "2", "--m", "20", "--seed", "42"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "SA matched the exact optimum" in out

def test_run_experiment_includes_betweenness():
    r = run_experiment("B", k=2, m=20, seed=42)
    assert "betweenness" in r
    assert "bc_values" in r
    assert isinstance(r["betweenness"].nodes, frozenset)
    # Betweenness placement must still be evaluated by the shared objective
    assert r["betweenness"].covered >= 1
    # Contract: SA never worse than any single-method baseline on B
    assert r["sa"].covered >= r["betweenness"].covered

def test_sa_beats_greedy_on_benchmark_b_at_k2():
    """The flagship finding: SA strictly improves on greedy at k=2 on B."""
    from src.experiments import run_experiment
    for seed in range(5):  # sample 5 seeds, full run is in scripts/
        r = run_experiment("B", k=2, m=6, seed=seed)
        assert r["sa"].covered == 6
        assert r["greedy"].covered == 5
        assert r["exhaustive"].covered == 6


def test_sa_ties_greedy_on_benchmark_c():
    """On real data, SA never hurts — it ties the greedy optimum."""
    from src.experiments import run_experiment
    r = run_experiment("C", k=2, m=100, seed=42)
    assert r["sa"].covered == r["greedy"].covered == 100
    assert r["exhaustive"].covered == 100


def test_betweenness_loses_coverage_on_real_data():
    """Headline C finding: betweenness is 25 points below path-aware."""
    from src.experiments import run_experiment
    r = run_experiment("C", k=2, m=100, seed=42)
    assert r["betweenness"].covered == 75
    assert r["greedy"].covered - r["betweenness"].covered == 25