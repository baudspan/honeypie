"""Tabs 9-11: Generated Results, Experiment Runner, Precinct6 Dataset."""
from __future__ import annotations
import time
import traceback

import pandas as pd
import streamlit as st

from ui import charts, compat, data, netviz, theme
from ui.theme import ALGO_COLORS, ALGO_LONG, callout, chips, header, tag


# ================================================== 9. Generated results
def results(p, r):
    header("Generated Results & Visualizations",
           "Everything found on disk in <code>results/</code> — figures and text reports produced by the CLI scripts. "
           "Nothing here is re-drawn or substituted by the dashboard.")
    pngs = data.discover_pngs()
    reports = data.discover_reports()
    c = st.columns(3)
    c[0].metric("PNG figures found", len(pngs))
    c[1].metric("Text reports found", len(reports))
    c[2].metric("Folder", "results/" if data.RESULTS_DIR.exists() else "missing")
    if not data.RESULTS_DIR.exists():
        callout("The <code>results/</code> folder does not exist yet. Generate figures from the "
                "<b>Experiment Runner</b> tab or run <code>python visualize.py --benchmark all</code>.", "warn")

    t_fig, t_rep = st.tabs(["Figures", "Text reports"])
    with t_fig:
        if not pngs:
            st.info("No PNG files found in results/. Use the Experiment Runner's *Generate benchmark PNG figures* "
                    "option, or run `python visualize.py --benchmark all`.")
        groups = {}
        for f in pngs:
            groups.setdefault(f["bench"] or "Other", []).append(f)
        present = [b for b in ("A", "B", "C") if b in groups] + (["Other"] if "Other" in groups else [])
        missing = [b for b in ("A", "B", "C") if b not in groups]
        if missing and pngs:
            st.caption("No generated figures yet for benchmark(s): " + ", ".join(missing)
                       + ". Generate them from the Experiment Runner tab.")
        if present:
            tabs = st.tabs([f"Benchmark {b}" if b != "Other" else "Other" for b in present])
            for tb, b in zip(tabs, present):
                with tb:
                    for f in groups[b]:
                        st.markdown(f"**{f['kind'].replace('_', ' ').title()}** · `{f['rel']}`"
                                    + ("" if f["run"] == "results/" else f" · run `{f['run']}`"))
                        compat.image(f["path"])
                        st.download_button("Download " + f["path"].name, f["path"].read_bytes(),
                                           file_name=f["path"].name, mime="image/png", key="dl_" + f["rel"])
                        st.divider()
    with t_rep:
        present_names = {x.name for x in reports}
        gone = [n for n in data.EXPECTED_REPORTS if n not in present_names]
        if gone:
            with st.expander(f"Missing expected reports ({len(gone)}) — how to generate", expanded=not reports):
                for n in gone:
                    st.markdown(f"`{n}` — not found. Generate with:")
                    st.code(data.REPORT_CMD[n], language="powershell")
        for f in reports:
            rel = f.relative_to(data.RESULTS_DIR).as_posix()
            try:
                text = data.read_report(f)
            except Exception as e:  # unreadable file should not break the page
                st.warning(f"Could not read `{rel}`: {e}")
                continue
            with st.expander(f"{rel}  ·  {len(text.splitlines())} lines", expanded=False):
                st.code(text, language=None)
                st.download_button("Download " + f.name, text.encode("utf-8"), file_name=f.name,
                                   mime="text/plain", key="dlr_" + rel)


# ================================================== 10. Experiment runner
def _preset(bench):
    k, m = data.BENCH_DEFAULTS[bench]
    st.session_state.update(rn_bench=bench, rn_k=k, rn_m=m)


def _reset_sa():
    from config import SA_ALPHA, SA_ITERS, SA_L, SA_T0
    st.session_state.update(rn_T0=float(SA_T0), rn_alpha=float(SA_ALPHA), rn_L=int(SA_L),
                            rn_iters=int(SA_ITERS))


def _init_form(p):
    for key, val in dict(rn_bench=p.benchmark, rn_k=p.k, rn_m=p.m, rn_seed=p.seed,
                         rn_T0=float(p.T0), rn_alpha=float(p.alpha), rn_L=int(p.L),
                         rn_iters=int(p.iters), rn_figs=False).items():
        st.session_state.setdefault(key, val)


