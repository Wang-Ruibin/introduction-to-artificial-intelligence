"""OR-Tools solvers for Assignment 1 (routing + GLS, and CP-SAT circuit model)."""
from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from ortools.sat.python import cp_model

from tsp_utils import canonical_tour, tour_length


@dataclass
class SolverResult:
    algorithm: str
    language: str
    tour: list[int]
    distance: int
    runtime_seconds: float
    progress: list[dict[str, float | int]]
    parameters: dict[str, int | float | str]


def solve_ortools_routing(distances: np.ndarray, time_limit_seconds: int = 20) -> SolverResult:
    """Routing model with PATH_CHEAPEST_ARC + GUIDED_LOCAL_SEARCH."""
    start = time.perf_counter()
    manager = pywrapcp.RoutingIndexManager(len(distances), 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index: int, to_index: int) -> int:
        return int(distances[manager.IndexToNode(from_index), manager.IndexToNode(to_index)])

    callback = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(callback)
    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    params.time_limit.FromSeconds(time_limit_seconds)
    progress: list[dict[str, float | int]] = []
    best = float("inf")

    def record() -> None:
        nonlocal best
        value = int(routing.CostVar().Value())
        if value < best:
            best = value
            progress.append({"step": len(progress), "distance": value,
                             "time_seconds": time.perf_counter() - start})

    routing.AddAtSolutionCallback(record)
    solution = routing.SolveWithParameters(params)
    if solution is None:
        raise RuntimeError("OR-Tools routing did not return a solution")
    tour: list[int] = []
    index = routing.Start(0)
    while not routing.IsEnd(index):
        tour.append(manager.IndexToNode(index))
        index = solution.Value(routing.NextVar(index))
    runtime = time.perf_counter() - start
    tour = canonical_tour(tour)
    return SolverResult("OR-Tools", "Python", tour, tour_length(tour, distances), runtime, progress,
                        {"model": "routing + GUIDED_LOCAL_SEARCH", "time_limit_seconds": time_limit_seconds,
                         "strategy": "PATH_CHEAPEST_ARC"})


def solve_ortools_cpsat(distances: np.ndarray, time_limit_seconds: int = 300) -> SolverResult:
    """CP-SAT AddCircuit formulation of the symmetric TSP.

    Every undirected edge {i, j} gets two boolean arc variables; AddCircuit
    enforces one Hamiltonian cycle and the objective is the EUC_2D length.
    """
    start = time.perf_counter()
    n = len(distances)
    model = cp_model.CpModel()
    arcs: list[tuple[int, int, cp_model.IntVar]] = []
    successor_vars: dict[int, tuple[int, int, cp_model.IntVar, cp_model.IntVar]] = {}
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
            successor_vars[(i, j)] = (i, j, forward, backward)
    model.AddCircuit(arcs)
    model.Minimize(sum(cost_terms))
    progress: list[dict[str, float | int]] = []

    class Recorder(cp_model.CpSolverSolutionCallback):
        def on_solution_callback(self) -> None:
            value = int(self.ObjectiveValue())
            if not progress or value < progress[-1]["distance"]:
                progress.append({"step": len(progress), "distance": value,
                                 "time_seconds": time.perf_counter() - start})

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit_seconds)
    solver.parameters.num_workers = 8
    status = solver.Solve(model, Recorder())
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(f"CP-SAT returned {solver.StatusName(status)}")
    successor: list[int] = [-1] * n
    for i, j, forward, backward in successor_vars.values():
        if solver.Value(forward):
            successor[i] = j
        elif solver.Value(backward):
            successor[j] = i
    tour = [0]
    while successor[tour[-1]] != 0:
        tour.append(successor[tour[-1]])
    runtime = time.perf_counter() - start
    tour = canonical_tour(tour)
    return SolverResult("OR-Tools", "Python", tour, tour_length(tour, distances), runtime, progress,
                        {"model": "CP-SAT AddCircuit", "time_limit_seconds": time_limit_seconds,
                         "status": solver.StatusName(status),
                         "proven_optimal": status == cp_model.OPTIMAL})


def solve_ortools(distances: np.ndarray, time_limit_seconds: int = 20, model: str = "routing") -> SolverResult:
    if model == "cpsat":
        return solve_ortools_cpsat(distances, time_limit_seconds)
    return solve_ortools_routing(distances, time_limit_seconds)
