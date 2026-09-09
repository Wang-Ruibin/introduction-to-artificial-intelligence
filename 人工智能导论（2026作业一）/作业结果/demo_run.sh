#!/usr/bin/env bash
# Live terminal demo for real run screenshots: build, tests, all solvers, validation.
set -e
cd "$(dirname "$0")"
PY=~/.venvs/introduction-to-artificial-intelligence/bin/python

echo "=== [1/5] build + unit tests ================================="
make
make test

echo
echo "=== [2/5] GA (C++) on berlin8 / berlin52 / pr76 ============="
for inst in berlin8 berlin52 pr76; do
  ./build/tsp_metaheuristics "../$inst.tsp" ga "/tmp/shot_${inst}_ga.json" 15
done

echo
echo "=== [3/5] ACO (C++) on berlin8 / berlin52 / pr76 ============="
for inst in berlin8 berlin52 pr76; do
  ./build/tsp_metaheuristics "../$inst.tsp" aco "/tmp/shot_${inst}_aco.json" 15
done

echo
echo "=== [4/5] OR-Tools CP-SAT (Python) ==========================="
$PY - <<'PYEOF'
import sys
sys.path.insert(0, "src")
from ortools_solver import solve_ortools_cpsat
from tsp_utils import distance_matrix, load_tsplib

for name, limit in [("berlin8", 30), ("berlin52", 60), ("pr76", 60)]:
    _, coords = load_tsplib(f"../{name}.tsp")
    r = solve_ortools_cpsat(distance_matrix(coords), limit)
    proven = r.parameters["proven_optimal"]
    print(f"{name} / CP-SAT: distance={r.distance}, runtime={r.runtime_seconds:.2f}s, "
          f"proven_optimal={proven}")
PYEOF

echo
echo "=== [5/5] validate all results ==============================="
$PY src/validate_results.py

echo
echo "=== demo finished ============================================"