def runner(p, r):
    header("Experiment Runner",
           "Configure and run the full backend pipeline (<code>src.experiments.run_experiment</code>). "
           "All dashboard tabs update to the latest run. Identical settings are served from cache.")
    flash = st.session_state.pop("flash", None)
    if flash:
        kind, msg = flash
        (st.success if kind == "ok" else st.error)(msg)
    _init_form(p or data.default_params())

    st.markdown("**Presets** (the configurations from the project README)")
    pc = st.columns(4)
    for col, b in zip(pc, "ABC"):
        col.button(f"{data.BENCH_INFO[b][0]} · k={data.BENCH_DEFAULTS[b][0]}, m={data.BENCH_DEFAULTS[b][1]}",
                   on_click=_preset, args=(b,), key=f"preset_{b}")
    pc[3].button("Reset SA parameters", on_click=_reset_sa, key="reset_sa")

    with st.form("run_form"):
        c1, c2, c3, c4 = st.columns([1.6, 1, 1, 1])
        bench = c1.selectbox("Benchmark", list("ABC"), key="rn_bench",
                             format_func=lambda b: f"{b} — {data.BENCH_INFO[b][1]}")
        k = c2.number_input("Honeypot budget k", min_value=0, max_value=50, step=1, key="rn_k",
                            help="Number of honeypots to place.")
        m = c3.number_input("Max candidate paths m", min_value=1, max_value=1000, step=1, key="rn_m",
                            help="Cap on Yen's K-shortest paths.")
        seed = c4.number_input("Random seed", min_value=0, step=1, key="rn_seed",
                               help="Explicit seed for simulated annealing (reproducible).")
        with st.expander("Simulated annealing parameters"):
            s1, s2, s3, s4 = st.columns(4)
            T0 = s1.number_input("T0 (initial temperature)", min_value=0.0001, step=0.1, format="%.4f", key="rn_T0")
            alpha = s2.number_input("α (cooling factor, 0<α<1)", min_value=0.001, max_value=0.999, step=0.001,
                                    format="%.3f", key="rn_alpha")
            L = s3.number_input("L (iterations per temperature)", min_value=1, step=1, key="rn_L")
            iters = s4.number_input("Iterations", min_value=0, step=100, key="rn_iters")
        figs = st.checkbox("Also generate benchmark PNG figures (network, paths, comparison)", key="rn_figs",
                           help="Uses the project's visualize.py pipeline. Files go to "
                                "results/dashboard_runs/<settings>/ so existing figures are never overwritten.")
        go_ = st.form_submit_button("Run experiment", type="primary")

    if go_:
        params = data.Params(bench, int(k), int(m), int(seed), float(T0), float(alpha), int(L), int(iters))
        t0 = time.perf_counter()
        try:
            with st.spinner(f"Running benchmark {bench} (k={params.k}, m={params.m}, seed={params.seed})…"):
                res = data.set_active(params)
                msg = (f"Benchmark {bench} finished in {time.perf_counter() - t0:.2f}s — "
                       f"greedy {res['greedy'].covered}, betweenness {res['betweenness'].covered}, "
                       f"SA {res['sa'].covered}"
                       + (f", exhaustive {res['exhaustive'].covered}" if res["exhaustive"] else ", exhaustive skipped")
                       + f" of {res['n_paths']} paths.")
                if figs:
                    msg += " " + _generate_figures(params, res)
            st.session_state["flash"] = ("ok", msg)
            st.rerun()
        except (ValueError, RuntimeError) as e:
            st.error(f"The experiment could not run: {e}")
        except Exception as e:  # noqa: BLE001 — surface anything unexpected, don't crash the app
            st.error(f"Unexpected error: {e}")
            with st.expander("Traceback"):
                st.code(traceback.format_exc())

    p, r = data.active()
    if r is not None:
        st.subheader("Latest run")
        compat.table(data.comparison_df(r)[["Algorithm", "Honeypots", "Coverage", "Coverage %",
                                            "Runtime (ms)", "Iterations"]],
                     column_config={"Runtime (ms)": st.column_config.NumberColumn(format="%.3f"),
                                    "Coverage %": st.column_config.NumberColumn(format="%.1f")})
        figs_info = st.session_state.get("last_figs")
        if figs_info and figs_info["params"] == p:
            st.markdown("**Generated figures for this run**")
            for kind, path in figs_info["files"].items():
                st.markdown(f"`{path}`")
                compat.image(path)

    hist = st.session_state.get("history", [])
    if len(hist) > 1:
        with st.expander(f"Run history this session ({len(hist)})"):
            compat.table(pd.DataFrame([h["summary"] for h in hist]))
            choice = st.selectbox("Re-activate a previous run (instant — served from cache)",
                                  range(len(hist)), index=len(hist) - 1,
                                  format_func=lambda i: f"#{i + 1} · {hist[i]['params'].benchmark} "
                                                        f"k={hist[i]['params'].k} m={hist[i]['params'].m} "
                                                        f"seed={hist[i]['params'].seed}")
            if st.button("Activate selected run"):
                data.set_active(hist[choice]["params"])
                st.rerun()


