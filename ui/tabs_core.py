"""Tabs 1-4: Overview, Network Topology, Attack Path Analysis, Centrality."""
from __future__ import annotations
import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ui import charts, compat, data, netviz, theme
from ui.theme import ALGO_COLORS, ALGO_LONG, callout, chips, header, tag


def _gap_ref(r):
    opt = data.optimum(r)
    if opt is not None:
        return opt, "exhaustive optimum"
    return r["coverage_upper_bound"], "coverage upper bound (exhaustive skipped)"


# ============================================================ 1. Overview
def overview(p, r):
    header("Overview", f"{data.BENCH_INFO[p.benchmark][0]} — {data.BENCH_INFO[p.benchmark][1]}")
    n_paths = r["n_paths"]
    best, tied = data.best_algorithm(r)
    best_res = data.algos(r)[best]
    ref, ref_name = _gap_ref(r)

    c = st.columns(5)
    c[0].metric("Hosts (nodes)", r["graph_nodes"])
    c[1].metric("Edges", r["graph_edges"])
    c[2].metric("Eligible honeypot sites", r["eligible_size"],
                help="Vc: nodes where a honeypot may be placed (V \\ {s, t}, or the benchmark's curated set).")
    c[3].metric("Candidate paths", n_paths,
                help="Yen's K-shortest loopless s→t paths, capped at m.")
    c[4].metric("Coverable paths", r["coverage_upper_bound"],
                help=f"{r['n_uncoverable']} paths contain no eligible node and can never be covered.")

    c = st.columns(5)
    c[0].metric("Budget k / path cap m", f"{r['k']} / {r['m']}")
    c[1].metric("Best coverage", f"{best_res.covered} / {n_paths}")
    c[2].metric("Best coverage %", f"{data.pct(best_res.covered, n_paths):.1f}%")
    c[3].metric("Best algorithm", best,
                help="Highest coverage; ties are broken by shortest runtime. "
                     + (f"Tied at this coverage: {', '.join(tied)}." if len(tied) > 1 else ""))
    gap_sa = ref - r["sa"].covered
    c[4].metric("SA gap to optimum" if data.optimum(r) is not None else "SA gap to bound",
                f"{gap_sa} path{'s' if gap_sa != 1 else ''}",
                delta=f"{data.pct(gap_sa, n_paths):.1f}% of paths", delta_color="off")

    # ----- narrative
    g, sa, bt = r["greedy"].covered, r["sa"].covered, r["betweenness"].covered
    msgs = []
    if sa > g:
        msgs.append(f"<b>Simulated annealing escaped the greedy trap:</b> {g} → {sa} paths "
                    f"(+{sa - g}).")
    elif sa == g:
        msgs.append(f"Simulated annealing matched greedy at {g} paths (greedy was already a local optimum).")
    if bt < g:
        msgs.append(f"Betweenness centrality trails greedy by {g - bt} paths "
                    f"({data.pct(bt, n_paths):.1f}% vs {data.pct(g, n_paths):.1f}%).")
    if data.optimum(r) is not None:
        if all(v is None or v.covered == ref for v in (r["greedy"], r["sa"])):
            msgs.append("Greedy and SA both reach the exact optimum.")
        elif sa == ref:
            msgs.append("SA reaches the exact optimum.")
    if msgs:
        callout(" ".join(msgs), "good" if sa >= g else "info")

    st.subheader("Algorithm comparison summary")
    df = data.comparison_df(r)
    show = df[["Algorithm", "Honeypots", "Coverage", "Coverage %", "Runtime (ms)",
               "Gap to optimum" if data.optimum(r) is not None else "Δ vs greedy"]]
    compat.table(show, column_config={
        "Coverage %": st.column_config.ProgressColumn("Coverage %", min_value=0, max_value=100, format="%.1f%%"),
        "Runtime (ms)": st.column_config.NumberColumn(format="%.3f"),
    })
    if r["exhaustive"] is None:
        callout("Exhaustive search was skipped for this configuration — see the "
                "<b>Exhaustive Search</b> tab. Gaps are measured against the coverage upper bound instead.", "warn")

    cols = st.columns(3)
    with cols[0]:
        compat.plot(charts.algo_bar(df, "Coverage", f"Paths covered (dotted = {n_paths} total)", ytitle="paths",
                                    fmt="{:.0f}", hline=n_paths),
                    key="ov_cov")
    with cols[1]:
        compat.plot(charts.algo_bar(df, "Runtime (ms)", "Runtime (log scale)", ytitle="ms",
                                    log=True, fmt="{:.3f}"), key="ov_rt")
    with cols[2]:
        d2 = df.copy()
        d2["Gap"] = (ref - d2["Coverage"])
        compat.plot(charts.algo_bar(d2, "Gap", f"Optimality gap vs {ref_name.split(' (')[0]}",
                                    ytitle="paths missed", fmt="{:.0f}"), key="ov_gap")

    with st.expander("Run configuration & technical details"):
        a, b = st.columns(2)
        with a:
            st.markdown(f"**Source →  Target:** `{r['s']}` → `{r['t']}`")
            st.markdown(f"**Min-cost route (Dijkstra):** cost {r['min_cost']:g}")
            st.markdown(f'<div>{chips(r["min_cost_path"])}</div>', unsafe_allow_html=True)
            st.markdown(f"**Exhaustive search space:** {data.n_combinations_text(r)}"
                        f" (cap {r['exhaustive_cap']:,})")
        with b:
            sp = r["sa_params"]
            st.markdown(f"**SA:** T0 = {sp['T0']:g}, α = {sp['alpha']:g}, L = {sp['L']}, "
                        f"iters = {sp['iters']}, seed = {sp['seed']}")
            if "incidence" in r:
                st.markdown("**Benchmark-B incidence (paths covered):** "
                            + ", ".join(f"`{k}`: {v}" for k, v in r["incidence"].items()))
        st.markdown("**Coverage verification** — the covered-path sets shown in this dashboard "
                    "are checked against the backend's `coverage()`:")
        compat.table(data.verify_coverage(r))


