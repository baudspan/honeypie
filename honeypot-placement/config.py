"""Central defaults for the pipeline. Change here, not in modules."""

# Path enumeration
DEFAULT_M = 20

# Honeypot budget
DEFAULT_K = 3

# Simulated Annealing (used in step 3 — locked here so later steps just import)
SA_T0 = 1.5
SA_ALPHA = 0.99
SA_L = 10
SA_ITERS = 3000
SA_SEED = 42