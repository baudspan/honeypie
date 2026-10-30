"""Console formatting for experiment results.

This is the ONLY module that calls print().
Every other module returns data; report.py turns data into tables.

Changing output format requires touching this file only.
"""
from __future__ import annotations


def _pct(covered, total):
    if total == 0:
        return "0.0%"
    return f"{100.0 * covered / total:.1f}%"


def _fmt_result_row(label, r):
    if r is None:
        return f"  {label:<11} {'(skipped)':<28} {'-':>4} {'-':>8} {'-':>11} {'-':>6}"
    nodes = ",".join(sorted(r.nodes, key=str)) or "(none)"
    return (
        f"  {label:<11} {nodes:<28} {r.covered:>4} "
        f"{_pct(r.covered, r.total_paths):>8} "
        f"{r.runtime_s * 1000.0:>9.2f}ms {r.iterations:>6}"
    )


def _header(title):
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def _section(title):
    print()
    print(f"-- {title} " + "-" * max(0, 74 - len(title) - 4))


def _print_common_header(r):
    _header(f"Benchmark {r['benchmark']}  |  s={r['s']!r}  t={r['t']!r}")

    _section("Network")
    print(f"  Nodes: {r['graph_nodes']}   Edges: {r['graph_edges']}")
    print(f"  Eligible honeypot locations (Vc): {r['eligible_size']} {r['eligible']}")
    print(f"  Budget k = {r['k']}   Candidate paths m = {r['m']}")

    _section("Reachability & shortest route")
    print(f"  t reachable from s: {r['reachable']}")
    print(f"  Min-cost route : {' -> '.join(str(n) for n in r['min_cost_path'])}")
    print(f"  Min-cost total : {r['min_cost']:.2f}")

    _section("Candidate attack paths")
    print(f"  Paths enumerated        : {r['n_paths']}")
    print(f"  Uncoverable (no Vc node): {r['n_uncoverable']}")
    print(f"  Coverage upper bound    : {r['coverage_upper_bound']}")
    if r['n_combinations'] > 0:
        print(f"  Exhaustive search space : C({r['eligible_size']},{r['k']}) "
              f"= {r['n_combinations']} placements")

    _section("Candidate paths")
    coverable = r["n_paths"] - r["n_uncoverable"]
    print(f"  Total candidate paths        : {r['n_paths']}")
    print(f"  Coverable paths (contain Vc) : {coverable}")
    print(f"  Uncoverable paths            : {r['n_uncoverable']}")

    # after the comparison table:
    total = r["n_paths"]
    coverable = total - r["n_uncoverable"]
    if coverable > 0:
        print(f"  Greedy covers {r['greedy'].covered}/{coverable} coverable "
              f"({100*r['greedy'].covered/coverable:.1f}%) and "
              f"{r['greedy'].covered}/{total} overall.")


def _print_incidence(r):
    if "incidence" not in r:
        return
    inc = r["incidence"]
    _section("Benchmark B incidence (sanity)")
    print(f"  |A|       = {inc['A']}")
    print(f"  |B|       = {inc['B']}")
    print(f"  |C|       = {inc['C']}")
    print(f"  |{{B,C}}|   = {inc['B,C']}   "
          f"(greedy trap: {{A,B}} and {{A,C}} cover only 5)")


def _print_comparison(r):
    _section("Placement comparison")
    print(f"  {'Method':<11} {'Nodes':<28} {'Cov':>4} {'Coverage':>8} "
          f"{'Runtime':>11} {'Iters':>6}")
    print("  " + "-" * 74)
    print(_fmt_result_row("Greedy", r["greedy"]))
    print(_fmt_result_row("Betweenness", r["betweenness"]))
    print(_fmt_result_row("SA", r["sa"]))
    print(_fmt_result_row("Exhaustive", r["exhaustive"]))

def _print_overlap(r):
    _section("Experiment F — betweenness overlap")
    bc_set = r["betweenness"].nodes
    g_set = r["greedy"].nodes
    sa_set = r["sa"].nodes

    # Show top-5 bc values
    bc = r["bc_values"]
    ranked = sorted(bc.items(), key=lambda kv: (-kv[1], str(kv[0])))[:5]
    print("  Top betweenness nodes:")
    for node, val in ranked:
        print(f"    {node:<8} {val:.4f}")

    print()
    print(f"  Betweenness set     : {sorted(bc_set, key=str)}")
    print(f"  Greedy set          : {sorted(g_set, key=str)}")
    print(f"  SA set              : {sorted(sa_set, key=str)}")
    print(f"  Overlap(bc, greedy) : {len(set(bc_set) & set(g_set))} / {len(bc_set)}")
    print(f"  Overlap(bc, SA)     : {len(set(bc_set) & set(sa_set))} / {len(bc_set)}")
    gap = r["sa"].covered - r["betweenness"].covered
    print(f"  Coverage gap SA vs betweenness : {gap:+d}")

def _print_verdict(r):
    g, sa, ex = r["greedy"], r["sa"], r["exhaustive"]

    _section("Verdict")
    print(f"  SA vs Greedy      : {sa.covered - g.covered:+d}  "
          f"(SA={sa.covered}, greedy={g.covered})")

    if ex is not None:
        print(f"  Greedy vs optimum : {g.covered - ex.covered:+d}  (optimum={ex.covered})")
        print(f"  SA     vs optimum : {sa.covered - ex.covered:+d}")

        if sa.covered > g.covered:
            print(f"  >>> SA IMPROVED on greedy by {sa.covered - g.covered} path(s).")
        elif sa.covered == g.covered and g.covered == ex.covered:
            print("  >>> Greedy was already optimal; SA tied it (valid result).")
        elif sa.covered == g.covered:
            print("  >>> SA tied greedy on this instance; both fell short of optimum.")
        else:
            print("  >>> WARNING: SA reported worse than greedy — contract violated.")

        if sa.covered == ex.covered:
            print("  >>> SA matched the exact optimum.")


def _print_sa_params(r):
    p = r["sa_params"]
    _section("SA parameters")
    print(f"  T0 = {p['T0']}   alpha = {p['alpha']}   L = {p['L']}   "
          f"iters = {p['iters']}   seed = {p['seed']}")


def print_experiment(result):
    """Print the full report for one experiment result dict."""
    _print_common_header(result)
    _print_incidence(result)
    _print_comparison(result)
    _print_overlap(result)
    _print_verdict(result)
    _print_sa_params(result)
    print()