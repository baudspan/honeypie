"""Find a good (s, t) pair for Benchmark C.

Key insight: the pair must have MANY candidate paths, not just deep ones.
With only 1 path, greedy = SA = exhaustive = trivial. We need paths that
share SOME but not ALL intermediate hosts, so honeypot placement is a real
combinatorial decision.

Filters:
  - shortest >= 2 hops (reject direct edges)
  - shortest <= 8 hops (moderate depth, so m=20 covers meaningful routes)
  - n_paths >= 5 (at least 5 distinct routes to optimize over)
  - n_intermediates >= 4 (different hosts used by different paths)

Ranking: score = n_paths * n_intermediates
  (rewards both path diversity and host diversity simultaneously)
"""
from __future__ import annotations
import networkx as nx

PATH = "data/precinct6_merged.graphml"
MAX_PATHS = 50
MIN_PATHS = 5
MIN_INTERMEDIATES = 4
MIN_HOPS = 2
MAX_HOPS = 8

G = nx.read_graphml(PATH)
print(f"nodes: {G.number_of_nodes()}  edges: {G.number_of_edges()}")
print()

candidates = []
nodes = list(G.nodes)

for s in nodes:
    for t in nodes:
        if s == t:
            continue
        if not nx.has_path(G, s, t):
            continue
        try:
            paths = []
            for i, p in enumerate(nx.shortest_simple_paths(G, s, t)):
                paths.append(p)
                if i + 1 >= MAX_PATHS:
                    break
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            continue

        shortest = len(paths[0]) - 1
        if shortest < MIN_HOPS or shortest > MAX_HOPS:
            continue
        if len(paths) < MIN_PATHS:
            continue

        intermediates = set()
        for p in paths:
            intermediates |= set(p[1:-1])
        if len(intermediates) < MIN_INTERMEDIATES:
            continue

        candidates.append({
            "s": s, "t": t,
            "n_paths": len(paths),
            "n_intermediates": len(intermediates),
            "shortest": shortest,
            "longest": len(paths[-1]) - 1,
            "score": len(paths) * len(intermediates),
        })

if not candidates:
    print("No pair passed the filters.")
    print("Relax: try MIN_PATHS=3, MIN_INTERMEDIATES=3, or MAX_HOPS=10.")
else:
    candidates.sort(key=lambda c: -c["score"])
    print(f"Found {len(candidates)} viable pairs. Top 15 by score (paths * intermediates):\n")
    print(f"  {'s':18s} {'t':18s} {'hops':>7} {'paths':>6} {'interm':>7} {'score':>6}")
    print("  " + "-" * 72)
    for c in candidates[:15]:
        print(f"  {c['s']:18s} {c['t']:18s} "
              f"{c['shortest']:>2}-{c['longest']:<2} "
              f"{c['n_paths']:>6} {c['n_intermediates']:>7} {c['score']:>6}")
    print()
    best = candidates[0]
    print("RECOMMENDED (paste into benchmark_c.py):")
    print(f'  SOURCE = "{best["s"]}"')
    print(f'  TARGET = "{best["t"]}"')
    print(f"  -> {best['n_paths']} candidate paths, "
          f"{best['n_intermediates']} intermediate hosts, "
          f"shortest {best['shortest']} hops")
    print()
    print("Alternatives (2nd / 3rd best, in case the top one behaves oddly):")
    for c in candidates[1:3]:
        print(f'  SOURCE = "{c["s"]}"  TARGET = "{c["t"]}"  '
              f'({c["n_paths"]} paths, {c["n_intermediates"]} intermediates)')