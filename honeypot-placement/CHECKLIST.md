# Build Checklist — single source of truth

> **Agent protocol (read before doing anything):**
> 1. Read `README.md`, then this file top to bottom.
> 2. Read the locked contracts in the "Contracts (do not alter)" section below.
> 3. Find the first unchecked task. Do **only that task**. Mark `[x]` and update `STATE`.
> 4. Do not re-scaffold files that already exist. Do not re-lock signatures.
> 5. Do not proceed past a checkpoint (`⛳`) until its verify command passes.
> 6. If a task is ambiguous, pick the simplest option, add `# ASSUMPTION:` in the touched file, and note it in the ASSUMPTIONS section here. Do not ask.

## STATE
- last_done: P0.5 (coverage metrics)
- next: P1.6 (Benchmark C — Precinct6 loader)
- blockers: none

## DONE THIS SESSION
- [x] P0.1 zero-budget combination count
- [x] P0.2 RuntimeError replaces assert
- [x] P0.3 SA parameter validation
- [x] P0.4 traversal-cost terminology (A + B)
- [x] P0.5 dual coverage metrics (total vs coverable)

## REMAINING
- [ ] P1.6 Benchmark C from Precinct6 GraphML
- [ ] P1.7 multi-seed stability on C
- [ ] P1.8 budget sweep on C
- [ ] P2.11 update README + CHECKLIST (14→15 edges, α 0.97→0.99)
- [ ] P3.17 GUI (partner)

## STATE
- last_done: P2.12 (documentation audit)
- next: report writing
- blockers: none

## DONE
- [x] P0.1 zero-budget combination count (returns 1 for k=0)
- [x] P0.2 RuntimeError replaces assert (survives python -O)
- [x] P0.3 SA parameter validation (T0, alpha, L, iters)
- [x] P0.4 traversal-cost terminology (A, B, README)
- [x] P0.5 dual coverage metrics (total + coverable)
- [x] P1.6 Benchmark C — real Precinct6 hybrid (17 hosts, 100 paths)
- [x] P2.11 CHECKLIST updated
- [x] P2.12 README updated
- [x] P2.13 NaN/infinity rejected in graph_builder
- [x] P2.14 plots.py comparison title uses benchmark name

## REMAINING (report phase — not blocking)
- [ ] Multi-seed stability run
- [ ] Budget sweep run
- [ ] Report writing

## KEY FINDINGS (for report)
- A: greedy already optimal (286 placements tied with exhaustive)
- B: SA beats greedy 5→6, matches exhaustive optimum
- C: betweenness fails at 75%, greedy/SA/exhaustive all hit 100%

## Contracts (do not alter once written)
Signatures in `src/models.py` and `src/coverage.py` are frozen. See the "Contracts to lock" block in the file-structure doc. No agent may change:
- `PlacementResult(nodes, covered, total_paths, runtime_s, iterations=0)`
- `build_index(paths, eligible) -> dict[node, frozenset[int]]`
- `coverage(S, index) -> int`
- Placement function signatures: `greedy_placement`, `betweenness_placement`, `simulated_annealing`, `exhaustive_search` (all take `index`, not the graph).

Rules (non-negotiable):
1. `coverage.py` is the only place the objective is computed.
2. Placement functions take `index`, not `nx.Graph`.
3. Only `report.py` prints.
4. Only `graph_builder`, `candidate_paths`, `centrality`, `reachability`, `shortest_path` touch NetworkX.
5. All randomness via explicit `seed=` arg; no `random.seed()` global calls.
6. Ties broken by sorted node name via one shared helper in `coverage.py`.
7. Imports flow one way: `models ← coverage ← {greedy,annealing,exhaustive} ← experiments ← main`.

## ASSUMPTIONS (append as needed)
- (none yet)

---

## Phase 0 — Scaffold
- [x] T0.1 Directory tree created per file-structure doc.
- [ ] T0.2 `requirements.txt` contains `networkx` and `matplotlib` — done when file exists with both lines.
- [ ] T0.3 `src/__init__.py` empty package marker — done when file exists.
- [ ] T0.4 `.gitignore` excludes `__pycache__/`, `results/`, `.venv/` — done when file exists.

⛳ **Checkpoint 0:** `python -c "import networkx"` succeeds and `pytest` collects 0 tests without error.

---

