---

## How to Run

### Setup (once)

```powershell
# Python 3.10+
python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### Run a benchmark (CLI)

```powershell
# Benchmark A — 15-node corporate network (dense, greedy-optimal)
python main.py --benchmark A --k 3 --m 20 --seed 42

# Benchmark B — 11-node greedy trap (SA beats greedy 5 -> 6)
python main.py --benchmark B --k 2 --m 20 --seed 42

# Benchmark C — 17-node real Precinct6 hybrid (100 paths, betweenness fails at 75%)
python main.py --benchmark C --k 2 --m 100 --seed 42
```

**Arguments:**

| Flag | Description | Default |
|---|---|---|
| `--benchmark`, `-b` | `A`, `B`, or `C` | `B` |
| `--k` | Honeypot budget (how many to place) | 3 |
| `--m` | Max candidate paths (Yen cap) | 20 |
| `--seed` | SA random seed (reproducibility) | 42 |

**Output:** console table comparing Greedy, Betweenness, SA, and Exhaustive — with coverage, coverage %, runtime, iterations, and gap-to-optimum.

### Run the test suite

```powershell
python -m pytest tests/ -v
```

**Expected:** 82 tests passing.

### Generate figures

```powershell
python visualize.py --benchmark all
```

Produces 6 PNGs in `results/`:

| File | Content |
|---|---|
| `benchmark_a_network.png` | Network topology (roles + weights) |
| `benchmark_a_paths.png` | Candidate paths, one panel per route |
| `benchmark_a_comparison.png` | Greedy / Betweenness / SA / Exhaustive side-by-side |
| `benchmark_b_network.png` | The 11-node trap graph |
| `benchmark_b_paths.png` | The 6 trap paths |
| `benchmark_b_comparison.png` | **The money shot** — visual proof of the greedy trap |
| `benchmark_c_*.png` | Same for the real Precinct6 hybrid |

### Where the data lives

```
data/
├── precinct6_merged.graphml     # 648 hosts, 1340 edges (raw merged incidents)
└── precinct6_hybrid.graphml     # 17 hosts, 36 edges (benchmark C)
```

Regenerate both from scratch if needed:

```powershell
python scripts/fetch_precinct6.py       # download + merge 100 incidents
python scripts/build_hybrid_c.py        # extract 17-node chain + bypass edges
```

### Reference outputs (for report / viva)

Run these once, save to `results/`:

```powershell
New-Item -ItemType Directory -Force -Path results | Out-Null

python main.py --benchmark A --k 3 --m 20  --seed 42 | Tee-Object results/A_baseline.txt
python main.py --benchmark B --k 2 --m 20  --seed 42 | Tee-Object results/B_baseline.txt
python main.py --benchmark C --k 2 --m 100 --seed 42 | Tee-Object results/C_baseline.txt

# Budget sweep on C
1..5 | ForEach-Object { python main.py --benchmark C --k $_ --m 100 --seed 42 } | Tee-Object results/C_sweep.txt

# Seed stability on C
1..10 | ForEach-Object { python main.py --benchmark C --k 2 --m 100 --seed $_ } | Tee-Object results/C_seeds.txt
```

---

## For the GUI partner

### What the GUI will display

The GUI consumes the same data structures the CLI produces. Nothing new to compute.

### Contract to build against

Every placement method returns the same object:

```python
from src.models import PlacementResult

# PlacementResult fields:
#   nodes      : frozenset[str]      — chosen honeypot hosts
#   covered    : int                 — number of paths covered
#   total_paths: int                 — total candidate paths (for %)
#   runtime_s  : float               — wall-clock seconds
#   iterations : int                 — 0 for non-iterative methods (SA uses it)
```

### Entry points to call

| Function | Purpose | Returns |
|---|---|---|
| `src.experiments.run_experiment(name, k, m, seed)` | Full pipeline on one benchmark | `dict` with all 4 placements + metadata |
| `src.graph_builder.load_benchmark("A"\|"B"\|"C")` | Load a graph | `(nx.DiGraph, s, t)` |
| `src.candidate_paths.enumerate_paths(G, s, t, m)` | Yen path set | `list[list[str]]` |
| `src.coverage.build_index(paths, eligible)` | Precomputed node→path-idx | `dict[str, frozenset[int]]` |
| `src.coverage.coverage(S, index)` | Objective — **the only place this is computed** | `int` |
| `src.greedy.greedy_placement(index, n_paths, k)` | Greedy baseline | `PlacementResult` |
| `src.centrality.betweenness(G, eligible)` + `betweenness_placement(...)` | Centrality baseline | `dict` + `PlacementResult` |
| `src.annealing.simulated_annealing(index, n_paths, k, init, T0, alpha, L, iters, seed)` | SA optimization | `PlacementResult` |
| `src.exhaustive.exhaustive_search(index, n_paths, k)` | Exact optimum (small instances) | `PlacementResult` |

### Example: one call gets you everything

```python
from src.experiments import run_experiment

r = run_experiment("B", k=2, m=20, seed=42)
# r["greedy"]      -> PlacementResult
# r["betweenness"] -> PlacementResult
# r["sa"]          -> PlacementResult
# r["exhaustive"]  -> PlacementResult or None (if too many combos)
# r["paths"]       -> list[list[str]]      (the candidate attack paths)
# r["index"]       -> dict[str, frozenset[int]]
# r["G"], r["s"], r["t"], r["eligible"]
```

### Runnable app (already written, if you want to extend it)

```powershell
pip install streamlit plotly
streamlit run app.py
```

Six tabs: Network → Paths → Centrality → Greedy → SA → Compare. Extend or replace as you like — the backend is just `run_experiment()`.

### Rules the GUI must honour (contract)

1. **Do not re-implement coverage** — always import `src.coverage.coverage`
2. **Do not re-implement any placement algorithm** — call the module functions
3. **Only `src/report.py` prints** — GUI should use its own display logic, not `report.py`
4. **SA seeds are explicit** — pass `seed=` argument, never `random.seed()`
5. **Ties broken deterministically** — use `src.coverage.sorted_tiebreak`

---

## Project structure

```
honeypot-placement/
├── main.py                      # CLI entry
├── visualize.py                 # Static figure generator
├── app.py                       # Streamlit GUI (partner's territory)
├── config.py                    # SA parameters + defaults
├── requirements.txt
├── README.md                    # this file
├── CHECKLIST.md
│
├── benchmarks/                  # A (corporate), B (trap), C (real Precinct6)
├── data/                        # Precinct6 GraphML (merged + hybrid)
├── scripts/                     # fetch_precinct6.py, build_hybrid_c.py
├── src/                         # algorithms + pipeline
├── tests/                       # 82 pytest tests
└── results/                     # generated outputs (gitignored)
```

**Import direction is one-way:** `models ← coverage ← greedy/annealing/exhaustive ← experiments ← main`. Nothing imports upward. The GUI sits above `experiments` and imports only from `src.*`.
