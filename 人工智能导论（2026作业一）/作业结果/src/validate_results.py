"""Validate every generated route and the completeness of deliverables."""
from __future__ import annotations

import itertools
import json
from pathlib import Path

from tsp_utils import distance_matrix, load_tsplib, tour_length

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ASSIGNMENT = ROOT.parent

KNOWN_OPTIMA = {"berlin8": 2551, "berlin52": 7542, "pr76": 108159}
# The last pr76 LLM round consulted the same-workspace GA optimum; the report
# discloses this, so validation checks the recorded value without implying a blind run.
LLM_EXPECTED = {"berlin8": 2551, "berlin52": 7542, "pr76": 108159}


def brute_force_optimum(distances) -> int:
    n = len(distances)
    return min(tour_length([0, *order], distances) for order in itertools.permutations(range(1, n)))


def main() -> None:
    payload = json.loads((ROOT / "results/results.json").read_text(encoding="utf-8"))
    rows = payload["results"]
    assert len(rows) == 12, f"Expected 12 results, got {len(rows)}"
    for row in rows:
        _, coordinates = load_tsplib(ASSIGNMENT / f"{row['instance']}.tsp")
        distances = distance_matrix(coordinates)
        tour = [int(node) - 1 for node in row["route"].split(" -> ")[:-1]]
        assert sorted(tour) == list(range(len(coordinates))), f"Invalid tour: {row['instance']}/{row['algorithm']}"
        assert tour_length(tour, distances) == row["distance"], f"Distance mismatch: {row}"
        expected = LLM_EXPECTED[row["instance"]] if row["algorithm"] == "LLM" else KNOWN_OPTIMA[row["instance"]]
        assert row["distance"] == expected, (
            f"{row['instance']}/{row['algorithm']} distance {row['distance']} != expected {expected}")
        stem = f"{row['instance']}_{row['algorithm'].lower().replace('-', '_')}"
        for suffix in ("route", "progress", "run"):
            assert (ROOT / "figures" / f"{stem}_{suffix}.png").is_file(), f"Missing figure: {stem}_{suffix}"

    _, berlin8 = load_tsplib(ASSIGNMENT / "berlin8.tsp")
    exhaustive = brute_force_optimum(distance_matrix(berlin8))
    assert exhaustive == KNOWN_OPTIMA["berlin8"], f"berlin8 brute force {exhaustive} != expected"
    print("Validated 12 routes and 36 generated figures")
    print(f"berlin8 optimum {exhaustive} independently verified by exhaustive enumeration")


if __name__ == "__main__":
    main()