# ================================================== 2. Network topology
def topology(p, r):
    header("Network Topology",
           "The actual benchmark graph. Arrows are directed edges; numbers are traversal-cost weights.")
    algs = data.available_algos(r)
    c1, c2, c3, c4 = st.columns([3, 2.2, 1, 1])
    with c1:
        sel = st.radio("Show honeypots chosen by", ["None"] + algs, horizontal=True, key="topo_algo")
    with c2:
        lay = st.selectbox("Layout", netviz.LAYOUTS, key="topo_layout")
    with c3:
        w = st.checkbox("Edge weights", True, key="topo_w")
    with c4:
        lb = st.checkbox("Labels", True, key="topo_l")

    hp, algo = (None, None) if sel == "None" else (data.algos(r)[sel].nodes, sel)
    fig = netviz.network_figure(r, layout=lay, honeypots=hp, honeypot_algo=algo,
                                show_weights=w, show_labels=lb, height=520)
    compat.plot(fig, key="topo_fig")

    if algo:
        res = data.algos(r)[algo]
        st.markdown(f"**{ALGO_LONG[algo]}** places honeypots at: {chips(res.nodes)} — covers "
                    f"**{res.covered}/{r['n_paths']}** paths ({data.pct(res.covered, r['n_paths']):.1f}%).",
                    unsafe_allow_html=True)
    st.caption("Gold ★ = honeypot. Blue = eligible, grey = ineligible, lime = source, red = target.")

    left, right = st.columns([1.2, 1])
    with left:
        st.subheader("Node information")
        nodes = sorted(r["G"].nodes, key=str)
        node = st.selectbox("Inspect node", nodes, key="topo_node")
        _node_panel(r, node)
    with right:
        st.subheader("Network statistics")
        G = r["G"]
        rows = [("Nodes", G.number_of_nodes()), ("Edges", G.number_of_edges()),
                ("Density", f"{nx.density(G):.3f}"),
                ("Acyclic (DAG)", "yes" if nx.is_directed_acyclic_graph(G) else "no (has cycles)"),
                ("Weakly connected", "yes" if nx.is_weakly_connected(G) else "no"),
                ("Mean out-degree", f"{sum(d for _, d in G.out_degree()) / G.number_of_nodes():.2f}"),
                ("Eligible nodes", r["eligible_size"]),
                ("Min-cost s→t cost", f"{r['min_cost']:g}"),
                ("Min-cost hops", len(r["min_cost_path"]) - 1),
                ("Weight range", f"{min(d.get('weight', 1) for *_, d in G.edges(data=True)):g} – "
                                 f"{max(d.get('weight', 1) for *_, d in G.edges(data=True)):g}")]
        compat.table(pd.DataFrame(rows, columns=["Metric", "Value"]).astype(str))


