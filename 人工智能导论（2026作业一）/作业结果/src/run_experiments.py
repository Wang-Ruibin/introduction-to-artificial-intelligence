"""Run all assignment experiments and generate tables, logs, and figures."""

from __future__ import annotations

import csv
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import ortools

from ortools_solver import SolverResult, solve_ortools
from tsp_utils import distance_matrix, load_tsplib


HERE = Path(__file__).resolve().parent
RESULT_ROOT = HERE.parent
ASSIGNMENT_ROOT = RESULT_ROOT.parent
RESULTS_DIR = RESULT_ROOT / "results"
FIGURES_DIR = RESULT_ROOT / "figures"
INSTANCES = ["berlin8", "berlin52", "pr76"]
CPP_EXECUTABLE = RESULT_ROOT / "build" / "tsp_metaheuristics"

def solve_cpp(instance_path: Path, algorithm: str) -> SolverResult:
    temporary = RESULTS_DIR / f".{instance_path.stem}_{algorithm}.json"
    completed = subprocess.run([str(CPP_EXECUTABLE), str(instance_path), algorithm, str(temporary)],
                               check=True, text=True, capture_output=True)
    print(completed.stdout.strip(), flush=True)
    payload = json.loads(temporary.read_text(encoding="utf-8"))
    temporary.unlink()
    return SolverResult(**payload)


def plot_route(name: str, coordinates: np.ndarray, result: SolverResult) -> None:
    route = np.asarray(result.tour + [result.tour[0]])
    fig, ax = plt.subplots(figsize=(8, 6), dpi=160)
    ax.plot(coordinates[route, 0], coordinates[route, 1], "o-", color="#2563eb", linewidth=1.4, markersize=3.8)
    for node, (x, y) in enumerate(coordinates):
        ax.annotate(str(node + 1), (x, y), xytext=(4, 4), textcoords="offset points", fontsize=7)
    ax.set_title(f"{name} — {result.algorithm} — distance {result.distance}")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_aspect("equal", adjustable="datalim")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / f"{name}_{result.algorithm.lower().replace('-', '_')}_route.png")
    plt.close(fig)


def plot_progress(name: str, result: SolverResult) -> None:
    steps = [point["step"] for point in result.progress]
    values = [point["distance"] for point in result.progress]
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=160)
    ax.plot(steps, values, color="#dc2626", linewidth=1.6)
    ax.set_title(f"{name} — {result.algorithm} optimization progress")
    ax.set_xlabel("solution / generation / iteration")
    ax.set_ylabel("best tour distance")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / f"{name}_{result.algorithm.lower().replace('-', '_')}_progress.png")
    plt.close(fig)


def render_run_capture(name: str, result: SolverResult) -> None:
    lines = [
        "$ python run_experiments.py",
        f"[instance]  {name}",
        f"[algorithm] {result.algorithm}",
        f"[status]    completed",
        f"[distance]  {result.distance}",
        f"[runtime]   {result.runtime_seconds:.6f} s",
        "[route]     " + " -> ".join(str(node + 1) for node in result.tour + [result.tour[0]]),
    ]
    fig = plt.figure(figsize=(12, 3.5), dpi=160, facecolor="#111827")
    fig.text(0.03, 0.93, "\n".join(lines), va="top", family="monospace", fontsize=10, color="#d1fae5", wrap=True)
    fig.savefig(FIGURES_DIR / f"{name}_{result.algorithm.lower().replace('-', '_')}_run.png", facecolor=fig.get_facecolor())
    plt.close(fig)


