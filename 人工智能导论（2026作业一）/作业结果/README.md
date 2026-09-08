# 作业一：三种算法求解 TSP

本目录是作业一的完整可复现实验成果。OR-Tools 使用 Python 实现，遗传算法（GA）与蚁群算法（ACO）使用 C++ 多文件工程实现。

C++ 工程只使用 C++20 标准库，不依赖任何第三方 C++ 库。

## WSL 环境

```bash
python3 -m venv ~/.venvs/introduction-to-artificial-intelligence
~/.venvs/introduction-to-artificial-intelligence/bin/python -m pip install -r requirements.txt
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

程序固定随机种子，并依照 TSPLIB `EUC_2D` 规则计算整数距离。默认配置中，OR-Tools 每个实例最多运行 20 秒，GA 和 ACO 每个实例均远低于作业要求的 2 分钟上限。

## 目录

```text
作业结果/
├── src/cpp/             # GA、ACO 的 C++ 多文件工程
├── src/*.py             # Python OR-Tools 与绘图代码
├── results/             # JSON、CSV 和逐次改进日志
├── figures/             # 路线图、收敛图和运行过程截图
├── 实验报告.md
└── README.md
```
