"""LLM solving harness for Assignment 1.

Protocol: a large language model (GLM, driving this agent) makes every search
decision; this harness only *scores* proposals and reports neutral diagnostics
(edge lengths). No move is ever proposed by the harness. Every interaction is
appended to results/llm_session/<instance>.jsonl so the full session can be
audited and replayed.

Commands (node ids are 1-based, as in the TSPLIB files):
  coords <instance>                     print the coordinate table
  score <instance> [--label TEXT]       read tours from stdin (one per line,
                                        ids separated by spaces or '-'), print
                                        the EUC_2D length of each closed tour
  inspect <instance>                    read one tour from stdin, print its
                                        edges sorted by length (longest first)
  dist <instance>                       read pairs from stdin (one per line,
                                        "a b"), print each EUC_2D distance
  best <instance>                       print the best valid tour so far
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from tsp_utils import distance_matrix, load_tsplib, tour_length

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ASSIGNMENT = ROOT.parent
SESSION_DIR = ROOT / "results" / "llm_session"


def now() -> float:
    return time.time()


def log_interaction(instance: str, command: str, payload: dict) -> None:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    record = {"utc": datetime.now(timezone.utc).isoformat(), "command": command, **payload}
    with (SESSION_DIR / f"{instance}.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def parse_tour(line: str, n: int) -> list[int]:
    ids = [int(token) for token in line.replace("-", " ").split()]
    tour = [node - 1 for node in ids]
    if sorted(tour) != list(range(n)):
        raise ValueError(f"tour is not a permutation of 1..{n}: {line[:80]}")
    return tour


def load_instance(name: str):
    _, coordinates = load_tsplib(ASSIGNMENT / f"{name}.tsp")
    return coordinates, distance_matrix(coordinates)


def cmd_coords(instance: str) -> None:
    coordinates, _ = load_instance(instance)
    lines = [f"{node + 1:>3}  {x:9.2f} {y:9.2f}" for node, (x, y) in enumerate(coordinates)]
    text = "\n".join(lines)
    print(f"{instance} coordinates (id x y):\n{text}")
    log_interaction(instance, "coords", {"output": lines})


def cmd_score(instance: str, label: str) -> None:
    _, distances = load_instance(instance)
    n = len(distances)
    results = []
    for line in sys.stdin.read().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            tour = parse_tour(line, n)
        except ValueError as error:
            results.append({"input": line, "valid": False, "error": str(error)})
            continue
        results.append({"input": line, "valid": True, "distance": int(tour_length(tour, distances)),
                        "tour_0based": tour})
    for entry in results:
        if entry["valid"]:
            print(f"distance = {entry['distance']}")
        else:
            print(f"INVALID: {entry['error']}")
    log_interaction(instance, "score", {"label": label, "results": results})


def cmd_inspect(instance: str) -> None:
    _, distances = load_instance(instance)
    n = len(distances)
    line = sys.stdin.read().strip().splitlines()[0]
    tour = parse_tour(line, n)
    edges = []
    for i in range(n):
        a, b = tour[i], tour[(i + 1) % n]
        edges.append({"positions": [i + 1, i + 2 if i + 1 < n else 1],
                      "nodes": [a + 1, b + 1], "length": int(distances[a, b])})
    edges.sort(key=lambda e: -e["length"])
    print(f"total = {int(tour_length(tour, distances))}")
    for e in edges:
        print(f"edge {e['nodes'][0]:>3}-{e['nodes'][1]:<3} (pos {e['positions'][0]:>2}-{e['positions'][1]:<2})  length {e['length']}")
    log_interaction(instance, "inspect", {"tour": [node + 1 for node in tour],
                                          "total": int(tour_length(tour, distances)),
                                          "edges": edges})


def cmd_dist(instance: str) -> None:
    """Neutral distance lookup: the LLM may consult it like a distance table."""
    _, distances = load_instance(instance)
    pairs = []
    for line in sys.stdin.read().splitlines():
        fields = line.replace("-", " ").split()
        if not fields:
            continue
        a, b = int(fields[0]) - 1, int(fields[1]) - 1
        pairs.append({"a": a + 1, "b": b + 1, "distance": int(distances[a, b])})
    for entry in pairs:
        print(f"d({entry['a']},{entry['b']}) = {entry['distance']}")
    log_interaction(instance, "dist", {"pairs": pairs})


def cmd_best(instance: str) -> None:
    path = SESSION_DIR / f"{instance}.jsonl"
    best: dict | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        record = json.loads(raw)
        if record.get("command") != "score":
            continue
        for entry in record["results"]:
            if entry.get("valid") and (best is None or entry["distance"] < best["distance"]):
                best = entry
    if best is None:
        print("no scored tours yet")
        return
    print(f"best distance = {best['distance']}")
    print(" -> ".join(str(node + 1) for node in best["tour_0based"]))


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    command, instance = args[0], args[1]
    if command == "coords":
        cmd_coords(instance)
    elif command == "score":
        label = args[args.index("--label") + 1] if "--label" in args else ""
        cmd_score(instance, label)
    elif command == "inspect":
        cmd_inspect(instance)
    elif command == "dist":
        cmd_dist(instance)
    elif command == "best":
        cmd_best(instance)
    else:
        raise SystemExit(f"unknown command: {command}")


if __name__ == "__main__":
    main()
