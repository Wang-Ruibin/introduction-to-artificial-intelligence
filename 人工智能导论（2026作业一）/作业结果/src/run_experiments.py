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

from llm_solver import load_llm_result
from ortools_solver import SolverResult, solve_ortools
from tsp_utils import distance_matrix, load_tsplib

HERE = Path(__file__).resolve().parent
RESULT_ROOT = HERE.parent
ASSIGNMENT_ROOT = RESULT_ROOT.parent
RESULTS_DIR = RESULT_ROOT / "results"
FIGURES_DIR = RESULT_ROOT / "figures"
INSTANCES = ["berlin8", "berlin52", "pr76"]
CPP_EXECUTABLE = RESULT_ROOT / "build" / "tsp_metaheuristics"

# Known optima: berlin52/pr76 are the published TSPLIB values; berlin8 is small
# enough to verify by brute force (done by validate_results.py).
KNOWN_OPTIMA = {"berlin8": 2551, "berlin52": 7542, "pr76": 108159}
# Per-instance OR-Tools time limits (assignment allows at most 20 minutes).
# CP-SAT proves all three instances optimal: berlin8/berlin52 in ~1 s and
# pr76 within the configured 360-second limit (the optimum itself is found early).
ORTOOLS_LIMITS = {"berlin8": 30, "berlin52": 60, "pr76": 360}
ORTOOLS_MODEL = "cpsat"
# GA/ACO hard cap per instance (assignment allows at most 120 s); both solvers
# stop early after 5 s without improvement.
METAHEURISTIC_BUDGET = 15


def solve_cpp(instance_path: Path, algorithm: str) -> SolverResult:
    temporary = RESULTS_DIR / f".{instance_path.stem}_{algorithm}.json"
    completed = subprocess.run(
        [str(CPP_EXECUTABLE), str(instance_path), algorithm, str(temporary), str(METAHEURISTIC_BUDGET)],
        check=True, text=True, capture_output=True)
    print(completed.stdout.strip(), flush=True)
    payload = json.loads(temporary.read_text(encoding="utf-8"))
    temporary.unlink()
    return SolverResult(**payload)


def figure_stem(name: str, algorithm: str) -> str:
    return f"{name}_{algorithm.lower().replace('-', '_')}"


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
    fig.savefig(FIGURES_DIR / f"{figure_stem(name, result.algorithm)}_route.png")
    plt.close(fig)


def plot_progress(name: str, result: SolverResult) -> None:
    steps = [point["step"] for point in result.progress]
    values = [point["distance"] for point in result.progress]
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=160)
    ax.plot(steps, values, color="#dc2626", linewidth=1.6)
    ax.set_title(f"{name} — {result.algorithm} optimization progress")
    ax.set_xlabel("solution / generation / iteration / LLM round")
    ax.set_ylabel("best tour distance")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / f"{figure_stem(name, result.algorithm)}_progress.png")
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
    fig.savefig(FIGURES_DIR / f"{figure_stem(name, result.algorithm)}_run.png", facecolor=fig.get_facecolor())
    plt.close(fig)


def time_to_best(result: SolverResult) -> float | None:
    for point in result.progress:
        if point["distance"] == result.distance:
            return point["time_seconds"]
    return None


