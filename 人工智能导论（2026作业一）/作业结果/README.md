# 作业一：四种方法求解 TSP

本目录是作业一的完整可复现实验成果。OR-Tools 使用 Python 实现，遗传算法（GA）与蚁群算法（ACO）使用 C++ 多文件工程实现，大语言模型（LLM）实验由 GLM 模型经录制会话完成。

C++ 工程只使用 C++20 标准库，不依赖任何第三方 C++ 库。

## WSL 环境

```bash
python3 -m venv ~/.venvs/introduction-to-artificial-intelligence
~/.venvs/introduction-to-artificial-intelligence/bin/python -m pip install -r \
  "人工智能导论（2026作业一）/作业结果/requirements.txt"
```

## 编译与测试 C++ 算法

```bash
cd "人工智能导论（2026作业一）/作业结果"
make
make test
```

## 一键复现

在仓库根目录执行：

```bash
cd "人工智能导论（2026作业一）/作业结果"
~/.venvs/introduction-to-artificial-intelligence/bin/python src/run_experiments.py
~/.venvs/introduction-to-artificial-intelligence/bin/python src/validate_results.py
```

程序固定随机种子，并依照 TSPLIB `EUC_2D` 规则计算整数距离。默认配置中，OR-Tools 使用 CP-SAT `AddCircuit` 回路模型（berlin8 与 berlin52 在 1 秒内证明最优，pr76 时限 360 秒，均远低于作业 20 分钟上限），GA 与 ACO 每实例时间上限 15 秒、连续 5 秒无改进即提前停止，均低于作业要求的 2 分钟上限。

## 大语言模型实验

LLM 实验采用“LLM 决策 + 程序评分”协议：模型阅读坐标、构造路线并决定每一次改进，`src/llm_harness.py` 只负责计算距离与输出边长诊断。评分交互记录在 `results/llm_session/*.jsonl`；这些日志不包含模型的隐藏推理过程。`src/llm_solver.py` 把录制会话聚合为结果行。复现管线会把 LLM 结果与三种算法并列汇总。重新运行 LLM 会话需要大语言模型参与，因此管线使用录制数据。

代码在线版本：<https://github.com/Wang-Ruibin/introduction-to-artificial-intelligence>

## 目录

```text
作业结果/
├── src/cpp/             # GA、ACO 的 C++ 多文件工程
├── src/*.py             # OR-Tools、LLM 协议与绘图代码
├── results/             # JSON、CSV、逐次改进日志与 LLM 会话记录
├── figures/             # 路线图、收敛图和运行过程截图
├── requirements.txt     # Python 依赖版本
├── 实验报告.md
└── README.md
```
