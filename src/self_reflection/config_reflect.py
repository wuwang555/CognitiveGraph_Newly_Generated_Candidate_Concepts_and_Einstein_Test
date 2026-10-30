# -*- coding: utf-8 -*-
"""自我推演循环配置。

所有路径统一解析到项目根下的 results/（与 src/ 同级）。
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_ROOT = PROJECT_ROOT / "results"

REFLECTION_CONFIG = {
    # ---------- 主循环 ----------
    "max_rounds": 5,
    "interval_iterations": 10000,
    "detection_interval": 100,
    "num_concepts": 51,
    "concept_config": os.environ.get("CONFIG_METHOD", "A"),
    "individual_id": 0,

    # ---------- 模式 ----------
    "mode": "original",

    # ---------- 不动点检测（和主仓库 run_endo.py 的默认参数一致） ----------
    "fixpoint_method": "B",
    "minsize": 1,
    "fp_min_support": 0.02,
    "fp_max_itemset_size": 8,
    "lattice_min_support": 0.02,
    "lattice_min_set_size": 1,
    "lattice_max_itemset_size": 8,
    "role_min_stability": 0.7,
    "role_min_support": 0.005,
    "role_min_set_size": 1,
    "role_max_itemset_size": 8,
    "max_candidates": 200000,
    "max_fixpoints": 1000,
    "use_joint_criteria": True,
    "joint_support_min": 0.02,
    "joint_stability_min": 0.6,
    "use_stability_hard_threshold": False,
    "use_lower_bound_filter": True,

    # ---------- 四维坐标 ----------
    "use_normalized_4d": True,

    # ---------- 生成图演化（和主仓库 config_gen.py 一致） ----------
    "gen_iterations": 3000,
    "gen_learning_rate": 0.1,
    "gen_forgetting_rate": 0.002,
    "gen_forget_interval": 10,
    "gen_random_walk_prob": 0.3,
    "gen_max_walk_length": 4,
    "gen_compression_phi_threshold": 1.5,
    "gen_min_cluster_size": 3,
    "gen_max_cluster_size": 8,
    "gen_migration_epsilon": 0.1,

    # ---------- IO ----------
    "input_root": str(RESULTS_ROOT),
    "output_root": str(RESULTS_ROOT / "self_reflection"),

    # ---------- G3 抽象阈值 ----------
    "min_g3_phi": 1.5,
    "min_g3_improvement": 0.1,

    # ---------- 能耗修正强度 ----------
    "edge_boost_scale": 0.3,

    # ---------- 保存 ----------
    "save_pickle": True,
    "save_csv": True,

    "random_seed": 42,
    "verbose": True,
}