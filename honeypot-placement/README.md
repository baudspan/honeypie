# Attack Path Analysis & Honeypot Placement Optimization

Console Python tool that models a simulated network as a directed weighted graph, enumerates realistic attacker routes with Yen's K-shortest loopless paths, and selects up to `k` honeypot locations to maximize distinct attack paths covered. Three placement methods — greedy, betweenness top-k, Simulated Annealing — are compared against each other and against exhaustive optimum on small instances.

## Problem
Given directed weighted graph `G=(V,E,w)`, source `s`, target `t`, candidate path set `P` (from Yen, capped at `m`), eligible honeypot set `Vc`, budget `k`:
maximize `|{ p ∈ P : p ∩ S ≠ ∅ }|` subject to `|S| ≤ k`, `S ⊆ Vc`.
This is **budgeted maximum coverage** (NP-hard in general). Greedy has a `(1−1/e)` worst-case guarantee; SA explores for improvement; exhaustive validates on small instances.

## Pipeline
```
edge list → build graph → BFS reachability → Dijkstra min-cost route
  → Yen K-shortest loopless paths (≤ m) → betweenness centrality
  → greedy → SA (init at greedy, best-so-far) → exhaustive (small only)
  → console tables + optional plot
```

## Algorithm stack
| Algorithm | Role | Mandatory |
|---|---|---|
| NetworkX directed weighted graph | Representation | yes |
| BFS | Reachability pre-check | yes |
| Dijkstra | Min-cost route; cross-check vs Yen's first path (compare cost, not identity) | yes |
| Yen K-shortest loopless | Candidate set `P` | yes |
| Betweenness centrality | Structural analysis + top-k baseline placement | yes |
| Greedy marginal coverage | Primary baseline | yes |
| Simulated Annealing | Metaheuristic improvement | yes |
| Exhaustive search | Exact optimum on small instances | yes (validation) |
| Matplotlib | Coverage-vs-k plot | optional |

## Definitions
- **Vc** (eligible): default `V \ {s,t}`; benchmarks may shrink it (e.g. routers ineligible).
- **Coverage** `f(S) = |{p ∈ P : p ∩ S ≠ ∅}|`, evaluated by one function in `coverage.py` used by all four methods.
- **"Covered"** = path contains ≥1 selected node. Simplified proxy for detection, not a guarantee.
- **Uncoverable paths:** if `p ∩ Vc = ∅`, coverage for `p` is 0; report count and coverage upper bound `r − |uncoverable|`.

## Benchmarks
**A — ~15-node corporate network.** Gateway→firewall→DMZ→switches→app/DB with side branches. Full-pipeline validation. Greedy may already be optimal here (valid result).

**B — 11-node greedy-failure graph.** All weights = 1. `Vc = {A,B,C}`. Ineligible: `q₁,q₂,r₁,r₂,r₃,r₄`. Endpoints: `s,t`.
Edges: `s→A, s→q₁, s→q₂, A→r₁, A→r₂, A→r₃, A→r₄, r₁→B, r₂→B, r₃→C, r₄→C, q₁→B, q₂→C, B→t, C→t`.
Paths (m≥6):
`p₁=s→A→r₁→B→t`, `p₂=s→A→r₂→B→t`, `p₃=s→A→r₃→C→t`, `p₄=s→A→r₄→C→t`, `p₅=s→q₁→B→t`, `p₆=s→q₂→C→t`.
Incidence: `A→{1,2,3,4}`, `B→{1,2,5}`, `C→{3,4,6}`.
Expected at `k=2`: greedy = 5, optimal `{B,C}` = 6, SA must reach 6.

**C — seeded random graph.** 30–50 nodes, `m∈[30,100]`, `k∈[3,5]`. Scan seeds; disclose the selected seed; report how often greedy was already optimal across all scanned seeds.

## Build order
**CORE (rubric-complete at end of step 4):**
1. `graph_builder`, `reachability`, `shortest_path`, `candidate_paths`
2. `models`, `coverage`, `greedy`, `exhaustive` + their tests
3. `annealing` + `benchmark_b` + `test_benchmark_b`
4. `experiments` + `report` (Experiments A, B)

**EXTENDED (only after core passes):**
5. `centrality` + betweenness baseline + Experiment F overlap
6. `plots` + budget sweep (Experiment C)
7. SA seed stability (Experiment E)
8. `benchmark_c` seed scan

## Run
```
python main.py --benchmark A --k 3 --m 20
python main.py --benchmark B --k 2 --m 6
pytest tests/ -q
```

## Limitations (one line each)
- Topology, weights, paths are simulated.
- Only first `m` shortest loopless paths considered.
- Cheapest path ≠ most dangerous path.
- Path covered ≠ attacker detected.
- Static, non-adaptive attacker.
- Greedy `(1−1/e)` approximation; may already be optimal.
- SA improvement is empirical, not guaranteed.
- Exhaustive only on small instances.
- Benchmark C is seed-selected to illustrate a difference.