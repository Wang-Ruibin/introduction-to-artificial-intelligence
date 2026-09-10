# 人工智能导论

用于保存《人工智能导论》课程作业、可复现实验以及后续课程设计的开源仓库。

[![许可证：MIT](https://img.shields.io/badge/License-MIT-0f766e.svg)](LICENSE)
[![Python 3.14](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![C++20](https://img.shields.io/badge/C%2B%2B-20-00599C?logo=cplusplus&logoColor=white)](https://zh.cppreference.com/)
[![GitHub Stars](https://img.shields.io/github/stars/Wang-Ruibin/introduction-to-artificial-intelligence?style=flat&logo=github)](https://github.com/Wang-Ruibin/introduction-to-artificial-intelligence/stargazers)

[English](README.md) · **简体中文**

[查看作业一](./人工智能导论（2026作业一）/) · [阅读实验报告](./人工智能导论（2026作业一）/作业结果/实验报告.md)

> 如果这个仓库对你的学习或实验有所帮助，欢迎点一个 ⭐，让更多人看到它。

## 为什么建立这个仓库

- 将每次作业、数据集、算法实现、报告和可视化统一纳入版本管理。
- 强调实验可复现性：固定随机种子、明确依赖、机器可读结果和验证脚本。
- 保留不同方法各自的求解过程，而不是把所有工作隐藏在单一求解器后面。
- 随课程持续更新，并最终加入课程设计。

## 快速开始

### 前置条件

- Ubuntu/Linux 或 WSL2
- Python 3.14+
- 支持 C++20 的编译器与 GNU Make

### 克隆与安装

```bash
git clone git@github.com:Wang-Ruibin/introduction-to-artificial-intelligence.git
cd introduction-to-artificial-intelligence

python3 -m venv ~/.venvs/introduction-to-artificial-intelligence
~/.venvs/introduction-to-artificial-intelligence/bin/python -m pip install \
  -r "人工智能导论（2026作业一）/作业结果/requirements.txt"
```

### 编译、运行并验证作业一

```bash
cd "人工智能导论（2026作业一）/作业结果"

make
make test
~/.venvs/introduction-to-artificial-intelligence/bin/python src/run_experiments.py
~/.venvs/introduction-to-artificial-intelligence/bin/python src/validate_results.py
```

## 当前结果

作业一求解 `berlin8`、`berlin52` 和 `pr76` 三个 TSPLIB 实例，记录结果统一采用 TSPLIB `EUC_2D` 距离规则。

| 实例 | 已知最优值 | OR-Tools | 遗传算法 | 蚁群算法 | 录制的 LLM 会话 |
|---|---:|---:|---:|---:|---:|
| berlin8 | 2,551 | 2,551 | 2,551 | 2,551 | 2,551 |
| berlin52 | 7,542 | 7,542 | 7,542 | 7,542 | 7,542 |
| pr76 | 108,159 | 108,159 | 108,159 | 108,159 | 108,159* |

`*` pr76 的最后一轮 LLM 求解参考了 GA 结果；报告中已明确区分其独立取得的结果与辅助后的最终结果。

## 实现方式

| 方法 | 语言 | 核心思路 |
|---|---|---|
| OR-Tools | Python | CP-SAT 哈密顿回路模型，并检查最优性状态 |
| 遗传算法 | C++20 标准库 | 顺序交叉、变异、重启、2-opt 与 or-opt 组成的模因算法 |
| 蚁群算法 | C++20 标准库 | 信息素有界并结合局部搜索的 MAX-MIN 蚁群系统 |
| 大语言模型会话 | LLM + Python 评分器 | 录制模型决策，由确定性距离程序进行评分 |

C++ 实现不依赖任何第三方 C++ 库。

## 仓库结构

```text
.
├── 人工智能导论（2026作业一）/
│   ├── 作业说明.txt
│   ├── berlin8.tsp, berlin52.tsp, pr76.tsp
│   └── 作业结果/
│       ├── src/          # 求解、实验与验证源码
│       ├── results/      # JSON/CSV 结果和 LLM 评分会话记录
│       ├── figures/      # 路线图、过程图与运行摘要图
│       └── 实验报告.md
├── README.md
└── README.zh-CN.md
```

## 可复现性与适用边界

- GA 与 ACO 使用固定随机种子 `2026`，并遵守作业运行时限。
- 所有生成路线都会独立复算；验证脚本检查城市完整性、距离和必需图片。
- LLM 日志记录评分交互，不包含模型的隐藏推理；相关局限与上下文污染已在报告中披露。
- 运行时间会随机器环境变化，不应视为通用性能基准。
- 本仓库将随课程继续更新，新增作业时接口和目录内容可能调整。

## 参与贡献

欢迎通过 GitHub Issue 或 Pull Request 提交纠错、复现结果和聚焦的改进。涉及结果或性能的声明请附带可核验证据。

## 许可证

源代码采用 [MIT License](LICENSE)。课程说明、数据集、实验报告和生成结果可能仍受教学要求或上游条款约束。