## Phase 1 — CORE-1: Graph & input
- [ ] T1.1 `src/models.py`: define `PlacementResult` exactly as in Contracts — done when importable, no other contents.
- [ ] T1.2 `src/graph_builder.py`: `load_benchmark(name) -> (nx.DiGraph, s, t)` and `define_eligible(G, s, t, excluded=None) -> set`. Validate: nodes exist, weights ≥ 0, `k ≥ 0` checked at caller. — done when `load_benchmark("A")` and `("B")` return without error and `t` is in `G`.
- [ ] T1.3 `benchmarks/benchmark_a.py`: build ~15-node corporate `nx.DiGraph` with non-negative weights and side branches. — done when `load_benchmark("A")` returns a graph with ≥14 nodes, `s` and `t` present, `t` reachable via any path.
- [ ] T1.4 `benchmarks/benchmark_b.py`: build the exact 11-node graph and 14 edges from README §Benchmarks; set `s="s"`, `t="t"`, `Vc={"A","B","C"}`. — done when the graph has 11 nodes and 14 edges.

⛳ **Checkpoint 1:** `python -c "from benchmarks.benchmark_b import *; G=build(); assert len(G.nodes)==11 and len(G.edges)==14"`

---

## Phase 2 — CORE-2: Reachability & shortest path
- [ ] T2.1 `src/reachability.py`: `is_reachable(G, s, t) -> bool` via BFS. — done when returns `True` for A and B; returns `False` for a graph where `t` is disconnected.
- [ ] T2.2 `src/shortest_path.py`: `min_cost_path(G, s, t) -> (list[node], float)`. — done when for B returns cost = 4 (all weights 1, path length 4 edges).
- [ ] T2.3 Note in module docstring: "Dijkstra result is compared to Yen's first path by **cost**, not path identity." — done when docstring present.

⛳ **Checkpoint 2:** `python -c "from benchmarks.benchmark_b import build; from src.shortest_path import min_cost_path; G=build(); p,c=min_cost_path(G,'s','t'); assert c==4"`

---

## Phase 3 — CORE-3: Yen's paths
- [ ] T3.1 `src/candidate_paths.py`: `enumerate_paths(G, s, t, m) -> list[list[node]]` via `nx.shortest_simple_paths`, capped at `m`; handles `m` larger than available. — done when B with `m≥6` returns exactly 6 paths and their node sets match the README incidence.
- [ ] T3.2 `count_uncoverable(paths, eligible) -> int` and `coverage_upper_bound(paths, eligible) -> int`. — done when B returns `uncoverable=0`, `upper_bound=6`.
- [ ] T3.3 Raise a clear exception if `m == 0` or `paths` is empty. — done when `enumerate_paths(G,'t','s',5)` raises `ValueError` or `NetworkXNoPath` with a readable message.

⛳ **Checkpoint 3:** `pytest tests/test_benchmark_b.py::test_incidence -q` passes (write the test first if missing).

---

## Phase 4 — CORE-4: Coverage (single source of truth)
- [ ] T4.1 `src/coverage.py`: `build_index(paths, eligible) -> dict[node, frozenset[int]]` — done when B gives `A→{1,2,3,4}`, `B→{1,2,5}`, `C→{3,4,6}` (0-based or 1-based consistently; document choice in docstring).
- [ ] T4.2 `coverage(S, index) -> int` = size of union of path-id sets. — done when `coverage({"B","C"}, idx)==6` and `coverage({"A"}, idx)==4` for B.
- [ ] T4.3 Shared tie-break helper `sorted_tiebreak(nodes) -> node`. — done when deterministic.

⛳ **Checkpoint 4:** `pytest tests/test_coverage.py tests/test_benchmark_b.py::test_incidence -q` passes.

---

## Phase 5 — CORE-5: Greedy + exhaustive
- [ ] T5.1 `src/greedy.py`: `greedy_placement(index, n_paths, k) -> PlacementResult` per §5.1. Records `runtime_s` with `time.perf_counter()`. — done when B, k=2 returns `covered=5` and `nodes` has size 2.
- [ ] T5.2 `src/exhaustive.py`: `exhaustive_search(index, n_paths, k) -> PlacementResult` — enumerate `itertools.combinations` of size `min(k, len(Vc))`. — done when B, k=2 returns `covered=6`.
- [ ] T5.3 Test `test_greedy ≤ exhaustive` on B. — done when `pytest tests/test_greedy.py tests/test_exhaustive.py -q` passes.

⛳ **Checkpoint 5:** `pytest tests/test_greedy.py tests/test_exhaustive.py -q` green.

---

