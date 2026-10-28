# -*- coding: utf-8 -*-
"""generative_graph 配置。"""

GENERATIVE_GRAPH_CONFIG = {
    # ---------- 输入 ----------
    "configs": ["A", "B", "C"],
    "scales": [51, 71, 91, 111],
    "minsize": 1,

    # ★ 输入根（上游数据所在位置）
    # 相对项目根；若上游数据也在项目根下 results/，就用这个
    "input_root": "results",

    # ★ 输出根（本模块写结果的位置）
    "output_root": "results/generative_graph",

    # ---------- 概念池 ----------
    "concept_pool": "B_minus_C",
    
    # ---------- 四维距离 ----------
    "use_normalized": True,

    # ---------- 演化 ----------
    "iterations": 3000,
    "learning_rate": 0.1,
    "forgetting_rate": 0.002,
    "forget_interval": 10,
    "random_walk_prob": 0.3,
    "max_walk_length": 4,

    # ---------- 压缩检测 ----------
    "compression_phi_threshold": 1.5,
    "min_cluster_size": 3,
    "max_cluster_size": 8,

    # ---------- 迁移检测 ----------
    "migration_epsilon": 0.1,

    # ---------- 其它 ----------
    "random_seed": 42,
    "verbose": True,
}