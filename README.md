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

**C — real Precinct6 hybrid.** 17 hosts, 36 edges. Host IPs, hostnames, role annotations, and the 16-hop chain come from 100 real WitFoo Precinct6 incidents merged by IP. Bypass edges (skip-1 and skip-3 forward) are **synthesized** to create multiple distinct routes — without them the merged graph is hub-and-spoke and has no multi-path structure to optimize over. Chain-edge weight = 1.0; synthetic bypass weight = 2.5–4.0 (higher cost models a costlier alternate pivot). Greedy is already optimal on this graph at most budgets; betweenness covers only 75% of the 100 candidate paths at `k=2` — the headline finding for Benchmark C. See §3.4 of the report for the full observed-vs-synthetic disclosure.

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
## Dashboard (Streamlit)

A dark-themed interactive dashboard that exposes everything the backend computes.

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Run it from the project root. Sidebar sections: Overview, Network Topology, Attack Path Analysis,
Centrality Analysis, Greedy Algorithm, Simulated Annealing, Exhaustive Search, Algorithm Comparison,
Generated Results, Experiment Runner, Precinct6 Dataset.

* All numbers come from `src.experiments.run_experiment()` - the UI re-implements no algorithm.
* The **Experiment Runner** changes benchmark, `k`, `m`, seed and the SA parameters (T0, alpha, L, iterations);
  identical settings are cached. Optional PNG generation writes to `results/dashboard_runs/<settings>/`
  and never overwrites the figures already in `results/`.
* Layout: `app.py` (entry), `ui/` (theme, data layer, network view, tabs), `.streamlit/config.toml` (theme).
* Additive backend hooks used by the dashboard (all backward compatible, CLI unchanged):
  `run_experiment(..., sa_params=None)` plus extra result keys (`G`, `paths`, `index`, `greedy_trace`,
  `sa_history`), `greedy_placement_with_trace`, `simulated_annealing_with_history`, `covered_ids`,
  and `visualize.generate_figures` (now also supports Benchmark C).
* Tests: `python -m pytest tests/ -v` (dashboard smoke tests are skipped if Streamlit is not installed).

