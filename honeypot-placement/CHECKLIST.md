# Build Checklist — single source of truth

> **Agent protocol:** Read STATE. Find the first task not marked `[x]`. Do only that task. Mark done. Update STATE.

## STATE
- last_done: P0 Phase 1 (pending completion)
- next: Phase 2, Task 6 (multi-seed SA)
- blockers: none

## Project constants (verify against code)
- Benchmark A: 15 nodes, 25 edges, weights = simulated traversal cost
- Benchmark B: 11 nodes, **15 edges**, unit weight
- Benchmark C: 17 nodes, 36 edges, Precinct6 hybrid (real hosts, synthetic bypass)
- SA params: T0=1.5, alpha=0.99, L=10, iters=3000, seed=42
- Tests: 82+ passing

## Phase 1 — P0 correctness

- [ ] T1.1 README Benchmark C description updated (no "random graph" references)
- [ ] T1.2 CHECKLIST.md consolidated (this file)
- [ ] T1.3 Graph weight validation (NaN, inf, non-numeric, negative) + tests
- [ ] T1.4 `src/experiments.py`: unknown-benchmark message includes C, remove dup `comb` import, fix indentation
- [ ] T1.5 pytest: 82+ green

## Phase 2 — P1 experiments

- [ ] T2.6 Multi-seed SA on B (30 seeds) -> results/B_seeds.txt
- [ ] T2.7 Budget sweep on B and C (k=0..5) -> results/B_sweep.txt, results/C_sweep.txt
- [ ] T2.8 Benchmark C stress (m=20, k=1,2) -> results/C_stress.txt
- [ ] T2.9 Regenerate A_baseline, B_baseline, C_baseline

## Phase 3 — Report (external)

- [ ] T3.10-15 Report sections (§2, §3, §6, §8, §9, §11)

## Phase 4 — Submit

- [ ] T4.16 Clean ZIP (exclude .git, .venv, __pycache__, .pytest_cache)
- [ ] T4.17 Fresh venv verification

## Done (history, keep for reference)

- [x] P0.1 zero-budget combination count (C(n,0)=1)
- [x] P0.2 RuntimeError replaces bare assert in Dijkstra-Yen check
- [x] P0.3 SA parameter validation (_validate_sa_params)
- [x] P0.4 traversal-cost terminology (Benchmarks A and B)
- [x] P0.5 dual coverage metrics (total + coverable)
- [x] P1.6 Benchmark C — Precinct6 hybrid
- [x] P1.9 exact-search validation
- [x] P1.10 standardized reporting