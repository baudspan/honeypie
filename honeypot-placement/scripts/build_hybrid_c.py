"""Hybrid Benchmark C: real Precinct6 hosts, multi-path pivot structure.

WHY:
The merged Precinct6 incident graph is hub-and-spoke: hosts appear in many
incidents as attacker/victim, but no pair of hosts has >2-3 distinct routes.
For the optimizer to have anything to optimize, we need a chain with
BYPASS edges that create alternate routes.

APPROACH:
1. Load the full merged graph (hundreds of hosts).
2. Find the LONGEST simple path between any pair (approximate via BFS).
3. Use that chain's hosts (real IPs, real roles) as the spine.
4. Add bypass edges (skip-1 and skip-2 forward) to create alternate routes.

DISCLOSURE (goes in report §Benchmark C):
  - Hosts, IPs, roles: real, from WitFoo Precinct6 (100 incidents merged)
  - Chain edges: real, from observed incident transitions
  - Bypass edges: SYNTHETIC (disclosed) — models alternate lateral-movement
    routes that skip an intermediate hop
  - Weight = 1.0 on chain, 2.0-3.0 on bypasses
"""
from __future__ import annotations
import networkx as nx

MERGED = "data/precinct6_merged.graphml"
OUTPUT = "data/precinct6_hybrid.graphml"
MAX_DEPTH = 20          # BFS cutoff when finding the chain


def find_longest_chain(G):
    """Return the node list of the longest shortest-path in G (approximate)."""
    best_hops = 0
    best_pair = None
    for s in G.nodes:
        try:
            lengths = nx.single_source_shortest_path_length(G, s, cutoff=MAX_DEPTH)
        except nx.NetworkXError:
            continue
        for t, hops in lengths.items():
            if hops > best_hops:
                best_hops = hops
                best_pair = (s, t)
    if best_pair is None:
        raise RuntimeError("No chain found — merged graph may be too small.")
    return nx.shortest_path(G, best_pair[0], best_pair[1])


def main():
    G_full = nx.read_graphml(MERGED)
    print(f"loaded merged graph: {G_full.number_of_nodes()} nodes, "
          f"{G_full.number_of_edges()} edges")

    chain = find_longest_chain(G_full)
    source, target = chain[0], chain[-1]
    print(f"found chain: {len(chain) - 1} hops, {len(chain)} hosts")
    print(f"  source: {source}")
    print(f"  target: {target}")

    if len(chain) < 4:
        raise RuntimeError(
            f"Chain only has {len(chain) - 1} hops — too short. "
            f"Try re-fetching with more incidents."
        )

    # --- build the hybrid graph ---
    H = nx.DiGraph()
    for i in range(len(chain) - 1):
        u, v = chain[i], chain[i + 1]
        meta = dict(G_full[u][v]) if G_full.has_edge(u, v) else {}
        meta["weight"] = 1.0
        meta["synthetic"] = "false"
        H.add_edge(u, v, **meta)

    # copy node metadata (roles, hostname, etc.)
    for n in chain:
        H.nodes[n].update(dict(G_full.nodes[n]))

       # --- BYPASS both even AND odd interior positions ---
    # The chain is n0 -> n1 -> n2 -> ... -> n16. Previously we only skipped
    # odd positions, leaving every even-position node as a dominator (any
    # path had to pass through it). Now we skip every position:
    n = len(chain)
    for i in range(0, n - 2):
        u, v = chain[i], chain[i + 2]   # skip chain[i+1] entirely
        if not H.has_edge(u, v):
            H.add_edge(u, v, weight=2.5, synthetic="true",
                       note=f"bypass of {chain[i+1]}")

    # --- a few long-range links to force length diversity ---
    for i in range(0, n - 4, 3):
        u, v = chain[i], chain[i + 4]
        if not H.has_edge(u, v):
            H.add_edge(u, v, weight=4.0, synthetic="true",
                       note="long bypass")

    H.graph["source"] = source
    H.graph["target"] = target
    H.graph["note"] = ("Hybrid Precinct6: real hosts, real chain edges, "
                       "synthesized bypass edges. See report §Benchmark C.")
    nx.write_graphml(H, OUTPUT)

    # --- verify ---
    paths = list(nx.shortest_simple_paths(H, source, target))
    capped = paths[:30]
    intermediates = set()
    for p in capped:
        intermediates |= set(p[1:-1])

    print()
    print(f"saved -> {OUTPUT}")
    print(f"  nodes: {H.number_of_nodes()}  edges: {H.number_of_edges()}")
    print(f"  simple paths (up to 30): {len(capped)}")
    print(f"  distinct intermediate hosts: {len(intermediates)}")
    print(f"  shortest path: {len(paths[0]) - 1} hops")
    print(f"  longest path : {len(paths[-1]) - 1} hops")
    print()
    print("REPORT-READY (paste into benchmark_c.py):")
    print(f'  SOURCE = "{source}"')
    print(f'  TARGET = "{target}"')


if __name__ == "__main__":
    main()