def _node_panel(r, n):
    G = r["G"]
    idx = r["index"]
    role = data.node_role(r, n)
    colr = theme.ROLE_COLORS[role]
    st.markdown(tag(role, colr), unsafe_allow_html=True)
    cc = st.columns(3)
    cc[0].metric("In / out degree", f"{G.in_degree(n)} / {G.out_degree(n)}")
    cc[1].metric("Paths through", len(idx[n]) if n in idx else "n/a")
    cc[2].metric("Betweenness", f"{r['bc_values'][n]:.4f}" if n in r["bc_values"] else "n/a")
    picks = [a for a in data.available_algos(r) if n in data.algos(r)[a].nodes]
    st.markdown("**Selected by:** " + (" ".join(tag(a, ALGO_COLORS[a]) for a in picks) if picks else "—"),
                unsafe_allow_html=True)
    st.markdown(f"**Predecessors:** {chips(G.predecessors(n))}", unsafe_allow_html=True)
    st.markdown(f"**Successors:** {chips(G.successors(n))}", unsafe_allow_html=True)
    meta = {k: v for k, v in G.nodes[n].items() if v not in (None, "")}
    if meta:
        with st.expander("Node attributes (from dataset)"):
            compat.table(pd.DataFrame(meta.items(), columns=["Attribute", "Value"]).astype(str))


