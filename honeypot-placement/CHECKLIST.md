# Build Checklist

## STATE
- last_done: Phase 1 P0 correctness re-applied
- next: Phase 3 experiments regeneration
- blockers: none

## Project constants
- A: 15 nodes, 25 edges, weights 1-5 (traversal cost)
- B: 11 nodes, 15 edges, unit weight
- C: 17 nodes, 36 edges, Precinct6 hybrid (real hosts + synthetic bypass)
- SA params: T0=1.5, alpha=0.99, L=10, iters=3000
- Tests: 90

## Done
- [x] P0.1 zero-budget combination count (C(n,0)=1)
- [x] P0.2 RuntimeError replaces assert (Dijkstra-Yen cost check)
- [x] P0.3 SA parameter validation (_validate_sa_params)
- [x] P0.4 traversal-cost terminology
- [x] P0.5 dual coverage metrics (total + coverable)
- [x] P0.6 graph weight validation (NaN, inf, non-numeric, bool, negative)
- [x] P0.7 unknown-benchmark message lists A, B, C
- [x] README Benchmark C hybrid description
- [x] P1.6 Benchmark C (Precinct6 hybrid)
- [x] P1.9 exact-search validation
- [x] P1.10 standardized reporting
- [x] Experiment scripts: experiment_seeds.py, experiment_sweep.py
- [x] 30-seed B/C results
- [x] Budget sweep B/C results

## Remaining
- [ ] P2.1 consolidate benchmark loader (delete _load in experiments.py, call graph_builder.load_benchmark)
- [ ] P2.2 arg validation in experiment scripts (--seeds >=1, --kmax >=0)
- [ ] P2.3 regenerate all results from current code
- [ ] P2.4 clean .gitignore + submission ZIP
- [ ] P2.5 fresh-extract verification

## Excluded (not my scope)
- GUI — partner
- Report writing — separate task