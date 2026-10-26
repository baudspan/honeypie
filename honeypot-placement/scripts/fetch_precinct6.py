"""Download ~60 incident GraphML files from Precinct6 and merge them by IP.

Produces data/precinct6_merged.graphml — a single directed attack graph
across multiple incidents, which is what Benchmark C loads.
"""
from __future__ import annotations
import json
import shutil
from collections import defaultdict

import networkx as nx
from huggingface_hub import hf_hub_download, list_repo_files

REPO = "witfoo/precinct6-cybersecurity"
N_INCIDENTS = 250


def list_incident_files(limit):
    files = list_repo_files(REPO, repo_type="dataset")
    inc = [f for f in files if f.startswith("graph/incidents_graphml/") and f.endswith(".graphml")]
    return inc[:limit]


def merge_incidents(paths):
    """Merge per-incident MultiDiGraphs into one DiGraph keyed by IP."""
    merged = nx.DiGraph()
    ip_map = {}          # uuid -> ip
    roles = defaultdict(set)
    techniques = defaultdict(set)

    for p in paths:
        Gi = nx.read_graphml(p)   # MultiDiGraph per incident

        # --- nodes: key by IP; union roles
        for n, d in Gi.nodes(data=True):
            ip = d.get("ip") or d.get("hostname") or n
            ip_map[n] = ip
            if ip not in merged:
                merged.add_node(ip, hostname=d.get("hostname", ip),
                                products=d.get("products", ""))
            for role in _parse_list(d.get("set_roles", "[]")):
                roles[ip].add(role)

        # --- edges: collapse parallel timestamps into one edge per pair
        pair_counts = defaultdict(int)
        pair_techs = defaultdict(set)
        for u, v, d in Gi.edges(data=True):
            u_ip, v_ip = ip_map[u], ip_map[v]
            if u_ip == v_ip:
                continue
            pair_counts[(u_ip, v_ip)] += 1
            for t in _parse_list(d.get("attack_techniques", "[]")):
                pair_techs[(u_ip, v_ip)].add(t)

        for (u, v), count in pair_counts.items():
            if merged.has_edge(u, v):
                merged[u][v]["weight"] += count
                merged[u][v]["incidents"] += 1
            else:
                merged.add_edge(u, v, weight=float(count), incidents=1)
            techniques[(u, v)] |= pair_techs[(u, v)]

    # attach roles + techniques
    for ip, r in roles.items():
        merged.nodes[ip]["roles"] = ",".join(sorted(r))
    for (u, v), ts in techniques.items():
        merged[u][v]["techniques"] = ",".join(sorted(ts))

    return merged


def _parse_list(s):
    if not s:
        return []
    try:
        v = json.loads(s)
        return v if isinstance(v, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def pick_source_target(G):
    """Source = host that only exploits others (never a target).
       Target = host with highest in-degree."""
    entry_candidates = [
        n for n, d in G.nodes(data=True)
        if "Exploiting Host" in d.get("roles", "")
        and "Exploiting Target" not in d.get("roles", "")
    ]
    if entry_candidates:
        s = max(entry_candidates, key=lambda n: G.out_degree(n))
    else:
        s = max(G.nodes, key=lambda n: G.out_degree(n) - G.in_degree(n))

    targets = [n for n in G.nodes if n != s]
    t = max(targets, key=lambda n: G.in_degree(n))
    return s, t


def main():
    print(f"Listing incidents in {REPO}...")
    files = list_incident_files(N_INCIDENTS)
    print(f"Found {len(files)} incident files. Downloading...")

    paths = []
    for i, f in enumerate(files):
        try:
            p = hf_hub_download(repo_id=REPO, filename=f, repo_type="dataset")
            paths.append(p)
            if (i + 1) % 10 == 0:
                print(f"  {i + 1}/{len(files)}")
        except Exception as e:
            print(f"  skip {f}: {e}")

    print(f"Merging {len(paths)} incidents...")
    G = merge_incidents(paths)

    # sanity checks
    if G.number_of_nodes() < 10:
        raise RuntimeError(f"Merged graph only has {G.number_of_nodes()} nodes — too small.")
    if not nx.is_weakly_connected(G):
        # keep the largest weakly-connected component
        largest = max(nx.weakly_connected_components(G), key=len)
        G = G.subgraph(largest).copy()
        print(f"Kept largest weakly-connected component: {G.number_of_nodes()} nodes")

    s, t = pick_source_target(G)
    if not nx.has_path(G, s, t):
        raise RuntimeError(f"No path from {s} to {t}. Try a different incident batch.")

    # cap size for Yen tractability
        # cap size for Yen tractability

        # NO cap — save the full largest-weakly-connected-component.
    # build_hybrid_c.py extracts a manageable chain from this.
    G.graph["source"] = s
    G.graph["target"] = t
    nx.write_graphml(G, "data/precinct6_merged.graphml")

    print()
    print(f"Saved -> data/precinct6_merged.graphml")
    print(f"  nodes={G.number_of_nodes()}  edges={G.number_of_edges()}")
    print(f"  (note: source/target stored for reference only — build_hybrid_c.py "
          f"selects its own chain)")

    print()
    print(f"Saved -> data/precinct6_merged.graphml")
    print(f"  nodes={G.number_of_nodes()}  edges={G.number_of_edges()}")
    print(f"  source={s}  target={t}")
    print(f"  path exists: {nx.has_path(G, s, t)}")
    print(f"  shortest path length: {nx.shortest_path_length(G, s, t, weight='weight')}")


if __name__ == "__main__":
    main()