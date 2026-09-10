# Introduction to Artificial Intelligence

Reproducible coursework, experiments, and the future course project for *Introduction to Artificial Intelligence*.

[![License: MIT](https://img.shields.io/badge/License-MIT-0f766e.svg)](LICENSE)
[![Python 3.14](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![C++20](https://img.shields.io/badge/C%2B%2B-20-00599C?logo=cplusplus&logoColor=white)](https://en.cppreference.com/)
[![GitHub stars](https://img.shields.io/github/stars/Wang-Ruibin/introduction-to-artificial-intelligence?style=flat&logo=github)](https://github.com/Wang-Ruibin/introduction-to-artificial-intelligence/stargazers)

**English** · [简体中文](README.zh-CN.md)

[Explore Assignment 1](./人工智能导论（2026作业一）/) · [Read the experiment report](./人工智能导论（2026作业一）/作业结果/实验报告.md)

> If this repository helps with your study or experiments, consider giving it a ⭐. It helps others discover the project.

## Why this repository

- Keeps every assignment, dataset, implementation, report, and visualization in one versioned place.
- Favors reproducible experiments: fixed random seeds, explicit dependencies, machine-readable results, and validation scripts.
- Preserves the intent of each method instead of hiding all work behind one solver.
- Will grow with the course and eventually include the final course project.

## Quick start

### Prerequisites

- Ubuntu/Linux or WSL2
- Python 3.14+
- A C++20 compiler and GNU Make

### Clone and install

```bash
git clone git@github.com:Wang-Ruibin/introduction-to-artificial-intelligence.git
cd introduction-to-artificial-intelligence

python3 -m venv ~/.venvs/introduction-to-artificial-intelligence
~/.venvs/introduction-to-artificial-intelligence/bin/python -m pip install \
  -r "人工智能导论（2026作业一）/作业结果/requirements.txt"
```

### Build, run, and verify Assignment 1

```bash
cd "人工智能导论（2026作业一）/作业结果"

make
make test
~/.venvs/introduction-to-artificial-intelligence/bin/python src/run_experiments.py
~/.venvs/introduction-to-artificial-intelligence/bin/python src/validate_results.py
```

## Current results

Assignment 1 solves the `berlin8`, `berlin52`, and `pr76` TSPLIB instances. The recorded runs use the TSPLIB `EUC_2D` distance rule.

| Instance | Known optimum | OR-Tools | Genetic algorithm | Ant colony optimization | Recorded LLM session |
|---|---:|---:|---:|---:|---:|
| berlin8 | 2,551 | 2,551 | 2,551 | 2,551 | 2,551 |
| berlin52 | 7,542 | 7,542 | 7,542 | 7,542 | 7,542 |
| pr76 | 108,159 | 108,159 | 108,159 | 108,159 | 108,159* |

`*` The final `pr76` LLM round consulted the GA result. The report explicitly separates its independently reached result from the assisted final result.

## Implementations

| Method | Language | Main idea |
|---|---|---|
| OR-Tools | Python | CP-SAT Hamiltonian circuit model with an optimality status check |
| Genetic algorithm | C++20 standard library | Memetic GA with order crossover, mutation, restart, 2-opt, and or-opt |
| Ant colony optimization | C++20 standard library | MAX-MIN ant system with bounded pheromones and local search |
| Large-language-model session | LLM + Python scorer | Recorded model decisions evaluated with a deterministic distance harness |

The C++ implementation has no third-party C++ dependencies.

## Repository layout

```text
.
├── 人工智能导论（2026作业一）/
│   ├── 作业说明.txt
│   ├── berlin8.tsp, berlin52.tsp, pr76.tsp
│   └── 作业结果/
│       ├── src/          # Solver, experiment, and validation source
│       ├── results/      # JSON/CSV results and recorded LLM scoring sessions
│       ├── figures/      # Route, progress, and run-summary figures
│       └── 实验报告.md
├── README.md
└── README.zh-CN.md
```

## Reproducibility and scope

- GA and ACO use a fixed seed (`2026`) and enforce the assignment time limits.
- Generated routes are independently rescored; validation checks all cities, distances, and required figures.
- LLM logs contain scoring interactions, not hidden model reasoning. Their limitations and context contamination are disclosed in the report.
- Runtime measurements depend on the machine and should not be treated as universal benchmarks.
- This is an evolving course repository. Interfaces and directory contents may change as new assignments are added.

## Contributing

Corrections, reproducibility reports, and focused improvements are welcome through GitHub issues or pull requests. Please keep changes scoped and include evidence for result or performance claims.

## License

Source code is available under the [MIT License](LICENSE). Course descriptions, datasets, reports, and generated results may remain subject to their educational or upstream terms.
