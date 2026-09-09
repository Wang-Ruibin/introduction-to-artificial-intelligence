"""Aggregate the recorded LLM solving sessions into result rows.

The sessions in results/llm_session/<instance>.jsonl were produced by a real
large language model (GLM, driving the ZCode agent) interacting with
src/llm_harness.py: the model made every search decision (tour construction
and every improvement move); the harness only scored proposals and printed
edge diagnostics. This module replays the logs so the report pipeline can
treat the LLM like any other solver.

Runtime is the wall-clock span between the first and last recorded
interaction of the session; the model's thinking time between interactions is
included for multi-round sessions, while single-round sessions only measure
the one evaluator call (disclosed in the report).
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from tsp_utils import distance_matrix, load_tsplib, tour_length

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ASSIGNMENT = ROOT.parent
SESSION_DIR = ROOT / "results" / "llm_session"

MODEL = "GLM (builtin:bigmodel-coding-plan/GLM-5.3) via ZCode agent"


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value)


def load_llm_result(instance: str) -> dict:
    """Replay the session log for one instance and build a result row."""
    path = SESSION_DIR / f"{instance}.jsonl"
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    scored = [(parse_timestamp(r["utc"]), r) for r in records if r.get("command") == "score"]

    _, coordinates = load_tsplib(ASSIGNMENT / f"{instance}.tsp")
    distances = distance_matrix(coordinates)

    best_distance = None
    best_tour = None
    progress = []
    for step, (stamp, record) in enumerate(scored):
        for entry in record["results"]:
            if not entry.get("valid"):
                continue
            if best_distance is None or entry["distance"] < best_distance:
                best_distance = entry["distance"]
                best_tour = entry["tour_0based"]
        elapsed = (stamp - scored[0][0]).total_seconds()
        progress.append({"step": step, "distance": best_distance, "time_seconds": elapsed})

    assert best_tour is not None, f"no valid tours scored for {instance}"
    assert tour_length(best_tour, distances) == best_distance, f"distance mismatch for {instance}"
    runtime = max(progress[-1]["time_seconds"], 1.0)
    proposals = sum(len(r["results"]) for _, r in scored)
    return {
        "algorithm": "LLM",
        "language": f"Python scorer + {MODEL}",
        "tour": best_tour,
        "distance": best_distance,
        "runtime_seconds": round(runtime, 3),
        "progress": progress,
        "parameters": {
            "protocol": "LLM decides, program scores (llm_harness.py)",
            "model": MODEL,
            "rounds": len(scored),
            "proposals": proposals,
            "note": "GLM had prior exposure to other solvers' best routes in this workspace; "
                    "see the report for the disclosure.",
        },
    }


def load_all(instances: list[str]) -> list[dict]:
    return [load_llm_result(name) for name in instances]


if __name__ == "__main__":
    for name in ("berlin8", "berlin52", "pr76"):
        row = load_llm_result(name)
        print(f"{name}: distance={row['distance']}, rounds={row['parameters']['rounds']}, "
              f"runtime={row['runtime_seconds']}s")
