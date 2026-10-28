# generative_graph — 从四维概念空间到生成图

## 一句话

把 B−C 概念作为节点，把 G2 的共现边作为图结构，把四维欧氏距离作为边权，
跑原论文的演化 + 压缩/迁移检测。**这是原论文的翻版，只是 `sim` 换成了 `d`。**

## 为什么是 B−C

- B = 最小频繁项集（结构稳定的单元）
- C = 角色一致的项集（功能单一的单元）
- **B−C = 结构稳定但角色混合**——这正是"毛边多"的概念。

"毛边多"意味着它们没有被压成定型的砖块，它们有富余的连接面，
**可以连接起来形成新概念**。用 C（毛边少）的话，连起来也只是把两块砖拼在一起，
没有化学反应；用 B−C（毛边多），连起来才有新东西。

## 三步

1. **节点** = B−C 概念
2. **边结构** = G2 共现边（非欧，所以迁移有意义）
3. **边权** = 四维欧氏距离 `d_ij = √(Δb² + Δc_norm² + Δg1_norm² + Δg2_norm²)`

## 与原论文的对应

| 原论文 | 本项目 |
|--------|--------|
| 全连接能量图 | B−C 稀疏共现图 |
| `E_ij = α(1−sim) + β/(1+H) + γ·div` | `E_ij = d_ij`（四维距离） |
| 能量下降 | 距离下降（趋近） |
| 压缩：Φ = 内部能量 / 外部能量 | 压缩：Φ = 外部距离 / 内部距离 |
| 迁移：`E_az + E_zb < E_ab − Δ` | 迁移：`d_az + d_zb < d_ab × (1−ε)` |

## 输入

- `results/four_dim_vectors/config_{X}/scale{N}.csv` — 四维坐标
- `results/endo_result/scale{N}/config_{X}/minsize_{K}/fixpoint_{B,C}/fixpoints.json` — B/C 集合
- `results/endo_result/raw_events_{X}/raw_compression_events.csv` — G2 边源

## 输出

- `results/generative_graph/config_{X}/scale{N}/`
  - `graph_nodes.csv` — 节点 + 四维坐标
  - `graph_edges.csv` — 边（weight = 四维距离，count = 共现次数）
  - `energy_history.csv` — 演化轨迹
  - `traversal_history.csv` — 遍历路径
  - `candidate_compressions.csv` — 压缩候选
  - `candidate_migrations.csv` — 迁移候选
  - `info.json` — 诊断信息
- `results/generative_graph/summary.csv` — 跨 config/scale 汇总

## 跑法

```bash
cd src/generative_graph
python run_generative.py
python run_generative.py --configs A --scales 51
```

## 一个观察点

B−C 图节点少（A@51 有 13 个，B@51 有 7 个，C@51 有 15 个），
边更少（因为要求两端都在 B−C 中，且要在 G2 中曾共现过）。

**规模小是特征，不是缺陷**——它对应"稳定核心有限"这件事。
如果压缩/迁移都为零，说明 B−C 内部确实没有足够密集的结构——这也是一种观察。

## 迁移的语义

在这个稀疏图上，`d(a,z) + d(z,b) < d(a,b)` 是可能的（G2 非欧），
所以迁移检测有意义。这是与"全连接欧氏图"的关键区别——如果图是全连接的，
三角不等式会保证路径永远不短于直接边，迁移永远为零。
```