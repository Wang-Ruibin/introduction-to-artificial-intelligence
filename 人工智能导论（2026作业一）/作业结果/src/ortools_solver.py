"""Python OR-Tools implementation for Assignment 1."""
from __future__ import annotations
import time
from dataclasses import dataclass
import numpy as np
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
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

def solve_ortools(distances: np.ndarray, time_limit_seconds: int = 20) -> SolverResult:
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
    params.time_limit.seconds = time_limit_seconds
    progress: list[dict[str, float | int]] = []
    best = float("inf")
    def record() -> None:
        nonlocal best
        value = int(routing.CostVar().Value())
        if value < best:
            best = value
            progress.append({"step": len(progress), "distance": value, "time_seconds": time.perf_counter() - start})
    routing.AddAtSolutionCallback(record)
    solution = routing.SolveWithParameters(params)
    if solution is None:
        raise RuntimeError("OR-Tools did not return a solution")
    tour: list[int] = []
    index = routing.Start(0)
    while not routing.IsEnd(index):
        tour.append(manager.IndexToNode(index))
        index = solution.Value(routing.NextVar(index))
    runtime = time.perf_counter() - start
    tour = canonical_tour(tour)
    return SolverResult("OR-Tools", "Python", tour, tour_length(tour, distances), runtime, progress,
        {"time_limit_seconds": time_limit_seconds, "strategy": "PATH_CHEAPEST_ARC + GUIDED_LOCAL_SEARCH"})
