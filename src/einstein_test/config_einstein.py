# -*- coding: utf-8 -*-
"""爱因斯坦测试配置。"""

EINSTEIN_CONFIG = {
    # ---------- 环境 ----------
    "network_seed": 42,
    "iterations": 10000,
    "detection_interval": 100,

    # ---------- 不动点检测 ----------
    # 三种方法都跑
    "fixpoint_methods": ["A", "B", "C"],
    "minsize": 1,

    # ---------- 生成图 ----------
    "concept_pools": ["B", "C", "B_minus_C"],
    "use_normalized": True,
    "gen_iterations": 3000,
    "gen_learning_rate": 0.1,
    "gen_forgetting_rate": 0.002,
    "gen_forget_interval": 10,
    "gen_random_walk_prob": 0.3,
    "gen_max_walk_length": 4,
    "compression_phi_threshold": 1.5,
    "min_cluster_size": 3,
    "max_cluster_size": 8,
    "migration_epsilon": 0.1,

    # ---------- 输出 ----------
    "output_root": "results/einstein_test",
}