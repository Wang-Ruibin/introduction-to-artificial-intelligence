"""TSPLIB parsing and shared TSP utilities."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np


def load_tsplib(path: Path) -> tuple[str, np.ndarray]:
    """Read a 2D TSPLIB instance and return its name and coordinates."""
    name = path.stem
    coordinates: list[tuple[float, float]] = []
    in_coordinates = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("NAME"):
            _, value = line.replace(":", " ", 1).split(maxsplit=1)
            name = value.strip()
        elif line == "NODE_COORD_SECTION":
            in_coordinates = True
        elif line == "EOF":
            break
        elif in_coordinates:
            fields = line.split()
            coordinates.append((float(fields[1]), float(fields[2])))
    if not coordinates:
        raise ValueError(f"No NODE_COORD_SECTION found in {path}")
    return name, np.asarray(coordinates, dtype=float)


def distance_matrix(coordinates: np.ndarray) -> np.ndarray:
    """Build the TSPLIB EUC_2D matrix: nint(sqrt(dx^2 + dy^2))."""
    delta = coordinates[:, None, :] - coordinates[None, :, :]
    euclidean = np.sqrt(np.sum(delta * delta, axis=2))
    return np.floor(euclidean + 0.5).astype(np.int64)


def tour_length(tour: list[int] | np.ndarray, distances: np.ndarray) -> int:
    route = np.asarray(tour, dtype=int)
    return int(distances[route, np.roll(route, -1)].sum())


def canonical_tour(tour: list[int]) -> list[int]:
    """Rotate to node 0 and choose a stable direction for presentation."""
    index = tour.index(0)
    forward = tour[index:] + tour[:index]
    reverse = [forward[0], *reversed(forward[1:])]
    return min(forward, reverse)


def two_opt(tour: list[int], distances: np.ndarray, max_passes: int = 20) -> list[int]:
    """Deterministic first-improvement 2-opt local search."""
    route = tour.copy()
    n = len(route)
    for _ in range(max_passes):
        improved = False
        for i in range(n - 1):
            a, b = route[i], route[(i + 1) % n]
            for k in range(i + 2, n if i else n - 1):
                c, d = route[k], route[(k + 1) % n]
                if distances[a, c] + distances[b, d] < distances[a, b] + distances[c, d]:
                    route[i + 1 : k + 1] = reversed(route[i + 1 : k + 1])
                    improved = True
        if not improved:
            break
    return route


def nearest_neighbor(start: int, distances: np.ndarray) -> list[int]:
    remaining = set(range(len(distances)))
    remaining.remove(start)
    route = [start]
    while remaining:
        current = route[-1]
        next_node = min(remaining, key=lambda node: (distances[current, node], node))
        route.append(next_node)
        remaining.remove(next_node)
    return route


def elapsed_seconds(start_ns: int, current_ns: int) -> float:
    return (current_ns - start_ns) / 1_000_000_000
