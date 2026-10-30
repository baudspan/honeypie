"""Honeypot Placement & Attack-Path Optimization — Streamlit dashboard.

Run:  streamlit run app.py

This file only wires the UI together. All computation is done by the existing
backend (src.experiments.run_experiment and friends); see ui/ for the tabs.
"""
from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Honeypot Placement Lab", page_icon="🍯", layout="wide",
                   initial_sidebar_state="expanded")

from ui import data, theme                                   # noqa: E402  (sets cwd / sys.path)
from ui.tabs_algos import annealing, comparison, exhaustive, greedy  # noqa: E402
from ui.tabs_core import centrality, overview, paths, topology      # noqa: E402
from ui.tabs_extra import precinct6, results, runner               # noqa: E402

theme.inject_css()

PAGES = {
    "Overview": overview,
    "Network Topology": topology,
    "Attack Path Analysis": paths,
    "Centrality Analysis": centrality,
    "Greedy Algorithm": greedy,
    "Simulated Annealing": annealing,
    "Exhaustive Search": exhaustive,
    "Algorithm Comparison": comparison,
    "Generated Results": results,
    "Experiment Runner": runner,
    "Precinct6 Dataset": precinct6,
}
NEEDS_RESULT = {n for n in PAGES if n not in ("Generated Results", "Experiment Runner")}


def _boot():
    """Load the default experiment once per session (cached by Streamlit)."""
    if "result" in st.session_state:
        return None
    try:
        with st.spinner("Running default experiment (Benchmark B)…"):
            data.set_active(data.default_params("B"))
        return None
    except Exception as e:  # noqa: BLE001
        return str(e)


boot_error = _boot()
params, result = data.active()

with st.sidebar:
    st.markdown('<div class="brand">HONEYPOT<span>·LAB</span></div>'
                '<div class="brand-sub">Attack-path coverage optimiser</div>', unsafe_allow_html=True)
    page = st.radio("Navigate", list(PAGES), key="nav", label_visibility="collapsed")
    st.divider()
    if params is not None:
        best, _ = data.best_algorithm(result)
        st.markdown(
            f'<div class="runcard"><b>Active experiment</b><br>'
            f'<span class="k">Benchmark</span> <b>{params.benchmark}</b> · '
            f'<span class="k">k</span> <b>{params.k}</b> · <span class="k">m</span> <b>{params.m}</b><br>'
            f'<span class="k">seed</span> <b>{params.seed}</b> · <span class="k">paths</span> <b>{result["n_paths"]}</b><br>'
            f'<span class="k">best</span> <b>{best}</b> '
            f'({result[{"Greedy": "greedy", "Betweenness": "betweenness", "SA": "sa", "Exhaustive": "exhaustive"}[best]].covered}'
            f'/{result["n_paths"]})</div>', unsafe_allow_html=True)
        st.caption("Change it in **Experiment Runner**.")
    else:
        st.warning("No experiment loaded.")
    st.caption("Backend: `src.experiments.run_experiment`")

if page in NEEDS_RESULT and result is None:
    st.error(f"No experiment is loaded{': ' + boot_error if boot_error else ''}. "
             "Open **Experiment Runner** and run one.")
    st.stop()

try:
    PAGES[page](params, result)
except Exception as e:  # noqa: BLE001 — keep the app alive and show what failed
    st.error(f"This tab hit an error: {e}")
    st.exception(e)