# ================================================= 3. Attack path analysis
def paths(p, r):
    header("Attack Path Analysis",
           "Candidate paths from Yen's K-shortest-paths algorithm, cheapest first. "
           "A path is covered when it contains at least one honeypot.")
    df = data.paths_df(r)
    algs = data.available_algos(r)

    c1, c2, c3 = st.columns([1.4, 1.4, 1.2])
    with c1:
        alg = st.radio("Evaluate coverage for", algs, horizontal=True, key="path_algo")
    with c2:
        flt = st.radio("Show", ["All", "Covered", "Uncovered"], horizontal=True, key="path_filter")
    covered = data.covered_by(r, alg)
    with c3:
        st.metric(f"{alg} coverage", f"{len(covered)} / {r['n_paths']}",
                  delta=f"{r['n_paths'] - len(covered)} uncovered", delta_color="off")

    view = df
    if flt == "Covered":
        view = df[df["_pid"].isin(covered)]
    elif flt == "Uncovered":
        view = df[~df["_pid"].isin(covered)]

    st.caption(f"Showing {len(view)} of {len(df)} paths. ID p*i* = backend path index *i−1* "
               "(matches the p1, p2, … panels in the PNG figures). ✓ = covered by that algorithm.")
    cols = ["ID", "Cost", "Hops"] + algs + ["Path"]
    compat.table(view[cols], height=300, column_config={
        "Cost": st.column_config.NumberColumn(format="%.2f"),
        "Path": st.column_config.TextColumn(width="large")})

    # coverage matrix
    z = [[1 if pid in data.covered_by(r, a) else 0 for pid in df["_pid"]] for a in algs]
    hm = go.Figure(go.Heatmap(
        z=z, x=list(df["ID"]), y=algs, showscale=False, xgap=1, ygap=2,
        colorscale=[[0, "#1e293b"], [1, "#22d3ee"]],
        hovertemplate="%{y} · %{x}: %{z:d}<extra></extra>"))
    theme.style(hm, height=60 + 48 * len(algs), legend=False, title="Coverage matrix (cyan = covered)")
    hm.update_yaxes(autorange="reversed")
    hm.update_xaxes(showticklabels=len(df) <= 30, type="category")
    compat.plot(hm, key="path_matrix")

    st.subheader("Inspect a path")
    if view.empty:
        st.info("No paths match this filter.")
        return
    labels = {row["_pid"]: f"{row['ID']} · cost {row['Cost']:g} · {row['Hops']} hops"
              for _, row in view.iterrows()}
    pid = st.selectbox("Path", list(labels), format_func=labels.get, key="path_sel")
    path = r["paths"][pid]
    hp_alg = st.radio("Overlay honeypots from", ["None"] + algs, horizontal=True, key="path_overlay",
                      index=1 + algs.index(alg))
    hp = None if hp_alg == "None" else data.algos(r)[hp_alg].nodes
    fig = netviz.network_figure(r, highlight_path=path, honeypots=hp,
                                honeypot_algo=None if hp_alg == "None" else hp_alg,
                                show_weights=True, height=520)
    compat.plot(fig, key="path_fig")

    left, right = st.columns([1.3, 1])
    with left:
        st.markdown("**Hop-by-hop**")
        G = r["G"]
        rows = []
        for i, n in enumerate(path):
            rows.append({"Hop": i, "Node": n, "Role": data.node_role(r, n),
                         "Edge cost in": G[path[i - 1]][n].get("weight", 1) if i else None,
                         "Honeypot": ("★ " + hp_alg) if hp and n in hp else ""})
        compat.table(pd.DataFrame(rows), column_config={
            "Edge cost in": st.column_config.NumberColumn(format="%.2f")})
    with right:
        st.markdown(f"**Path {df.loc[df['_pid'] == pid, 'ID'].iloc[0]}** — total cost "
                    f"{data.path_cost(r['G'], path):g}")
        rows = []
        for a in algs:
            hit = [n for n in path if n in data.algos(r)[a].nodes]
            rows.append({"Algorithm": a, "Covered": "✓" if hit else "✗",
                         "Honeypots on path": ", ".join(hit) or "—"})
        compat.table(pd.DataFrame(rows))
        elig_on = [n for n in path if n in set(r["eligible"])]
        st.markdown(f"Eligible sites on this path: {chips(elig_on)}", unsafe_allow_html=True)


