# self_reflection — 自我推演循环

## 一句话

在不修改主仓库任何代码的前提下，把一阶系统的每一轮演化结果
（G2、不动点、四维、生成图、G3 压缩/迁移）抽象为反馈规则 K，
写回一阶系统的能耗公式、遍历偏好、压缩/迁移判据，让下一轮演化
"记住"上一轮的推演经验。

## 为什么单独放一个文件夹

- 主仓库只做"抓重点"，不做"概念生成图构造与降层级"；
- 本模块属于"概念生成"范畴，消费主仓库的 G3 结果；
- 通过包装 `RawRecordingUniverseEnhanced` 实现，不修改主仓库代码。

## 文件夹结构

```
src/self_reflection/
├── config_reflect.py      # 主循环配置（路径基于项目根）
├── state_io.py            # 保存 / 加载 universe 状态
├── feedback_rules.py      # 从 G3 抽象 K
├── energy_patch.py        # 能耗公式 / 遍历偏好修正
├── reflected_universe.py  # 包装 RawRecordingUniverseEnhanced
├── pipeline_adapter.py    # G2 + 压缩/迁移检测
├── reflect_loop.py        # 主循环
├── run_reflection.py      # 入口
└── README.md
```

## 路径约定

所有路径**统一解析到项目根下的 `results/`**（与 `src/` 同级）：

```
项目根/
├── src/
│   └── self_reflection/
└── results/
    └── self_reflection/
        ├── round_001/
        ├── round_002/
        └── ...
```

`config_reflect.py` 中：

- `PROJECT_ROOT = Path(__file__).resolve().parents[2]`
- `RESULTS_ROOT = PROJECT_ROOT / "results"`
- `output_root = RESULTS_ROOT / "self_reflection"`

`run_reflection.py --output_root` 若传相对路径，也一律解析为**项目根下**。

## 反馈规则 K 的数据结构

```json
{
  "version": 1,
  "source": {"n_clusters": 23, "n_migrations": 7},
  "edge_boosts": [
    {"u": "...", "v": "...", "delta": 0.18, "source": "cluster"}
  ],
  "preferred_paths": [
    {"path": ["...", "...", "..."], "improvement": 0.42}
  ],
  "cluster_patterns": [
    {"members": ["...", "...", "..."], "phi": 2.31}
  ]
}
```

- `edge_boosts`：每一对概念的边权额外降低量（学习率乘 1 + delta）。
- `preferred_paths`：G3 中高 improvement 的路径模式。
- `cluster_patterns`：G3 中高 phi 的压缩簇模式。

## 三种反馈

| 反馈 | 作用点 | 机制 |
|------|--------|------|
| 能耗公式 | `record_edge_activation` | 学习率 × (1 + boost) |
| 遍历偏好 | `_random_traversal` | 按 (1/w) × (1+boost) 加权选邻居 |
| 判据 | `_detect_emergence` | 给匹配 G3 模式的事件打 `g3_matched` 标记 |

当前 G3 反馈不改变"保留/丢弃"的行为，只标记。后续可扩展为"只保留 g3_matched"。

## 输出目录

```
results/self_reflection/
├── round_001/
│   ├── universe_state/
│   │   ├── graph.pkl
│   │   ├── state.json
│   │   └── raw_compressions.csv
│   ├── g3/
│   │   ├── raw_compression_events.csv
│   │   └── g3_result.json
│   └── feedback_K.json
├── round_002/
│   └── ...
```

- 第一轮 `mode=original`，`feedback_K=null`。
- 后续 `mode=reflected`，加载上一轮 `universe_state` 和 `feedback_K`。

## 运行

```bash
cd src/self_reflection
CONFIG_METHOD=A python run_reflection.py --rounds 5 --interval 10000 --num_concepts 51
```

参数：

- `--rounds`：总轮数（默认 5）
- `--interval`：每轮迭代次数（默认 10000）
- `--num_concepts`：概念规模（默认 51）
- `--concept_config`：A / B / C
- `--output_root`：输出根目录（相对路径按项目根解析）
- `--random_seed`

## 接口预留

- `interval_iterations` 是固定间隔；可以在 `reflect_loop.py` 中用 `interval = f(G3)` 动态决定。
- 当前"记住"只改变遍历和边权；后续可以把"G3 模式匹配"作为压缩/迁移判据的硬条件。
- 当前 G3 只调现有的 `CompressionGraphDetector`；后续可以接入不动点、四维、生成图等更下游的流程。

## 与前面工作的仓库的边界

- 前仓库只做"抓重点"：`endo_concept` 输出不动点与结构化定义。
- `self_reflection` 消费这些输出，做"概念生成 + 降层级 + 反馈"。
- 两个模块可以独立运行；`self_reflection` 也可以作为未来概念生成项目的入口。