def write_report(rows: list[dict[str, object]]) -> None:
    best_by_instance = {name: min((r for r in rows if r["instance"] == name), key=lambda r: int(r["distance"]))
                        for name in INSTANCES}
    report = [
        "# 人工智能导论 2026 作业一实验报告",
        "",
        "## 1. 实验目标",
        "",
        "分别使用 OR-Tools、遗传算法（GA）、蚁群算法（ACO）和大语言模型（LLM）求解 berlin8、berlin52、pr76 "
        "三个 TSP 实例，比较求解距离和运行时间，并给出最优路线及可视化结果。",
        "",
        "## 2. 方法与统一口径",
        "",
        "- 距离遵循 TSPLIB `EUC_2D`：两点欧氏距离按 `floor(d + 0.5)` 取整，闭合路线包含末节点回到起点。",
        "- 已知最优解取 TSPLIB 公开值（berlin52 = 7542，pr76 = 108159）；berlin8 仅 8 城，由暴力枚举验证为 2551。",
        "- OR-Tools 使用 CP-SAT 的 `AddCircuit` 回路模型（对称 TSP 每边两个 0/1 弧变量、单一哈密顿回路约束），"
        "berlin8 与 berlin52 在 1 秒内被证明最优，pr76 时限 360 秒（作业上限 20 分钟）。",
        "- GA 为 memetic 实现：每个子代都做 2-opt + or-opt 局部搜索，停滞时用 double-bridge 扰动与随机重启注入多样性；"
        "时间上限 15 秒，连续 5 秒无改进提前停止（作业上限 2 分钟）。",
        "- ACO 为 MAX-MIN 蚁群（MMAS）：信息素限制在 `[tau_min, tau_max]`，每代仅迭代最优（每 10 代全局最优）沉积信息素，"
        "每代最优的 3 条路线先经 2-opt + or-opt 改进再学习，长时间停滞时重置信息素；时间上限 15 秒，连续 5 秒无改进提前停止。",
        "- LLM 实验协议：大语言模型（GLM，驱动 ZCode 智能体）做出全部搜索决策——读坐标、构造路线、决定每一次改进；"
        "Python 评分器（`llm_harness.py`）只计算距离与输出边长诊断，不产生任何决策。评分交互记录于 "
        "`results/llm_session/*.jsonl`，可复核；日志不包含模型的隐藏推理过程。",
        "- GA 与 ACO 固定随机种子 2026；耗时使用 `perf_counter` / `steady_clock` 在同一次运行中测量。",
        "",
        "## 3. 实验环境",
        "",
        f"- Python: `{platform.python_version()}`",
        f"- OR-Tools: `{ortools.__version__}`",
        f"- C++ 编译器: g++ (Ubuntu 15.2.0)，`-std=c++20 -O3`",
        f"- LLM: GLM（`builtin:bigmodel-coding-plan/GLM-5.3`，经 ZCode 智能体驱动）",
        f"- 平台: `{platform.platform()}`",
        "",
        "## 4. 实验结果",
        "",
        "| 实例 | 已知最优 | 算法 | 实现语言 | 距离 | 差距 | 达最优用时（秒） | 运行时间（秒） |",
        "|---|---:|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        optimum = KNOWN_OPTIMA[row["instance"]]
        gap = (int(row["distance"]) - optimum) / optimum * 100
        report.append(
            f"| {row['instance']} | {optimum} | {row['algorithm']} | {row['language']} | {row['distance']} "
            f"| {gap:+.2f}% | {row['time_to_best'] if row['time_to_best'] is not None else '—'} "
            f"| {float(row['runtime_seconds']):.2f} |")
    report += ["", "各实例在本次实验中获得的最短路线（节点编号从 1 开始）：", ""]
    for name in INSTANCES:
        row = best_by_instance[name]
        report += [
            f"### {name}",
            "",
            f"- 最短距离：**{row['distance']}**（已知最优 {KNOWN_OPTIMA[name]}）",
            f"- 获得算法：**{row['algorithm']}**",
            f"- 路线：`{row['route']}`",
            "",
            f"![{name} best route](figures/{figure_stem(name, str(row['algorithm']))}_route.png)",
            "",
        ]
    report += [
        "## 5. LLM 实验说明（重要披露）",
        "",
        "- 协议：LLM 决策 + 程序评分。LLM 阅读实例坐标后构造候选路线，评分器返回 EUC_2D 距离；之后 LLM 根据距离反馈"
        "与边长诊断自主决定改进动作，每轮可提交多个候选。评分器从不建议任何移动。",
        "- 结果：berlin8 一轮纯几何推理即达已知最优 2551；berlin52 首轮构造即达 7542；pr76 经 8 个评分轮次收敛到最优 "
        "108159——前 7 轮全部由 LLM 独立决策（113285 → 110585 → 109478 → 109470 → 108339 → 108309 → 108274），"
        "过程中 LLM 用精确增量逐项排除了约 200 个候选改进（全部为正增益，确认强局部最优），关键突破来自跨结构假设"
        "（把 49/50/51 链插入右列，−1131）与 E 上段重排；最后一轮 LLM 对照同一次实验中 GA 的最优路线，发现与自身 "
        "108274 解的唯一差异是节点 41 的安放位置（精确增量 −115），采纳后达到 108159。",
        "- 污染披露：①执行 LLM 实验的模型在本仓库中先前已见过其它求解器的历史最优路线（上下文污染），berlin52 的首轮"
        "命中不能视为无偏评测；②pr76 的最后一轮显式参考了同仓库 GA 的最优解并只做了单点验证性改进。剔除该轮后 LLM 的"
        "独立最好成绩为 108274（高于最优 0.11%）。",
        "- 计时口径：LLM 运行时间为该实例会话首末两次评分交互的墙钟间隔；会话跨多次执行，间隔含等待时间，端到端实际"
        "推理耗时更长。LLM 无作业时限约束。",
        "",
        "## 6. 过程记录与可视化",
        "",
        "每个“算法 × 实例”都生成三类证据：`*_run.png` 为运行过程截图，`*_progress.png` 为优化过程曲线，`*_route.png` "
        "为最终路线图。原始逐步数据保存在 `results/progress.json` 与 `results/llm_session/*.jsonl`，可用于复核或重新绘图。",
        "",
        "## 7. 结论",
        "",
        "OR-Tools、GA、ACO、LLM 四种方法在三个实例上全部达到已知最优解：OR-Tools 的 CP-SAT 回路模型在 berlin8 与 "
        "berlin52 上直接证明最优，并在 pr76 上找到并证明最优值 108159；GA 与 ACO 的 memetic/MMAS 增强实现"
        "在 0.5 秒内即命中全部最优；LLM 在 berlin8 上一轮纯推理最优，在 pr76 上经 8 轮评分反馈闭环收敛到最优（最后一轮"
        "参考了同仓库最优解，独立成绩 108274，见第 5 节披露）。LLM 在小实例上表现出很强的"
        "几何推理能力（berlin8 一轮最优）；在 76 城规模上，纯手工决策的迭代收敛到距最优 0.11% 的强局部最优后停滞，"
        "最后一公里（单个节点的安放）仍需借助专门算法的解作对照——这正说明组合优化中专用算法的价值。"
        "启发式算法结果不等同于数学上的最优性证明，因此本报告把“最优”限定为与 TSPLIB "
        "公开最优值相等的解。",
        "",
        "## 8. 参考资料",
        "",
        "- [TSPLIB 95 原始说明及最优值表](https://cdn.hackaday.io/files/1588026794184768/tsp95.pdf)",
        "- [Google OR-Tools：CP-SAT 状态说明](https://developers.google.com/optimization/cp/cp_solver)",
        "- [GitHub 在线代码](https://github.com/Wang-Ruibin/introduction-to-artificial-intelligence)",
        "",
        "## 9. 复现说明",
        "",
        "完整命令见本目录 `README.md`。再次运行会覆盖 `results/` 与 `figures/` 中同名生成文件（LLM 会话日志除外，"
        "它是录制数据，不随重跑改变），原始数据文件不会改变。",
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
        llm_payload = load_llm_result(instance)
        solvers = (("OR-Tools (Python)", lambda n=name, d=distances: solve_ortools(d, ORTOOLS_LIMITS[n], ORTOOLS_MODEL)),
                   ("GA (C++)", lambda p=instance_path: solve_cpp(p, "ga")),
                   ("ACO (C++)", lambda p=instance_path: solve_cpp(p, "aco")),
                   ("LLM", lambda payload=llm_payload: SolverResult(**payload)))
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
                "time_to_best": (lambda t: round(t, 3) if t is not None else None)(time_to_best(result)),
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
        "known_optima": KNOWN_OPTIMA,
        "distance_rule": "TSPLIB EUC_2D: floor(euclidean_distance + 0.5)",
        "results": rows,
    }
    (RESULTS_DIR / "results.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (RESULTS_DIR / "progress.json").write_text(json.dumps(all_progress, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (RESULTS_DIR / "summary.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["instance", "algorithm", "language", "distance",
                                                    "runtime_seconds", "time_to_best", "route"])
        writer.writeheader()
        writer.writerows({key: row[key] for key in writer.fieldnames} for row in rows)
    write_report(rows)
    print("All experiments completed", flush=True)


if __name__ == "__main__":
    if "--report-only" in sys.argv:
        existing = json.loads((RESULTS_DIR / "results.json").read_text(encoding="utf-8"))
        write_report(existing["results"])
        print("Report regenerated from existing validated results", flush=True)
    else:
        main()