# ====================================================== 4. Centrality
def centrality(p, r):
    header("Centrality Analysis",
           "Weighted betweenness centrality of each eligible host (NetworkX, normalised). "
           "The betweenness baseline simply picks the top-k.")
    bc = r["bc_values"]
    algs = data.available_algos(r)
    ranked = sorted(bc, key=lambda n: (-bc[n], str(n)))
    marks = st.multiselect("Highlight nodes selected by", algs, default=["Betweenness"], key="cent_marks")

    def owners(n):
        return [a for a in marks if n in data.algos(r)[a].nodes]

    # bar chart
    y = list(reversed(ranked))
    colors, lines = [], []
    for n in y:
        o = owners(n)
        colors.append(ALGO_COLORS[o[0]] if o else "#334155")
        lines.append("#facc15" if o else "#0b1220")
    fig = go.Figure(go.Bar(
        x=[bc[n] for n in y], y=[str(n) for n in y], orientation="h",
        marker=dict(color=colors, line=dict(color=lines, width=[2 if l != "#0b1220" else 0 for l in lines])),
        text=[f"{bc[n]:.4f}" for n in y], textposition="outside", cliponaxis=False,
        customdata=[[len(r["index"][n]), ", ".join(owners(n)) or "—"] for n in y],
        hovertemplate="<b>%{y}</b><br>Betweenness: %{x:.4f}<br>Paths through: %{customdata[0]}"
                      "<br>Highlighted: %{customdata[1]}<extra></extra>"))
    theme.style(fig, height=max(300, 26 * len(y) + 80), legend=False,
                title="Betweenness ranking (outlined = selected)")
    fig.update_xaxes(title="betweenness centrality", range=[0, max(bc.values() or [1]) * 1.18 or 1])
    fig.update_yaxes(type="category")

    c1, c2 = st.columns([1, 1.15])
    with c1:
        compat.plot(fig, key="cent_bar")
    with c2:
        hp = set().union(*[data.algos(r)[a].nodes for a in marks]) if marks else None
        nf = netviz.network_figure(r, node_values=bc, value_title="Betweenness", honeypots=hp,
                                   show_weights=False, height=max(380, 26 * len(y) + 80))
        compat.plot(nf, key="cent_net")
        st.caption("Node colour = betweenness. ★ = selected by the algorithms highlighted.")

    st.subheader("Centrality ranking vs. actual path coverage")
    nt = data.node_table(r)
    nt = nt[nt["Role"] == "Eligible"].copy()
    corr = None
    if len(nt) >= 3 and nt["BC score"].nunique() > 1 and nt["Paths through"].nunique() > 1:
        corr = nt["BC score"].corr(nt["Paths through"], method="spearman")
    a, b = st.columns([1.2, 1])
    with a:
        sc = go.Figure()
        hl = set().union(*[data.algos(r)[x].nodes for x in marks]) if marks else set()
        labs = netviz.short_label(nt["Node"])
        for flag, name, col in ((False, "Other eligible", "#475569"), (True, "Highlighted", "#facc15")):
            d = nt[nt["Node"].isin(hl) == flag]
            if d.empty:
                continue
            sc.add_trace(go.Scatter(x=d["BC score"], y=d["Paths through"], mode="markers+text",
                                    text=[labs[n] for n in d["Node"]], textposition="top center",
                                    name=name, marker=dict(size=14, color=col,
                                                           line=dict(color="#0b1220", width=1.5)),
                                    hovertext=d["Node"], hoverinfo="text+x+y"))
        theme.style(sc, height=360, title="Betweenness vs number of candidate paths through the node")
        sc.update_xaxes(title="betweenness centrality")
        sc.update_yaxes(title="candidate paths through node")
        compat.plot(sc, key="cent_scatter")
    with b:
        if corr is not None and corr == corr:
            st.metric("Spearman rank correlation", f"{corr:.2f}",
                      help="Between betweenness and the number of candidate paths each eligible node lies on.")
        bt, gr = r["betweenness"], r["greedy"]
        st.markdown(f"**Betweenness top-{r['k']}** covers **{bt.covered}/{r['n_paths']}** paths "
                    f"({data.pct(bt.covered, r['n_paths']):.1f}%); **greedy** covers **{gr.covered}** "
                    f"({data.pct(gr.covered, r['n_paths']):.1f}%).")
        if bt.covered < gr.covered:
            callout("High-centrality nodes are not the same as <i>complementary</i> coverage: "
                    "top-k betweenness nodes tend to sit on the same paths, so their coverage overlaps.", "warn")
        elif bt.covered == gr.covered:
            callout("Here betweenness happens to match greedy's coverage.", "good")
        st.markdown(f"Overlap betweenness ∩ greedy: **{len(bt.nodes & gr.nodes)}/{r['k']}**, "
                    f"betweenness ∩ SA: **{len(bt.nodes & r['sa'].nodes)}/{r['k']}**")

    show = nt[["Node", "BC score", "BC rank", "Paths through", "Path-count rank"] + algs]
    show = show.sort_values("BC rank")
    compat.table(show, column_config={"BC score": st.column_config.NumberColumn(format="%.4f")})