def _generate_figures(params, res) -> str:
    """Generate PNGs once per distinct settings; never overwrite existing files."""
    from visualize import generate_figures
    out_dir = data.figure_dir_for(params)
    prefix = f"benchmark_{params.benchmark.lower()}"
    files = {k: str(out_dir / f"{prefix}_{k}.png") for k in ("network", "paths", "comparison")}
    if all(__import__("pathlib").Path(f).exists() for f in files.values()):
        note = f"Figures already existed in {out_dir.relative_to(data.ROOT).as_posix()}/ (reused)."
    else:
        out = generate_figures(params.benchmark, params.k, params.m, params.seed, str(out_dir), result=res)
        files = out["files"]
        note = f"Figures written to {out_dir.relative_to(data.ROOT).as_posix()}/."
    st.session_state["last_figs"] = {"params": params, "files": files}
    return note


# ================================================== 11. Precinct6 dataset
def precinct6(p, r):
    header("Precinct6 Dataset — Benchmark C",
           "A hybrid attack graph built on real WitFoo Precinct6 hosts. Read the disclosure below before citing results.")
    if p.benchmark == "C":
        pc, rc = p, r
    else:
        pc = data.default_params("C")
        try:
            rc = data.cached_run(pc)
        except Exception as e:  # noqa: BLE001
            st.error(f"Benchmark C could not be loaded: {e}")
            return
        callout(f"The active experiment is Benchmark {p.benchmark}. This tab shows Benchmark C at its README "
                f"configuration (k={pc.k}, m={pc.m}, seed={pc.seed}). Run C in the Experiment Runner to change it.")

    G = rc["G"]
    syn = [(u, v, d) for u, v, d in G.edges(data=True) if str(d.get("synthetic", "")).lower() == "true"]
    real = [(u, v, d) for u, v, d in G.edges(data=True) if str(d.get("synthetic", "")).lower() != "true"]
    merged = data.merged_dataset_stats()

    callout(f"<b>Disclosure — which parts are real and which are synthetic.</b> "
            f"Hosts, IP addresses, roles and the <b>{len(real)} chain edges</b> are real, taken from 100 Precinct6 "
            f"incidents merged by IP. The remaining <b>{len(syn)} of {G.number_of_edges()} edges are synthetic</b>: "
            "bypass edges (weight 2.5) that skip one host and long bypass edges (weight 4.0) that skip three, added "
            "so the graph has alternate lateral-movement routes for the optimiser to choose between. "
            "Results on this benchmark therefore demonstrate the algorithms on a realistic-host topology, "
            "not measured attacker behaviour.", "warn")

    c = st.columns(5)
    c[0].metric("Merged dataset hosts", f"{merged['nodes']:,}" if merged else "n/a")
    c[1].metric("Merged dataset edges", f"{merged['edges']:,}" if merged else "n/a")
    c[2].metric("Hybrid hosts / edges", f"{G.number_of_nodes()} / {G.number_of_edges()}")
    c[3].metric("Real edges", len(real))
    c[4].metric("Synthetic edges", len(syn))
    if merged:
        found = sum(1 for u, v, _ in real if (u, v) in merged["edge_set"])
        st.caption(f"Cross-check: {found} of {len(real)} real chain edges are present in the merged dataset "
                   f"(data/precinct6_merged.graphml).")

    st.subheader("Network (synthetic edges in pink)")
    algs = data.available_algos(rc)
    sel = st.radio("Show honeypots chosen by", ["None"] + algs, horizontal=True, key="p6_algo")
    lay = st.selectbox("Layout", netviz.LAYOUTS, key="p6_layout")
    hp = None if sel == "None" else data.algos(rc)[sel].nodes
    compat.plot(netviz.network_figure(rc, layout=lay, honeypots=hp, honeypot_algo=None if sel == "None" else sel,
                                      mark_synthetic=True, show_weights=True, height=560), key="p6_net")
    st.caption(f"Source `{rc['s']}` → target `{rc['t']}`. Labels show the last two octets; hover for the full IP.")

    st.subheader("Algorithm results on Benchmark C")
    df = data.comparison_df(rc)
    a, b = st.columns([1.3, 1])
    with a:
        compat.table(df[["Algorithm", "Honeypots", "Coverage", "Coverage %", "Runtime (ms)", "Gap to optimum"]],
                     column_config={"Runtime (ms)": st.column_config.NumberColumn(format="%.3f"),
                                    "Coverage %": st.column_config.NumberColumn(format="%.1f")})
        bt, gr = rc["betweenness"], rc["greedy"]
        if bt.covered < gr.covered:
            st.markdown(f"Betweenness covers only **{bt.covered}/{rc['n_paths']}** paths versus greedy's "
                        f"**{gr.covered}** — central hosts are not the ones that intercept the most distinct routes.")
    with b:
        compat.plot(charts.algo_bar(df, "Coverage", f"Paths covered (dotted = {rc['n_paths']} total)", ytitle="paths",
                                    fmt="{:.0f}", hline=rc["n_paths"]), key="p6_cov")

    t1, t2, t3 = st.tabs(["Candidate paths", "Edges (real vs synthetic)", "Hosts"])
    with t1:
        pdf = data.paths_df(rc)
        compat.table(pdf[[c for c in pdf.columns if c != "_pid"]], height=320)
    with t2:
        rows = [{"From": u, "To": v, "Weight": d.get("weight", 1),
                 "Origin": "SYNTHETIC" if str(d.get("synthetic", "")).lower() == "true" else "Real",
                 "Note / evidence": d.get("note") or (f"{d.get('incidents', '')} incident(s); {d.get('techniques', '')}"
                                                      if d.get("techniques") else "")}
                for u, v, d in G.edges(data=True)]
        edf = pd.DataFrame(rows).sort_values(["Origin", "From"], ascending=[False, True])
        compat.table(edf)
    with t3:
        rows = [{"Host": n, "Role in graph": data.node_role(rc, n),
                 "Dataset roles": G.nodes[n].get("roles", ""), "Products": G.nodes[n].get("products", ""),
                 "Paths through": len(rc["index"].get(n, ()))} for n in G.nodes]
        compat.table(pd.DataFrame(rows))

    st.subheader("About the datasets")
    left, right = st.columns(2)
    with left:
        st.markdown("**Merged Precinct6 graph** (`data/precinct6_merged.graphml`)")
        if merged:
            compat.table(pd.DataFrame([
                ("Hosts", f"{merged['nodes']:,}"), ("Directed edges", f"{merged['edges']:,}"),
                ("Density", f"{merged['density']:.4f}"), ("Mean degree", f"{merged['mean_degree']:.2f}"),
                ("Max degree", merged["max_degree"]), ("Weakly-connected components", merged["components"]),
                ("Largest component (hosts)", merged["largest_component"])],
                columns=["Property", "Value"]).astype(str))
            st.markdown("Highest-degree hosts: " + chips([f"{n} ({d})" for n, d in merged["top_hubs"][:5]]),
                        unsafe_allow_html=True)
        else:
            st.info("data/precinct6_merged.graphml not found. Regenerate with `python scripts/fetch_precinct6.py`.")
    with right:
        st.markdown("**Why a hybrid benchmark?**")
        st.markdown(
            "The merged incident graph is hub-and-spoke: hosts appear in many incidents, but no pair has more than a "
            "few distinct routes, so there is little for an optimiser to decide. The hybrid keeps the longest real "
            "chain of hosts (17 hosts, 16 hops) as a spine, then adds forward bypass edges so that many alternate "
            "attack paths exist. Weights: 1.0 on real chain edges, 2.5 on bypass edges, 4.0 on long bypasses.")
        st.caption("Built by scripts/build_hybrid_c.py → data/precinct6_hybrid.graphml")

    st.subheader("Generated figures for Benchmark C")
    cf = [f for f in data.discover_pngs() if f["bench"] == "C"]
    if not cf:
        st.info("No benchmark_c_*.png files in results/ yet. Tick *Generate benchmark PNG figures* in the "
                "Experiment Runner with Benchmark C, or run `python visualize.py --benchmark C`.")
    for f in cf:
        st.markdown(f"**{f['kind'].title()}** · `{f['rel']}`")
        compat.image(f["path"])