def write_report(rows: list[dict[str, object]]) -> None:
    best_by_instance = {name: min((r for r in rows if r["instance"] == name), key=lambda r: int(r["distance"])) for name in INSTANCES}
    report = [
        "# 人工智能导论 2026 作业一实验报告",
        "",
        "## 1. 实验目标",
        "",
        "分别使用 OR-Tools、遗传算法（GA）和蚁群算法（ACO）求解 berlin8、berlin52、pr76 三个 TSP 实例，比较求解距离和运行时间，并给出最优路线及可视化结果。",
        "",
        "## 2. 方法与统一口径",
        "",
        "- 距离遵循 TSPLIB `EUC_2D`：两点欧氏距离按 `floor(d + 0.5)` 取整，闭合路线包含末节点回到起点。",
        "- OR-Tools 使用 `PATH_CHEAPEST_ARC` 初始解和 `GUIDED_LOCAL_SEARCH`，每例上限 20 秒。",
        "- GA 使用顺序交叉、锦标赛选择、区间反转变异、精英保留和 2-opt 局部改进。",
        "- ACO 使用信息素挥发、启发函数、精英信息素强化，并以 2-opt 改进最终路线。",
        "- GA 与 ACO 固定随机种子 2026；耗时使用 `perf_counter` 在同一次运行中测量。",
        "",
        "## 3. 实验环境",
        "",
        f"- Python: `{platform.python_version()}`",
        f"- OR-Tools: `{ortools.__version__}`",
        f"- 平台: `{platform.platform()}`",
        "",
        "## 4. 实验结果",
        "",
        "| 实例 | 算法 | 实现语言 | 距离 | 运行时间（秒） |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        report.append(f"| {row['instance']} | {row['algorithm']} | {row['language']} | {row['distance']} | {float(row['runtime_seconds']):.6f} |")
    report += ["", "各实例在本次实验中获得的最短路线（节点编号从 1 开始）：", ""]
    for name in INSTANCES:
        row = best_by_instance[name]
        report += [
            f"### {name}",
            "",
            f"- 最短距离：**{row['distance']}**",
            f"- 获得算法：**{row['algorithm']}**",
            f"- 路线：`{row['route']}`",
            "",
            f"![{name} best route](figures/{name}_{str(row['algorithm']).lower().replace('-', '_')}_route.png)",
            "",
        ]
    report += [
        "## 5. 过程记录与可视化",
        "",
        "每个“算法 × 实例”都生成三类证据：`*_run.png` 为运行过程截图，`*_progress.png` 为优化过程曲线，`*_route.png` 为最终路线图。原始逐步数据保存在 `results/progress.json`，可用于复核或重新绘图。",
        "",
        "## 6. 结论",
        "",
        "OR-Tools 的引导式局部搜索在固定时限内提供稳定的高质量基线；GA 和 ACO 能清楚展示群体智能算法逐步收敛的过程。启发式算法结果不等同于数学上的最优性证明，因此本报告把“最优”限定为本次三种算法运行结果中的最短路线。",
        "",
        "## 7. 复现说明",
        "",
        "完整命令见本目录 `README.md`。再次运行会覆盖 `results/` 与 `figures/` 中同名生成文件，原始数据文件不会改变。",
    ]
    (RESULT_ROOT / "实验报告.md").write_text("\n".join(report) + "\n", encoding="utf-8")


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    all_progress: dict[str, list[dict[str, float | int]]] = {}
    print("TSP experiments started", flush=True)
    for instance in INSTANCES:
        name, coordinates = load_tsplib(ASSIGNMENT_ROOT / f"{instance}.tsp")
        distances = distance_matrix(coordinates)
        instance_path = ASSIGNMENT_ROOT / f"{instance}.tsp"
        solvers = (("OR-Tools (Python)", lambda: solve_ortools(distances)),
                   ("GA (C++)", lambda: solve_cpp(instance_path, "ga")),
                   ("ACO (C++)", lambda: solve_cpp(instance_path, "aco")))
        for solver_name, solver in solvers:
            print(f"Running {name} / {solver_name} ...", flush=True)
            result = solver()
            route_text = " -> ".join(str(node + 1) for node in result.tour + [result.tour[0]])
            row = {
                "instance": name,
                "algorithm": result.algorithm,
                "language": result.language,
                "distance": result.distance,
                "runtime_seconds": round(result.runtime_seconds, 6),
                "route": route_text,
                "parameters": result.parameters,
            }
            rows.append(row)
            all_progress[f"{name}/{result.algorithm}"] = result.progress
            plot_route(name, coordinates, result)
            plot_progress(name, result)
            render_run_capture(name, result)
            print(f"Completed: distance={result.distance}, runtime={result.runtime_seconds:.6f}s", flush=True)

    metadata = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "ortools": ortools.__version__,
        "distance_rule": "TSPLIB EUC_2D: floor(euclidean_distance + 0.5)",
        "results": rows,
    }
    (RESULTS_DIR / "results.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (RESULTS_DIR / "progress.json").write_text(json.dumps(all_progress, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (RESULTS_DIR / "summary.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["instance", "algorithm", "language", "distance", "runtime_seconds", "route"])
        writer.writeheader()
        writer.writerows({key: row[key] for key in writer.fieldnames} for row in rows)
    write_report(rows)
    print("All experiments completed", flush=True)


if __name__ == "__main__":
    main()
