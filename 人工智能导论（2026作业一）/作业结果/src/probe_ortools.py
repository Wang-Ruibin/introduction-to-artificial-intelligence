"""Probe OR-Tools configurations for pr76: which reaches the optimum 108159?

Usage: probe_ortools.py <seconds> <gls|tabu|sa|cpsat> [instance]
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ortools_solver import SolverResult, solve_ortools
from tsp_utils import distance_matrix, load_tsplib

HERE = Path(__file__).resolve().parent
ASSIGNMENT = HERE.parent.parent


def run_routing(distances, seconds: int, meta: str) -> None:
    from ortools.constraint_solver import pywrapcp, routing_enums_pb2
    import numpy as np

    start = time.perf_counter()
    manager = pywrapcp.RoutingIndexManager(len(distances), 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def cb(i, j):
        return int(distances[manager.IndexToNode(i), manager.IndexToNode(j)])

    transit = routing.RegisterTransitCallback(cb)
    routing.SetArcCostEvaluatorOfAllVehicles(transit)
    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    params.local_search_metaheuristic = {
        "gls": routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH,
        "tabu": routing_enums_pb2.LocalSearchMetaheuristic.TABU_SEARCH,
        "sa": routing_enums_pb2.LocalSearchMetaheuristic.SIMULATED_ANNEALING,
    }[meta]
    params.time_limit.FromSeconds(seconds)

    progress = []
    best = float("inf")

    def record():
        nonlocal best
        value = int(routing.CostVar().Value())
        if value < best:
            best = value
            progress.append((value, time.perf_counter() - start))

    routing.AddAtSolutionCallback(record)
    solution = routing.SolveWithParameters(params)
    if solution is None:
        print("no solution")
        return
    print(f"[{meta}] final={best} runtime={time.perf_counter()-start:.0f}s")
    target = 108159
    hit = [p for p in progress if p[0] <= target]
    print(f"[{meta}] reached {target} at {hit[0][1]:.1f}s" if hit else f"[{meta}] did NOT reach {target}")
    for value, t in progress[-6:]:
        print(f"  t={t:7.1f}s  d={value}")


def run_cpsat(distances, seconds: int) -> None:
    from ortools.sat.python import cp_model
    import numpy as np

    n = len(distances)
    start = time.perf_counter()
    model = cp_model.CpModel()
    arcs = []
    cost_terms = []
    for i in range(n):
        for j in range(i + 1, n):
            forward = model.NewBoolVar(f"x_{i}_{j}")
            backward = model.NewBoolVar(f"x_{j}_{i}")
            arcs.append((i, j, forward))
            arcs.append((j, i, backward))
            cost = int(distances[i, j])
            cost_terms.append(cost * forward)
            cost_terms.append(cost * backward)
    model.AddCircuit(arcs)
    model.Minimize(sum(cost_terms))
    improvements = []

    class Recorder(cp_model.CpSolverSolutionCallback):
        def on_solution_callback(self):
            improvements.append((self.ObjectiveValue(), time.perf_counter() - start))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(seconds)
    solver.parameters.num_workers = 8
    status = solver.Solve(model, Recorder())
    print(f"[cpsat] status={solver.StatusName(status)} objective={solver.ObjectiveValue():.0f} "
          f"bound={solver.BestObjectiveBound():.0f} time={time.perf_counter()-start:.0f}s")
    for value, t in improvements[-8:]:
        print(f"  t={t:7.1f}s  d={value:.0f}")
    target = 108159 if n == 76 else (7542 if n == 52 else 2551)
    hit = [p for p in improvements if p[0] <= target]
    print(f"[cpsat] reached {target} at {hit[0][1]:.1f}s" if hit else f"[cpsat] did NOT reach {target}")


def main() -> None:
    seconds = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    mode = sys.argv[2] if len(sys.argv) > 2 else "gls"
    instance = sys.argv[3] if len(sys.argv) > 3 else "pr76"
    _, coords = load_tsplib(ASSIGNMENT / f"{instance}.tsp")
    dist = distance_matrix(coords)
    if mode == "cpsat":
        run_cpsat(dist, seconds)
    else:
        run_routing(dist, seconds, mode)


if __name__ == "__main__":
    main()
