"""Data layer for the dashboard.

Everything numeric comes from the existing backend (src.*). This module only
(a) runs/caches experiments, (b) reshapes backend objects into DataFrames, and
(c) discovers generated files in results/. No algorithm is implemented here.
"""
from __future__ import annotations
import os
import re
import sys
from collections import namedtuple
from math import comb
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent


def setup_env():
    """Make `src`, `benchmarks`, `config` importable and paths (data/…) valid."""
    os.chdir(ROOT)
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))


setup_env()

import config  # noqa: E402
from src.experiments import run_experiment  # noqa: E402
from src.coverage import covered_ids, coverage  # noqa: E402
from src.centrality import overlap  # noqa: E402
from ui.theme import ALGO_ORDER  # noqa: E402

RESULTS_DIR = ROOT / "results"
DATA_DIR = ROOT / "data"
DASH_RUNS_DIR = RESULTS_DIR / "dashboard_runs"

Params = namedtuple("Params", "benchmark k m seed T0 alpha L iters")

BENCH_INFO = {
    "A": ("Benchmark A", "15-node corporate network (dense; greedy is optimal)"),
    "B": ("Benchmark B", "11-node greedy trap (SA beats greedy 5 → 6)"),
    "C": ("Benchmark C", "17-node Precinct6 hybrid (betweenness fails at 75%)"),
}
BENCH_DEFAULTS = {"A": (3, 20), "B": (2, 20), "C": (2, 100)}   # README configs


def default_params(benchmark="B", **over) -> Params:
    k, m = BENCH_DEFAULTS[benchmark]
    base = dict(benchmark=benchmark, k=k, m=m, seed=config.SA_SEED,
                T0=config.SA_T0, alpha=config.SA_ALPHA, L=config.SA_L,
                iters=config.SA_ITERS)
    base.update(over)
    return Params(**base)


def is_default_sa(p: Params) -> bool:
    return (p.T0, p.alpha, p.L, p.iters) == (
        config.SA_T0, config.SA_ALPHA, config.SA_L, config.SA_ITERS)


@st.cache_resource(show_spinner=False, max_entries=64)
def cached_run(p: Params):
    """Run the backend pipeline once per distinct parameter set.

    The returned dict is shared across reruns — treat it as read-only.
    """
    return run_experiment(
        p.benchmark, p.k, p.m, p.seed,
        sa_params={"T0": p.T0, "alpha": p.alpha, "L": p.L, "iters": p.iters},
    )


# --------------------------------------------------------------------------
# session helpers
# --------------------------------------------------------------------------

def active():
    """(Params, result) of the experiment every tab is showing, or (None, None)."""
    return st.session_state.get("params"), st.session_state.get("result")


def set_active(p: Params):
    """Run (or fetch from cache) and make this experiment the active one."""
    r = cached_run(p)
    st.session_state["params"] = p
    st.session_state["result"] = r
    hist = st.session_state.setdefault("history", [])
    if not hist or hist[-1]["params"] != p:
        hist.append({"params": p, "summary": summary_row(p, r)})
    return r


def summary_row(p: Params, r) -> dict:
    row = {"Benchmark": p.benchmark, "k": p.k, "m": p.m, "seed": p.seed,
           "SA (T0/α/L/iters)": f"{p.T0:g}/{p.alpha:g}/{p.L}/{p.iters}",
           "Paths": r["n_paths"]}
    for name, res in algos(r).items():
        row[name] = res.covered if res is not None else None
    return row


# --------------------------------------------------------------------------
# result reshaping
# --------------------------------------------------------------------------

def algos(r) -> dict:
    """Ordered {name: PlacementResult | None}."""
    return {"Greedy": r["greedy"], "Betweenness": r["betweenness"],
            "SA": r["sa"], "Exhaustive": r["exhaustive"]}


def available_algos(r) -> list[str]:
    return [n for n, v in algos(r).items() if v is not None]


def nodes_str(nodes) -> str:
    return ", ".join(sorted(nodes, key=str)) if nodes else "(none)"


def pct(c, total) -> float:
    return 100.0 * c / total if total else 0.0


def optimum(r):
    """Coverage of the exhaustive optimum, or None if exhaustive was skipped."""
    ex = r["exhaustive"]
    return ex.covered if ex is not None else None


def best_algorithm(r):
    """(name, tied_names): highest coverage, then fastest. Ties are reported."""
    items = [(n, v) for n, v in algos(r).items() if v is not None]
    top = max(v.covered for _, v in items)
    tied = [n for n, v in items if v.covered == top]
    winner = min(tied, key=lambda n: algos(r)[n].runtime_s)
    return winner, tied


def covered_by(r, name) -> frozenset:
    res = algos(r)[name]
    return covered_ids(res.nodes, r["index"]) if res is not None else frozenset()


