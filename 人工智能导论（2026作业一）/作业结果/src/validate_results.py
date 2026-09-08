"""Validate every generated route and the completeness of deliverables."""
from __future__ import annotations
import json
from pathlib import Path
from tsp_utils import distance_matrix, load_tsplib, tour_length

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ASSIGNMENT = ROOT.parent

def main() -> None:
    payload = json.loads((ROOT / "results/results.json").read_text(encoding="utf-8"))
    rows = payload["results"]
    assert len(rows) == 9, f"Expected 9 results, got {len(rows)}"
    for row in rows:
        _, coordinates = load_tsplib(ASSIGNMENT / f"{row['instance']}.tsp")
        distances = distance_matrix(coordinates)
        tour = [int(node) - 1 for node in row["route"].split(" -> ")[:-1]]
        assert sorted(tour) == list(range(len(coordinates))), f"Invalid tour: {row['instance']}/{row['algorithm']}"
        assert tour_length(tour, distances) == row["distance"], f"Distance mismatch: {row}"
        stem = f"{row['instance']}_{row['algorithm'].lower().replace('-', '_')}"
        for suffix in ("route", "progress", "run"):
            assert (ROOT / "figures" / f"{stem}_{suffix}.png").is_file(), f"Missing figure: {stem}_{suffix}"
    print("Validated 9 routes and 27 generated figures")

if __name__ == "__main__":
    main()
