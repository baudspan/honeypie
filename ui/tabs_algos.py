"""Tabs 5-8: Greedy, Simulated Annealing, Exhaustive Search, Algorithm Comparison."""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ui import charts, compat, data, netviz, theme
from ui.theme import ALGO_COLORS, ALGO_LONG, callout, chips, header, tag


def _result_cards(res, n_paths, extra=None):
    c = st.columns(4 if not extra else 5)
    c[0].metric("Honeypots placed", len(res.nodes))
    c[1].metric("Coverage", f"{res.covered} / {n_paths}")
    c[2].metric("Coverage %", f"{data.pct(res.covered, n_paths):.1f}%")
    c[3].metric("Runtime", f"{res.runtime_s * 1000:.3f} ms")
    if extra:
        c[4].metric(*extra)


# =============================================================== 5. Greedy
def greedy(p, r):
    header("Greedy Algorithm", "Repeatedly add the eligible node that covers the most still-uncovered paths.")
    res, trace = r["greedy"], r["greedy_trace"]
    n_paths = r["n_paths"]
    _result_cards(res, n_paths, ("Selection steps", len(trace)))
    st.markdown(f"**Selected honeypots (in selection order):** "
                f"{chips([t['node'] for t in trace]) if trace else chips([])}", unsafe_allow_html=True)
    if len(trace) < r["k"]:
        callout(f"Greedy stopped after {len(trace)} of k = {r['k']} picks because no remaining node "
                "adds any new coverage — extra honeypots could not help.", "info")

    left, right = st.columns([1, 1.2])
    with left:
        if trace:
            steps = [f"#{t['step']} {t['node']}" for t in trace]
            fig = go.Figure()
            fig.add_trace(go.Bar(x=steps, y=[t["gain"] for t in trace], name="Marginal gain (new paths)",
                                 marker=dict(color=ALGO_COLORS["Greedy"], line=dict(color="#0b1220", width=1)),
                                 text=[f"+{t['gain']}" for t in trace], textposition="outside"))
            fig.add_trace(go.Scatter(x=steps, y=[t["cumulative"] for t in trace], name="Cumulative coverage",
                                     mode="lines+markers", line=dict(color="#facc15", width=3),
                                     marker=dict(size=9)))
            theme.style(fig, height=360, title="Marginal vs cumulative coverage")
            fig.update_yaxes(title_text="paths", range=[0, n_paths * 1.15])
            fig.update_xaxes(type="category")
            compat.plot(fig, key="greedy_steps")
        else:
            st.info("Greedy selected no nodes (k = 0 or nothing coverable).")
    with right:
        compat.plot(netviz.network_figure(r, honeypots=res.nodes, honeypot_algo="Greedy",
                                          show_weights=False, height=360), key="greedy_net")

    if trace:
        st.subheader("Selection steps")
        rows = [{"Step": t["step"], "Node picked": t["node"], "Marginal coverage added": t["gain"],
                 "Cumulative coverage": t["cumulative"],
                 "Cumulative %": data.pct(t["cumulative"], n_paths),
                 "Remaining uncovered": n_paths - t["cumulative"],
                 "Runners-up (gain)": ", ".join(
                     f"{n} (+{g})" for n, g in sorted(t["candidate_gains"].items(),
                                                       key=lambda kv: (-kv[1], str(kv[0])))
                     if n != t["node"] and g > 0)[:120] or "—"} for t in trace]
        compat.table(pd.DataFrame(rows), column_config={
            "Cumulative %": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%")})

        pick = st.selectbox("Candidate gains at step", [t["step"] for t in trace], key="greedy_step_sel",
                            format_func=lambda s: f"Step {s} — picked {trace[s - 1]['node']}")
        t = trace[pick - 1]
        items = sorted(t["candidate_gains"].items(), key=lambda kv: (kv[1], str(kv[0])))
        bar = go.Figure(go.Bar(
            x=[g for _, g in items], y=[str(n) for n, _ in items], orientation="h",
            marker=dict(color=[ALGO_COLORS["Greedy"] if n == t["node"] else "#334155" for n, _ in items]),
            text=[f"+{g}" for _, g in items], textposition="outside", cliponaxis=False))
        theme.style(bar, height=max(260, 24 * len(items) + 80), legend=False,
                    title=f"Marginal gain of every remaining candidate at step {pick}")
        bar.update_yaxes(type="category")
        bar.update_xaxes(title="new paths covered if added", range=[0, max([g for _, g in items] + [1]) * 1.2])
        compat.plot(bar, key="greedy_cand")

    with st.expander("How greedy selection works"):
        st.markdown(f"""
1. Start with no honeypots and an empty set of covered paths.
2. For every unselected eligible node, compute its **marginal gain** = number of paths through it that are **not yet covered**.
3. Pick the node with the largest gain. **Ties are broken deterministically** by the smallest node name (`sorted_tiebreak`).
4. Repeat until k = **{r['k']}** nodes are chosen, or no node has positive gain.

Greedy is fast (no randomness, one pass per pick) but myopic: a node that looks best now can block a better *pair*.
That is exactly the trap in Benchmark B — greedy picks the node on the most paths (`A`), but the optimal pair is `{{B, C}}`.
""")


# ======================================================= 6. Simulated annealing
def annealing(p, r):
    header("Simulated Annealing",
           "Starts from the greedy solution, then swaps one honeypot at a time, sometimes accepting worse moves "
           "while the temperature is high. The reported answer is the best-so-far.")
    sa, gr, sp, hist = r["sa"], r["greedy"], r["sa_params"], r["sa_history"]
    n_paths = r["n_paths"]

    c = st.columns(5)
    c[0].metric("Initial (greedy)", f"{gr.covered} / {n_paths}")
    c[1].metric("Final (SA best)", f"{sa.covered} / {n_paths}",
                delta=f"{sa.covered - gr.covered:+d} vs greedy")
    c[2].metric("Improvement", f"{data.pct(sa.covered - gr.covered, n_paths):+.1f} pp")
    c[3].metric("Iterations run", f"{sa.iterations:,}")
    c[4].metric("Runtime", f"{sa.runtime_s * 1000:.2f} ms")
    c = st.columns(5)
    c[0].metric("Initial temperature T0", f"{sp['T0']:g}")
    c[1].metric("Cooling factor α", f"{sp['alpha']:g}")
    c[2].metric("Moves per temp step L", sp["L"])
    c[3].metric("Max iterations", f"{sp['iters']:,}")
    c[4].metric("Random seed", sp["seed"])

    a, b = st.columns(2)
    with a:
        st.markdown("**Initial (greedy) solution**")
        st.markdown(chips(gr.nodes), unsafe_allow_html=True)
    with b:
        st.markdown("**Final SA solution**")
        st.markdown(chips(sa.nodes), unsafe_allow_html=True)
    if sa.nodes != gr.nodes:
        st.markdown(f"Swapped out: {chips(gr.nodes - sa.nodes)} → swapped in: {chips(sa.nodes - gr.nodes)}",
                    unsafe_allow_html=True)

    if not hist:
        why = data.sa_skip_reason(r)
        callout(f"<b>SA performed no iterations</b> — {why or 'no history was recorded.'} "
                "There is therefore no coverage/temperature trajectory to plot; the result equals the initial solution.",
                "warn")
    else:
        df = pd.DataFrame(hist)
        accepted = int(df["accepted"].sum())
        first_best = df.index[df["best"] >= sa.covered][0] + 1 if (df["best"] >= sa.covered).any() else None
        c = st.columns(4)
        c[0].metric("Accepted moves", f"{accepted:,}", help="Accepted swaps (improving, equal, or worsening).")
        c[1].metric("Acceptance rate", f"{100 * accepted / len(df):.1f}%")
        c[2].metric("Final temperature", f"{df['T'].iloc[-1]:.4f}")
        c[3].metric("Best reached at iteration",
                    f"{first_best:,}" if sa.covered > gr.covered and first_best else "— (init kept)")

        fig = go.Figure()
        win_c = max(1, min(50, len(df) // 20))
        raw = st.checkbox("Show raw current coverage (noisy)", False, key="sa_raw")
        if raw:
            fig.add_trace(go.Scatter(x=df["iter"], y=df["current"], mode="lines", name="Current coverage (raw)",
                                     line=dict(color="rgba(148,163,184,0.45)", width=1, shape="hv"),
                                     hovertemplate="iter %{x}: %{y}<extra>current</extra>"))
        fig.add_trace(go.Scatter(x=df["iter"], y=df["current"].rolling(win_c, min_periods=1).mean(),
                                 mode="lines", name=f"Current coverage (rolling mean, {win_c})",
                                 line=dict(color="#94a3b8", width=2),
                                 hovertemplate="iter %{x}: %{y:.2f}<extra>current (avg)</extra>"))
        fig.add_trace(go.Scatter(x=df["iter"], y=df["best"], mode="lines", name="Best so far",
                                 line=dict(color=ALGO_COLORS["SA"], width=3, shape="hv")))
        fig.add_hline(y=gr.covered, line=dict(color=ALGO_COLORS["Greedy"], dash="dot"),
                      annotation_text="greedy start", annotation_font_color=ALGO_COLORS["Greedy"],
                      annotation_position="bottom right")
        if data.optimum(r) is not None:
            fig.add_hline(y=data.optimum(r), line=dict(color=ALGO_COLORS["Exhaustive"], dash="dash"),
                          annotation_text="exhaustive optimum", annotation_font_color=ALGO_COLORS["Exhaustive"],
                          annotation_position="top right")
        theme.style(fig, height=340, title="Coverage vs iteration")
        fig.update_xaxes(title="iteration")
        fig.update_yaxes(title="paths covered", dtick=1 if n_paths <= 12 else None)
        compat.plot(fig, key="sa_cov")

        l, rr = st.columns(2)
        with l:
            tf = go.Figure(go.Scatter(x=df["iter"], y=df["T"], mode="lines",
                                      line=dict(color="#fbbf24", width=2.5, shape="hv")))
            theme.style(tf, height=300, legend=False,
                        title=f"Temperature vs iteration (T ← T·{sp['alpha']:g} every {sp['L']} iterations)")
            tf.update_xaxes(title="iteration")
            tf.update_yaxes(title="temperature")
            compat.plot(tf, key="sa_temp")
        with rr:
            win = max(1, min(100, len(df) // 10))
            roll = df["accepted"].astype(float).rolling(win, min_periods=1).mean() * 100
            af = go.Figure(go.Scatter(x=df["iter"], y=roll, mode="lines",
                                      line=dict(color=ALGO_COLORS["SA"], width=2.5)))
            theme.style(af, height=300, legend=False, title=f"Acceptance rate (rolling {win} iterations)")
            af.update_xaxes(title="iteration")
            af.update_yaxes(title="% accepted", range=[0, 102])
            compat.plot(af, key="sa_acc")

    st.subheader("Final honeypot locations")
    compat.plot(netviz.network_figure(r, honeypots=sa.nodes, honeypot_algo="SA", show_weights=False,
                                      height=460), key="sa_net")

    with st.expander("How the annealing works"):
        st.markdown(f"""
- **Start:** the greedy placement (so SA can never report less than greedy).
- **Move:** swap one selected honeypot for a random unselected eligible node.
- **Accept** if coverage does not drop; otherwise accept with probability `exp(Δ / T)` where Δ < 0.
- **Cooling:** every L = **{sp['L']}** iterations, `T ← T × {sp['alpha']:g}` (from T0 = **{sp['T0']:g}**).
- **Reproducibility:** a private `random.Random(seed={sp['seed']})` — the same seed always gives the same trajectory.
- The reported solution is the **best-so-far**, not the final state of the walk.

SA is stochastic: a different seed can find a different path to the same (or a different) answer. Improvement over greedy is empirical, not guaranteed.
""")


# ======================================================= 7. Exhaustive search
def exhaustive(p, r):
    header("Exhaustive Search", "Evaluates every k-subset of eligible nodes — the exact optimum when feasible.")
    ex = r["exhaustive"]
    n_paths = r["n_paths"]
    st.markdown(f"**Search space:** {data.n_combinations_text(r)} placements · "
                f"feasibility cap: {r['exhaustive_cap']:,}")
    if ex is None:
        callout(f"<b>Exhaustive search was skipped.</b> The number of k-subsets ({r['n_combinations']:,}) exceeds the "
                f"cap of {r['exhaustive_cap']:,} placements, so evaluating them all would be too slow. "
                "Reduce the honeypot budget k (or use a smaller benchmark) in the Experiment Runner to re-enable it. "
                "Gaps elsewhere in the dashboard are measured against the coverage upper bound "
                f"({r['coverage_upper_bound']}) instead.", "warn")
        return

    _result_cards(ex, n_paths, ("Combinations evaluated", f"{ex.iterations:,}"))
    st.markdown(f"**Optimal honeypot combination:** {chips(ex.nodes)}", unsafe_allow_html=True)
    callout("When several placements tie for the optimum, the lexicographically smallest one is reported. "
            "Other algorithms may reach the same coverage with a <i>different</i> node set.")

    df = data.comparison_df(r)
    opt = ex.covered
    rows = []
    for a, res in data.algos(r).items():
        rows.append({"Algorithm": a, "Honeypots": data.nodes_str(res.nodes), "Coverage": res.covered,
                     "Gap to optimum": opt - res.covered,
                     "Reaches optimum": "✓" if res.covered == opt else "✗",
                     "Same node set as optimum": "✓" if res.nodes == ex.nodes else "—"})
    left, right = st.columns([1.1, 1])
    with left:
        compat.table(pd.DataFrame(rows))
        sa_t = r["sa"].runtime_s
        if sa_t > 0:
            st.caption(f"Exhaustive took {ex.runtime_s * 1000:.3f} ms vs SA {sa_t * 1000:.3f} ms "
                       f"(×{ex.runtime_s / sa_t:.1f}). Exhaustive cost grows combinatorially with k and |Vc|; SA's does not.")
    with right:
        compat.plot(charts.algo_bar(df, "Coverage", f"Coverage vs the exact optimum (dotted = {opt})", ytitle="paths",
                                    fmt="{:.0f}", hline=opt), key="ex_cmp")
    compat.plot(netviz.network_figure(r, honeypots=ex.nodes, honeypot_algo="Exhaustive",
                                      show_weights=False, height=440), key="ex_net")


# ====================================================== 8. Algorithm comparison
def comparison(p, r):
    header("Algorithm Comparison", "All four placement methods evaluated on the same candidate paths.")
    df = data.comparison_df(r)
    valid = df.dropna(subset=["Coverage"])
    best_cov = valid["Coverage"].max()
    fastest = valid.loc[valid["Runtime (ms)"].idxmin(), "Algorithm"]
    best_names = list(valid.loc[valid["Coverage"] == best_cov, "Algorithm"])

    c = st.columns(3)
    c[0].metric("Highest coverage", f"{int(best_cov)} / {r['n_paths']}", help="Tied: " + ", ".join(best_names))
    c[1].metric("Achieved by", ", ".join(best_names))
    c[2].metric("Fastest", fastest, help="Single-run wall-clock times at the sub-millisecond scale are noisy.")

    def hl(row):
        out = [""] * len(row)
        for i, col in enumerate(row.index):
            if col == "Coverage" and row["Coverage"] == best_cov:
                out[i] = "background-color: rgba(52,211,153,0.25); font-weight:700"
            if col == "Runtime (ms)" and row["Algorithm"] == fastest:
                out[i] = "background-color: rgba(56,189,248,0.25); font-weight:700"
        return out

    styled = (df.style.apply(hl, axis=1)
              .format({"Coverage %": "{:.1f}", "Runtime (ms)": "{:.3f}", "Gap %": "{:.1f}"}, na_rep="—"))
    compat.table(styled)
    st.caption("Green = best coverage · Blue = fastest. Gap = optimum − coverage (needs the exhaustive result).")

    c1, c2 = st.columns(2)
    with c1:
        compat.plot(charts.algo_bar(df, "Coverage", f"Coverage (dotted = {r['n_paths']} total paths)", ytitle="paths",
                                    fmt="{:.0f}", hline=r["n_paths"]), key="cmp_cov")
    with c2:
        compat.plot(charts.algo_bar(df, "Runtime (ms)", "Runtime (log scale)", ytitle="ms", log=True,
                                    fmt="{:.3f}"), key="cmp_rt")
    c1, c2 = st.columns(2)
    with c1:
        compat.plot(charts.cov_runtime_scatter(df), key="cmp_scatter")
    with c2:
        if data.optimum(r) is not None:
            compat.plot(charts.algo_bar(df, "Gap to optimum", "Optimality gap (paths below optimum)",
                                        ytitle="paths", fmt="{:.0f}"), key="cmp_gap")
        else:
            callout("Optimality gap unavailable — exhaustive search was skipped.", "warn")

    st.subheader("Selected-node overlap")
    mat = data.overlap_matrix(r)
    c1, c2 = st.columns([1, 1.2])
    with c1:
        compat.plot(charts.overlap_heatmap(mat), key="cmp_overlap")
    with c2:
        rows = []
        for a, res in data.algos(r).items():
            if res is None:
                continue
            rows.append({"Algorithm": a, "Honeypots": data.nodes_str(res.nodes)})
        compat.table(pd.DataFrame(rows))
        st.caption("Diagonal = size of each set; off-diagonal = number of honeypots two algorithms share. "
                   "Different node sets can still reach the same coverage.")