def verify_coverage(r) -> pd.DataFrame:
    """Cross-check: per-path coverage set size == the backend's reported count,
    and == src.coverage.coverage() recomputed on the same placement."""
    rows = []
    for name, res in algos(r).items():
        if res is None:
            continue
        ids = covered_ids(res.nodes, r["index"])
        backend = coverage(res.nodes, r["index"])
        rows.append({"Algorithm": name, "Reported (PlacementResult)": res.covered,
                     "coverage() recomputed": backend,
                     "Covered-path set size": len(ids),
                     "Consistent": res.covered == backend == len(ids)})
    return pd.DataFrame(rows)


def path_cost(G, path) -> float:
    return float(sum(G[u][v].get("weight", 1) for u, v in zip(path[:-1], path[1:])))


def paths_df(r) -> pd.DataFrame:
    G = r["G"]
    cov = {n: covered_by(r, n) for n in available_algos(r)}
    rows = []
    for pid, p in enumerate(r["paths"]):
        row = {"ID": f"p{pid + 1}", "Cost": path_cost(G, p), "Hops": len(p) - 1,
               "Path": " → ".join(map(str, p))}
        for n, ids in cov.items():
            row[n] = "✓" if pid in ids else "–"
        row["_pid"] = pid
        rows.append(row)
    return pd.DataFrame(rows)


def comparison_df(r) -> pd.DataFrame:
    n_paths = r["n_paths"]
    opt = optimum(r)
    greedy_cov = r["greedy"].covered
    rows = []
    for name, res in algos(r).items():
        if res is None:
            rows.append({"Algorithm": name, "Honeypots": "(skipped)", "Coverage": None,
                         "Coverage %": None, "Runtime (ms)": None, "Iterations": None,
                         "Gap to optimum": None, "Gap %": None, "Δ vs greedy": None})
            continue
        rows.append({
            "Algorithm": name, "Honeypots": nodes_str(res.nodes),
            "Coverage": res.covered, "Coverage %": pct(res.covered, n_paths),
            "Runtime (ms)": res.runtime_s * 1000.0, "Iterations": res.iterations,
            "Gap to optimum": (opt - res.covered) if opt is not None else None,
            "Gap %": pct(opt - res.covered, n_paths) if opt is not None else None,
            "Δ vs greedy": res.covered - greedy_cov,
        })
    return pd.DataFrame(rows)


def overlap_matrix(r) -> pd.DataFrame:
    names = available_algos(r)
    algs = algos(r)
    mat = [[overlap(algs[a].nodes, algs[b].nodes) for b in names] for a in names]
    return pd.DataFrame(mat, index=names, columns=names)


def node_role(r, n) -> str:
    if n == r["s"]:
        return "Source"
    if n == r["t"]:
        return "Target"
    return "Eligible" if n in set(r["eligible"]) else "Ineligible"


def node_table(r) -> pd.DataFrame:
    G, idx, bc = r["G"], r["index"], r["bc_values"]
    algs = {n: v for n, v in algos(r).items() if v is not None}
    ranked = sorted(bc, key=lambda n: (-bc[n], str(n)))
    bc_rank = {n: i + 1 for i, n in enumerate(ranked)}
    thru = {n: len(idx.get(n, ())) for n in G.nodes}
    cov_rank_order = sorted(idx, key=lambda n: (-thru[n], str(n)))
    cov_rank = {n: i + 1 for i, n in enumerate(cov_rank_order)}
    rows = []
    for n in G.nodes:
        row = {"Node": n, "Role": node_role(r, n),
               "In-degree": G.in_degree(n), "Out-degree": G.out_degree(n),
               "Paths through": thru[n],
               "BC score": bc.get(n), "BC rank": bc_rank.get(n),
               "Path-count rank": cov_rank.get(n)}
        for a, res in algs.items():
            row[a] = "★" if n in res.nodes else ""
        rows.append(row)
    return pd.DataFrame(rows)


def sa_skip_reason(r) -> str | None:
    """Why SA did no iterations (mirrors the backend's early-exit conditions)."""
    if r["sa"].iterations > 0:
        return None
    k, idx = r["k"], r["index"]
    coverable = set()
    for pids in idx.values():
        coverable |= pids
    if k <= 0:
        return "the honeypot budget is k = 0, so there is nothing to place."
    if not idx:
        return "there are no eligible nodes."
    if k >= len(idx):
        return (f"k = {k} ≥ number of eligible nodes ({len(idx)}), so every eligible "
                "node is already selected — there is nothing to swap.")
    if r["greedy"].covered >= len(coverable):
        return (f"the greedy start already covers all {len(coverable)} coverable "
                "paths, so no neighbour can improve it (SA returns the initial "
                "solution unchanged, by design).")
    if r["sa_params"]["iters"] == 0:
        return "the iteration count was set to 0."
    return "the search had no unselected nodes to swap in."