## Phase 6 — CORE-6: Simulated Annealing
- [ ] T6.1 `src/annealing.py`: `simulated_annealing(index, n_paths, k, init, T0, alpha, L, iters, seed) -> PlacementResult`. Implement: early exits, padding, single-swap neighbour, `Δ = f(new) − f(cur)`, accept `Δ≥0` else `exp(Δ/T)` with `Δ<0`, geometric cooling every `L` iters, **best-so-far**, record iteration count. — done when B, k=2, `init=greedy` returns `covered=6`.
- [ ] T6.2 Early-exit cases (k=0, Vc empty, k≥|Vc|, greedy already covers upper bound) return `init` with `iterations=0`. — done when unit test covers each.
- [ ] T6.3 Parameter defaults in `config.py`: `T0=1.5, alpha=0.97, L=10, iters=3000`. — done when present.
- [ ] T6.4 Log early acceptance rate; assert it falls in `[0.30, 0.60]` on B run with seed=42 — done when test passes; tune T0 if outside range and record in ASSUMPTIONS.

⛳ **Checkpoint 6:** `pytest tests/test_annealing.py tests/test_benchmark_b.py -q` green; `test_benchmark_b.py` asserts both incidence AND `greedy=5, SA=6, exhaustive=6`.

---

## Phase 7 — CORE-7: Experiments A/B + report
- [ ] T7.1 `src/experiments.py`: `run_experiment_A(G, s, t, Vc, k, m) -> dict` and `run_experiment_B() -> dict` returning structured results (no printing). — done when both callable and return the expected keys.
- [ ] T7.2 `src/report.py`: format Experiment A and B output (paths+costs, min route, Vc, per-method placement/coverage/runtime/iterations, gap to optimum). — done when `format_experiment_A(result)` and `_B(result)` return strings.
- [ ] T7.3 `main.py`: argparse `--benchmark {A,B} --k --m`; wires loader → pipeline → report. — done when `python main.py --benchmark B --k 2 --m 6` prints the comparison table and exits 0.

⛳ **Checkpoint 7 (CORE COMPLETE — rubric satisfied):** `python main.py --benchmark B --k 2 --m 6` shows greedy=5, SA=6, exhaustive=6 and gap=0 for SA.

---

## Phase 8 — EXTENDED-1: Betweenness baseline
- [ ] T8.1 `src/centrality.py`: `betweenness(G, Vc) -> dict[node,float]` and `betweenness_placement(bc, index, n_paths, k) -> PlacementResult` (top-k by bc, tie-break sorted name, evaluated with shared `coverage`). — done when callable, returns `PlacementResult`.
- [ ] T8.2 `overlap(a, b) -> int` helper. — done when returns size of intersection.
- [ ] T8.3 Experiment F in `experiments.py` + report section. — done when report prints betweenness set, coverage, and overlap with greedy/SA.

⛳ **Checkpoint 8:** `python main.py --benchmark A --k 3 --m 20 --with-betweenness` runs, prints F output.

---

## Phase 9 — EXTENDED-2: Budget sweep
- [ ] T9.1 `experiments.py::run_experiment_C(benchmark, k_range)` returning table `{method: {k: covered}}`. — done when callable.
- [ ] T9.2 `src/plots.py`: `plot_budget_sweep(table, out_path)`; graceful skip if matplotlib missing. — done when produces `results/budget_sweep.png` (or prints a skip message).

⛳ **Checkpoint 9:** `python main.py --benchmark A --sweep 1 5` produces the table and (optionally) the plot.

---

## Phase 10 — EXTENDED-3: SA stability
- [ ] T10.1 `experiments.py::run_experiment_E(benchmark, k, seeds=range(10))` reports best/mean/std of `covered`. — done when callable; results saved.

⛳ **Checkpoint 10:** `python main.py --benchmark B --stability` prints best/mean/std.

---

## Phase 11 — EXTENDED-4: Benchmark C
- [ ] T11.1 `benchmarks/benchmark_c.py`: seeded random `DiGraph`, `n∈[30,50]`, non-negative weights, layered or Erdős–Rényi. Exposes `build(seed)`.
- [ ] T11.2 Seed scan: loop seeds, keep the first where `greedy < exhaustive`; report selected seed AND frequency of greedy-optimal across all scanned seeds. — done when `experiments.py::run_benchmark_c_scan()` prints both.
- [ ] T11.3 Note in report: "Benchmark C instance is seed-selected; the reported greedy-optimal frequency is the honest base rate."

⛳ **Checkpoint 11:** `python main.py --benchmark C --scan-seeds 100` runs to completion and prints scan disclosure.

---

## Phase 12 — Wrap
- [ ] T12.1 Freeze `requirements.txt` to installed versions.
- [ ] T12.2 `results/` snapshot of final Experiment A–F outputs committed (or ignored per `.gitignore`).
- [ ] T12.3 `pytest tests/ -q` green from clean checkout.
- [ ] T12.4 Update `STATE`: `next: DONE`; `blockers: none`.

⛳ **Final gate:** all checkpoints 0–11 passed; `main.py` runs all benchmarks with `--help` describing every flag.