def n_combinations_text(r) -> str:
    n, k = r["eligible_size"], min(r["k"], r["eligible_size"])
    return f"C({n}, {k}) = {comb(n, k):,}"


# --------------------------------------------------------------------------
# generated files (results/)
# --------------------------------------------------------------------------

EXPECTED_REPORTS = ["A_baseline.txt", "B_baseline.txt", "C_baseline.txt",
                    "C_sweep.txt", "C_seeds.txt"]
REPORT_CMD = {
    "A_baseline.txt": "python main.py --benchmark A --k 3 --m 20 --seed 42 | Tee-Object results/A_baseline.txt",
    "B_baseline.txt": "python main.py --benchmark B --k 2 --m 20 --seed 42 | Tee-Object results/B_baseline.txt",
    "C_baseline.txt": "python main.py --benchmark C --k 2 --m 100 --seed 42 | Tee-Object results/C_baseline.txt",
    "C_sweep.txt": "1..5 | ForEach-Object { python main.py --benchmark C --k $_ --m 100 --seed 42 } | Tee-Object results/C_sweep.txt",
    "C_seeds.txt": "1..10 | ForEach-Object { python main.py --benchmark C --k 2 --m 100 --seed $_ } | Tee-Object results/C_seeds.txt",
}
_FIG_KIND_ORDER = {"network": 0, "paths": 1, "comparison": 2}


def discover_pngs(results_dir: Path = RESULTS_DIR) -> list[dict]:
    """Every PNG under results/ (recursively), tagged with benchmark & kind."""
    out = []
    if not results_dir.exists():
        return out
    for p in sorted(results_dir.rglob("*.png")):
        m = re.match(r"benchmark_([a-z])_(.+)\.png$", p.name, re.I)
        bench = m.group(1).upper() if m else None
        kind = m.group(2).lower() if m else p.stem
        out.append({"path": p, "bench": bench, "kind": kind,
                    "rel": p.relative_to(results_dir).as_posix(),
                    "run": p.parent.name if p.parent != results_dir else "results/"})
    out.sort(key=lambda d: (d["bench"] or "~", d["run"] != "results/", d["run"],
                            _FIG_KIND_ORDER.get(d["kind"], 9), d["rel"]))
    return out


def discover_reports(results_dir: Path = RESULTS_DIR) -> list[Path]:
    if not results_dir.exists():
        return []
    files = sorted(results_dir.rglob("*.txt"))

    def key(p):
        try:
            return (0, EXPECTED_REPORTS.index(p.name))
        except ValueError:
            return (1, p.name)
    return sorted(files, key=key)


def read_report(path: Path) -> str:
    """Decode a report robustly. PowerShell's Tee-Object writes UTF-16 LE
    (with BOM), so sniff the BOM before falling back to UTF-8 / cp1252."""
    raw = path.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        text = raw.decode("utf-16", errors="replace")
    elif raw.startswith(b"\xef\xbb\xbf"):
        text = raw.decode("utf-8-sig", errors="replace")
    else:
        # BOM-less UTF-16 shows up as lots of NUL bytes
        if raw[:200].count(b"\x00") > 20:
            text = raw.decode("utf-16-le", errors="replace")
        else:
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                text = raw.decode("cp1252", errors="replace")
    return text.replace("\r\n", "\n").replace("\r", "\n").lstrip("﻿")


def figure_dir_for(p: Params) -> Path:
    tag = f"{p.benchmark.lower()}_k{p.k}_m{p.m}_seed{p.seed}"
    if not is_default_sa(p):
        tag += f"_sa-T{p.T0:g}-a{p.alpha:g}-L{p.L}-i{p.iters}"
    return DASH_RUNS_DIR / tag


# --------------------------------------------------------------------------
# Precinct6 dataset
# --------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def merged_dataset_stats():
    """Stats of the raw merged Precinct6 incident graph (None if file missing)."""
    import networkx as nx
    path = DATA_DIR / "precinct6_merged.graphml"
    if not path.exists():
        return None
    M = nx.read_graphml(path)
    deg = sorted(((n, M.degree(n)) for n in M.nodes), key=lambda x: (-x[1], str(x[0])))
    und = M.to_undirected()
    comps = sorted((len(c) for c in nx.connected_components(und)), reverse=True)
    return {
        "nodes": M.number_of_nodes(), "edges": M.number_of_edges(),
        "directed": M.is_directed(),
        "density": nx.density(M),
        "max_degree": deg[0][1] if deg else 0,
        "mean_degree": (sum(d for _, d in deg) / len(deg)) if deg else 0,
        "top_hubs": deg[:8],
        "components": len(comps), "largest_component": comps[0] if comps else 0,
        "source": M.graph.get("source"), "target": M.graph.get("target"),
        "edge_set": set(M.edges()),
    }
